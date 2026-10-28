"""Stable-ID classification with bounded, newline-preserving line detail."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import cast

from contextdiff.models import (
    BlockChange,
    LineDetail,
    LineOpcode,
    LineTag,
    Snapshot,
    Status,
)

MAX_COMBINED_LINES = 2_000
MAX_PAIR_PRODUCT = 1_000_000
MAX_COMPARISON_PRODUCT = 2_000_000


def _line_detail(before: str, after: str, remaining: int) -> tuple[LineDetail, int]:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    product = len(before_lines) * len(after_lines)
    reason = None
    if len(before_lines) + len(after_lines) > MAX_COMBINED_LINES:
        reason = f"Combined line count exceeds {MAX_COMBINED_LINES}."
    elif product > MAX_PAIR_PRODUCT:
        reason = f"Line-count product exceeds {MAX_PAIR_PRODUCT}."
    elif product > remaining:
        reason = (
            f"Comparison line-product budget of {MAX_COMPARISON_PRODUCT} exhausted."
        )
    if reason:
        return LineDetail("skipped", skip_reason=reason), 0
    matcher = SequenceMatcher(None, before_lines, after_lines, autojunk=False)
    opcodes = tuple(
        LineOpcode(
            cast(LineTag, tag),
            i1,
            i2,
            j1,
            j2,
            tuple(before_lines[i1:i2]),
            tuple(after_lines[j1:j2]),
        )
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
    )
    return LineDetail("available", opcodes), product


def diff_snapshots(before: Snapshot, after: Snapshot) -> tuple[BlockChange, ...]:
    """Compare validated snapshots in after order, then before-only order."""
    before_index = {block.id: (i, block) for i, block in enumerate(before.blocks)}
    after_ids = {block.id for block in after.blocks}
    changes: list[BlockChange] = []
    remaining = MAX_COMPARISON_PRODUCT
    for position, block in enumerate(after.blocks):
        previous_position, previous = before_index.get(block.id, (None, None))
        status: Status = (
            "added"
            if previous is None
            else "retained"
            if previous == block
            else "modified"
        )
        detail = None
        if previous is not None and previous.content != block.content:
            detail, used = _line_detail(previous.content, block.content, remaining)
            remaining -= used
        changes.append(
            BlockChange(
                block.id, status, previous, block, previous_position, position, detail
            )
        )
    for position, block in enumerate(before.blocks):
        if block.id not in after_ids:
            changes.append(
                BlockChange(block.id, "removed", block, None, position, None)
            )
    return tuple(changes)
