# ContextDiff progress

Last updated: **2026-10-28** (America/Los_Angeles).

## Current stage

**Stages 1–3 complete within the verification boundaries below.** The local demo
is delivered. No next implementation stage, publication, deployment, or outreach
is scheduled. No user input, account, credential, or private snapshot is needed.

| Stage | Status |
| --- | --- |
| Setup and planning | Complete; historical record retained below |
| 1. Core comparison engine | Complete; original 119 core tests reverified |
| 2. Interactive visualization | Complete; original 133-test baseline reverified |
| 3. Polish, demo, delivery | Complete; 141 tests, delivery and browser checks below |

## Delivered and verified in Stage 3 — 2026-10-28

- Read AGENTS, PROGRESS, PLAN, PROJECT, ARCHITECTURE, DECISIONS, RESEARCH, source,
  tests, config, and Git state. Reverified the unchanged Stage 1/2 baseline:
  **133 passed in 1.79s**, lint passed, **24 files already formatted**.
- Added hand-authored synthetic lossy/preserved webhook handoffs and the smaller
  retrieval swap. No provider/Nessie format, actual webhook execution, model
  experiment, external retrieval service, or private data is implied.
- Independently inspected stable IDs and literal watch sources. Directly counted
  every scenario block with tiktoken 0.14.0
  `encoding.encode(content, disallowed_special=())`, outside ContextDiff's counter
  and report orchestration. Manually summed the results. Expectations are in
  examples/README and fixed as regression goldens in tests/test_scenarios.py.
- Both handoffs have 1 added / 3 removed / 1 retained / 1 modified. Lossy is
  **271 → 52 (-219, -80.8%)**; preserved is **271 → 64 (-207, -76.4%)**. The window
  watch disappears only in lossy; atomic-claim text moves into both new summaries;
  privacy stays in the original instruction. Retrieval is **38 → 34 (-4, -10.5%)**,
  with 1 added / 1 removed / 1 retained / 0 modified and a missing window watch.
- Extended the existing native selector to four choices. Added explicit synthetic
  data and Load sample → Compare guidance. Choosing another example clears derived
  state; Load sample resets JSON and both Paste inputs. Compare remains explicit.
  Actual walkthrough supported retaining the existing spacing, bounded scroll
  panels, safe rendering, newline labels, and recovery notices. No frontend stack,
  runtime dependency, schema/report version, or core algorithm changed.
- Added three real-tokenizer scenario cases and five AppTest cases for scenario
  selection/reset/evidence, role-only edits, final-LF-only edits, Unicode/special
  text, and empty JSON snapshots/export. Reused existing coverage for identical,
  all-added/all-removed, paraphrase/negation, limits, repetitive data, and unavailable
  tokenizer. Final suite has **141 cases: 18 AppTest, 9 integration**, no skips.
- Added DEMO.md, an actual running-app screenshot, and requirements-tested.txt;
  finalized README and project status/architecture/decision records. The snapshot
  contains **42 exact installed distribution pins**, including pip, excluding
  ContextDiff's editable path. Build-isolation dependencies are separate. No
  universal lockfile or Python/dependency compatibility matrix is claimed.

### Stage 3 commands and outcomes

Commands ran from the repository root. The original `.venv` and two new isolated
venvs use **CPython 3.12.2 / macOS-26.5.2-arm64-arm-64bit**. Fresh paths are temporary
verification artifacts, not README installation requirements. Installed direct
versions match Stage 1: tiktoken 0.14.0, Streamlit 1.66.1, pytest 9.2.0, Ruff 0.17.3,
ContextDiff 0.1.0; pip 24.0. All installed transitive/tool pins are in the snapshot.

