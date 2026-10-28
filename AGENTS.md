# ContextDiff agent instructions

## Purpose and current state

Build a small, polished local tool that compares two supplied LLM context snapshots. Explain additions, removals, retained and modified blocks, content-token changes, and disappearance of explicitly watched phrases. This is an approximately one-day engineering demonstration relevant to context preservation, intended for eventual sharing with Nessie. There is no affiliation or integration with Nessie.

The setup session created documentation and empty directories only. **Stages 1–3 are complete within the verification boundaries in docs/PROGRESS.md: the core, local Streamlit app, synthetic examples, tests, and demo/delivery records exist.** Check `docs/PROGRESS.md` for verified outcomes. No further stage is scheduled; make additional changes only when requested.

## Read before changing files

1. Read `docs/PROGRESS.md` and the requested stage in `docs/PLAN.md`.
2. Read `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, and `docs/DECISIONS.md` before implementation or changing a contract.
3. Consult `docs/RESEARCH.md` when making claims about Nessie, context management, or library behavior. Distinguish verified facts from our design judgments.
4. Inspect current code and Git changes; preserve work outside the task. Documentation describes intended behavior until implementation and verification establish otherwise.

## Architecture and repository

- Python 3.10+; recommend Python 3.12 for a fresh environment. Confirm actual library compatibility when installing.
- Pure Python core in `src/contextdiff/`; standard-library dataclasses, JSON, and `difflib`.
- `tiktoken` for one fixed reference encoding, `cl100k_base`. Counts cover supplied content, not provider billing or hidden context.
- Streamlit entry point `app.py`, introduced in Stage 2. No web framework or UI imports inside core modules.
- `tests/` for pytest tests; `tests/fixtures/` added in Stage 1.
- `examples/` for synthetic, human-readable demo pairs added during implementation.
- `docs/` for specification, architecture, plan, progress, decisions, research, and eventual demo instructions.
- `pyproject.toml` and package initialization are Stage 1 deliverables, not setup-session files.

## Coding conventions

- Type public functions and data structures. Use small functions and explicit dataclasses; prefer `snake_case`, clear names, and short docstrings for non-obvious behavior.
- Keep parsing, diffing, tokenization, analysis, and rendering separate. Functions should not mutate snapshots.
- Follow the schema and algorithms in `docs/ARCHITECTURE.md`. Do not add fuzzy identity matching, semantic equivalence claims, or implicit provider-format detection.
- Validate external inputs at the boundary. Raise descriptive domain errors without including full private snapshots in logs or tracebacks shown to users.
- Use a single formatting/linting tool, Ruff, and pytest. Do not introduce a type-checking toolchain or framework abstraction without a concrete need.
- Render user content as text/code. Never evaluate it or insert it as unescaped executable HTML.

## Development commands

These commands become usable as their stage delivers the necessary files. Do not present them as already verified.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"       # Stage 1: pyproject + package exist
python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"
python -m pytest                       # Stage 1 onward
python -m ruff check .
python -m ruff format --check .
python -m streamlit run app.py --server.address 127.0.0.1  # Stage 2 onward
```

The tokenizer warm-up can download public vocabulary data. No API key is needed; snapshot content must never be sent to a model. Document cache behavior and test a warmed-cache run without network before claiming offline readiness.

## Verification requirements

- Test core contracts: validation, identity matching, duplicates, reorder, newline handling, exact equality, missing phrases, token accounting, and resource limits.
- Use hand-checked fixtures and conservation invariants, not just assertions that duplicate the implementation.
- Test the real tokenizer separately from deterministic counter stubs. Explicitly report any skipped or blocked integration test.
- In Stage 2, add a few Streamlit AppTest checks for meaningful flows and manually inspect uploads/downloads and layout in a browser.
- Test errors and recovery as well as the demo's happy path. Do not add brittle screenshot snapshots or a large browser automation stack.
- Run checks appropriate to each change. Record exact commands and outcomes, including failures or unrun checks. Never claim tests passed unless executed successfully.

## Scope and complexity rules

- One local app, two snapshots, two runtime dependencies. Core comparisons require no LLM API, accounts, or paid services.
- No database, authentication, cloud deployment, background ingestion, provider adapters, vector search, embeddings, agents, or live Nessie integration.
- No summarizer or compaction engine. Compare supplied before/after states; do not generate them with an LLM.
- Stable IDs establish block identity. Retained means text and relevant block metadata are unchanged, not that a model understood or remembered the information.
- Watched-phrase absence is a review signal, not proof of semantic loss, contradiction detection, or downstream model failure.
- Bound expensive operations. Preserve complete source text in results when detailed alignment is skipped.
- Solve the requested stage before adding features. Keep optional enhancements out when they threaten the one-day budget. Do not create parallel agent work unless the user explicitly requests it.

## Documentation maintenance

- Update `docs/PROGRESS.md` at each stage boundary and when work stops: status, completed work, remaining work, blockers, checks, and the precise next action.
- Keep `docs/PLAN.md` aligned with actual scope. Record material departures and rationale in `docs/DECISIONS.md`; update `docs/ARCHITECTURE.md` for contract changes.
- Update README status and commands when runnable behavior changes. Remove future-tense claims only after verification.
- Preserve research URLs, retrieval dates, and uncertainty. Do not invent Nessie's internal implementation or imply product endorsement.
- Stage completion requires its acceptance criteria and documentation updates. If incomplete, state what remains instead of marking it done.
