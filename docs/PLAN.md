# Three-stage implementation plan

Baseline established 2026-10-28. **Stages 1–3 are complete within the verification boundaries in PROGRESS.** The setup session produced documentation only; subsequent implementation and verification are recorded in [PROGRESS.md](PROGRESS.md).

Read AGENTS, PROJECT, ARCHITECTURE, DECISIONS, and PROGRESS before each stage. The architecture is the behavioral contract; update it and the decision log if a necessary implementation discovery changes the contract. Do not silently expand scope. Each stage has a complete prompt below and can be run in a separate Codex session after its prerequisite is complete.

## Schedule and scope budget

| Stage | Time | Required outcome |
| --- | --- | --- |
| 1 | 2.5–3 hours | Correct, tested comparison engine |
| 2 | 2–2.5 hours | Usable local interface and sample comparison |
| 3 | 1.5–2 hours | Realistic demo, robustness, repeatable delivery |

Total 6–7.5 focused hours, plus up to 30 minutes contingency. This excludes the initial research/setup session. Time estimates are not measured execution times. If work takes longer, preserve validation, core tests, truthful labels, and a coherent demo; reduce optional styling and extra visual detail. Do not add intraline diffing, integrations, or semantic models.

## Stage 1 — Core context comparison engine

**Status: complete (2026-10-28).** All 119 core tests, real-tokenizer checks, lint, formatting, and dependency consistency checks pass. The task list below is retained as the acceptance record. Only Python 3.12.2 was tested; the UI and full offline walkthrough are later-stage work.

**Objective:** Implement the UI-independent Python library for loading, comparing, tokenizing, and analyzing snapshots. No Streamlit application yet.

**Prerequisite:** Setup documentation exists; confirm the installed Python and inspect current Git changes. A previous partial implementation must be inspected before creating files.

### Tasks and files

1. Create `pyproject.toml`: setuptools `src/` package discovery, Python 3.10+ support, bounded compatible runtime requirements for tiktoken/Streamlit, pytest/Ruff development extra, and minimal test/lint/format configuration. Create `src/contextdiff/__init__.py`; remove its obsolete `.gitkeep` once real files exist. Create a local venv and install the project. Record actual Python and direct dependency versions; do not claim a Python version matrix was tested.
2. Create `models.py` and `loaders.py` implementing the version-1 contract. Validate required/unknown keys, types, enum values, duplicate JSON keys and IDs, UTF-8, newlines, and all size/count bounds. Accept empty blocks/content according to ARCHITECTURE. Provide field-specific errors and explicit JSON versus text loaders.
3. Create `diffing.py`: stable-ID status classification, deterministic ordering, both positions, exact content/role/kind equality, and line opcodes with work budgets and full-text fallback. No similarity matching or word highlighting.
4. Create `tokens.py`: fixed reference encoding, ordinary-text counts, cache warm-up instructions, and a recognizable initialization failure. Tokenization must not invoke an LLM. Use a counter injection boundary for tests.
5. Create `analysis.py`: assemble the serializable comparison, status totals, per-block/per-kind token accounting, signed/percentage changes, null unavailable metrics, and before-watchlist evidence. No UI imports or global user-data cache.
6. Create `tests/fixtures/` and `test_loaders.py`, `test_diffing.py`, `test_tokens.py`, `test_analysis.py`. Use small hand-authored cases and independently expected classifications/totals. Remove the tests directory placeholder after adding real files.
7. Update README with actual engine installation/testing status; update PROGRESS with outcomes, versions, limitations, and Stage 2 next. Align PLAN/ARCHITECTURE/DECISIONS if necessary. Keep Stage 2 and 3 pending.

### Acceptance criteria