| Command | Observed result |
| --- | --- |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest` before changes | **133 passed in 1.79s**, exit 0, no skips. |
| `.venv/bin/python -m ruff check .` / `.venv/bin/python -m ruff format --check .` before changes | Exit 0; all checks passed, **24 files already formatted**. |
| `python3.12 -m venv /private/tmp/contextdiff-stage3/venv` | Exit 0; isolated environment created. |
| `/private/tmp/contextdiff-stage3/venv/bin/python -m pip install -e '.[dev]'` | Sandboxed first attempt exit 1: PyPI DNS unavailable during isolated setuptools installation. Same command with approved network access exit 0; package and all dependencies installed. Default pip-cache warning only in restricted runs. |
| `TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /private/tmp/contextdiff-stage3/venv/bin/python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"` | Exit 0 with approved network access; fresh cache warmed from public vocabulary only. |
| `.venv/bin/python -m ruff format tests/test_scenarios.py tests/test_app.py app.py` | Exit 0; 3 files formatted. Subsequent lint passed. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest` after implementation | **141 passed in 2.29s**, exit 0; no skips. |
| `TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /private/tmp/contextdiff-stage3/venv/bin/python -m pytest` | **141 passed in 2.20s**, exit 0; no skips in the fresh environment. |
| `/private/tmp/contextdiff-stage3/venv/bin/python -m pip check` | Exit 0: **No broken requirements found**. |
| `/private/tmp/contextdiff-stage3/venv/bin/python -m ruff check .` / `... -m ruff format --check .` at implementation boundary | Exit 0; all checks passed, **25 files already formatted**. |
| Fresh Python `importlib.metadata.distributions()` snapshot script | Exit 0; sorted `Name==version` for all distributions except ContextDiff; **42 pins**, asserted no slash or ` @ ` paths. Wrote requirements-tested.txt with Python/platform/boundary comments. |
| `python3.12 -m venv /private/tmp/contextdiff-stage3/repeat` then `/private/tmp/contextdiff-stage3/repeat/bin/python -m pip install -r requirements-tested.txt` then `... -m pip install --no-deps -e '.[dev]'` | All exit 0 with approved network access; clean repeat install using README's snapshot path. |
| `TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /private/tmp/contextdiff-stage3/repeat/bin/python -m pytest -m integration` | **9 passed, 132 deselected in 1.22s**, exit 0, no skips. |
| `/private/tmp/contextdiff-stage3/repeat/bin/python -m pip check` and inline distribution comparison | Exit 0; no broken requirements; **all 42 pins match** after normalizing package name case/underscores. |
| `TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /private/tmp/contextdiff-stage3/venv/bin/python - <<'PY'` timing/report audit | Exit 0; 100 warmed comparisons per sample and repetitive fallback, four JSON round trips, full fallback source equality, browser lossy download field-for-field equality. Method/results below. |

The two fresh installs exercise the range-based and exact-snapshot instructions.
They share the same source checkout but not site-packages. Neither copied the old
venv. Public wheels came from pip's cache/PyPI; vocabulary used its own new cache.
Other platforms, Python versions, and package resolutions remain untested.

### Full-app offline boundary and actual browser checks

Used macOS `sandbox-exec` with this exact profile:

```text
(version 1) (allow default) (deny network-outbound) (allow network-outbound (remote ip "localhost:*"))
```

The initial nested-sandbox `/usr/bin/true` probe failed with
`sandbox_apply: Operation not permitted`. The same profile with approved sandbox
escalation exited 0. An external connection probe under that profile,
`.venv/bin/python -c 'import socket; s=socket.socket(); s.settimeout(1); s.connect(("1.1.1.1",443))'`,
exited 1 with **PermissionError: [Errno 1] Operation not permitted**. This is an
expected negative control, not an app failure. No request payload was sent.

Launched the freshly installed app with:

```sh
TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /usr/bin/sandbox-exec \
  -p '(version 1) (allow default) (deny network-outbound) (allow network-outbound (remote ip "localhost:*"))' \
  /private/tmp/contextdiff-stage3/venv/bin/python -m streamlit run app.py \
  --server.address 127.0.0.1 --server.port 8503 --server.headless true
