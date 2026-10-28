import json
from dataclasses import FrozenInstanceError

import pytest

from contextdiff import SnapshotValidationError, load_json_snapshot, load_text_snapshot
from contextdiff.loaders import MAX_INPUT_BYTES


def encode(value):
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def document(**overrides):
    return {"schema_version": 1, "blocks": [], **overrides}


def block(**overrides):
    return {"id": "a", "kind": "message", "content": "", **overrides}


def watch(**overrides):
    return {"id": "w", "text": "phrase", **overrides}


def test_fixture_loads_immutable_without_collapsing_content(status_pair):
    before, after = status_pair
    assert before.label == "Synthetic before"
    assert [b.id for b in before.blocks] == ["keep", "task", "gone", "dup-a", "dup-b"]
    assert before.blocks[3].content == before.blocks[4].content
    assert len(after.blocks) == 5
    with pytest.raises(FrozenInstanceError):
        before.blocks[0].content = "mutated"


@pytest.mark.parametrize("version", [True, False, 0, 2, 1.0, "1", None, [], {}])
def test_invalid_versions(version):
    with pytest.raises(SnapshotValidationError, match="schema_version"):
        load_json_snapshot(encode(document(schema_version=version)))


@pytest.mark.parametrize("raw", [b"", b" \n\t", b"{", b"just text", b'{"blocks":[],}'])
def test_malformed_json_never_falls_back(raw):
    with pytest.raises(SnapshotValidationError, match="invalid JSON"):
        load_json_snapshot(raw)


@pytest.mark.parametrize(
    "value,path",
    [
        ([], "snapshot"),
        (None, "snapshot"),
        (1, "snapshot"),
        ({}, "blocks"),
        ({"schema_version": 1}, "blocks"),
        (document(label=None), "label"),
        (document(blocks=None), "blocks"),
        (document(watchlist={}), "watchlist"),
        (document(secret="private"), "unknown field"),
        (document(blocks=[None]), r"blocks\[0\]"),
        (document(blocks=[{"id": "a", "content": ""}]), r"blocks\[0\].kind"),
        (document(blocks=[block(id=" \t")]), r"blocks\[0\].id"),
        (document(blocks=[block(id=1)]), r"blocks\[0\].id"),
        (document(blocks=[block(kind="other")]), r"blocks\[0\].kind"),
        (document(blocks=[block(kind=[])]), r"blocks\[0\].kind"),
        (document(blocks=[block(role=None)]), r"blocks\[0\].role"),
        (document(blocks=[block(role="narrator")]), r"blocks\[0\].role"),
        (document(blocks=[block(content={})]), r"blocks\[0\].content"),
        (document(blocks=[block(extra="private")]), r"blocks\[0\].*unknown"),
        (document(watchlist=[watch(text=" \n")]), r"watchlist\[0\].text"),
        (document(watchlist=[watch(text=False)]), r"watchlist\[0\].text"),
        (document(watchlist=[watch(note=None)]), r"watchlist\[0\].note"),
        (document(watchlist=[{"text": "x"}]), r"watchlist\[0\].id"),
        (document(watchlist=[watch(extra=True)]), r"watchlist\[0\].*unknown"),
    ],
)
def test_field_errors(value, path):
    with pytest.raises(SnapshotValidationError, match=path):
        load_json_snapshot(encode(value))


@pytest.mark.parametrize(
    "raw,path",
    [
        (b'{"schema_version":1,"blocks":[],"blocks":[]}', "snapshot"),
        (b'{"schema_version":1,"blocks":[{"id":"a","id":"b"}]}', r"blocks\[0\]"),
        (
            b'{"schema_version":1,"blocks":[],"watchlist":[{"text":"x","text":"y"}]}',
            r"watchlist\[0\]",
        ),
    ],
)
def test_duplicate_json_keys(raw, path):
    with pytest.raises(SnapshotValidationError, match=path + ".*duplicate JSON"):
        load_json_snapshot(raw)


@pytest.mark.parametrize(
    "field,items",
    [
        ("blocks", [block(), block()]),
        ("watchlist", [watch(), watch()]),
    ],
)
def test_duplicate_ids(field, items):
    with pytest.raises(
        SnapshotValidationError, match=field + r"\[1\].id: duplicate ID"
    ):
        load_json_snapshot(encode(document(**{field: items})))


def test_id_namespaces_are_independent():
    result = load_json_snapshot(
        encode(document(blocks=[block(id="same")], watchlist=[watch(id="same")]))
    )
    assert result.blocks[0].id == result.watchlist[0].id


@pytest.mark.parametrize("raw", [b"\xff", b"\xed\xa0\x80", b"\xc3"])
def test_invalid_utf8_in_both_loaders(raw):
    for loader in (
        load_json_snapshot,
        lambda data: load_text_snapshot(data, label="x"),
    ):
        with pytest.raises(SnapshotValidationError, match="valid UTF-8"):
            loader(raw)


