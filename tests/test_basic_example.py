"""Independent expectations for the single Stage 2 bundled sample."""

from pathlib import Path

import pytest

from contextdiff import compare_snapshots, create_token_counter, load_json_snapshot

EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.mark.integration
def test_bundled_sample():
    before = load_json_snapshot((EXAMPLES / "basic.before.json").read_bytes())
    after = load_json_snapshot((EXAMPLES / "basic.after.json").read_bytes())
    report = compare_snapshots(before, after, counter=create_token_counter())
    assert [(change.id, change.status) for change in report.blocks] == [
        ("rule", "retained"),
        ("task", "modified"),
        ("finding", "modified"),
        ("summary", "added"),
        ("constraint", "removed"),
    ]
    assert report.watches[0].before_block_ids == ("rule",)
    assert report.watches[0].after_block_ids == ("rule",)
    assert report.watches[1].status == "missing_after"
    assert report.watches[2].status == "unverified_baseline"
    assert report.blocks[2].line_detail is None
    assert report.blocks[2].token_delta == 0
    assert report.blocks[2].before.kind == "tool_result"
    assert report.blocks[2].after.kind == "memory"
    assert report.tokens.status == "available"
    assert (
        report.tokens.before_total,
        report.tokens.after_total,
        report.tokens.delta,
    ) == (30, 28, -2)
    assert report.tokens.after_total - report.tokens.before_total == report.tokens.delta
    # Hand count whitespace words: before 4 + 7 + 3 + 5, after 4 + 8 + 3 + 6.
    words = compare_snapshots(before, after, counter=lambda text: len(text.split()))
    assert words.tokens.before_total == 19
    assert words.tokens.after_total == 21
    assert words.tokens.delta == 2
