"""Widget flows; real uploads, downloads, and layout also require a browser."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import contextdiff

ROOT = Path(__file__).parents[1]


@pytest.fixture
def app(monkeypatch):
    # UI arithmetic is not a tokenizer test; real encoding has separate coverage.
    monkeypatch.setattr(
        contextdiff, "create_token_counter", lambda: lambda text: len(text.split())
    )
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()


def sample(app):
    app.button[0].click().run()
    app.button[1].click().run()
    assert not app.exception
    return app.session_state["report"]


def test_sample_metrics_watches_filters_and_export(app):
    report = sample(app)
    assert [metric.value for metric in app.metric] == [
        "19",
        "21",
        "+2",
        "1",
        "1",
        "1",
        "2",
    ]
    assert [watch.status for watch in report.watches] == [
        "present_after",
        "missing_after",
        "unverified_baseline",
    ]
    assert report.watches[1].before_block_ids == ("constraint",)
    assert report.watches[1].after_block_ids == ()
    assert any("metadata-only" in item.value for item in app.info)
    baseline = [metric.value for metric in app.metric]
    app.multiselect(key="statuses").set_value(["modified"]).run()
    app.multiselect(key="kinds").set_value(["tool_result"]).run()
    assert [metric.value for metric in app.metric] == baseline
    assert any("Showing 1 of 5" in item.value for item in app.caption)
    assert any("Block ID: finding" in item.value for item in app.text)
    app.multiselect(key="statuses").set_value([]).run()
    assert any("No blocks match" in item.value for item in app.info)
    assert app.session_state["report"] == report
    exported = json.loads(json.dumps(report.to_dict()))
    assert len(exported["blocks"]) == 5
    assert exported["reference_encoding"] == "cl100k_base"
    assert exported["limitations"]
    assert len(app.get("download_button")) == 1
    assert not app.exception


@pytest.mark.parametrize(
    "change", ["before", "after", "format", "before_source", "after_source", "sample"]
)
def test_input_changes_remove_stale_results(app, change):
    sample(app)
    if change in ("before", "after"):
        app.text_area(key=f"{change}_paste").set_value("broken").run()
    elif change == "format":
        app.radio(key="format").set_value("Text").run()
    elif change == "sample":
        app.button[0].click().run()
    else:
        app.radio(key=change).set_value("Upload").run()
    assert "report" not in app.session_state
    assert not app.metric
    assert not app.get("download_button")
    assert not app.exception


def test_invalid_json_safe_error_and_recovery(app):
    app.text_area(key="before_paste").set_value('{"PRIVATE_MARKER":').run()
    app.button[1].click().run()
    assert len(app.error) == 2
    assert all("invalid JSON" in error.value for error in app.error)
    assert all("PRIVATE_MARKER" not in error.value for error in app.error)
    assert not app.exception
    sample(app)
    assert not app.error


def test_missing_upload_is_distinct_from_empty_text(app):
    app.radio(key="format").set_value("Text").run()
    app.radio(key="before_source").set_value("Upload").run()
    app.button[1].click().run()
    assert "choose a file" in app.error[0].value
    app.radio(key="before_source").set_value("Paste").run()
    app.button[1].click().run()
    assert not app.error
    assert app.session_state["report"].tokens.before_total == 0
    assert any("Percentage change unavailable" in item.value for item in app.caption)
    assert any("No watched phrases configured" in item.value for item in app.info)


def test_tokenizer_unavailable_and_retry(app, monkeypatch):
    def unavailable():
        raise contextdiff.TokenizerUnavailableError("PRIVATE_SETUP_DETAIL")

    monkeypatch.setattr(contextdiff, "create_token_counter", unavailable)
    sample(app)
    assert any("Reference tokens unavailable" in item.value for item in app.warning)
    assert all("PRIVATE_SETUP_DETAIL" not in item.value for item in app.warning)
    report = app.session_state["report"]
    assert report.tokens.before_total is None
    assert report.tokens.delta is None
    assert report.status_counts.modified == 2
    assert report.watches[1].status == "missing_after"
    assert [metric.value for metric in app.metric][:3] == ["Unavailable"] * 3
    monkeypatch.setattr(contextdiff, "create_token_counter", lambda: len)
    app.button[1].click().run()
    assert app.session_state["report"].tokens.status == "available"
    assert not any("Reference tokens unavailable" in item.value for item in app.warning)


@pytest.mark.parametrize(
    "value, message",
    [
        ("é" * 131073, "262144 UTF-8 bytes"),
        ("x" * 50001, "50000 characters"),
    ],
)
def test_paste_limits(app, value, message):
    app.radio(key="format").set_value("Text").run()
    app.text_area(key="before_paste").set_value(value).run()
    app.button[1].click().run()
    assert message in app.error[0].value
    assert "report" not in app.session_state
    assert not app.exception


def test_literal_content_and_alignment_fallback(app):
    app.radio(key="format").set_value("Text").run()
    before = "<script>alert('literal')</script>\n" + "same\n" * 1001
    after = "<img src=x onerror=alert('literal')>\n" + "same\n" * 1001
    app.text_area(key="before_paste").set_value(before).run()
    app.text_area(key="after_paste").set_value(after).run()
    app.button[1].click().run()
    assert not app.exception
    assert any("Detailed alignment skipped" in item.value for item in app.info)
    # Streamlit removes one boundary newline from a code panel, not the report.
    assert app.code[0].value == before.removesuffix("\n")
    assert app.code[1].value == after.removesuffix("\n")
    assert app.session_state["report"].blocks[0].before.content == before
    assert app.session_state["report"].blocks[0].after.content == after
    assert any("Ends with LF newline" in item.value for item in app.caption)


@pytest.mark.parametrize(
    "choice, missing, added, removed, modified",
    [
        ("Coding handoff · lossy", True, 1, 3, 1),
        ("Coding handoff · preserved", False, 1, 3, 1),
        ("Retrieval · source swap", True, 1, 1, 0),
    ],
)
def test_scenario_selection_load_reset_and_watch_evidence(
    app, choice, missing, added, removed, modified
):
    sample(app)
    app.selectbox(key="example").select(choice).run()
    assert "report" not in app.session_state
    app.radio(key="format").set_value("Text").run()
    app.radio(key="before_source").set_value("Upload").run()
    report = sample(app)
    assert app.radio(key="format").value == "JSON"
    assert app.radio(key="before_source").value == "Paste"
    assert report.status_counts.added == added
    assert report.status_counts.removed == removed
    assert report.status_counts.modified == modified
    assert report.status_counts.retained == 1
    assert (report.watches[0].status == "missing_after") is missing
    assert any("handoff-summary" in t.value for t in app.text) or modified == 0
    assert not app.error


def test_final_newline_only_change_and_role_only_edit(app):
    app.radio(key="format").set_value("Text").run()
    app.text_area(key="before_paste").set_value("café <|endoftext|>").run()
    app.text_area(key="after_paste").set_value("café <|endoftext|>\n").run()
    app.button[1].click().run()
    assert app.session_state["report"].status_counts.modified == 1
    assert any("No final LF newline" in c.value for c in app.caption)
    assert any("Ends with LF newline" in c.value for c in app.caption)
    assert any("No newline at end of source" in c.value for c in app.code)
    app.radio(key="format").set_value("JSON").run()
    for side, role in (("before", "user"), ("after", "assistant")):
        value = {
            "schema_version": 1,
            "blocks": [
                {"id": "role", "kind": "message", "role": role, "content": "same"}
            ],
        }
        app.text_area(key=f"{side}_paste").set_value(json.dumps(value)).run()
    app.button[1].click().run()
    assert any("metadata-only" in i.value for i in app.info)
    assert any("role user → assistant" in t.value for t in app.text)
    assert not app.exception


def test_empty_json_snapshots_have_clear_empty_state_and_export(app):
    for side in ("before", "after"):
        app.text_area(key=f"{side}_paste").set_value(
            '{"schema_version":1,"blocks":[]}'
        ).run()
    app.button[1].click().run()
    assert [m.value for m in app.metric] == ["0", "0", "+0", "0", "0", "0", "0"]
    assert any("both snapshots contain no blocks" in i.value for i in app.info)
    assert len(app.get("download_button")) == 1
    assert not app.exception