```

The approved launch stayed running at **127.0.0.1:8503**. All Stage 3 browser checks
below used this fresh app with real reference tokens and external outbound
connections denied to its process. Browser networking and other apps were not
globally disabled; this is a verified app-process isolation boundary. The
localhost browser must still communicate with the server. No machine-wide or
browser-wide offline claim is made.

| Actual in-app browser action | Observed result |
| --- | --- |
| Load/Compare lossy, preserved, retrieval through selector | Exact token/status table and watch source IDs above. Selecting another example clears the old comparison/download; Load sample fills JSON/Paste on both sides. |
| Expand lossy token chart | Native chart renders all six categories, Before/After labels; trace accounts for 188 removed tokens, new summary 26 tokens. |
| Inspect modified task, new summary, removed constraint/trace/finding | Correct metadata/positions and readable source/line panels; verbose trace scrolls; retained instruction starts collapsed. |
| Upload handoff.before.json and handoff.preserved.after.json with real file choosers | Same 271 → 64 totals, 1/3/1/1 counts, and constraint → handoff-summary evidence as bundled sample. |
| Remove added, retained, modified from status filter | 5 → 4 → 3 of 6 blocks; before/after totals remain 271/64. |
| Replace before upload with synthetic malformed JSON | Side-specific invalid JSON line 1, column 21; supplied marker omitted; no traceback. Upload rerun clears stale report; Compare after upload completion shows error. |
| Replace before upload with 262,145 bytes | Core safely rejects at 262,144 UTF-8 bytes; loading a sample resets sources and clears errors. |
| Compare script-looking text plus café and `<|endoftext|>` with/without a final LF | Literal code, no script execution; 14 → 14 tokens but 1 modified block, 52/53 characters, distinct final-LF labels, explicit missing-newline diff marker, no-watchlist notice. |
| Commit an after edit without comparing | After blur and input rerun, comparison and Download JSON report disappear. |
| Download lossy report via actual browser and parse saved file | JSON parses and equals the real core report field for field, including complete source text, reference encoding, watches, positions, token totals, and limitations. |
| Inspect screenshots at 1366 × 900 and a 390 × 844 override | Laptop columns pair; narrow inputs stack with width 356 px at x=17 and different vertical positions. Labels and text carry status independently of color. Overrides restored. |
| Paced script rehearsal | **93.4 seconds** including explicit pauses for the suggested narration: lossy reviewed at 43.0s, preserved at 68.3s, retrieval and limits by 73.3s, final review through 93.4s. This was a paced browser rehearsal, not an independently timed spoken presentation or a speed benchmark. |

As in Stage 2, Streamlit's underlying radio input did not toggle with a direct
programmatic check; clicking its visible Text label worked and the resulting
state was verified. Browser snapshots can briefly precede a Streamlit rerun;
checks waited for the resulting state/download disappearance. These are test
interaction notes, not hidden application failures. No app exception occurred.

The actual screenshot is `docs/assets/lossy-handoff.jpg`. Synthetic malformed,
oversized, and text check files plus both fresh environments/caches are only in
`/private/tmp/contextdiff-stage3`; downloaded synthetic reports are in Downloads.
No private inputs or machine-specific cache files enter repository deliverables.

### Timing and report evidence

Fresh Python 3.12.2 environment, warmed encoding, snapshots parsed before timing;
one untimed comparison then **100 runs** per case using `perf_counter_ns` around
only `compare_snapshots`. Includes token encoding, line detail, watches, and report
dataclasses. Excludes loading, tokenizer setup, JSON serialization, UI/startup,
and human interaction. These are observed machine results, not test thresholds.

| Pair | Median ms | Max ms |
| --- | --- | --- |
| Basic | 0.033 | 0.067 |
| Lossy | 0.070 | 0.145 |
| Preserved | 0.072 | 0.292 |
| Retrieval | 0.024 | 0.426 |
| Repetitive fallback | 0.560 | 0.900 |

Repetitive inputs: `"repeat\n" * 1001 + "old\n"` versus `"repeat\n" * 1001 + "new\n"`,
7,011 characters each; combined lines exceed 2,000. Asserted `skipped` detail and
exact full before/after source equality. No scalability promise follows.
DEMO.md contains a reproducible timing snippet with the same measurement boundary.
The timing audit also round-tripped all four example reports with
`json.dumps(..., allow_nan=False)` and matched the saved browser lossy report
against the complete core dictionary. Scenario tests separately recover each
input's original source order/content from the round-tripped report.

### Stage 3 limits and next action

No required item remains unverified **within the stated app-process offline and
single-platform boundaries**. Cross-platform installation, Python 3.10/3.11,
other dependency versions, browser-wide/machine-wide disconnection, and an
independently timed human presentation remain unverified and are not claimed.
No schema, algorithm, or scope departure was needed. No known failing test,
skipped tokenizer integration, or application error remains. Final documentation
and whitespace audit results are recorded below.

Final verification after documentation updates:

| Command | Observed result |
| --- | --- |
| `TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /private/tmp/contextdiff-stage3/venv/bin/python -m pytest` | **141 passed in 2.35s**, exit 0; no skips. |
| `/private/tmp/contextdiff-stage3/venv/bin/python -m ruff check .` | Exit 0; all checks passed. |
| `/private/tmp/contextdiff-stage3/venv/bin/python -m ruff format --check .` | Exit 0; **26 files already formatted**. |
| `/private/tmp/contextdiff-stage3/venv/bin/python -m pip check` | Exit 0; no broken requirements (restricted pip-cache warning only). |
| `git diff --check` / `git status --short --untracked-files=all` | Exit 0; unborn main and untracked source/deliverables preserved. No tracked diff exists, so the separate audit checks untracked whitespace. |
| `TIKTOKEN_CACHE_DIR=/private/tmp/contextdiff-stage3/tiktoken-cache /private/tmp/contextdiff-stage3/venv/bin/python /private/tmp/contextdiff-stage3/audit_docs.py` | First exit 1 at the final image-signature assertion: native browser capture returned JPEG bytes despite the provisional .png filename. Renamed the file to .jpg and fixed both doc links; no image alteration. Rerun exit 0: **11 Markdown files, 33 local links/images, balanced fences, README/DEMO Python smoke, 41 untracked text files without whitespace errors, 7 valid examples, 42 clean pins, core/UI boundary, actual JPEG passed**. |

The temporary audit reads the named Markdown files and local link/image targets,
executes both documented Python snippets with captured stdout, checks untracked
text EOF/whitespace, validates all example JSON, checks the dependency-pin format,
asserts exactly two runtime dependencies and no core Streamlit imports, and
verifies the actual screenshot signature. No private data is read or exported.

The precise next action is to follow DEMO.md locally if desired. No additional
stage begins automatically. The Stage 3 sandboxed server is left available on
localhost:8503 for review; the pre-existing Stage 2 server on :8501 was not changed.
No publication, deployment, commit, staging, or contact with anyone occurred.

## Historical Stage 2 boundary

The following record describes the earlier Stage 2 completion; its then-pending
Stage 3 work is superseded by the delivery record above.

## Delivered and verified in Stage 2 — 2026-10-28

- Read AGENTS, PROGRESS, PLAN, PROJECT, ARCHITECTURE, DECISIONS, RESEARCH, current source/tests, and Git status before implementation. Reverified all 119 Stage 1 tests, lint, and formatting. No core source, core tests, packaging contract, or dependencies changed; the repository remains on unborn `main` with pre-existing files untracked. No staging or commit was requested/performed.
- Added `app.py` with explicit JSON/text format, independent paste/upload sources, Compare, and one basic-example selector/Load sample action. Committed input/source/format/sample changes clear results, notices, errors, and filter state. Both sides validate through the unchanged loaders; upload size is checked before reading. Errors identify the side and recovery without echoing input.
- Token/status summaries come directly from the core report, including signed/percentage change, null/unavailable and zero-baseline behavior. A grouped native chart shows tokens by kind. Before-watchlist evidence includes all three states and source IDs, lexical limitations, and no-watchlist messaging.
- Status and either-side-kind filters narrow block panels while global totals, watches, and export stay complete. Paired source panels show kind/role, metadata-only changes, one-based positions, complete content, character/final-LF labels, and readable core opcodes or alignment-budget notices. Long code panels scroll. No user content is inserted into Markdown/HTML.
- JSON report is serialized in memory directly from `Comparison.to_dict()`, with complete source blocks, encoding, and limitations. Download explains that supplied text is included. No global user-data cache, default input/report disk persistence, model call, or external integration was introduced.
- Added `.streamlit/config.toml`: localhost binding, usage collection off, 1 MiB upload transport, no file watching, and a light slate/teal native theme. Python retains the stricter 256 KiB limit for paste/upload. Reload/restart after source edits.
- Added the single basic JSON pair, hand-checked `examples/README.md`, 13 parametrized AppTest cases in `tests/test_app.py`, and a real-tokenizer sample integration test. Removed only the obsolete examples placeholder. The sample has 1 added, 1 removed, 1 retained, 2 modified, including one metadata-only edit; tokens are 30 → 28 (-2, -6.7%). The missing watch points to before's `constraint`; privacy is retained and the third baseline is unverified.
- Updated README, AGENTS, PROJECT, PLAN, ARCHITECTURE, DECISIONS, and RESEARCH to reflect actual behavior and the Stage 3 boundary. No core contract departure was needed. Native code panels hide one boundary newline, so UI labels disclose that; report strings remain exact.

### Stage 2 commands and outcomes

Commands ran from the repository root with the existing Python 3.12.2 `.venv` and warmed `.venv/tiktoken-cache`. Dependency/environment versions remain those in the Stage 1 table below; no installation or version-matrix check was done in Stage 2.

| Command | Observed outcome |
| --- | --- |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest` before changes | **119 passed in 0.44s**, exit 0, no skips; Stage 1 prerequisite verified. |
| `.venv/bin/python -m ruff check .` and `.venv/bin/python -m ruff format --check .` before changes | Exit 0; all checks passed, **20 files already formatted**. |
| `.venv/bin/python -m ruff check app.py tests/test_app.py tests/test_basic_example.py --fix` | Initial exit 1: 10 E501 long-line findings. Formatting reduced these to 5; split/shortened the remaining strings. Subsequent lint passed. |
| `.venv/bin/python -m ruff format app.py tests/test_app.py tests/test_basic_example.py` | Exit 0; formatted 3 new Python files. Later format runs passed. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest tests/test_app.py tests/test_basic_example.py` | Initial **13 passed, 1 failed in 10.48s**: the test expected a trailing LF in native code output, but Streamlit hides one boundary LF. Inspected installed implementation, disclosed display behavior, and asserted the exact report source separately. Rerun: **14 passed in 1.39s**, exit 0. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.headless true` | First sandboxed launch exited 1 at localhost socket bind (`PermissionError`); the same command with approved sandbox escalation started successfully at **127.0.0.1:8501**. Headless only suppresses automatic browser opening; browser inspection used the in-app browser. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest` final implementation run | **133 passed in 1.94s**, exit 0, no skips. Includes unchanged 119 Stage 1 tests, 13 AppTest cases, and 1 bundled-sample test. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest -m integration` | **6 passed, 127 deselected in 0.44s**, exit 0; includes the real-tokenizer sample plus Stage 1 tokenizer/offline-core cases. |
| `.venv/bin/python -m ruff check .` | Exit 0: **All checks passed!** |
| `.venv/bin/python -m ruff format --check .` | Exit 0: **24 files already formatted** at the implementation verification point, including enabled Markdown code formatting. |
| `.venv/bin/python -m pip check` | Exit 0: **No broken requirements found.** Existing unwritable default pip-cache warning is environmental. |
| Final `.venv/bin/python -m ruff check .` / `.venv/bin/python -m ruff format --check .` after documentation updates | Both exit 0: all checks passed, **24 files already formatted**. |
| Final `git diff --check` / `git status --short --untracked-files=all` | Exit 0; all setup/implementation files remain untracked on unborn `main`. The diff check has no tracked changes to inspect; a separate text audit covers untracked-file whitespace. No staging/commit performed. |
| Final inline `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python - <<'PY'` documentation/scope audit | Exit 0: **10 Markdown files, 20 local links, balanced fences, 28 files without trailing whitespace, README API smoke, config/core boundary, browser report equality, and Stage 2 scope passed.** The script checked local links/fences, executed the README Python example with captured stdout, parsed config, confirmed two runtime dependencies and no UI imports in core, compared the saved browser report, and asserted absence of Stage 3 files/scenarios. |

