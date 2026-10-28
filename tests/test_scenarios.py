"""Hand-checked scenario identities, evidence, and reference token goldens."""

import json
from pathlib import Path

import pytest

from contextdiff import compare_snapshots, create_token_counter, load_json_snapshot

EXAMPLES = Path(__file__).parents[1] / "examples"


@pytest.mark.integration
@pytest.mark.parametrize(
    "after_name, before_name, counts, sources, totals, ordered",
    [
        (
            "handoff.lossy.after",
            "handoff.before",
            [(13, 13), (18, 13), (0, 26), (30, 0), (188, 0), (22, 0)],
            [
                ("missing_after", ["constraint"], []),
                ("present_after", ["finding"], ["handoff-summary"]),
                ("present_after", ["instruction"], ["instruction"]),
            ],
            (271, 52, -219),
            [
                ("instruction", "retained"),
                ("task", "modified"),
                ("handoff-summary", "added"),
                ("constraint", "removed"),
                ("trace", "removed"),
                ("finding", "removed"),
            ],
        ),
        (
            "handoff.preserved.after",
            "handoff.before",
            [(13, 13), (18, 13), (0, 38), (30, 0), (188, 0), (22, 0)],
            [
                ("present_after", ["constraint"], ["handoff-summary"]),
                ("present_after", ["finding"], ["handoff-summary"]),
                ("present_after", ["instruction"], ["instruction"]),
            ],
            (271, 64, -207),
            [
                ("instruction", "retained"),
                ("task", "modified"),
                ("handoff-summary", "added"),
                ("constraint", "removed"),
                ("trace", "removed"),
                ("finding", "removed"),
            ],
        ),
        (
            "retrieval.after",
            "retrieval.before",
            [(15, 15), (0, 19), (23, 0)],
            [("missing_after", ["runbook-retention-v1"], [])],
            (38, 34, -4),
            [
                ("task", "retained"),
                ("runbook-concurrency-v1", "added"),
                ("runbook-retention-v1", "removed"),
            ],
        ),
    ],
)
def test_scenario_goldens(after_name, before_name, counts, sources, totals, ordered):
    before, after = [
        load_json_snapshot((EXAMPLES / f"{name}.json").read_bytes())
        for name in (before_name, after_name)
    ]
    report = compare_snapshots(before, after, counter=create_token_counter())
    assert [(b.id, b.status) for b in report.blocks] == ordered
    assert [(b.before_tokens, b.after_tokens) for b in report.blocks] == counts
    assert [
        (w.status, list(w.before_block_ids), list(w.after_block_ids))
        for w in report.watches
    ] == sources
    assert (
        report.tokens.before_total,
        report.tokens.after_total,
        report.tokens.delta,
    ) == totals
    assert sum(b.token_delta for b in report.blocks) == totals[2]
    assert sum(k.before for k in report.tokens.by_kind) == totals[0]
    assert sum(k.after for k in report.tokens.by_kind) == totals[1]
    assert totals[1] < totals[0]
    # JSON export must recover complete ordered input sources, including LF endings.
    data = json.loads(json.dumps(report.to_dict(), ensure_ascii=False, allow_nan=False))
    for side, snapshot in (("before", before), ("after", after)):
        recovered = sorted(
            (b for b in data["blocks"] if b[side] is not None),
            key=lambda b: b[f"{side}_position"],
        )
        assert [(b[side]["id"], b[side]["content"]) for b in recovered] == [
            (b.id, b.content) for b in snapshot.blocks
        ]