- Valid JSON/text load through explicit APIs; malformed JSON does not silently become text. Boundary violations identify the problem. Raw whitespace and final newlines behave as documented.
- One fixture covers all four block statuses; identical snapshots produce only retained blocks. Stable-ID edits are modified; a new ID with identical content is added/removed. Duplicate content is not collapsed. Reorder preserves status and exposes positions. Role/kind-only changes remain visible.
- Both block-count conservation equations hold. Output order is stable and inputs are unchanged.
- Bounded line diffs produce expected insert/delete/replace/equal segments; repetitive or over-budget cases return complete sources and a reason for skipped detail.
- Reference counts use actual tiktoken; ordinary special-token-like strings do not fail. Real-tokenizer tests supplement stub-counter arithmetic tests.
- Before/after kind totals and the block-delta identity reconcile. Zero-token baselines give unavailable percentage change. Missing tokenizer metrics are null, while diff/watchlist results remain available.
- Watch checks return correct before/after source IDs and all three states. A phrase retained in a newly added summary is present_after. Unconfigured watches never imply complete preservation.
- Core code imports without Streamlit and has no model API requirement.

### Testing instructions

Run from the project root after creating the venv/package:

```sh
python -m pip install -e ".[dev]"
python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"
python -m pytest tests/test_loaders.py tests/test_diffing.py tests/test_tokens.py tests/test_analysis.py
python -m ruff check .
python -m ruff format --check .
```

Test invalid versions including `true`, wrong types, unknown keys, duplicate IDs/JSON keys, malformed UTF-8, Unicode byte limits, empty values, at-limit/over-limit inputs, repeated lines, final newline changes, missing baseline watches, changed kinds/roles, empty snapshots, and `counter=None`. Assert exact golden outcomes for a few tiny text diffs rather than testing only that output exists. A blocked tokenizer integration test must be reported explicitly; stubs alone do not complete tokenizer acceptance.

**Deliverables:** installable core package, fixture-based test suite, verified commands, and updated project records. No `app.py`, live UI, or polished scenario assets required.

**Definition of done:** all required core acceptance checks and lint/format checks pass, or any unresolved blocker is explicitly recorded and Stage 1 remains incomplete. Successful completion marks Stage 1 complete and Stage 2 pending in PROGRESS. Do not begin Stage 2 automatically.

### Exact Stage 1 prompt

```text
Implement Stage 1 of ContextDiff as specified in docs/PLAN.md. First read AGENTS.md, docs/PROGRESS.md, docs/PROJECT.md, docs/ARCHITECTURE.md, and docs/DECISIONS.md, then inspect the existing repository. Build only the UI-independent Python comparison engine, packaging, fixtures, and core tests. Follow the documented schema, stable-ID matching, bounded line diffs, reference token accounting, tokenizer-unavailable behavior, and watched-phrase limitations. Run the required checks and record exact outcomes and installed versions. Update README.md and the project documentation to reflect actual progress. Do not build the Streamlit app or start Stage 2. Finish by reporting what works, verification results, remaining issues, and the next recommended action.
```

## Stage 2 — Interactive visualization

**Status: complete (2026-10-28).** The local interface, basic sample, report export, 13 focused AppTest cases, and sample integration test are delivered. All 133 tests, lint, formatting, and dependency checks pass. Actual browser uploads/downloads, validation/recovery, filters, literal text, metadata, and laptop/narrow layouts were inspected. Exact outcomes are in PROGRESS. At that Stage 2 boundary no Stage 3 work had started; tasks below remain as the acceptance record.

**Objective:** Make the tested engine understandable and usable through a local Streamlit app.

**Prerequisite:** Stage 1 is complete and its tests pass. If it is incomplete, finish required core work and record the scope before proceeding; do not build a UI on knowingly incorrect comparisons.

### Tasks and files

1. Create `app.py` as a thin renderer/orchestrator. Add a brief explanation, one JSON/text selector, Before/After columns, explicit paste/upload selection on each side, a Compare action, and a single bundled-example selector. Respect byte limits for pasted content as well as uploaded files. Clear old results on input/source/format changes.
2. Create a small `examples/basic.before.json` / `basic.after.json` pair with hand-checked expectations; remove `examples/.gitkeep`. It must exercise all four block statuses and a missing watched phrase. Reuse the example in a core integration test.
3. Render before/after content-token metrics, signed/percentage change, four status counts, and watched-phrase review results with source IDs. Include unavailable-token and no-watchlist states. Add one native before/after token chart by kind; no Plotly dependency.
4. Add status/kind filters and labeled source panels. Show metadata changes, positions, full text, and readable line edits. Native code/text blocks are sufficient. Provide clear notices when detailed alignment was skipped. Avoid raw HTML for user content; use text labels alongside color.
5. Add in-memory JSON report download, including the reference encoding and limitations. Explain that the report contains supplied text. Keep summary totals global when filtering rows.
6. Create `.streamlit/config.toml` to disable usage collection and set a reasonable upload transport limit; Python remains responsible for the stricter 256 KiB cap. Document binding to localhost.
7. Add `tests/test_app.py` using Streamlit AppTest for sample loading/comparison, invalid pasted input, input-change invalidation, and tokenizer-unavailable messaging. Update README/PROGRESS/PLAN and relevant architecture decisions based on actual behavior.