AppTest sometimes emits its documented bare-mode `missing ScriptRunContext` warning during setup; no app exceptions or skipped UI tests remain. UI arithmetic uses an explicit word-count stub; the integration sample and browser use real tiktoken. New cases cover sample metrics/evidence, metadata-only UI, filter invariance/empty state, invalid JSON and recovery, input/format/source/sample invalidation, missing upload versus blank text, null token metrics and retry, Unicode byte/content caps, literal source, and alignment fallback preserving the report sources.

### Stage 2 browser inspection (separate from AppTest)

Used the actual running localhost app in the in-app browser with real native file chooser transfers. Inspected screenshots at a requested laptop viewport override of **1366 × 900** and the default narrow panel (319 CSS pixels wide); columns pair on the laptop and stack in the narrow panel. Restored the viewport override after checks. No screenshot snapshots or browser test dependency were added.

| Browser action | Observed result |
| --- | --- |
| Load sample; Compare; expand token chart | 30 before, 28 after, -2 (-6.7%); 1 added, 1 removed, 1 retained, 2 modified. Chart includes Before/After labels and all six kinds. All three watch outcomes and source IDs are readable. |
| Inspect source and diff panels | Text edits, paired positions, and the tool_result/tool → memory/assistant metadata-only change are visible, with zero token delta for that block. Statuses have text labels. Long text uses scroll panels. |
| Compare `old` / `new` plus 1,001 repeated lines on each side | Both 7,011-character sources remain in bounded scroll panels; notice says combined line count exceeds 2,000 and complete sources remain available. The document stays modified; 2,004 content tokens per side. Sample restored afterward. |
| Filter each status, then kind `tool_result` under modified | Added/removed/retained each show 1 of 5; modified shows 2 of 5. `tool_result` shows the single metadata-only block using its before kind. Empty selection shows 0 of 5 and a recovery notice. Aggregate totals remain 30/28/-2 and 1/1/1/2. |
| Upload both `examples/basic.*.json` files | Same results as sample paste. Switching sources clears the prior report. |
| Replace before upload with synthetic malformed JSON | Safe before-side JSON line/column error; no supplied test key or traceback in the UI. Corrected input/sample reload recovers. |
| Upload 262,145-byte JSON | Transport accepts it; Python rejects it with the exact 262,144-byte input cap and recovery instruction. |
| Upload 1,048,577-byte JSON | Native transport rejects it with “File must be 1.0MB or smaller.” This limit is separate from the stricter core cap. |
| Upload UTF-8 text pair containing script/img-looking strings and café | Modified document, 10 → 14 tokens, literal source/code and line edits; no script dialog or image interpretation. No-watchlist notice appears. |
| Upload invalid UTF-8 text | Safe before-side “must be valid UTF-8” error; recovered by switching to paste. |
| Paste `alpha\nkeep\n` / `beta\nkeep\n` as Text | One modified document, 4 → 4 tokens, visible line edit, no watch assessment. |
| Commit an input edit after comparison | Waited for the input-triggered rerun: comparison and download disappear. Native text areas commit on blur or Ctrl/Cmd+Enter. |
| Compare two blank Text inputs, then invalid/blank JSON | Blank Text is valid: 0/0/+0 tokens, 1 retained, unavailable percentage. JSON is explicitly parsed and rejected with side-specific errors; never falls back to Text. |
| Download JSON report and reopen it | Browser saved `contextdiff-report.json` in Downloads. An inline Python check parsed it and asserted field-for-field equality against `json.loads(json.dumps(compare_snapshots(..., counter=create_token_counter()).to_dict()))` for the sample, including full sources, watches, metrics, encoding, and limitations. |