@pytest.mark.parametrize(
    "value",
    [
        document(label="\ud800"),
        document(blocks=[block(content="\udfff")]),
        document(blocks=[block(id="\ud800")]),
        document(watchlist=[watch(text="\ud800")]),
        document(watchlist=[watch(note="\ud800")]),
        document(**{"\ud800": "x"}),
    ],
)
def test_escaped_unpaired_surrogates(value):
    with pytest.raises(SnapshotValidationError, match="surrogates"):
        load_json_snapshot(json.dumps(value).encode())


def test_paired_surrogate_is_valid_unicode():
    result = load_json_snapshot(
        json.dumps(document(blocks=[block(content="😀")])).encode()
    )
    assert result.blocks[0].content == "😀"


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonstandard_json_numbers(constant):
    raw = ('{"schema_version":' + constant + ',"blocks":[]}').encode()
    with pytest.raises(SnapshotValidationError, match="nonstandard JSON"):
        load_json_snapshot(raw)


def test_pathological_json_errors_are_sanitized():
    for raw in [
        b"[" * 2000 + b"]" * 2000,
        b'{"schema_version":' + b"9" * 5000 + b',"blocks":[]}',
    ]:
        with pytest.raises(SnapshotValidationError, match="input:") as error:
            load_json_snapshot(raw)
        assert len(str(error.value)) < 100


def test_empty_whitespace_bom_newlines_and_no_unicode_normalization():
    assert (
        load_json_snapshot(b'\xef\xbb\xbf{"schema_version":1,"blocks":[]}').blocks == ()
    )
    assert load_json_snapshot(encode(document(label="", watchlist=[]))).label == ""
    for text in ["", " \t", "a\r\nb\rc\n", "e\u0301", "é", "<script>x</script>"]:
        expected = text.replace("\r\n", "\n").replace("\r", "\n")
        plain = load_text_snapshot(b"\xef\xbb\xbf" + text.encode(), label="")
        structured = load_json_snapshot(encode(document(blocks=[block(content=text)])))
        assert plain.blocks[0].content == structured.blocks[0].content == expected
        assert plain.blocks[0].id == "document"
        assert plain.blocks[0].role is None
    assert load_text_snapshot(b"a\n", label="x").blocks[0].content != "a"


@pytest.mark.parametrize(
    "field,limit",
    [
        ("label", 200),
        ("id", 128),
        ("content", 50_000),
        ("watch_id", 128),
        ("text", 500),
        ("note", 500),
    ],
)
def test_string_limits_at_and_over(field, limit):
    def make(size):
        value = "é" * size
        if field == "label":
            return document(label=value)
        if field in ("id", "content"):
            return document(blocks=[block(**{field: value})])
        return document(
            watchlist=[watch(**{"id" if field == "watch_id" else field: value})]
        )

    load_json_snapshot(encode(make(limit)))
    with pytest.raises(SnapshotValidationError, match=f"at most {limit} characters"):
        load_json_snapshot(encode(make(limit + 1)))


@pytest.mark.parametrize(
    "field,limit,factory",
    [
        ("blocks", 200, block),
        ("watchlist", 50, watch),
    ],
)
def test_count_limits_at_and_over(field, limit, factory):
    items = [factory(id=str(i)) for i in range(limit + 1)]
    load_json_snapshot(encode(document(**{field: items[:limit]})))
    with pytest.raises(SnapshotValidationError, match=f"at most {limit} items"):
        load_json_snapshot(encode(document(**{field: items})))


def test_json_byte_cap_includes_bom_and_uses_unicode_bytes():
    # Content stays within 50k characters; each emoji occupies four UTF-8 bytes.
    raw = encode(
        document(
            blocks=[
                block(id="a", content="😀" * 40_000),
                block(id="b", content="😀" * 20_000),
            ]
        )
    )
    at_limit = raw + b" " * (MAX_INPUT_BYTES - len(raw))
    load_json_snapshot(at_limit)
    for over in [at_limit + b" ", b"\xef\xbb\xbf" + at_limit]:
        with pytest.raises(SnapshotValidationError, match="UTF-8 bytes"):
            load_json_snapshot(over)


def test_text_content_and_byte_caps():
    assert len(load_text_snapshot(b"a" * 50_000, label="x").blocks[0].content) == 50_000
    with pytest.raises(SnapshotValidationError, match="50000 characters"):
        load_text_snapshot(b"a" * 50_001, label="x")
    with pytest.raises(SnapshotValidationError, match="UTF-8 bytes"):
        load_text_snapshot(b"x" * (MAX_INPUT_BYTES + 1), label="x")
    with pytest.raises(SnapshotValidationError, match="label"):
        load_text_snapshot(b"", label="x" * 201)


def test_bytes_boundary_and_recovery():
    for loader in [
        load_json_snapshot,
        lambda data: load_text_snapshot(data, label="x"),
    ]:
        with pytest.raises(SnapshotValidationError, match="UTF-8 bytes"):
            loader("not bytes")
    for value in [
        document(blocks=[block(id="PRIVATE", role="PRIVATE")]),
        document(**{"PRIVATE": "PRIVATE"}),
        document(blocks=[block(), block()]),
    ]:
        with pytest.raises(SnapshotValidationError) as error:
            load_json_snapshot(encode(value))
        assert "PRIVATE" not in str(error.value)
    assert load_json_snapshot(encode(document())).blocks == ()
