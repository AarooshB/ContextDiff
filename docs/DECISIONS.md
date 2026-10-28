# Technical decisions

Recorded 2026-10-28. All decisions below are accepted for the MVP. Stages 1–3 are implemented and verified within PROGRESS's stated boundaries. Update this log when a material choice changes.

| ID | Decision and rationale | Alternatives rejected or deferred |
| --- | --- | --- |
| D01 | One local Python process with a pure core and Streamlit UI. Fits a one-day solo build and lets the UI reuse tested results directly. | FastAPI + React adds API contracts and frontend tooling; a CLI alone gives a weaker visual demo. |
| D02 | Standard-library dataclasses and explicit validation for a small versioned JSON format. | Pydantic/JSON Schema dependencies are unnecessary at this scale; provider schemas and automatic chat segmentation multiply scope. |
| D03 | Required stable JSON block IDs determine identity. Exact content/kind/role equality determines retention. Show positions separately. | Fuzzy matching and embeddings can pair unrelated repeated messages or mistake a paraphrase for preservation. No-ID JSON import is deferred. |
| D04 | Plain text is one document block with a line diff. | Paragraph/role inference creates fragile identities and misrepresents arbitrary pasted text. |
| D05 | Use difflib line opcodes with `autojunk=False` and explicit work budgets. Preserve full text if alignment is skipped. | RapidFuzz similarity is useful for approximate search but unnecessary for identity-based comparison. Character/word diff is deferred. Unbounded alignment is unsuitable for repetitive inputs. |
| D06 | Use one fixed `cl100k_base` tiktoken reference, summed per block. Exclude transport metadata and expose the counting convention. | Automatic model selection suggests unjustified provider accuracy. Hugging Face Tokenizers is versatile but adds model-asset choices we do not need. Character heuristics are not a silent fallback. |
| D07 | Document tokenizer warm-up and cache requirements. Comparison remains usable with token metrics unavailable. | Claiming complete first-run offline operation would ignore tokenizer data downloads. Bundling vocabulary assets adds distribution work outside this demo. |
| D08 | Optional before-snapshot watchlist uses literal, casefolded, whitespace-normalized phrase checks with source block IDs. | Automatic importance scores and LLM-based fact extraction introduce unverifiable judgments, nondeterminism, and API requirements. Semantic equivalence/contradiction detection is deferred. |
| D09 | A summary with a new ID is added; original messages are removed. Phrase checks can still find a tracked detail in the summary. | Treating a summary as a verified modification of multiple messages would claim provenance or meaning we cannot establish. |
| D10 | Bound input to 256 KiB, 200 blocks, 50,000 characters per block, and 50 watches. Bound line alignment separately. | Million-token support and trace ingestion would exceed the demo's performance and UI budget. |
| D11 | No database, accounts, paid APIs, cloud deployment, vector store, or live Nessie integration. Keep inputs in local session memory. | Production observability and reusable memory services are separate products, not prerequisites for this comparison tool. |
| D12 | Two runtime dependencies; pytest and Ruff for development. Add pyproject in Stage 1 and record tested versions; capture reproducible dependencies at delivery. | User-requested minimal GitHub Actions CI was added in the post-stage polish; Docker, package publishing, coverage gates, and additional tooling remain deferred. No unsupported version pins in setup docs. |
| D13 | Synthetic, hand-authored demo data with manually checked expectations. Show a lossy summary, preserved alternative, and small retrieval swap. | Real private traces create sharing friction; generated benchmark claims would require model experiments outside the MVP. |
| D14 | Setup session produces only docs/configuration/placeholders. Stage 1 begins through a separate user prompt. | Implementing an attractive prototype now would violate the requested session boundary. |

## Interpretation rules

“Retained” means an unchanged block under the same ID, not preserved model knowledge. “Missing” means a watched phrase is absent under the documented match rule, not proven semantic loss. “Content tokens” means a reference encoding count, not provider billing. No decision assumes a verified Nessie diff feature, compression algorithm, or private architecture.

## Stage 1 implementation record — 2026-10-28

