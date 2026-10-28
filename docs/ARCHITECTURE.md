# ContextDiff architecture

Status: Stages 1–3 implemented and verified on 2026-10-28. The core schema, algorithms, and report version remain unchanged. See [PROGRESS.md](PROGRESS.md) for executed checks and tested versions. Delivery evidence and the app-process offline boundary are recorded in DEMO and PROGRESS.

## Stack and boundaries

| Choice | Rationale and tradeoff |
| --- | --- |
| Python 3.10+; 3.12 recommended | Core syntax targets 3.10+. Stage 1 was tested only on Python 3.12.2; default `python3` is 3.10.12. Pip resolves dependencies for the chosen interpreter; installed Streamlit 1.66.1 requires 3.11+. |
| Streamlit | One local Python process and native inputs, columns, charts, and downloads. Less layout control than a custom frontend, but much faster to deliver. |
| Standard-library dataclasses and JSON | A small explicit schema needs no additional validation framework. Errors must identify a field path. |
| Stable IDs plus `difflib.SequenceMatcher` | Deterministic block identity and readable line alignment without a diff dependency. No semantic inference; bound expensive alignment. |
| `tiktoken`, fixed `cl100k_base` | Repeatable reference counts without API calls. Not a universal tokenizer or billing estimator. |
| pytest and Ruff | Focused correctness tests and one lint/format tool. |

Two direct runtime dependencies: Streamlit and tiktoken. Their transitive dependencies still exist. Stage 1 created `pyproject.toml` with setuptools packaging, a `dev` extra for pytest/Ruff, and runtime ranges `tiktoken>=0.12,<1` and `streamlit>=1.50,<2`. The tested resolution is tiktoken 0.14.0 and Streamlit 1.66.1 on Python 3.12.2. Other allowed versions/interpreters are untested. Stage 3 records all 42 installed distribution pins in requirements-tested.txt (including pip, excluding the local editable package). Two clean environments verified range-based and snapshot-based installs; isolated build dependencies remain separately resolved. Core imports do not import either runtime dependency; tokenizer initialization is explicit.

## Intended files and responsibilities

```text
app.py                         # Stage 2: Streamlit entry point
src/contextdiff/
  __init__.py                  # Small public surface
  models.py                    # Snapshot, Block, WatchItem, diff/report dataclasses
  loaders.py                   # Explicit JSON/text parsing, validation, limits
  diffing.py                   # ID matching and bounded line opcodes
  tokens.py                    # Reference encoding initialization and content counts
  analysis.py                  # Comparison orchestration and watchlist checks
tests/
  fixtures/                    # Small manually checked inputs and expected outcomes
  test_loaders.py
  test_diffing.py
  test_tokens.py
  test_analysis.py
  test_app.py                  # Stage 2: a few AppTest flows
examples/                      # Basic, lossy/preserved handoff, retrieval swap
docs/DEMO.md                   # Paced local walkthrough and measured results
requirements-tested.txt        # Single tested environment; no editable paths
.streamlit/config.toml          # Stage 2: disable usage statistics, local upload cap
```

Keep validation errors and resource constants in `loaders.py` until extraction is justified. No service container, repository layer, plugin architecture, or separate HTTP API.

## Data flow

```text
Paste / uploaded bytes / bundled example
    -> explicit format + input-size checks
    -> UTF-8 decoding, newline normalization, schema validation
    -> immutable Snapshot values
    -> ID-based block comparison + bounded line detail
    -> per-block content-token counts (when tokenizer available)
    -> before-watchlist checks across both snapshots
    -> serializable Comparison
    -> Streamlit summary, filters, source panels, JSON download
```

The core never imports Streamlit and never reads session state. UI code owns input choices, tokenizer initialization failures, and result invalidation. Pass the token counter into the analysis function to make arithmetic independently testable.

Implemented public contract: `load_json_snapshot(data: bytes) -> Snapshot`, `load_text_snapshot(data: bytes, *, label: str) -> Snapshot`, and `compare_snapshots(before, after, *, counter) -> Comparison`. `counter` is a deterministic callable from text to a nonnegative integer, or `None` if reference tokenization is unavailable. `create_token_counter()` initializes the fixed reference tokenizer or raises `TokenizerUnavailableError` for dependency/network/cache setup failures. The caller handles that specific error and passes `None`; unrelated programming errors propagate. The package also exports `SnapshotValidationError` and the principal input/report dataclasses.

