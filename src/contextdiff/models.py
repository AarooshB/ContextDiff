"""Immutable validated inputs and deterministic, JSON-serializable reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

Kind = Literal[
    "instruction", "message", "tool_result", "memory", "retrieval", "summary"
]
Role = Literal["system", "developer", "user", "assistant", "tool"]
Status = Literal["added", "removed", "retained", "modified"]
WatchStatus = Literal["present_after", "missing_after", "unverified_baseline"]
LineTag = Literal["equal", "insert", "delete", "replace"]
KINDS: tuple[Kind, ...] = (
    "instruction",
    "message",
    "tool_result",
    "memory",
    "retrieval",
    "summary",
)
ROLES: tuple[Role, ...] = ("system", "developer", "user", "assistant", "tool")


@dataclass(frozen=True)
class Block:
    id: str
    kind: Kind
    content: str
    role: Role | None = None


@dataclass(frozen=True)
class WatchItem:
    id: str
    text: str
    note: str | None = None


@dataclass(frozen=True)
class Snapshot:
    blocks: tuple[Block, ...]
    label: str | None = None
    watchlist: tuple[WatchItem, ...] = ()
    schema_version: int = 1


@dataclass(frozen=True)
class LineOpcode:
    tag: LineTag
    before_start: int
    before_end: int
    after_start: int
    after_end: int
    before_lines: tuple[str, ...]
    after_lines: tuple[str, ...]


@dataclass(frozen=True)
class LineDetail:
    status: Literal["available", "skipped"]
    opcodes: tuple[LineOpcode, ...] = ()
    skip_reason: str | None = None


@dataclass(frozen=True)
class BlockChange:
    id: str
    status: Status
    before: Block | None
    after: Block | None
    before_position: int | None
    after_position: int | None
    line_detail: LineDetail | None = None
    before_tokens: int | None = None
    after_tokens: int | None = None
    token_delta: int | None = None


@dataclass(frozen=True)
class StatusCounts:
    added: int
    removed: int
    retained: int
    modified: int


@dataclass(frozen=True)
class KindTokens:
    kind: Kind
    before: int | None
    after: int | None
    delta: int | None


@dataclass(frozen=True)
class TokenSummary:
    status: Literal["available", "unavailable"]
    before_total: int | None
    after_total: int | None
    delta: int | None
    percentage_change: float | None
    by_kind: tuple[KindTokens, ...]


@dataclass(frozen=True)
class WatchResult:
    item: WatchItem
    status: WatchStatus
    before_block_ids: tuple[str, ...]
    after_block_ids: tuple[str, ...]


@dataclass(frozen=True)
class Comparison:
    report_version: int
    before_label: str | None
    after_label: str | None
    reference_encoding: str
    blocks: tuple[BlockChange, ...]
    status_counts: StatusCounts
    tokens: TokenSummary
    watchlist_status: Literal["configured", "not_configured"]
    watches: tuple[WatchResult, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a detached representation accepted by json.dumps."""
        return asdict(self)
