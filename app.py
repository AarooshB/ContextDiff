"""Local Streamlit UI; all comparison semantics live in contextdiff."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from contextdiff import (
    Comparison,
    Snapshot,
    SnapshotValidationError,
    TokenizerUnavailableError,
    compare_snapshots,
    create_token_counter,
    load_json_snapshot,
    load_text_snapshot,
)
from contextdiff.loaders import MAX_INPUT_BYTES
from contextdiff.models import Block, BlockChange, LineDetail

EXAMPLES = Path(__file__).parent / "examples"
SAMPLES = {
    "Basic comparison": ("basic.before.json", "basic.after.json"),
    "Coding handoff · lossy": ("handoff.before.json", "handoff.lossy.after.json"),
    "Coding handoff · preserved": (
        "handoff.before.json",
        "handoff.preserved.after.json",
    ),
    "Retrieval · source swap": ("retrieval.before.json", "retrieval.after.json"),
}
STATUSES = ("added", "removed", "retained", "modified")


def clear_result() -> None:
    """Discard comparison and its view state whenever an input changes."""
    for key in ("report", "token_warning", "input_errors", "statuses", "kinds"):
        st.session_state.pop(key, None)


def load_sample() -> None:
    clear_result()
    st.session_state["format"] = "JSON"
    paths = SAMPLES[st.session_state["example"]]
    for side, filename in zip(("before", "after"), paths, strict=True):
        st.session_state[f"{side}_source"] = "Paste"
        st.session_state[f"{side}_paste"] = (EXAMPLES / filename).read_text(
            encoding="utf-8"
        )


def input_panel(side: str, file_format: str) -> None:
    st.subheader(side.title())
    source = st.radio(
        f"{side.title()} source",
        ("Paste", "Upload"),
        horizontal=True,
        key=f"{side}_source",
        on_change=clear_result,
    )
    if source == "Paste":
        st.text_area(
            f"{side.title()} content",
            height=210,
            key=f"{side}_paste",
            on_change=clear_result,
            placeholder="Paste a version-1 snapshot" if file_format == "JSON" else "",
        )
    else:
        st.file_uploader(
            f"{side.title()} file",
            type=["json"] if file_format == "JSON" else ["txt", "text"],
            key=f"{side}_upload_{file_format}",
            on_change=clear_result,
            help="UTF-8; at most 256 KiB. The selected format is always used.",
        )


def read_input(side: str, file_format: str) -> Snapshot:
    if st.session_state[f"{side}_source"] == "Upload":
        uploaded = st.session_state.get(f"{side}_upload_{file_format}")
        if uploaded is None:
            raise SnapshotValidationError("choose a file or switch to Paste")
        if uploaded.size > MAX_INPUT_BYTES:
            raise SnapshotValidationError("input: must be at most 262144 UTF-8 bytes")
        data = uploaded.getvalue()
    else:
        try:
            data = st.session_state.get(f"{side}_paste", "").encode("utf-8")
        except UnicodeEncodeError:
            raise SnapshotValidationError("input: must be valid UTF-8") from None
    if file_format == "JSON":
        return load_json_snapshot(data)
    return load_text_snapshot(data, label=side.title())


def run_comparison(file_format: str) -> None:
    clear_result()
    snapshots = {}
    errors = []
    for side in ("before", "after"):
        try:
            snapshots[side] = read_input(side, file_format)
        except SnapshotValidationError as error:
            errors.append(
                f"{side.title()}: {error}. Correct the input and Compare again."
            )
    if errors:
        st.session_state["input_errors"] = errors
        return
    try:
        counter = create_token_counter()
    except TokenizerUnavailableError:
        counter = None
        st.session_state["token_warning"] = (
            "Reference tokens unavailable. Diff and watched-phrase checks still work. "
            "Check network/cache access, run the README tokenizer warm-up command, "
            "then Compare again to retry. Token metrics in the report are null."
        )
    st.session_state["report"] = compare_snapshots(
        snapshots["before"], snapshots["after"], counter=counter
    )


def render_summary(report: Comparison) -> None:
    st.subheader("Comparison")
    if report.before_label is not None:
        st.text(f"Before: {report.before_label}")
    if report.after_label is not None:
        st.text(f"After: {report.after_label}")
    st.caption("Content tokens · cl100k_base reference. Content counted per block.")
    tokens = report.tokens
    values = (tokens.before_total, tokens.after_total, tokens.delta)
    for column, label, value in zip(
        st.columns(3),
        ("Before tokens", "After tokens", "Token change"),
        values,
        strict=True,
    ):
        display = "Unavailable" if value is None else f"{value:,}"
        if label == "Token change" and value is not None:
            display = f"{value:+,}"
        column.metric(label, display)
    percentage = tokens.percentage_change
    st.caption(
        f"Change from before: {percentage:+.1f}%"
        if percentage is not None
        else "Percentage change unavailable: no tokens or before total is zero."
    )
    for column, status in zip(st.columns(4), STATUSES, strict=True):
        column.metric(status.title(), getattr(report.status_counts, status))
    if tokens.status == "available":
        with st.expander("Content tokens by kind"):
            st.bar_chart(
                [
                    {"Kind": row.kind, "Before": row.before, "After": row.after}
                    for row in tokens.by_kind
                ],
                x="Kind",
                y=["Before", "After"],
                stack=False,
                color=["#526D82", "#087F8C"],
            )
    st.caption(
        "Counts exclude metadata, provider wrappers, hidden context, and billing."
    )


def render_watches(report: Comparison) -> None:
    st.subheader("Watched phrases")
    if report.watchlist_status == "not_configured":
        st.info("No watched phrases configured. This is not a preservation assessment.")
        return
    st.caption(
        "Only the before watchlist defines checks. Matching ignores case and collapses "
        "whitespace within each block. Paraphrases can be missed; negation can match."
    )
    for watch in report.watches:
        with st.container(border=True):
            if watch.status == "missing_after":
                st.warning("Potential loss: watched phrase missing")
                st.caption(
                    "Phrase not found in the supplied after snapshot; it may have been "
                    "paraphrased or remain in external memory."
                )
            elif watch.status == "unverified_baseline":
                st.info("Unverified baseline: phrase not found before")
            else:
                st.success("Present after: watched phrase found")
            st.code(watch.item.text, language=None, wrap_lines=True)
            st.text(f"Watch ID: {watch.item.id}")
            if watch.item.note:
                st.text(watch.item.note)
            st.text(
                "Before source IDs: " + (", ".join(watch.before_block_ids) or "None")
            )
            st.text("After source IDs: " + (", ".join(watch.after_block_ids) or "None"))


def source_panel(label: str, block: Block | None, position: int | None) -> None:
    st.markdown(f"**{label} source**")
    if block is None:
        st.caption("Block absent")
        return
    st.text(f"Kind: {block.kind} | Role: {block.role or 'none'}")
    st.caption(f"Position: {position + 1} (one-based)")
    content = block.content
    st.caption(
        f"{len(content):,} characters | "
        + ("Ends with LF newline" if content.endswith("\n") else "No final LF newline")
    )
    if not content:
        st.caption("Empty content")
    st.code(
        content,
        language=None,
        wrap_lines=True,
        height=240 if len(content) > 1200 or content.count("\n") > 12 else "content",
    )


def line_edits(detail: LineDetail) -> str:
    """Render the core opcodes without recomputing or hiding newline differences."""
    lines = []
    for opcode in detail.opcodes:
        lines.append(
            f"@@ Before [{opcode.before_start + 1}:{opcode.before_end}] "
            f"After [{opcode.after_start + 1}:{opcode.after_end}] "
            f"{opcode.tag} @@\n"
        )
        groups = (
            ((" ", opcode.before_lines),)
            if opcode.tag == "equal"
            else (("-", opcode.before_lines), ("+", opcode.after_lines))
        )
        for prefix, source_lines in groups:
            for line in source_lines:
                lines.append(prefix + line)
                if not line.endswith("\n"):
                    lines.append("\n\\ No newline at end of source\n")
    return "".join(lines)


def render_change(change: BlockChange, index: int) -> None:
    with st.expander(
        f"{change.status.title()} block {index}", expanded=change.status != "retained"
    ):
        st.text(f"Block ID: {change.id}")
        if change.token_delta is not None:
            st.caption(
                f"Content tokens: {change.before_tokens} before / "
                f"{change.after_tokens} after / {change.token_delta:+} change"
            )
        for column, label, block, position in zip(
            st.columns(2),
            ("Before", "After"),
            (change.before, change.after),
            (change.before_position, change.after_position),
            strict=True,
        ):
            with column:
                source_panel(label, block, position)
        if change.before and change.after:
            if (change.before.kind, change.before.role) != (
                change.after.kind,
                change.after.role,
            ):
                st.text(
                    f"Metadata changed: kind {change.before.kind} → "
                    f"{change.after.kind}; role {change.before.role or 'none'} → "
                    f"{change.after.role or 'none'}"
                )
            if change.status == "modified" and change.line_detail is None:
                st.info("Content unchanged; metadata-only modification.")
        if change.line_detail:
            if change.line_detail.status == "skipped":
                st.info(
                    "Detailed alignment skipped: "
                    f"{change.line_detail.skip_reason} "
                    "Complete sources are shown above."
                )
            else:
                st.caption(
                    "Line edits: − before, + after, space unchanged. "
                    "Ranges use one-based starts and inclusive ends; empty ranges "
                    "have an end smaller than the start."
                )
                st.code(
                    line_edits(change.line_detail),
                    language="diff",
                    wrap_lines=True,
                    height=280,
                )


def render_blocks(report: Comparison) -> None:
    st.subheader("Blocks and line edits")
    st.caption(
        "Filters affect only the blocks below. Summary totals, watched phrases, "
        "and the downloaded report always cover the full comparison. "
        "Retained means unchanged content, kind, and role under the same ID."
    )
    st.caption(
        "Code panels can hide a boundary newline. Character counts and final-newline "
        "labels describe the original text; JSON export preserves it exactly."
    )
    left, right = st.columns(2)
    statuses = left.multiselect("Statuses", STATUSES, default=STATUSES, key="statuses")
    kinds = sorted(
        {
            block.kind
            for change in report.blocks
            for block in (change.before, change.after)
            if block is not None
        }
    )
    selected_kinds = right.multiselect("Kinds", kinds, default=kinds, key="kinds")
    shown = [
        (index, change)
        for index, change in enumerate(report.blocks, 1)
        if change.status in statuses
        and any(
            block and block.kind in selected_kinds
            for block in (change.before, change.after)
        )
    ]
    st.caption(
        f"Showing {len(shown)} of {len(report.blocks)} blocks "
        "(after order, then removed)."
    )
    if not shown:
        st.info("No blocks match these filters, or both snapshots contain no blocks.")
    for index, change in shown:
        render_change(change, index)


def main() -> None:
    st.set_page_config(page_title="ContextDiff", layout="wide")
    st.title("ContextDiff")
    st.write(
        "Compare supplied LLM context snapshots. See what changed, "
        "how content tokens shifted, and which watched phrases disappeared."
    )
    st.caption("Local comparison. No model calls, accounts, or API keys.")
    example, action = st.columns([3, 1], vertical_alignment="bottom")
    example.selectbox(
        "Bundled example", tuple(SAMPLES), key="example", on_change=clear_result
    )
    action.button("Load sample", on_click=load_sample, use_container_width=True)
    st.caption(
        "Choose an example, Load sample, then Compare. All examples are synthetic. "
        "Compare the lossy and preserved handoffs to review the same constraint."
    )
    file_format = st.radio(
        "Input format",
        ("JSON", "Text"),
        key="format",
        horizontal=True,
        on_change=clear_result,
    )
    st.caption(
        "256 KiB per input; 200 blocks; 50,000 characters per block; 50 watches. "
        "JSON uses the ContextDiff v1 schema and stable IDs. "
        "Text is one document; blank text is valid. Input changes clear results."
    )
    for column, side in zip(st.columns(2), ("before", "after"), strict=True):
        with column:
            input_panel(side, file_format)
    if st.button("Compare", type="primary"):
        run_comparison(file_format)
    for error in st.session_state.get("input_errors", []):
        st.error(error)
    if "token_warning" in st.session_state:
        st.warning(st.session_state["token_warning"])
    report = st.session_state.get("report")
    if report is None:
        st.info("Load the sample or supply both inputs, then Compare.")
        return
    st.divider()
    render_summary(report)
    st.download_button(
        "Download JSON report",
        data=json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        file_name="contextdiff-report.json",
        mime="application/json",
        on_click="ignore",
    )
    st.caption(
        "The report contains complete supplied text. Save or share it intentionally."
    )
    render_watches(report)
    render_blocks(report)
    with st.expander("Interpretation limits"):
        for limitation in report.limitations:
            st.write(limitation)


if __name__ == "__main__":
    main()