Loaders are the validation boundary. Frozen dataclasses with tuple collections hold their validated results. Direct dataclass constructors are for trusted internal/test values; they do not revalidate schema or limits. Diff/analysis functions expect loader-validated snapshots. Snapshot text remains in local memory; the core has no user-data persistence or global cache.

## Snapshot format, version 1

This is our own interchange format, not a provider export or verified Nessie schema.

```json
{
  "schema_version": 1,
  "label": "Before compaction",
  "blocks": [
    {
      "id": "instruction-1",
      "kind": "instruction",
      "role": "system",
      "content": "Use Python. Never log customer payloads."
    },
    {
      "id": "task-1",
      "kind": "message",
      "role": "user",
      "content": "Fix duplicate webhook handling. Preserve the 24-hour idempotency window."
    }
  ],
  "watchlist": [
    {
      "id": "idempotency-window",
      "text": "24-hour idempotency window",
      "note": "Required behavior during the rollout."
    }
  ]
}
```

| Field | Contract |
| --- | --- |
| `schema_version` | Required integer exactly `1`; booleans and unknown versions are rejected. |
| `label` | Optional string, maximum 200 characters; display metadata only. |
| `blocks` | Required ordered array; may be empty. |
| Block `id` | Required nonblank string, maximum 128 characters; unique within its snapshot. Reuse the same ID across snapshots only for the same logical block. |
| Block `kind` | Required: `instruction`, `message`, `tool_result`, `memory`, `retrieval`, or `summary`. |
| Block `role` | Optional: `system`, `developer`, `user`, `assistant`, or `tool`. Omission means no role; explicit null is invalid. |
| Block `content` | Required string; empty is allowed. Text only; no nested provider objects. |
| `watchlist` | Optional array, default empty. Only the before snapshot's watchlist defines checks. The after watchlist does not remove or weaken them. |
| Watch item | Required unique nonblank `id` (up to 128 characters) and nonblank `text` (up to 500); optional `note` string (up to 500). IDs need not match block IDs. |

Reject unknown keys, duplicate JSON object keys, duplicate block/watch IDs, invalid types, invalid UTF-8, and unpaired Unicode surrogates. Preserve content except that CRLF and CR become LF. Do not strip content whitespace or Unicode-normalize it. Error examples should identify a path such as `blocks[2].id` and explain the correction.

**Input bounds:** at most 256 KiB of UTF-8 bytes per snapshot, 200 blocks, 50,000 normalized content characters per block, and 50 watch items. The byte cap applies before BOM removal/newline normalization; the content-character cap applies after newline normalization. Validate pasted text against the same byte cap as uploads. Accept a UTF-8 BOM at the file boundary. These are small-demo limits; they do not promise production-scale context support. Nonstandard JSON constants, excessive parser nesting, and oversized JSON integers are rejected with sanitized domain errors. Diagnostics identify a known field/path or containing object without echoing supplied values or unknown key names.

Plain text is explicitly selected, decoded and newline-normalized, then wrapped in one block: `id="document"`, `kind="message"`, no role. It follows the same content/byte bounds; empty text is a valid empty document. JSON with `blocks=[]` is also valid. Whitespace-only JSON and a zero-byte JSON upload are invalid JSON. Malformed JSON must never silently become plain text. There is no automatic message segmentation; plain-text watchlist authoring is outside the MVP.

## Diffing methodology

1. Index each snapshot by ID after validating uniqueness.
2. For every ID in the after order, classify it: absent before = **added**; same ID and equal `(kind, role, content)` = **retained**; otherwise = **modified**.
3. Append IDs found only before in before order as **removed**. Include nullable before/after positions on each result; these are zero-based internally and labeled as one-based in the UI.
4. Ignore snapshot labels and watchlists for block classification. A role/kind-only edit is modified even when token change is zero. Reordering does not change a block's content status; expose both positions and preserve input order in source views.
5. Different IDs remain an addition and removal even if the text is identical. Do not pair them through similarity. A new summary replacing several messages is an addition plus removals, not a verified many-to-one modification.
6. For a content modification, align `splitlines(keepends=True)` using `SequenceMatcher(autojunk=False)`. Store `equal`, `insert`, `delete`, and `replace` opcodes with before/after slices. These are lexical edits, not facts. Preserve final-newline differences.
7. Bound alignment: no more than 2,000 combined lines per block pair, a before-line-count × after-line-count product of 1,000,000 per pair, and a cumulative product budget of 2,000,000 per comparison. Apply budgets in deterministic result order. When exceeded, keep the modified classification and complete source text, mark detail as skipped, and explain why. Never silently truncate the underlying comparison.

