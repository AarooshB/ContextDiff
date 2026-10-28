# ContextDiff project specification

Status: Stages 1–3 implemented and verified on 2026-10-28 within the single-platform
and app-process offline boundaries recorded in [PROGRESS.md](PROGRESS.md).
Specification established 2026-10-28. The local UI includes a basic sample,
lossy/preserved synthetic handoffs, and a retrieval swap. Fresh installations,
checked reports, sample timings, and the paced demonstration are delivered in
[DEMO.md](DEMO.md). No further stage is scheduled.

## Problem

An agent's next request may contain a different set of instructions, messages, summaries, tool results, and retrieved documents from its preceding request. Token totals alone do not reveal what disappeared. Ordinary text diffs expose edits but lack block identity, context categories, and explicit checks for facts the engineer cares about.

ContextDiff accepts two exported or manually prepared snapshots and explains the visible change. The snapshots must represent the context the developer wants to inspect; a chat transcript is not necessarily the complete input sent to a model. Hidden instructions, opaque compaction state, and unexported memory remain outside the tool's visibility.

## Users and use cases

- Agent developers inspecting a context before and after compaction or truncation.
- Engineers reviewing changes to retrieved documents or memory included in consecutive requests.
- Context-tool builders demonstrating the relationship between smaller inputs and preservation of explicitly tracked details.

Relevance to Nessie is an engineering judgment based on its public emphasis on reusable context and source-grounded history; see [RESEARCH.md](RESEARCH.md). We do not know its internal algorithms or assume it needs this exact feature.

## MVP functionality

1. Load two explicitly selected JSON snapshots or two UTF-8 text inputs, pasted or uploaded.
2. Validate inputs with actionable errors and fixed resource limits.
3. Classify structured blocks as added, removed, retained, or modified using stable IDs. Show original positions without implying that every index shift is a meaningful move.
4. Show line edits inside changed content and full source text when detailed alignment exceeds its budget.
5. Count supplied content tokens using one fixed reference encoding, with totals and per-kind breakdowns.
6. Check the before snapshot's optional watchlist against both snapshots and explain each result.
7. Offer bundled synthetic examples, status/kind filters, and a JSON report download.

## Intended user experience

The opening screen explains the tool in one sentence and offers a sample comparison. A single format selector applies to both inputs; each side accepts a paste or upload with explicit source selection. The user presses Compare after choosing Before and After. Input changes invalidate the previous result so stale output is never presented as current.

Results start with before/after tokens and signed change, four block-status counts, and watched phrases needing review. A small native chart breaks down content tokens by kind. Below it, labeled before/after panels show full block text, role/kind changes, and readable line edits. Filters narrow the view without altering global totals. Color has accompanying text labels; unchanged content can be collapsed. Blank, malformed, oversized, and tokenizer-unavailable states explain how to recover.

A watchlist notice says: “Phrase not found in the supplied after snapshot; it may have been paraphrased or remain in external memory.” Phrase presence also does not establish agreement or correctness; a negated sentence can contain the same words.

## Technical design

Use Python 3.10+, a pure core package, Streamlit, and tiktoken. Use standard-library dataclasses, JSON validation, and difflib; pytest and Ruff are development tools. The architecture and precise schema live in [ARCHITECTURE.md](ARCHITECTURE.md). No model calls, embeddings, or automatic semantic judgments are needed.

The backend is a library within the same process as Streamlit, not a separately deployed server. Read supplied files into memory; create downloadable reports in memory. There is no default storage of user inputs or reports.

## Success criteria

- A fresh developer can install and launch using the final README, without an account or API key.
- All four structured statuses and line edits agree with hand-checked fixtures.
- Token deltas reconcile with per-block changes; empty baselines never divide by zero.
- A watched constraint disappears in one synthetic summary and survives in another, with evidence traceable to the source text.
- The demo explains additions/removals under changed IDs honestly and does not claim semantic matching.
- Invalid input, repetitive content, special-token-like strings, and tokenizer setup failures produce useful behavior.
- A warmed-cache offline demo succeeds and its verification is recorded. Normal sample comparisons aim for under one second on the development machine; Stage 3 measurements meet that aim within the recorded engine-only boundary, without a universal performance promise.
- A 90-second walkthrough communicates the tool's value and limitations. Tests and current progress are accurately documented.

## Explicit non-goals

Production observability, tracing ingestion, automatic provider exports, Nessie API integration, multi-user collaboration, authentication, persistence, cloud hosting, continuous monitoring, context generation, summarization, compression, vector search, semantic equivalence, contradiction detection, importance scoring, recovery of hidden state, cost estimates, provider billing accuracy, and model-quality benchmarks.

## Delivery budget

Stages 1–3 target 6–7.5 hours, plus at most 30 minutes contingency. Preserve core correctness and a coherent demo if time is tight. Cut word-level highlighting, elaborate styling, and extra scenarios before weakening validation, tests, truthful labels, or the documented limitations.
