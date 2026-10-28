import json
from dataclasses import asdict, replace

import pytest

from contextdiff import (
    Block,
    Snapshot,
    WatchItem,
    compare_snapshots,
    create_token_counter,
)


def words(text):
    """Deterministic arithmetic stub; explicitly not a reference tokenizer."""
    return len(text.split())


def test_fixture_golden_accounting_and_watches(status_pair, expected_statuses):
    before, after = status_pair
    original = asdict(before), asdict(after)
    report = compare_snapshots(before, after, counter=words)
    totals = expected_statuses["word_counter_totals"]
    assert asdict(report.status_counts) == {
        "added": 1,
        "removed": 1,
        "retained": 3,
        "modified": 1,
    }
    assert report.tokens.status == "available"
    assert report.tokens.before_total == totals["before"] == 11
    assert report.tokens.after_total == totals["after"] == 10
    assert report.tokens.delta == totals["delta"] == -1
    assert report.tokens.percentage_change == pytest.approx(-100 / 11)
    assert {
        k.kind: [k.before, k.after, k.delta] for k in report.tokens.by_kind
    } == expected_statuses["word_counter_kinds"]
    assert [
        [w.item.id, w.status, list(w.before_block_ids), list(w.after_block_ids)]
        for w in report.watches
    ] == expected_statuses["watches"]
    assert [
        (b.before_tokens, b.after_tokens, b.token_delta) for b in report.blocks
    ] == [(3, 4, 1), (3, 3, 0), (0, 1, 1), (1, 1, 0), (1, 1, 0), (3, 0, -3)]
    assert report.watchlist_status == "configured"
    assert (asdict(before), asdict(after)) == original
    assert compare_snapshots(before, after, counter=words) == report


@pytest.mark.parametrize("counter", [words, None])
def test_serialization_full_sources_detached_and_deterministic(status_pair, counter):
    report = compare_snapshots(*status_pair, counter=counter)
    data = report.to_dict()
    encoded = json.dumps(data, ensure_ascii=False, allow_nan=False)
    assert json.loads(encoded)["blocks"][0]["before"]["content"] == "Fix retries now."
    assert json.loads(encoded)["reference_encoding"] == "cl100k_base"
    assert json.loads(encoded)["report_version"] == 1
    assert json.loads(encoded)["limitations"]
    data["blocks"][0]["before"]["content"] = "mutated detached dict"
    assert report.blocks[0].before.content == "Fix retries now."
    assert json.dumps(report.to_dict(), ensure_ascii=False, allow_nan=False) == encoded
    assert "timestamp" not in data


def test_unavailable_metrics_are_null_and_other_results_survive(status_pair):
    report = compare_snapshots(*status_pair, counter=None)
    assert report.tokens.status == "unavailable"
    assert (
        report.tokens.before_total,
        report.tokens.after_total,
        report.tokens.delta,
        report.tokens.percentage_change,
    ) == (None, None, None, None)
    assert all(
        (k.before, k.after, k.delta) == (None, None, None)
        for k in report.tokens.by_kind
    )
    assert all(
        (b.before_tokens, b.after_tokens, b.token_delta) == (None, None, None)
        for b in report.blocks
    )
    assert report.status_counts.modified == 1
    assert report.blocks[0].line_detail.status == "available"
    assert report.watches[1].status == "missing_after"


@pytest.mark.parametrize("counter", [words, None])
def test_empty_baseline_and_no_watches(counter):
    for before in [Snapshot(()), Snapshot((Block("empty", "message", ""),))]:
        report = compare_snapshots(before, Snapshot(()), counter=counter)
        assert report.tokens.percentage_change is None
        assert report.watchlist_status == "not_configured"
        assert report.watches == ()
    report = compare_snapshots(
        Snapshot(()), Snapshot((Block("a", "summary", "new"),)), counter=counter
    )
    assert report.tokens.percentage_change is None
    if counter is not None:
        assert report.tokens.delta == 1
        assert report.tokens.before_total == 0


def test_kind_transfer_and_role_edit_have_zero_overall_delta():
    before = Snapshot(
        (
            Block("a", "message", "two words", "user"),
            Block("b", "memory", "one", "system"),
        )
    )
    after = Snapshot(
        (
            replace(before.blocks[0], kind="summary"),
            replace(before.blocks[1], role="developer"),
        )
    )
    report = compare_snapshots(before, after, counter=words)
    assert report.tokens.delta == report.tokens.percentage_change == 0
    assert report.status_counts.modified == 2
    assert all(b.token_delta == 0 and b.line_detail is None for b in report.blocks)
    assert {k.kind: k.delta for k in report.tokens.by_kind} == {
        "instruction": 0,
        "message": -2,
        "tool_result": 0,
        "memory": 0,
        "retrieval": 0,
        "summary": 2,
    }