- No schema or algorithm departure was required. Report version 1 is concretized in ARCHITECTURE using frozen dataclasses, tuple collections, and a detached `to_dict()` representation. Loaders own external validation; trusted internal/test constructors do not duplicate it.
- Byte bounds are checked on original input, including a BOM; content-character bounds follow newline normalization. Unknown-key/duplicate-key errors name the containing object without printing arbitrary supplied keys. Deep JSON and parser numeric-limit errors are sanitized alongside syntax errors.
- Packaging uses Python `>=3.10`, tiktoken `>=0.12,<1`, Streamlit `>=1.50,<2`, pytest `>=8,<10`, and Ruff `>=0.14,<1`. Actual verified resolution on Python 3.12.2 is recorded in PROGRESS. Installed Streamlit 1.66.1 requires Python 3.11+; pip must select a compatible earlier release for Python 3.10, which was not tested. No compatibility-matrix claim is made.
- Tokenizer initialization wraps expected dependency/network/cache errors only. No tokenizer is initialized at core import time; callers explicitly pass the reference counter or `None`. Invalid counter results and programming errors are allowed to fail visibly.
- A project-local cache under ignored `.venv/tiktoken-cache` makes warm-up reproducible within this workspace. Socket-blocked subprocess tests cover warmed core operation, cold-cache unavailability, and recovery. They do not establish a complete offline UI walkthrough or machine-wide network isolation; those delivery checks remain Stage 3.

## Stage 2 implementation record — 2026-10-28

- No core/schema/report contract change and no dependency additions. `app.py` is a renderer/orchestrator over the existing loaders, tokenizer factory, and comparison report. The supplied text, IDs, labels, and notes use native text/code; static headings alone use Markdown.
- Native controls and a light slate/teal theme keep the UI within the Streamlit scope. A single basic-example selector and explicit Load sample action reset format/sources/text; Compare remains an explicit action. Input callbacks discard derived state; filters never recalculate aggregate metrics or narrow export data.
- Kind filters include either side of a change. This keeps a tool_result → memory transfer visible under both kinds. Positions render one-based while reports retain zero-based indexes.
- Native Streamlit 1.66.1 code panels remove one leading/trailing newline for display (verified in its installed `elements/code.py` and AppTest). Keep the original strings in report data, disclose the display behavior, show character/final-LF labels, and mark missing endings in line edits. Custom HTML rendering and intraline diffing remain deferred.
- Upload transport is 1 MiB; Python applies the existing 256 KiB boundary to uploads and paste. Usage statistics and file watching are disabled; source edits require browser reload/server restart. The server binds to localhost. This does not establish the full offline app condition, which remains Stage 3 work.
- AppTest covers supported widget flows; a real browser separately verifies file selection/transfers, saved JSON, error recovery, filters, literal content, and layout. The browser-downloaded sample report was reopened and compared field-for-field against the real-tokenizer core report. Detailed outcomes are in PROGRESS.

## Stage 3 delivery record — 2026-10-28

- D13 is realized with hand-authored lossy/preserved webhook handoffs sharing one
  before, plus a smaller retrieval source swap. Checked identities and watch
  evidence are independent of token counts. Direct per-block tokenizer calls and
  manually reconciled totals establish the fixed scenario goldens. No semantic,
  real webhook execution, or model-quality claims follow.
- The existing selector adds three choices with a fixed local filename mapping.
  Changing the choice invalidates results; Load sample resets both JSON/Paste
  inputs, and Compare remains explicit. Native layout, scrolling source panels,
  boundary-newline disclosure, and lexical limitations survived actual walkthrough
  checks; additional styling or a frontend framework was unnecessary.
- D12's tested snapshot is requirements-tested.txt: all 42 installed distribution
  versions including pip, excluding ContextDiff and local editable paths. A second
  fresh venv installed the pins then the local editable package with `--no-deps`;
  all pins matched and real-tokenizer integrations passed. Build-isolation tooling
  is separately resolved. This is one tested macOS/Python environment, not a
  cross-platform lock or tested compatibility matrix.
- D07's full-app offline check uses macOS process sandboxing to deny external
  outbound connections while permitting localhost. A denied external TCP probe
  and successful full browser flow establish this boundary. Machine-wide network
  changes were unnecessary; the browser itself was not disconnected. No general
  offline-first cold-start claim or new runtime network guard was introduced.
- Timings bracket only warmed `compare_snapshots`, with parsing, vocabulary setup,
  export, startup, and UI excluded. No flaky timing assertions were added. A
  93.4-second paced browser rehearsal exercises the 90-second script; independent
  human narration duration is not claimed. The screenshot is from the actual app.
- No core/schema/report contract or dependency change was required. Publication,
  deployment, model experiments, integrations, and outreach remain outside scope.

## Change log template

For a new decision, record date, status, concrete choice, reason, rejected alternatives, and affected contracts/tests. If replacing an accepted decision, identify its ID and update ARCHITECTURE, PLAN, PROJECT, README, and PROGRESS as applicable.
