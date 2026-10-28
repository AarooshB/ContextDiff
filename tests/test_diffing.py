from dataclasses import asdict, replace

import pytest

from contextdiff import Block, Snapshot, load_text_snapshot
from contextdiff.diffing import diff_snapshots


def pair(before, after):
    return (
        load_text_snapshot(before.encode(), label="Before"),
        load_text_snapshot(after.encode(), label="After"),
    )


def test_golden_classification_positions_conservation_and_no_mutation(
    status_pair, expected_statuses
):
    before, after = status_pair
    originals = asdict(before), asdict(after)
    changes = diff_snapshots(before, after)
    assert [[b.id, b.status] for b in changes] == expected_statuses["ordered_statuses"]
    assert [(b.before_position, b.after_position) for b in changes] == [
        (1, 0),
        (0, 1),
        (None, 2),
        (4, 3),
        (3, 4),
        (2, None),
    ]
    assert sum(b.status in ("retained", "modified", "removed") for b in changes) == 5
    assert sum(b.status in ("retained", "modified", "added") for b in changes) == 5
    assert (asdict(before), asdict(after)) == originals
    assert diff_snapshots(before, after) == changes


def test_identical_ignores_labels_and_watches(status_pair):
    before, _ = status_pair
    after = replace(before, label="Different", watchlist=())
    changes = diff_snapshots(before, after)
    assert all(b.status == "retained" and b.line_detail is None for b in changes)


def test_changed_id_with_same_content_is_added_and_removed():
    before = Snapshot((Block("old", "message", "same"),))
    after = Snapshot((Block("new", "message", "same"),))
    assert [(b.id, b.status) for b in diff_snapshots(before, after)] == [
        ("new", "added"),
        ("old", "removed"),
    ]


@pytest.mark.parametrize(
    "changes", [{"kind": "summary"}, {"role": "assistant"}, {"role": None}]
)
def test_metadata_only_change_is_modified(changes):
    block = Block("a", "message", "same", "user")
    (result,) = diff_snapshots(
        Snapshot((block,)), Snapshot((replace(block, **changes),))
    )
    assert result.status == "modified"
    assert result.line_detail is None
    assert result.before.content == result.after.content == "same"


@pytest.mark.parametrize(
    "before,after,expected",
    [
        (
            "a\nb\nc\nd\n",
            "a\nB\nc\nx\nd\n",
            [
                ("equal", 0, 1, 0, 1, ("a\n",), ("a\n",)),
                ("replace", 1, 2, 1, 2, ("b\n",), ("B\n",)),
                ("equal", 2, 3, 2, 3, ("c\n",), ("c\n",)),
                ("insert", 3, 3, 3, 4, (), ("x\n",)),
                ("equal", 3, 4, 4, 5, ("d\n",), ("d\n",)),
            ],
        ),
        (
            "a\nb\nc\n",
            "a\nc\n",
            [
                ("equal", 0, 1, 0, 1, ("a\n",), ("a\n",)),
                ("delete", 1, 2, 1, 1, ("b\n",), ()),
                ("equal", 2, 3, 1, 2, ("c\n",), ("c\n",)),
            ],
        ),
        ("", "a\n", [("insert", 0, 0, 0, 1, (), ("a\n",))]),
        ("a\n", "", [("delete", 0, 1, 0, 0, ("a\n",), ())]),
        ("a", "a\n", [("replace", 0, 1, 0, 1, ("a",), ("a\n",))]),
        (
            "a\nb\n",
            "a\nb",
            [
                ("equal", 0, 1, 0, 1, ("a\n",), ("a\n",)),
                ("replace", 1, 2, 1, 2, ("b\n",), ("b",)),
            ],
        ),
    ],
)
def test_golden_line_opcodes(before, after, expected):
    (result,) = diff_snapshots(*pair(before, after))
    assert result.status == "modified"
    assert result.line_detail.status == "available"
    assert [tuple(asdict(op).values()) for op in result.line_detail.opcodes] == expected
    assert (
        "".join(line for op in result.line_detail.opcodes for line in op.before_lines)
        == before
    )
    assert (
        "".join(line for op in result.line_detail.opcodes for line in op.after_lines)
        == after
    )


def test_repetitive_alignment_keeps_rare_change():
    (result,) = diff_snapshots(
        *pair("repeat\n" * 300 + "old\n", "repeat\n" * 300 + "new\n")
    )
    assert [op.tag for op in result.line_detail.opcodes] == ["equal", "replace"]
    assert result.line_detail.opcodes[0].before_end == 300


def test_pair_line_budget_at_and_over_preserves_sources():
    before = "repeat\n" * 1000
    (at_limit,) = diff_snapshots(*pair(before, "different\n" * 1000))
    assert at_limit.line_detail.status == "available"  # product = exactly 1,000,000
    after = "repeat\n" * 1000 + "extra\n"
    (over,) = diff_snapshots(*pair(before, after))
    assert over.status == "modified"
    assert over.line_detail.status == "skipped"
    assert "Combined line count" in over.line_detail.skip_reason
    assert over.line_detail.opcodes == ()
    assert over.before.content == before
    assert over.after.content == after


def test_product_guard_independently(monkeypatch):
    # With a 2,000 combined-line cap, a >1,000,000 product is unreachable.
    # Relax only that first guard to exercise the independent product guard.
    monkeypatch.setattr("contextdiff.diffing.MAX_COMBINED_LINES", 3000)
    (result,) = diff_snapshots(*pair("a\n" * 1001, "b\n" * 1000))
    assert result.line_detail.status == "skipped"
    assert "product exceeds" in result.line_detail.skip_reason


def test_cumulative_budget_in_after_order_and_skipped_pair_spends_nothing():
    before = Snapshot(tuple(Block(str(i), "message", "x\n" * 1000) for i in range(4)))
    after = Snapshot(
        tuple(
            Block(str(i), "message", "y\n" * n)
            for i, n in [(3, 1001), (2, 1000), (0, 1000), (1, 1000)]
        )
    )
    results = diff_snapshots(before, after)
    assert [r.id for r in results] == ["3", "2", "0", "1"]
    assert [r.line_detail.status for r in results] == [
        "skipped",
        "available",
        "available",
        "skipped",
    ]
    assert "Comparison line-product budget" in results[3].line_detail.skip_reason
    assert results[3].before.content == "x\n" * 1000
    assert results[3].after.content == "y\n" * 1000


def test_empty_all_added_and_all_removed():
    empty = Snapshot(())
    two = Snapshot((Block("a", "message", ""), Block("b", "summary", "b")))
    assert diff_snapshots(empty, empty) == ()
    assert [r.status for r in diff_snapshots(empty, two)] == ["added", "added"]
    assert [r.status for r in diff_snapshots(two, empty)] == ["removed", "removed"]


def test_newline_normalization_precedes_equality():
    (result,) = diff_snapshots(*pair("a\r\nb\r", "a\nb\n"))
    assert result.status == "retained"
