# Research and MVP implications

Research date: **2026-10-28**. Sources below are public primary sources: vendor documentation, upstream repositories, and the original research paper. Public positioning can change. This document supports a small independent demonstration, not an assertion about Nessie's private needs or implementation.

## What Nessie publicly builds

Nessie's [product page](https://www.nessielabs.com/) describes collecting AI sessions and other work sources so people and agents can reuse them. It describes search and full-transcript access through CLI/MCP, with source grounding and permission controls. Its [YC profile](https://www.ycombinator.com/companies/nessie) lists the company in Fall 2025 and emphasizes shared organizational context. The profile also contains an older personal-knowledge launch; do not treat that older launch as the whole current product.

The public approach is capture, organize, and make past work available again. The [docs index](https://www.nessielabs.com/docs) lists integrations, generated contexts, session resumption, CLI, and MCP topics. Individual linked context-generation/resumption/reference pages could not be fetched during this session. We verified their presence in the index, not their underlying detailed behavior.

**Unknown:** internal storage/indexing architecture, retrieval/ranking algorithms, summarization or compaction policies, evaluation methods, snapshot export contracts, and whether Nessie already offers an equivalent diff. There is no verified public evidence here for a Nessie-specific compressor, token-budget algorithm, or automatic fact-preservation guarantee.

**Our inference:** a source-inspectable before/after comparison is relevant to evaluating reusable context and handoffs. ContextDiff can demonstrate careful handling of provenance, identity, token budgets, and preservation signals. It should not imitate Nessie's whole product or claim integration, novelty, or endorsement.

## Context-management problems

| Mechanism or challenge | What changes | Implication for ContextDiff |
| --- | --- | --- |
| Compaction/summarization | Earlier material is replaced by a shorter representation. Subtle constraints can disappear or be paraphrased. | Show the actual before/after text and tracked phrases; do not infer meaning from token reduction alone. |
| Truncation/sliding window | Earlier messages or selected tool results are excluded. A removed item may still exist outside active context. | Report removals from the supplied snapshot, not permanent deletion from all memory. |
| Retrieval | Selected external items enter and leave active context as queries/results change. | Distinguish block churn from knowledge destruction; preserve stable IDs and display both snapshots. |
| Context pollution and long inputs | Redundant, stale, or conflicting material competes with useful state. | A shorter input can be an improvement; avoid labeling every deletion harmful. |
| Position and visibility | Where evidence appears can matter; exported logs may omit actual model input components. | Expose order, qualify snapshot completeness, and avoid model-quality guarantees. |
| Model-specific accounting | Tokenization and request framing vary by provider/model. | Use a named reference encoding and state exclusions. |

These implications are engineering judgments informed by the following sources:

- Anthropic's [Effective context engineering for AI agents](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) discusses token selection, just-in-time retrieval, summarization, persistent notes, and the risk of dropping important details. It supports treating context as curated working state rather than equating it with the entire historical record.
- Anthropic's [context editing documentation](https://platform.claude.com/docs/en/build-with-claude/context-editing) describes selective clearing of old tool results and distinguishes this from summary-based compaction. Removed raw tool content can therefore be intentional.
- OpenAI's [compaction documentation](https://developers.openai.com/api/docs/guides/compaction) describes compaction output that includes opaque encrypted state. A text-only comparison cannot decode that state or determine what it preserves; the MVP should not advertise inspection of arbitrary provider compaction internals.
- Liu et al.'s [Lost in the Middle](https://arxiv.org/abs/2307.03172) reports position-sensitive performance on its evaluated long-context tasks and models. This motivates visibility into ordering, but does not establish performance behavior for every current model or validate ContextDiff as a quality metric.

## Existing debugging and observability approaches

| Tool | Publicly documented capability | What we take from it |
| --- | --- | --- |
| [Langfuse](https://langfuse.com/docs/observability/overview) | Application traces include prompts, responses, token usage, latency, tools, and retrieval steps. | Inspectable inputs and token breakdowns are useful developer affordances. |
| [Phoenix](https://arize.com/docs/phoenix/tracing/concepts-tracing/how-tracing-works) | Instrumented spans flow through exporters to a collector and troubleshooting UI. | ContextDiff can work on supplied files without implementing tracing infrastructure. |
| [LangSmith](https://docs.langchain.com/langsmith/manage-trace) | Trace management, sharing, and associated execution logs. | Make comparison results reviewable. The former `compare-traces` URL redirected to this page; no current comparison feature details were verified from that redirect. |

These are broader observability systems, not dependencies for this project. ContextDiff's chosen scope is one explicit two-snapshot comparison with evidence for watched phrases. This research does **not** establish that existing tools lack equivalent functionality.

## Practical comparison methods

| Method | Strength | Limitation and decision |
| --- | --- | --- |
| Whole-document line diff | Simple and deterministic for arbitrary text. | Weak message identity; use for plain-text document detail. |
| Stable block IDs + equality | Unambiguous additions, removals, and edits even with repeated content. | Users/exporters must preserve logical IDs. Chosen structured-input method. |
| Content hashes/exact-text matching | Can find exact duplicates efficiently. | Cannot establish logical identity or distinguish duplicate occurrences by itself. Not needed for a small ID-based MVP. |
| Fuzzy lexical similarity | Can suggest near matches when IDs are missing. | Thresholds and ambiguous pairings need explanation; high lexical similarity does not mean identical facts. Defer. |
| Embeddings or LLM judgments | May detect paraphrases. | Additional assets/APIs, calibration, nondeterminism, and semantic false positives exceed scope. Defer. |
| Explicit phrase watchlist | Cheap, deterministic, and source-inspectable check of engineer-selected details. | Misses paraphrases, contradictions, and phrases split across blocks. Use as a review signal only. |

## Library evaluation

- Python's official [difflib documentation](https://docs.python.org/3/library/difflib.html) provides line alignment and opcodes in the standard library. SequenceMatcher has worst-case quadratic behavior and an automatic repeated-item heuristic. Use explicit IDs for block matching, disable `autojunk` for line detail, and enforce line/product budgets. Do not promise a minimal edit script.
- [RapidFuzz's official reference](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html) provides lexical similarity functions. It is an option for future approximate matching, but the chosen MVP does not require it.
- The upstream [tiktoken repository](https://github.com/openai/tiktoken) provides reference BPE encodings. Use one named encoding and ordinary-text handling. Its [vocabulary definitions](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py) reference public assets; its [loader implementation](https://github.com/openai/tiktoken/blob/main/tiktoken/load.py) fetches and caches data and honors `TIKTOKEN_CACHE_DIR`. Installation alone does not guarantee a cold offline run. Do not upload snapshot content as part of token counting.
- [Hugging Face Tokenizers](https://huggingface.co/docs/tokenizers/index) supports diverse tokenization pipelines. It is a reasonable alternative for model-specific expansion; asset selection adds complexity with no core MVP benefit.
- Streamlit's [uploader documentation](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader) documents upload controls and notes that file-type filtering is best effort. Validate content and size in the core. Its [AppTest reference](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest) supports simulated UI checks; still manually verify actual file interactions and layout.

## Technical risks and planned mitigations

Stage 1 evidence (2026-10-28): the core tests now cover identity, lexical-watch limitations, real reference token counts, reconciliation, validation, and bounded repetitive diffs. Inspected the installed tiktoken 0.14.0 `tiktoken/load.py` to verify the documented cache precedence, empty-setting behavior, public vocabulary download, and expected setup exceptions. Installed distribution metadata confirms tiktoken 0.14.0 requires Python 3.9+ and Streamlit 1.66.1 requires 3.11+; only Python 3.12.2 was exercised. Socket-blocked subprocess tests establish warmed core operation and cold-cache recovery, not the complete offline UI demo. Exact commands/results are in [PROGRESS.md](PROGRESS.md). This implementation evidence does not change the public-product findings or their uncertainty above.

| Risk | Mitigation | Required evidence before delivery |
| --- | --- | --- |
| Incorrect block correspondence | Require stable IDs; reject duplicates; never silently fuzzy-match. | Tests for repeated content, changed IDs, reorder, and metadata-only edits. |
| Phrase checks mistaken for semantic guarantees | Display match rule, source IDs, and limitations; use neutral labels. | Preserved-summary, paraphrase, negation, and missing-baseline cases. |
| Misleading token figures | Named encoding, additive per-block convention, explicit exclusions and null unavailable values. | Real-tokenizer tests and total/delta reconciliation. |
| First-run tokenizer network requirement | Warm vocabulary explicitly and document cache setup. | Warmed-cache demo with network disabled; clear failure path when unavailable. |
| Slow repetitive diffs | Input bounds plus per-pair and cumulative alignment budgets; complete-text fallback. | Boundary/repetitive tests and measured normal-demo timing. |
| Private traces or unsafe rendering | Synthetic examples; no content logging/global data cache; text/code rendering. | Manual inspection of HTML-looking inputs, exports, and local-only operation. |
| Dependency/environment friction | Small dependency set, isolated venv, actual version recording. | Fresh-environment install and launch instructions tested in Stage 3. |
| Scope creep | Three bounded stages; no live capture, semantic matching, or paid APIs. | PLAN and PROGRESS stay aligned; optional visual detail is cut first. |

## Research conclusion for this build

Stage 2 library verification (2026-10-28): consulted the official [AppTest reference](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), [file uploader reference](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader), and [download button reference](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button). Inspected installed Streamlit 1.66.1 signatures and `elements/code.py`: native code display removes one boundary LF even though the core/report preserves it. AppTest now checks that distinction. Real browser checks separately verified uploads (including transport/core byte limits), literal source display, and JSON download. These findings support the implementation choices, not a broader compatibility or offline claim; exact evidence is recorded in PROGRESS. Public-product findings and uncertainty above remain unchanged.

The useful demonstration is a transparent audit of visible context changes: exact identities where available, readable text evidence, reconciled reference token counts, and an explicit preservation watchlist. Its strength is explainability and honest limits. It is not an evaluation of hidden memory or a replacement for observing actual agent behavior.