Line alignment is a readability aid, not a minimal edit-distance guarantee. No intraline character/word alignment in the required MVP. Full added/removed block text is already directly available.

**Conservation checks:** `before_blocks = retained + modified + removed`; `after_blocks = retained + modified + added`. Every input block participates once. A duplicate-content block with a different ID remains a separate occurrence. No fuzzy identity ambiguity is hidden.

## Token accounting

- Initialize `tiktoken.get_encoding("cl100k_base")` explicitly. Use `encode_ordinary(content)` so special-token-looking strings are treated as ordinary supplied text.
- A block count is the length of this encoding of its normalized content. A snapshot total is the sum of its block counts, not an encoding of concatenated text or serialized JSON. Block boundaries can affect BPE merges; this additive convention is intentional.
- Exclude labels, IDs, kinds, roles, watchlists, JSON syntax, provider message wrappers, hidden reasoning/state, and multimodal data. If tool definitions should be counted, the user must supply their visible text as a block.
- Show “Content tokens · cl100k_base reference.” Counts are exact for that encoding and convention; they estimate neither total model input nor billable tokens across providers.
- Define `delta = after_total - before_total`. A negative value is a decrease. Percentage change is `100 * delta / before_total`, and is unavailable when the baseline is zero. Do not call it compression savings unless the scenario actually represents compression.
- Per-kind before and after totals each reconcile to their snapshot total. A kind change transfers tokens between categories even if the text is identical.
- Reconciliation: `delta = added_tokens - removed_tokens + sum(modified_after_tokens - modified_before_tokens)`. Retained blocks contribute zero delta.
- Vocabulary loading can download public data once and then reuse a local cache. Provide an explicit warm-up command. Do not imply that installing the package alone ensures offline operation.
- If initialization fails, display a setup explanation and keep the non-token diff/watchlist results usable. Set token status to `unavailable` and all affected token metrics to null, never zero or an undisclosed characters-per-token fallback. Inject `counter=None` for this path; tests must cover it. Do not catch unrelated programming errors as tokenizer failures.

## Watched-phrase checks

An engineer chooses phrases whose visibility matters. For matching only, normalize each phrase and each individual block using Unicode `casefold()` and whitespace collapse (`" ".join(text.split())`). Use a literal substring check within each block. Punctuation is significant; a phrase split across different blocks does not match. Content used for diffing and tokenization is not modified by this matching normalization.

For every before-watchlist item, return matching before/after block IDs and one result:

- **present_after:** the phrase is found before and after, even if it moved into an added summary.
- **missing_after:** found before but not after; label “Potential loss: watched phrase missing.”
- **unverified_baseline:** not found before, whether or not found after; do not describe it as newly lost.

No watch items means “No watched phrases configured,” not “No information lost.” Do not infer importance from a keyword, assign a preservation score, or claim semantic equivalence. Paraphrases can trigger false alarms; negation, stale copies, and contradictory statements can still contain a phrase. Human review remains necessary.

## Comparison result and UI behavior

Use serializable dataclasses with a report version, before/after labels, reference encoding, complete block records, status counts, before/after positions, line detail or skip reasons, optional token metrics, and watchlist evidence. The downloaded report contains supplied text; label it accordingly. Deterministic ordering and omission of generated timestamps make results easy to test.

The implemented report version is `1`. `Comparison.to_dict()` returns a detached dataclass representation accepted by `json.dumps` (tuples become JSON arrays). Its fields are:

| Field | Implemented representation |
| --- | --- |
| `report_version`, `before_label`, `after_label`, `reference_encoding` | Version `1`, optional labels, and `cl100k_base`, even when token metrics are unavailable. |
| `blocks` | Ordered `BlockChange` records: `id`, `status`, full nullable `before`/`after` blocks, nullable zero-based positions, `line_detail`, and nullable `before_tokens`, `after_tokens`, `token_delta`. |
| `line_detail` | Null for unchanged content/additions/removals; otherwise status `available` with opcodes, or `skipped` with `skip_reason`. Opcodes carry tag, half-open before/after line indexes, and exact line tuples including endings. Skipped pairs consume no alignment budget; sources remain in the block records. |
| `status_counts` | Integer `added`, `removed`, `retained`, `modified` counts. |
| `tokens` | `status` (`available`/`unavailable`), nullable `before_total`, `after_total`, `delta`, `percentage_change`, and `by_kind` entries for all six kinds in the documented enum order. Each entry has `kind`, `before`, `after`, and `delta`. |
| `watches`, `watchlist_status` | Before-order watch results contain the complete `item`, result `status`, and `before_block_ids`/`after_block_ids` in source order. Watchlist status is `configured` or `not_configured`. |
| `limitations` | Fixed explanatory text on identity, token convention, lexical watch matching, and supplied-text visibility. |

With tokens available, an absent side of an added/removed block has zero tokens; an empty present block also has zero. With `counter=None`, every affected token value, including all kind/block values, is null. A zero baseline keeps totals/delta available while percentage change is null. No timestamp or private diagnostic is added.

The Stage 2 implementation uses native Streamlit text/code rendering and a grouped native token chart. User-controlled labels, IDs, notes, and content render as text/code; no supplied text goes into Markdown or raw HTML. Session state holds the current inputs/report/errors; there is no global user-data cache or input logging. Callbacks clear results, errors, tokenizer notices, and filters when a committed paste edit, uploaded file, source choice, format, or sample load changes. Native text areas commit on blur or the platform's Ctrl/Cmd+Enter shortcut. Inactive widgets may be discarded by Streamlit when switching sources. A single bundled-example selector offers Basic comparison, Coding handoff · lossy, Coding handoff · preserved, and Retrieval · source swap. Changing the choice clears derived state; Load sample sets JSON and both paste inputs consistently from a fixed filename mapping. Compare remains explicit and uses the visible inputs. Static guidance identifies all examples as synthetic. Both handoffs reuse exactly the same before snapshot; a new summary stays added even when a watch moves into it.

Status/kind multiselects narrow only block panels; kind matches either before or after, so a category transfer remains discoverable from both kinds. Summary metrics, watched evidence, and JSON download always cover the full report. Each panel shows ID, both one-based positions, kind/role, character/final-LF labels, complete sources, and core line opcodes or a skip reason. Native code rendering removes one boundary newline in the tested Streamlit; the UI discloses this, line edits label missing LF endings, and export preserves complete normalized source strings. Long source and line-edit panels scroll without truncating report data. Retained blocks start collapsed.

The app serializes `Comparison.to_dict()` directly to an in-memory JSON download, including full sources, reference encoding, and limitations. It catches only safe loader errors and the explicit tokenizer setup error. Both sides are validated before tokenizer setup; failed setup produces unavailable/null metrics and a recovery notice, and Compare retries initialization. Programming errors are not converted into setup failures.

`.streamlit/config.toml` disables usage collection, binds to `127.0.0.1`, sets a 1 MiB upload transport cap, and disables file watching (reload/restart after code changes). Python checks uploaded size before reading bytes and the loaders enforce the stricter 256 KiB bound for both uploads and paste. There is no automatic upload to another service or application disk persistence of private inputs. The two runtime dependencies and core boundaries are unchanged.

## Deferred choices and limits

Installed versions, measured engine-only sample timings, and their boundaries are in PROGRESS and DEMO. The warmed-cache app walkthrough was verified under a macOS process sandbox denying external outbound connections and allowing localhost. The browser and machine were not globally disconnected. No new runtime offline mechanism is built into the app. Multi-provider tokenizers, semantic matching, import adapters, many-snapshot timelines, and live context capture remain out of scope. An exported snapshot can be incomplete; ContextDiff reports only what it was given. Opaque encrypted compaction items cannot be decoded or assessed for fact preservation by this text-only MVP.