### Acceptance criteria

- The app launches with the documented single command and no API key. Both input methods and both formats work; blank text and invalid JSON are distinguished.
- A new user can load the sample and identify additions, removals, modification, retained content, token change, and the missing phrase without reading code.
- Every displayed metric comes from the core report. Status/kind filters do not change aggregate totals. Changed roles/kinds and detail-budget notices remain visible.
- Changing inputs invalidates stale output. A validation or tokenizer problem explains recovery without exposing private content in a traceback. Non-token comparison remains usable when reference tokens are unavailable.
- Reports download as valid JSON consistent with the displayed comparison. User text is never treated as executable markup.
- The layout is readable on a normal laptop viewport; labels and text communicate statuses without relying only on color.

### Testing instructions

```sh
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m streamlit run app.py --server.address 127.0.0.1
```

Use AppTest for supported widget flows, then manually inspect browser behavior: load sample, compare pasted text, upload valid JSON/text, upload malformed/oversized input, change an input after comparison, filter each category, inspect metadata-only edits, and download/reopen the report. Test HTML/script-looking content as literal text. Record manual checks separately from automated tests. AppTest alone does not establish visual quality or real upload/download behavior.

**Deliverables:** runnable interface, one coherent sample, report export, focused UI tests, and accurate setup documentation.

**Definition of done:** core and UI checks pass, the manual demo flow is inspected, documentation reflects observed behavior, and PROGRESS marks Stage 2 complete and Stage 3 pending. No cloud deployment or live integrations. Do not start Stage 3 automatically.

### Exact Stage 2 prompt

```text
Implement Stage 2 of ContextDiff from docs/PLAN.md. Read AGENTS.md and the project, architecture, decisions, and progress documents first. Verify Stage 1 is complete and preserve its core contracts. Build a thin Streamlit interface for explicit JSON/text paste and upload inputs, a bundled sample, token/status summaries, watched-phrase evidence, filters, readable source/diff panels, and JSON report download. Add focused AppTest coverage and inspect actual browser uploads, downloads, errors, and layout. Run the full relevant checks and update README.md and project documentation with exact outcomes. Stop after Stage 2; do not add integrations or start Stage 3.
```

## Stage 3 — Polish, realistic demo, and delivery

**Status: complete (2026-10-28).** All 141 tests, lint/format, fresh range-based
installation, second snapshot-based installation, sample/report checks, timings,
and actual browser flows passed. The full warmed app flow ran under macOS
app-process isolation that denied external outbound connections while allowing
localhost; the browser/machine were not globally offline. The paced browser
rehearsal took 93.4 seconds; independent spoken delivery was not timed. Other
platforms/Python versions remain untested. Exact evidence and boundaries are in
PROGRESS. Tasks below remain as the acceptance record; no next stage is scheduled.

**Objective:** Deliver a convincing, honest demonstration that another engineer can reproduce locally.

**Prerequisite:** Stages 1 and 2 are complete and runnable.

### Tasks and files

