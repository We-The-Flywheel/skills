---
name: ultrahumanizer
version: 1.0.0
description: |
  Iterative human-in-the-loop rewrite loop that takes a text to a passing Pangram
  score. Runs the humanizer skill's craft patterns, scores the text with the
  Pangram API, maps flagged windows back to passages, and coaches the HUMAN to
  rewrite those passages in their own words — then re-scores until the text
  passes or the loop stalls. The agent never regenerates flagged prose itself
  (empirically proven not to move Pangram); it structures, scores, and flags.
  Use when the user says "ultrahumanizer", "get this past Pangram", "make this
  pass AI detection", "rewrite with me until it passes", or wants a
  detector-passing version of a draft. Requires a PANGRAM_API_KEY environment
  variable.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

# Ultrahumanizer: Human-in-the-Loop Pangram Pass Loop

Take a draft to a passing Pangram verdict through iterative **human** rewriting,
with the agent as scorer, mapper, and craft coach — never as the rewrite engine.

## The one rule that makes this work (read first)

Our Pangram experiments (June 2026 test set + a July 2026 real-world masking
test — full evidence note at the top of the `humanizer` skill in this pack)
proved:

1. **Agent rewrites of AI-origin text NEVER lower the score.** Vocab swaps,
   burstiness, register transplants, multi-pass regeneration, "messy human"
   rewrites — all stayed at 100% AI. So this skill must NOT loop
   "agent rewrites → re-score". That loop cannot converge and only burns API credit.
2. **Human-origin prose passes.** Genuine human drafting scores 0%. A strongly
   idiosyncratic human-voiced frame can even mask a small residual AI span
   (~10–15% in one window) — but that's fragile, never a target.
3. **Therefore the ONLY converging loop is:** Pangram flags a window → the
   **user** rewrites/re-dictates that passage in their own words → agent
   integrates it near-verbatim → re-score.

**Agent hard limits during this loop:**
- Integrate the user's rewrite **verbatim**. Allowed fixes: typos, punctuation,
  capitalization, paragraph breaks. NOT allowed: rephrasing sentences,
  "smoothing", adding transitions, generating even one new sentence of body
  prose. Every agent-generated sentence re-injects the AI fingerprint you're
  trying to remove.
- Craft feedback (humanizer patterns) is delivered as **suggestions the user
  applies in their own words**, not as agent edits.

If the user wants the agent to just rewrite it for them, stop and say plainly:
that produces better prose but will NOT pass Pangram — evidence says so.

## Your task

### Step 0 — Setup & expectations

1. Get the text (file path or pasted). Save a working copy to a temp working
   directory as `ultrahumanizer/draft_v0.txt`.
2. Tell the user the deal in two sentences: *you* will do the rewriting of
   flagged passages (typing or dictation), the agent scores and coaches.
   Mention cost: each scoring pass ≈ `words/1000 × $0.05`.
3. Ask for the pass bar with AskUserQuestion:
   - **Strict (recommended):** `prediction_short == "Human"` and `fraction_ai == 0.0`
   - **Lenient:** `fraction_ai < 0.2` ("Unclear" band or better)
4. Max iterations: 5 (then stop and report honestly).

### Step 1 — Baseline Pangram score

Scoring mechanics live in the `pangram` skill in this pack — follow its
submit/poll flow. Key facts inline:

- `POST https://text.external-api.pangram.com/task`, header `x-api-key`,
  body `{"text": ...}` → returns `task_id`
- Poll `GET .../task/<task_id>` until `stage == "STAGE_SUCCESS"`. Tasks can take
  1–3 minutes on longer texts — poll every 5 s with a generous timeout, or
  submit, wait ~60 s, then check.
- Auth: set `PANGRAM_API_KEY` in your environment (a Pangram Labs API key from
  pangram.com). If unset, stop and tell the user to set it before re-running.
- **Gotcha:** the result JSON contains raw control characters (the echoed text).
  Parse with `json.loads(raw, strict=False)` in Python — plain `json.load` throws.

If baseline already passes the chosen bar → skip to Step 5 (craft-only pass).

### Step 2 — Map flagged windows to passages

The result's `windows` array gives per-window `label`, `ai_assistance_score`,
`confidence`, `start_index`, `end_index`, `word_count` (~380 words per window).