Synthetic malformed/oversized/UTF-8/text check files and the captured proof screenshot live only under `/private/tmp/contextdiff-stage2-checks`; the browser report is a synthetic sample in Downloads. They are not repository data. Native browser controls sometimes required clicking visible labels rather than programmatically checking the underlying radio input; visible state was verified after each successful action. The browser can briefly show the previous DOM while a Streamlit rerun is in flight; invalidation was verified after the committed rerun completed. No private data, credentials, publication, outreach, or paid service was involved.

### Stage 2 limits and next action

No known failing Stage 2 check or unresolved blocker remains. No user input is needed. Full-app offline verification, fresh installation, version snapshot, timings, realistic scenarios, and DEMO.md remain **unrun Stage 3 acceptance work**. The existing socket-blocked tests still establish only the core offline boundary. Other Python/Streamlit versions remain untested. Code-panel boundary-newline presentation is disclosed; reports preserve exact normalized text. The local app was left running for review, with its sample restored.

Stop here. Begin Stage 3 only on a new explicit user request using its prompt in PLAN.

## Historical Stage 1 record

The following delivery/environment/command details record the earlier Stage 1 boundary; later Stage 2 outcomes above supersede its UI-pending status.

## Delivered in Stage 1

- `pyproject.toml`: setuptools `src/` discovery, Python 3.10+ declaration, two bounded runtime dependencies, pytest/Ruff development extra, and test/lint/format configuration. Installed editable package in local `.venv` using available Python 3.12.2.
- Immutable snapshot/block/watch/report dataclasses; explicit JSON and text loaders; field/path validation, duplicate JSON-key/ID detection, UTF-8/BOM/surrogate handling, newline preservation rules, and byte/character/count limits. Nonstandard numbers and pathological JSON failures produce safe domain errors without supplied values.
- Stable-ID matching in after order followed by before-only order, all four statuses, both zero-based positions, exact metadata/content equality, newline-sensitive opcodes, and full-source fallback under per-pair/cumulative budgets. No fuzzy identity or semantic inference.
- Explicit `cl100k_base` setup and ordinary-text counts, per-block additive totals, per-kind transfers, signed/percentage deltas, null unavailable metrics, zero-baseline handling, and a typed counter injection boundary. Core imports require neither Streamlit nor tiktoken initialization.
- Before-watchlist-only checks with casefold/whitespace collapse, source IDs, all three outcomes, and explicit lexical limitations. Reports are deterministic, contain complete supplied blocks, and serialize through `Comparison.to_dict()` plus `json.dumps`.
- Hand-authored before/after fixtures, independent expected classifications and word-stub arithmetic, and four core test modules plus fixtures. Real tokenizer tests are separate from deterministic arithmetic stubs.
- README installation/API instructions and accurate stage status in AGENTS, PROJECT, PLAN, ARCHITECTURE, DECISIONS, and RESEARCH. ARCHITECTURE now describes the concrete report shape and validation boundary. No schema/algorithm departure was needed.

