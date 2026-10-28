# Stage 1 synthetic fixtures

These are hand-authored engine test data, not provider exports or a Stage 2 bundled example. `statuses.expected.json` records independently counted outcomes.

- Before order: keep, task, gone, dup-a, dup-b. After order: task, keep, new, dup-b, dup-a.
- Expected report order/status: task modified; keep retained; new added; dup-b retained; dup-a retained; gone removed. Both snapshots contain five blocks. The three retained blocks plus one modified plus one removed/added reconcile each side.
- Whitespace-word arithmetic stub: before `3 + 3 + 3 + 1 + 1 = 11`; after `4 + 3 + 1 + 1 + 1 = 10`; signed delta `-1`, or `-100/11` percent. Added `1` minus removed `3` plus modified delta `1` also equals `-1`. These are word-stub values, not reference tokens. Real-tokenizer tests are separate.
- Privacy matches keep on both sides after casefold/whitespace collapse. Window matches gone before and nothing after. Baseline's unseen phrase is absent before and after, so it is unverified, not newly lost.
- Equal duplicate text under dup-a and dup-b remains two independent blocks. Reordering does not change retention. Separate focused tests cover changed IDs, metadata edits, added summaries preserving phrases, punctuation/paraphrase/negation limits, and resource bounds.