For every window not labeled `Human Written`:
1. Slice the draft by `start_index:end_index` to recover the flagged passage.
2. Within it, run the humanizer pattern scan (all patterns from the `humanizer`
   skill in this pack) to point at the most AI-fingerprinted sentences —
   uniform 15–25-word sentences, -ing tails, copula avoidance, AI vocabulary
   clusters, rule-of-three, negative parallelisms.
3. Reduce the passage to **content bullets**: what facts/points it conveys,
   stripped of all phrasing. This is what the user rewrites *from*, so they
   aren't anchored to the AI sentences.

### Step 3 — The human rewrite (the actual engine)

Per flagged passage, present a rewrite card:

```
PASSAGE 2 of 3 — flagged AI (window 1, confidence High)
Says: • <content bullet> • <content bullet> • <content bullet>
Most-fingerprinted lines: "<worst sentence>", "<second worst>"
Your move: rewrite this from the bullets in your own words. Don't look at the
original while writing. Talk it, don't compose it.
```

Coaching (from what actually carried the 0%-scoring human text in our tests):
first-person asides, specific memories and numbers only they know, rhetorical
questions, sentence fragments, uneven rhythm, their own idioms — **written or
spoken by them**, never pasted from a stock-phrase list (canned colloquialisms
like "at the end of the day" are themselves AI tells — see the humanizer's
sentence-opener-cliché pattern).

Input paths:
- Typed directly in chat (fine).
- **Dictation (best):** if the user has any voice-memo → transcription
  workflow, offer it — the user re-dictates the passage on their phone and the
  transcript comes in as the rewrite. Spoken re-dictation is the strongest
  human-origin signal we know of.

Integrate each rewrite verbatim (mechanical fixes only). Save as
`draft_v<N>.txt` — keep every version for diffing.

### Step 4 — Re-score and iterate

Re-run Pangram on the full new draft. Report per iteration:

```
Iteration 2 — 1129 words (~$0.06)
  overall: fraction_ai 0.34 → 0.0   prediction: AI → Human
  window 0: AI (0.99) → Human (0.004)   [user re-dictated]
  window 1: Human — unchanged
```

- Window still flagged after a real human rewrite → the human share of that
  window may still be too thin; widen the rewrite to neighboring paragraphs
  (window boundaries at ~380 words mean surrounding prose votes too).
- No improvement after 2 rounds on the same window → check the user isn't
  paraphrasing the AI original line-by-line (anchoring). Re-issue content
  bullets only, original hidden.
- Hit max iterations without passing → stop, show the trajectory, say what's
  left honestly. Do not quietly agent-rewrite as a "last resort".

### Step 5 — Craft pass + final verdict

Once the bar is passed:
1. Run the full humanizer pattern review over the final text — as flags with
   suggested phrasings for the user to accept in their own words. If a
   `VOICE.md` applies (walk up from the target file), load it per the
   humanizer's Step 0. Substantive rewrites the user accepts here should
   ideally come from them; trivial mechanical fixes (straight quotes, title
   case, em dashes per voice rules) the agent may apply directly.
2. **If craft edits changed more than punctuation, re-score once more** —
   the passing verdict must be for the shipped text, not an ancestor of it.
3. Final report: verdict + fraction_ai, iteration history table, total Pangram
   spend, path to final file, and the standing caveats — the verdict is
   Pangram-specific and dated (other detectors window differently; model
   updates can change results), and Pangram's dashboard sentence-level view may
   still flag individual sentences the API verdict absorbed.

## Failure modes to name, not hide

- **User has no time to rewrite** → this skill cannot help; offer plain
  humanizer (better prose, no detector promise).
- **Text must stay verbatim** (legal, quotes) → flagged windows can't be
  rewritten; report as unpassable.
- **Repeated 100% with no movement** → the draft is likely too AI-dense for
  masking; recommend a fresh human draft from an outline (agent may write the
  outline — outlines don't ship).

## Cost & etiquette

- Score at most once per iteration (full text). Never score per-passage.
- 5 iterations on a 1,200-word post ≈ $0.30 total. Say the number up front.
- Log iteration results to the working directory (`ultrahumanizer/scores.jsonl`)
  so a resumed session doesn't re-burn scoring calls.