## Environment and installed versions

Observed with `python3 --version`, `python3.12 --version`, and an inline `.venv/bin/python` script using `sys.version`, `platform.platform()`, and `importlib.metadata`:

| Component | Observed value |
| --- | --- |
| Default `python3` | 3.10.12; not used for installation/tests |
| Tested interpreter | CPython 3.12.2, Clang 13.0.0 |
| Platform | `macOS-26.5.2-arm64-arm-64bit` |
| ContextDiff | 0.1.0 (editable local installation) |
| pip | 24.0 |
| tiktoken | 0.14.0; installed metadata requires Python >=3.9 |
| Streamlit | 1.66.1; installed metadata requires Python >=3.11 |
| pytest | 9.2.0 |
| Ruff | 0.17.3 |

Declared runtime ranges are `tiktoken>=0.12,<1`, `streamlit>=1.50,<2`; development ranges are `pytest>=8,<10`, `ruff>=0.14,<1`. These are bounds, not a lockfile or verified version matrix. Other Python/dependency versions were not tested. Python 3.10 needs a compatible earlier Streamlit resolution, which remains unverified. A complete tested-environment dependency snapshot is Stage 3 work.

## Exact commands and outcomes

All commands ran from the repository root. `.venv/bin/python` is used explicitly; shell activation was unnecessary. Cache-bearing commands use the same ignored project-local directory.