1. Add `examples/handoff.before.json`, `handoff.lossy.after.json`, and `handoff.preserved.after.json`: synthetic webhook-debugging context with a stable instruction, edited task, verbose removed tool output, new summary, and a critical 24-hour idempotency constraint. The lossy version drops that phrase; the alternative preserves it. Include one phrase preserved across both summaries. Do not label ordinary debugging logs as a real Nessie export.
2. Add `examples/retrieval.before.json` / `retrieval.after.json` as a small source-swap example illustrating that removed active context may remain externally retrievable. Keep this scenario smaller than the main demo. Document IDs, expected statuses, watch evidence, and independently checked token results in `examples/README.md`.
3. Update `app.py` example choices and polish spacing, empty states, labels, error recovery, long-text panels, and final-newline readability. Improve only what the actual walkthrough exposes; no new frontend stack.
4. Extend existing tests with scenario expectations and any uncovered boundary regressions. Exercise identical inputs, all-added/all-removed, empty inputs, role-only edits, paraphrases, negation, non-ASCII/special-token text, repetitive data, and unavailable tokenizer. Reuse covered Stage 1 cases rather than duplicating them.
5. Create `docs/DEMO.md`: 90-second script, setup/cache prerequisites, expected observations, limitations, and a small result table using actual computed metrics. The script compares lossy then preserved handoffs and briefly shows retrieval churn. Add a real screenshot only if the app is running and the image is captured; do not fabricate one.
6. Record normal-example comparison timing with warmed encoding on the actual machine. Aim for under one second; avoid flaky wall-clock assertions in the unit suite. Confirm budget fallback remains responsive on repetitive input.
7. Verify a fresh venv installation and localhost launch. Record Python/OS and resolved direct/transitive versions in `requirements-tested.txt` from the tested isolated environment, excluding local editable paths. Treat it as the tested-environment dependency snapshot, not a universal cross-platform lock. Document repeat installation with that snapshot plus editable package installation.
8. Verify the sample flow with external network access disabled after dependency installation and tokenizer warm-up. Record the method and result; if the environment cannot establish that condition, state that offline verification remains unverified and do not mark that acceptance item passed.
9. Finalize README with actual functionality, setup, test commands, example flow, limitations, and demo link. Update PROGRESS, PLAN, ARCHITECTURE, and DECISIONS as needed. Keep private inputs and machine-specific caches out of Git changes.

### Acceptance criteria

- Both handoff variants and the retrieval swap load through the normal user flow. Their statuses and watched-phrase outcomes match written expectations.
- The lossy summary actually uses fewer reference content tokens; compute and inspect this rather than inventing savings. The preserved version demonstrates a watched phrase surviving in a new summary despite removed source blocks.
- Paraphrase/negation limitations and absent watches are explained. No screen claims semantic completeness, universal billing accuracy, hidden-state inspection, or measured model-quality improvement.
- The walkthrough lasts approximately 90 seconds and works without accounts, paid services, or live model calls. Another engineer has sufficient instructions to reproduce it.
- Fresh installation, launch, offline warmed-cache flow, core/UI tests, lint, formatting, and actual manual UI checks have recorded results. Any unverified requirement remains visible and blocks a false “fully complete” claim.
- Typical sample timing and environment are recorded. No unsupported scalability promise is added.

### Testing instructions

Run the same full suite, lint, format check, and local launch command as Stage 2. Also execute the documented clean-environment install, all example comparisons, report round trip, repetitive-input fallback, and warmed-cache offline walkthrough. Measure engine comparison independently from Streamlit startup/encoding initialization and report the timing boundary. Confirm the final README matches commands actually run.

**Deliverables:** polished local app, realistic synthetic examples and expectations, demo guide, tested dependency snapshot, and final honest project documentation. No public publication or outreach is requested.

**Definition of done:** all delivery acceptance items are verified; PROGRESS records Stages 1–3 complete, checks and environment, known limits, and any truly optional follow-ups. If required work remains, record it and leave Stage 3 incomplete.

### Exact Stage 3 prompt

```text
Implement Stage 3 of ContextDiff from docs/PLAN.md. Read AGENTS.md and all relevant project records, verify Stages 1 and 2, and finish the local demonstration without expanding scope. Add synthetic lossy/preserved coding-agent handoffs and a small retrieval-swap example with checked expectations. Polish the actual UI flow, cover remaining meaningful edge cases, write docs/DEMO.md, and finalize README.md. Run and record core/UI checks, manual browser checks, fresh-environment installation, sample timings, report validation, and a warmed-cache offline walkthrough. Capture tested dependency versions without local editable paths. Update PROGRESS.md, PLAN.md, ARCHITECTURE.md, and DECISIONS.md as needed. State any unverified acceptance item explicitly; do not claim completion or performance without evidence. Do not publish, deploy, or contact anyone.
```
