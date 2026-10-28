"""Explicit UTF-8 loaders and version-1 boundary validation."""

from __future__ import annotations

import json
from typing import cast

from contextdiff.models import KINDS, ROLES, Block, Kind, Role, Snapshot, WatchItem

MAX_INPUT_BYTES = 256 * 1024
MAX_BLOCKS = 200
MAX_CONTENT_CHARS = 50_000
MAX_WATCHES = 50
MAX_ID_CHARS = 128
MAX_LABEL_CHARS = 200
MAX_WATCH_TEXT_CHARS = 500
MAX_NOTE_CHARS = 500


class SnapshotValidationError(ValueError):
    """Safe to display: describes a field/limit without echoing supplied text."""


class _ObjectPairs(list):
    """Keep JSON object pairs until their paths and duplicates can be checked."""


def _fail(path: str, message: str) -> None:
    raise SnapshotValidationError(f"{path}: {message}")


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _decode(data: bytes) -> str:
    if not isinstance(data, bytes):
        _fail("input", "expected UTF-8 bytes")
    if len(data) > MAX_INPUT_BYTES:
        _fail("input", f"must be at most {MAX_INPUT_BYTES} UTF-8 bytes")
    try:
        return _normalize(data.decode("utf-8-sig"))
    except UnicodeDecodeError:
        raise SnapshotValidationError("input: must be valid UTF-8") from None


def _string(
    value: object, path: str, *, limit: int | None = None, nonblank: bool = False
) -> str:
    if not isinstance(value, str):
        _fail(path, "expected a string")
    value = cast(str, value)
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        _fail(path, "unpaired Unicode surrogates are not allowed")
    if limit is not None and len(value) > limit:
        _fail(path, f"must be at most {limit} characters")
    if nonblank and not value.strip():
        _fail(path, "must be nonblank")
    return value


def _materialize(value: object, path: str = "snapshot") -> object:
    if isinstance(value, _ObjectPairs):
        result: dict[str, object] = {}
        for key, child in value:
            # Unknown user keys are never included in diagnostics.
            _string(key, path)
            if key in result:
                _fail(path, "duplicate JSON object key; remove repeated keys")
            child_path = (
                (key if path == "snapshot" else f"{path}.{key}")
                if key
                in {
                    "schema_version",
                    "label",
                    "blocks",
                    "watchlist",
                    "id",
                    "kind",
                    "role",
                    "content",
                    "text",
                    "note",
                }
                else f"{path}.<unknown>"
            )
            result[key] = _materialize(child, child_path)
        return result
    if isinstance(value, list):
        return [_materialize(child, f"{path}[{i}]") for i, child in enumerate(value)]
    if isinstance(value, str):
        _string(value, path)
    return value


def _object(
    value: object, path: str, *, required: set[str], optional: set[str]
) -> dict[str, object]:
    if not isinstance(value, dict):
        _fail(path, "expected an object")
    value = cast(dict[str, object], value)
    if value.keys() - required - optional:
        _fail(path, "unknown field; use only the documented schema keys")
    for key in sorted(required - value.keys()):
        _fail(f"{path}.{key}", "required field is missing")
    return value


def _array(value: object, path: str, limit: int) -> list[object]:
    if not isinstance(value, list):
        _fail(path, "expected an array")
    value = cast(list[object], value)
    if len(value) > limit:
        _fail(path, f"must contain at most {limit} items")
    return value


def _id(value: object, path: str, seen: set[str]) -> str:
    identifier = _string(value, path, limit=MAX_ID_CHARS, nonblank=True)
    if identifier in seen:
        _fail(path, "duplicate ID; use a unique ID within this array")
    seen.add(identifier)
    return identifier


def _block(value: object, index: int, seen: set[str]) -> Block:
    path = f"blocks[{index}]"
    obj = _object(value, path, required={"id", "kind", "content"}, optional={"role"})
    identifier = _id(obj["id"], f"{path}.id", seen)
    kind = _string(obj["kind"], f"{path}.kind")
    if kind not in KINDS:
        _fail(f"{path}.kind", f"expected one of {', '.join(KINDS)}")
    role = None
    if "role" in obj:
        role = _string(obj["role"], f"{path}.role")
        if role not in ROLES:
            _fail(f"{path}.role", f"expected one of {', '.join(ROLES)}")
    content = _normalize(_string(obj["content"], f"{path}.content"))
    _string(content, f"{path}.content", limit=MAX_CONTENT_CHARS)
    return Block(identifier, cast(Kind, kind), content, cast(Role | None, role))


def _watch(value: object, index: int, seen: set[str]) -> WatchItem:
    path = f"watchlist[{index}]"
    obj = _object(value, path, required={"id", "text"}, optional={"note"})
    identifier = _id(obj["id"], f"{path}.id", seen)
    text = _string(
        obj["text"], f"{path}.text", limit=MAX_WATCH_TEXT_CHARS, nonblank=True
    )
    note = (
        _string(obj["note"], f"{path}.note", limit=MAX_NOTE_CHARS)
        if "note" in obj
        else None
    )
    return WatchItem(identifier, text, note)


def _reject_constant(_: str) -> None:
    _fail("input", "nonstandard JSON numbers are not allowed")


def load_json_snapshot(data: bytes) -> Snapshot:
    """Load only our JSON schema; malformed JSON never falls back to text."""
    text = _decode(data)
    try:
        value = _materialize(
            json.loads(
                text, object_pairs_hook=_ObjectPairs, parse_constant=_reject_constant
            )
        )
    except json.JSONDecodeError as error:
        raise SnapshotValidationError(
            f"input: invalid JSON at line {error.lineno}, column {error.colno}"
        ) from None
    except RecursionError:
        raise SnapshotValidationError("input: JSON nesting is too deep") from None
    except SnapshotValidationError:
        raise
    except ValueError:
        raise SnapshotValidationError(
            "input: JSON number exceeds parser limits"
        ) from None
    obj = _object(
        value,
        "snapshot",
        required={"schema_version", "blocks"},
        optional={"label", "watchlist"},
    )
    if type(obj["schema_version"]) is not int or obj["schema_version"] != 1:
        _fail("schema_version", "expected integer 1 (booleans are invalid)")
    label = (
        _string(obj["label"], "label", limit=MAX_LABEL_CHARS)
        if "label" in obj
        else None
    )
    block_ids: set[str] = set()
    watch_ids: set[str] = set()
    blocks = tuple(
        _block(item, i, block_ids)
        for i, item in enumerate(_array(obj["blocks"], "blocks", MAX_BLOCKS))
    )
    watches = tuple(
        _watch(item, i, watch_ids)
        for i, item in enumerate(
            _array(obj.get("watchlist", []), "watchlist", MAX_WATCHES)
        )
    )
    return Snapshot(blocks, label, watches)


def load_text_snapshot(data: bytes, *, label: str) -> Snapshot:
    """Wrap normalized text in a single document block, including empty text."""
    label = _string(label, "label", limit=MAX_LABEL_CHARS)
    content = _decode(data)
    _string(content, "blocks[0].content", limit=MAX_CONTENT_CHARS)
    return Snapshot((Block("document", "message", content),), label)