| Command | Outcome |
| --- | --- |
| `python3.12 -m venv .venv` | Exit 0; created the isolated environment. |
| `.venv/bin/python -m pip install -e '.[dev]'` | First sandboxed attempt exited 1: PyPI DNS/network unavailable during build-dependency installation, with an unwritable default pip-cache warning. Retried the same command with approved network access: exit 0, editable build and dependency installation succeeded. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"` | First sandboxed cold-cache attempt exited 1: public vocabulary host could not resolve. Retried the same command with approved network access: exit 0; vocabulary cache warmed. No snapshots were passed to this command. |
| `.venv/bin/python -m pytest tests/test_loaders.py tests/test_diffing.py` | Initial run: 88 passed, 1 failed. Empty-object validation reports missing `blocks` first in sorted required-field order, while the test expected `schema_version`. Corrected that test expectation; rerun: **89 passed in 0.06s**, exit 0. |
| `.venv/bin/python -m ruff check .` | Initial run exited 1 with 44 formatting/import/line-length findings. Organized imports, split long strings, and formatted code. Subsequent lint checks exit 0: **All checks passed!** |
| `.venv/bin/python -m ruff check . --select I --fix` | Exit 0; fixed 2 import findings. |
| `.venv/bin/python -m ruff format .` | Exit 0; applied formatting. A later added subprocess-script line triggered one E501 lint failure; split the line and reran successfully. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest tests/test_loaders.py tests/test_diffing.py tests/test_tokens.py tests/test_analysis.py` | Initial full core run: 118 passed in 0.31s. Added the cold-cache/recovery integration case and explicit integration marker; final required run: **119 passed in 0.42s**, exit 0, no skips. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest` | **119 passed in 0.40s**, exit 0, no skips. |
| `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python -m pytest -m integration` | **5 passed, 114 deselected in 0.33s**, exit 0. Real vocabulary/count tests, real reconciliation, per-block token convention, warmed socket-blocked comparison, and cold-cache failure/recovery all passed. |
| `.venv/bin/python -m ruff format --check .` | Passed after initial code formatting. Later README edit caused one embedded-Python formatting failure (exit 1); shortened the comment and reran successfully. Final check: exit 0, **20 files already formatted**. |
| `.venv/bin/python -m pip check` | Exit 0: **No broken requirements found.** Default pip-cache warning is environmental and does not affect dependency consistency. |
| `git status --short --untracked-files=all` | Existing repository remains on unborn `main`, with setup and implementation files untracked; no commit/stage action requested or performed. `.venv` and tokenizer cache are ignored. |
| `git diff --check` | Exit 0, but there are no tracked-file diffs in this unborn repository, so this does not validate untracked file whitespace. |
| `git check-ignore .venv/example .venv/tiktoken-cache local_data/example.json exports/example.json .env .streamlit/secrets.toml` | Exit 0; all six ignored paths matched, including the tokenizer cache. |