@pytest.mark.parametrize(
    "real", [False, pytest.param(True, marks=pytest.mark.integration)]
)
def test_accounting_conservation_across_cases(status_pair, real):
    counter = create_token_counter() if real else words
    before, after = status_pair
    for left, right in [
        (before, after),
        (after, before),
        (before, before),
        (Snapshot(()), after),
        (before, Snapshot(())),
        (Snapshot(()), Snapshot(())),
    ]:
        report = compare_snapshots(left, right, counter=counter)
        counts = report.status_counts
        assert len(left.blocks) == counts.retained + counts.modified + counts.removed
        assert len(right.blocks) == counts.retained + counts.modified + counts.added
        assert (
            sum(k.before for k in report.tokens.by_kind) == report.tokens.before_total
        )
        assert sum(k.after for k in report.tokens.by_kind) == report.tokens.after_total
        assert sum(b.token_delta for b in report.blocks) == report.tokens.delta
        added = sum(b.after_tokens for b in report.blocks if b.status == "added")
        removed = sum(b.before_tokens for b in report.blocks if b.status == "removed")
        modified = sum(
            b.after_tokens - b.before_tokens
            for b in report.blocks
            if b.status == "modified"
        )
        assert added - removed + modified == report.tokens.delta


@pytest.mark.integration
def test_real_tokenizer_additive_per_block_excludes_metadata():
    # A concatenation of these blocks is 'hello' (one token), but each is one token.
    before = Snapshot(
        (
            Block("a", "instruction", "hel", "system"),
            Block("b", "message", "lo", "user"),
        ),
        label="Metadata excluded",
        watchlist=(WatchItem("watch", "absent"),),
    )
    report = compare_snapshots(before, before, counter=create_token_counter())
    assert report.tokens.before_total == report.tokens.after_total == 2
    assert [b.before_tokens for b in report.blocks] == [1, 1]
    assert report.tokens.delta == 0


def test_watch_moves_into_added_summary_with_all_source_ids():
    watches = (WatchItem("w", "STRASSE \t Window"),)
    before = Snapshot(
        (
            Block("a", "message", "Straße\nwindow"),
            Block("b", "memory", "straße window"),
        ),
        watchlist=watches,
    )
    after = Snapshot((Block("summary", "summary", "Do not use strasse   window."),))
    report = compare_snapshots(before, after, counter=words)
    (result,) = report.watches
    assert (
        result.status == "present_after"
    )  # Negation does not defeat substring matching.
    assert result.before_block_ids == ("a", "b")
    assert result.after_block_ids == ("summary",)
    assert [b.status for b in report.blocks] == ["added", "removed", "removed"]
    assert before.blocks[0].content == "Straße\nwindow"


@pytest.mark.parametrize(
    "after_text", ["24 hour window", "one day window", "unrelated"]
)
def test_paraphrase_and_punctuation_are_not_semantic_matches(after_text):
    before = Snapshot(
        (Block("a", "message", "24-hour window"),),
        watchlist=(WatchItem("w", "24-hour window"),),
    )
    after = Snapshot((Block("a", "summary", after_text),))
    assert (
        compare_snapshots(before, after, counter=None).watches[0].status
        == "missing_after"
    )


def test_phrase_split_across_blocks_does_not_match_and_after_watches_cannot_override():
    before = Snapshot(
        (Block("a", "message", "first second"),),
        watchlist=(WatchItem("w", "first second"),),
    )
    after = Snapshot(
        (Block("x", "message", "first"), Block("y", "message", "second")),
        watchlist=(WatchItem("w", "first"), WatchItem("new", "second")),
    )
    report = compare_snapshots(before, after, counter=None)
    assert len(report.watches) == 1
    assert report.watches[0].status == "missing_after"
    assert report.watches[0].item.text == "first second"


@pytest.mark.parametrize("after_content", ["absent initially", "unrelated"])
def test_unverified_baseline_even_when_present_after(after_content):
    before = Snapshot((), watchlist=(WatchItem("w", "absent initially"),))
    after = Snapshot((Block("a", "summary", after_content),))
    (watch,) = compare_snapshots(before, after, counter=None).watches
    assert watch.status == "unverified_baseline"
    assert watch.before_block_ids == ()
    assert watch.after_block_ids == (
        ("a",) if after_content == "absent initially" else ()
    )


@pytest.mark.parametrize("bad", [True, -1, 1.5, None])
def test_invalid_counter_results_and_programming_errors_are_not_unavailable(bad):
    snapshot = Snapshot((Block("a", "message", "x"),))
    with pytest.raises(ValueError, match="nonnegative integer"):
        compare_snapshots(snapshot, snapshot, counter=lambda _: bad)

    def fail(_):
        raise RuntimeError("counter programming error")

    with pytest.raises(RuntimeError, match="programming error"):
        compare_snapshots(snapshot, snapshot, counter=fail)
