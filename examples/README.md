# Synthetic examples

## Basic comparison

`basic.before.json` and `basic.after.json` are hand-authored synthetic ContextDiff
v1 snapshots. Load them with **Load sample**, then **Compare**, or upload each file
with JSON selected. They are not provider or Nessie exports.

| Block ID | Expected status | Evidence |
| --- | --- | --- |
| `rule` | retained | Same text, kind, role, and first position |
| `task` | modified | Second line changes; stable ID and metadata |
| `finding` | modified | Identical text; kind changes from tool_result to memory and role from tool to assistant |
| `summary` | added | New ID in after position 4 |
| `constraint` | removed | Before position 4; absent after |

Before and after each contain four blocks: 1 retained, 2 modified, and 1
removed/added. The before watchlist checks three independently chosen phrases:
`privacy` is present in `rule` on both sides; `window` is found only in before's
`constraint`; `baseline` is absent on both sides and is an unverified baseline.

The real `cl100k_base` counts observed on 2026-10-28 are:

| Block ID | Before content tokens | After content tokens | Change |
| --- | --- | --- | --- |
| `rule` | 5 | 5 | 0 |
| `task` | 9 | 12 | +3 |
| `finding` | 4 | 4 | 0 |
| `summary` | 0 | 7 | +7 |
| `constraint` | 12 | 0 | -12 |
| Total | 30 | 28 | -2 (-6.7%) |

These are reference content counts summed per block, not provider billing.
The fixture test also independently hand-counts whitespace words (a test stub):
before `4 + 7 + 3 + 5 = 19`, after `4 + 8 + 3 + 6 = 21`. That deliberately
different result is not presented as reference tokens in the app.

This basic pair remains the compact all-status and metadata-only example.

## Coding-agent handoffs

`handoff.before.json` pairs with `handoff.lossy.after.json` or
`handoff.preserved.after.json`. These are hand-authored webhook-debugging contexts,
including a fictional test failure, not executed webhook tests or provider exports.
The app choices are **Coding handoff · lossy** and **Coding handoff · preserved**.
Select one, **Load sample**, then **Compare**. Uploading the named JSON files gives
the same result.

Both comparisons have the same independently inspected identities and order:

| Result order / block ID | Expected status | Evidence |
| --- | --- | --- |
| 1 / `instruction` | retained | Same instruction, system role, first position |
| 2 / `task` | modified | Investigation becomes a patch request under the same ID |
| 3 / `handoff-summary` | added | New summary ID; no many-to-one identity inference |
| 4 / `constraint` | removed | Original retention instruction absent as a block |
| 5 / `trace` | removed | Verbose tool output absent |
| 6 / `finding` | removed | Original memory block absent |

Each before has 5 blocks and each after 3: **1 added, 3 removed, 1 retained,
1 modified**. A removed source can still have its watched phrase in a new block.

| Watch ID / phrase | Before source | Lossy after | Preserved after |
| --- | --- | --- | --- |
| `window` / `24-hour idempotency window` | `constraint` | missing_after; no source | present_after; `handoff-summary` |
| `claim` / `atomic claim before enqueue` | `finding` | present_after; `handoff-summary` | present_after; `handoff-summary` |
| `privacy` / `Never log customer payloads` | `instruction` | present_after; `instruction` | present_after; `instruction` |

All authored block contents end in LF. Watch notes and labels are excluded from
matching and token totals. Only the before watchlist defines these checks.

| Block ID | Before tokens | Lossy after | Preserved after |
| --- | --- | --- | --- |
| `instruction` | 13 | 13 | 13 |
| `task` | 18 | 13 | 13 |
| `constraint` | 30 | 0 | 0 |
| `trace` | 188 | 0 | 0 |
| `finding` | 22 | 0 | 0 |
| `handoff-summary` | 0 | 26 | 38 |
| **Total** | **271** | **52** | **64** |
| **Change** | — | **-219 (-80.8%)** | **-207 (-76.4%)** |

Arithmetic checked independently: before `13 + 18 + 30 + 188 + 22 = 271`;
lossy `13 + 13 + 26 = 52`; preserved `13 + 13 + 38 = 64`. Relative to lossy,
the preserved alternative adds 12 reference tokens for the explicit constraint.
Both summaries are smaller than the removed source material, but these synthetic
reductions do not measure model quality, summarizer quality, or universal savings.

## Retrieval source swap

`retrieval.before.json` / `retrieval.after.json` is the **Retrieval · source swap**
choice. It has two blocks on each side, smaller than the handoff.

| Result order / block ID | Expected status | Before tokens | After tokens |
| --- | --- | --- | --- |
| 1 / `task` | retained | 15 | 15 |
| 2 / `runbook-concurrency-v1` | added | 0 | 19 |
| 3 / `runbook-retention-v1` | removed | 23 | 0 |
| **Total** | **1 added, 1 removed, 1 retained, 0 modified** | **38** | **34** |

The before `window` watch matches `runbook-retention-v1`; it has no after source
and is `missing_after`. Delta is `19 - 23 = -4`, or **-10.5%** of 38.
This illustrates active-context churn: the removed source *may* remain externally
retrievable. The named document paths are fictional identifiers in supplied text;
ContextDiff neither stores those documents nor connects to a retrieval service.

## Expectation checks and interpretation

All Stage 3 counts were checked on 2026-10-28 with tiktoken 0.14.0's
`cl100k_base`: directly encode each content string via
`encoding.encode(content, disallowed_special=())`, inspect per-block counts, and
sum them independently of ContextDiff. `tests/test_scenarios.py` fixes those
numbers, exact ordered identities, and watch source IDs as regression goldens.
It also checks kind/block reconciliation and recovers both complete input sources
from a JSON report round trip. Run `python -m pytest tests/test_scenarios.py` with
the warmed cache setting from README.

A paraphrase such as “retain keys for one day” misses the window watch. “Ignore the
24-hour idempotency window” still matches it. No watches means no preservation
assessment. Presence establishes a literal phrase match, not agreement, retained
model knowledge, semantic completeness, or downstream correctness. See the
[90-second walkthrough](../docs/DEMO.md) and [verification record](../docs/PROGRESS.md).