Final inline `TIKTOKEN_CACHE_DIR="$PWD/.venv/tiktoken-cache" .venv/bin/python - <<'PY'` audit exited 0: **9 Markdown files, 18 local links, balanced code fences, README API smoke test, JSON report round trip, and Stage 1 scope**. The script read README/AGENTS/docs/fixture documentation with `pathlib` and regular expressions, verified local link existence and balanced fences, compiled/executed the README Python snippet with captured stdout, asserted its status counts and real-token availability, round-tripped its report through JSON, and asserted no `app.py`/`.streamlit`, unchanged placeholder-only examples, and removed source/test placeholders. No private input or generated report was saved.

The short test durations above are observed suite durations, not comparison benchmarks or universal performance claims. No tokenizer integration was skipped or blocked after warm-up. At the Stage 1 boundary no UI/browser checks were run; subsequent Stage 2 browser checks are recorded above.

## Verification coverage and offline boundary

The 119 tests cover schema types (including boolean versions), unknown/missing keys, nested duplicate JSON keys, duplicate IDs, invalid UTF-8, unpaired/pair-surrogate behavior, empty/BOM inputs, raw whitespace/final newlines, Unicode byte bounds, every string/count limit at and above its boundary, malformed/deep/numeric JSON, safe diagnostics, and recovery after invalid input. Classification tests cover all statuses, repeated content, changed IDs, reordering, metadata-only edits, conservation, determinism, and non-mutation. Golden line tests check exact slices/indexes for equal/replace/insert/delete and final-newline edits; repetitive, exact-budget, over-budget, and cumulative-budget cases preserve source text. The product guard is also exercised independently: with the default 2,000 combined-line cap, a product above 1,000,000 cannot occur, so that test temporarily relaxes only the combined-line cap.

Token tests exercise golden real counts including special-token-like strings and Unicode, the additive block-boundary convention, real and stub reconciliation, kind transfers, empty baselines, unavailable/null values, setup errors, and propagation of programming errors. Watch tests cover source IDs, all three states, matching in an added summary, multiple source matches, ignored after-watch changes, block boundaries, punctuation/paraphrase/negation limitations, and unconfigured watches.

Offline core verification uses fresh subprocesses so no parent in-memory encoding is inherited. The warmed test blocks `socket.socket.connect`, `connect_ex`, and `socket.create_connection`, initializes the real encoding from cache, and compares the normal JSON fixtures with token and watch results. The cold-cache test additionally blocks DNS, verifies `TokenizerUnavailableError` from an empty cache, performs a non-token comparison with null metrics, switches back to the warmed cache, and successfully compares with reference counts. This establishes the Python core path under those network guards, not a machine-wide network shutdown or complete offline UI demonstration. The latter remains a Stage 3 acceptance item.

## Known limits and remaining work

- No unresolved Stage 1 blocker or known failing check. Only the observed Python 3.12.2 dependency resolution has been verified.
- At the Stage 1 boundary the UI/config/sample/AppTest/browser/export work was pending. Stage 2 has since delivered and verified those items above.
- Stage 3 still owns realistic synthetic scenarios, timings, fresh installation, tested dependency snapshot, full offline walkthrough, and demo/delivery documentation. No complete-app offline or performance claim is made.
- Structured identity requires supplied stable IDs; changed IDs are additions/removals. Watched phrases are lexical review signals, not semantic loss/contradiction detection. Counts cover normalized supplied content only, not provider billing or hidden context.
- Tokenizer cold setup needs network access. Preserve the warmed `.venv/tiktoken-cache` and its environment setting. Missing setup leaves token metrics unavailable without disabling diff/watch results.
- Research uncertainty about Nessie's internal implementation/export compatibility is unchanged. No affiliation, integration, publication, or outreach was introduced.

## Historical setup record

Setup inspected an empty, already initialized Git repository on `main` with no commits, confirmed default Python 3.10.12, researched primary sources, and created eight Markdown documents plus ignore/editor configuration and three placeholders. The setup inline documentation audit exited 0 after checking 11 local links, code fences, the schema example, three stage prompts, and placeholder-only directories. `git check-ignore .venv/example local_data/example.json exports/example.json .env .streamlit/secrets.toml` exited 0 with every intended match. Application tests were not run then because implementation did not exist. Stage 1 preserved that setup work, replaced only the source/test placeholders, and left `examples/.gitkeep` for Stage 2.

## Next recommended action

Stages 1–3 are complete. Follow [DEMO.md](DEMO.md) for the local demonstration. No further implementation, publication, deployment, or outreach is scheduled. No user input is needed.

## Stage update template

At each stage boundary record date, status, delivered behavior, exact commands/outcomes, environment, failures/skips/unverified items, departures, remaining tasks, and the precise next action. Completion requires executed acceptance checks and documentation, not just source files.
