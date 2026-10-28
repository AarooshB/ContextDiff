"""Assemble comparison, additive reference counts, and lexical watch evidence."""

from __future__ import annotations

from dataclasses import replace

from contextdiff.diffing import diff_snapshots
from contextdiff.models import (
    KINDS,
    BlockChange,
    Comparison,
    KindTokens,
    Snapshot,
    StatusCounts,
    TokenSummary,
    WatchResult,
    WatchStatus,
)
from contextdiff.tokens import REFERENCE_ENCODING, TokenCounter

LIMITATIONS = (
    "Retained means identical content/kind/role under the same stable ID, "
    "not model memory.",
    "Content tokens use the cl100k_base reference summed per block, "
    "not provider billing or hidden context.",
    "Watched phrases use casefolded, whitespace-collapsed literal substrings within "
    "individual blocks. Paraphrases can be absent; negation and "
    "contradictions can match.",
    "Only before-watchlist items are checked. No watches means "
    "no preservation assessment.",
    "Reports contain supplied text; snapshot completeness and semantic preservation "
    "require human review.",
)


def _match_text(text: str) -> str:
    return " ".join(text.casefold().split())


def check_watches(before: Snapshot, after: Snapshot) -> tuple[WatchResult, ...]:
    """Check only before watches, returning source IDs in their original order."""
    before_text = tuple(
        (block.id, _match_text(block.content)) for block in before.blocks
    )
    after_text = tuple((block.id, _match_text(block.content)) for block in after.blocks)
    results = []
    for item in before.watchlist:
        phrase = _match_text(item.text)
        before_ids = tuple(
            identifier for identifier, text in before_text if phrase in text
        )
        after_ids = tuple(
            identifier for identifier, text in after_text if phrase in text
        )
        status: WatchStatus = (
            "unverified_baseline"
            if not before_ids
            else "present_after"
            if after_ids
            else "missing_after"
        )
        results.append(WatchResult(item, status, before_ids, after_ids))
    return tuple(results)


def _counts(snapshot: Snapshot, counter: TokenCounter) -> dict[str, int]:
    result = {}
    for block in snapshot.blocks:
        value = counter(block.content)
        if type(value) is not int or value < 0:
            raise ValueError("Token counter must return a nonnegative integer")
        result[block.id] = value
    return result


def _token_metrics(
    before: Snapshot,
    after: Snapshot,
    changes: tuple[BlockChange, ...],
    counter: TokenCounter | None,
) -> tuple[tuple[BlockChange, ...], TokenSummary]:
    if counter is None:
        return changes, TokenSummary(
            "unavailable",
            None,
            None,
            None,
            None,
            tuple(KindTokens(kind, None, None, None) for kind in KINDS),
        )
    before_counts = _counts(before, counter)
    after_counts = _counts(after, counter)
    counted = tuple(
        replace(
            change,
            before_tokens=before_counts.get(change.id, 0),
            after_tokens=after_counts.get(change.id, 0),
            token_delta=after_counts.get(change.id, 0)
            - before_counts.get(change.id, 0),
        )
        for change in changes
    )
    kinds = []
    for kind in KINDS:
        previous = sum(before_counts[b.id] for b in before.blocks if b.kind == kind)
        current = sum(after_counts[b.id] for b in after.blocks if b.kind == kind)
        kinds.append(KindTokens(kind, previous, current, current - previous))
    previous, current = sum(before_counts.values()), sum(after_counts.values())
    delta = current - previous
    summary = TokenSummary(
        "available",
        previous,
        current,
        delta,
        100 * delta / previous if previous else None,
        tuple(kinds),
    )
    return counted, summary


def compare_snapshots(
    before: Snapshot, after: Snapshot, *, counter: TokenCounter | None
) -> Comparison:
    """Compare loader-validated values; None explicitly disables all token metrics."""
    changes, tokens = _token_metrics(
        before, after, diff_snapshots(before, after), counter
    )
    counts = StatusCounts(
        **{
            status: sum(change.status == status for change in changes)
            for status in ("added", "removed", "retained", "modified")
        }
    )
    return Comparison(
        1,
        before.label,
        after.label,
        REFERENCE_ENCODING,
        changes,
        counts,
        tokens,
        "configured" if before.watchlist else "not_configured",
        check_watches(before, after),
        LIMITATIONS,
    )
