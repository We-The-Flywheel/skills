---
name: multi-llm-deliberation
description: Use when you need diverse AI perspectives on architecture decisions, code review, or complex questions - runs a 3-stage deliberation (diverge, rank, synthesize) across 5 models for consensus answers. Also runs Content Truth-Check Mode to fact-check claims in content drafts before publishing. Triggers on "ask multiple models", "get consensus", "llm council", "fact-check this draft", "truth check", or any request for multi-model review.
---

# Multi-LLM Deliberation - Multi-Model Consensus

Get diverse AI perspectives through a 3-stage consensus process with 5 models via OpenRouter.

Self-contained — no external backend or dependencies beyond Python 3 and an OpenRouter API key.

## When to Use

- **Architecture decisions:** "Should we use PostgreSQL or MongoDB?"
- **Code review:** "Review this authentication implementation"
- **Design debates:** "Best approach for handling user sessions?"
- **Complex questions:** When you want multiple AI perspectives
- **Reduce bias:** Get consensus from diverse models (open-source + commercial)
- **Plan review:** After a planning exercise, get multi-model critique and improvement
- **Content truth-check:** Fact-validate a content draft before publishing

## Plan Review Mode (Default After Planning)

When invoked after a planning exercise or while in plan mode, **automatically frame the deliberation as a plan review**. Do NOT ask the user what question to send — construct it yourself.

**How to detect:** You just finished writing or discussing a plan (PLAN.md, implementation plan, feature plan, architecture plan, etc.), or the user is in plan mode, or the user said "review the plan" / "get feedback on this".

**What to do:**

1. Read the current plan content (from the active plan file, plan mode buffer, or recent conversation)
2. Construct the deliberation question using this template:

```
Review and improve this implementation plan. For each section:

1. What's missing or underspecified?
2. What could go wrong that isn't addressed?
3. What would you change to make this more robust?
4. Are there simpler approaches for any part?
5. Rate the overall plan 1-10 and explain what would make it a 10.

Here is the plan:

<paste full plan content here>
```

3. Run the council with that constructed question
4. After receiving the consensus, **apply the feedback to the plan** — update the plan file or present the improved version, don't just show the raw council output

This saves the user from having to manually copy-paste the plan and write review instructions every time.

## Content Truth-Check Mode (Fact-Validating Drafts)

When the input is a **content piece** (article, blog post, landing page, guide — anything headed for a public URL), frame the deliberation as **fact verification, not opinion consensus**.

**How to detect:** The user says "fact-check this", "truth check", "validate the claims", "is this accurate", on a piece of content (not a plan) — or you're running a pre-publish review pass on a draft.

**Division of labor — read this before running anything:**

The council models have **no web access**. Their verdicts come from training data, so their value is the *cross-model agreement signal*: five diverse models (3 ecosystems) independently disagreeing on a claim is a strong hallucination flag; unanimous agreement on a stable fact is meaningful support. They can NOT settle anything volatile or post-cutoff. **You (the in-session agent) have web search/fetch tools — claim extraction happens before the council, and web verification of everything the council can't settle happens after.** Never treat council consensus alone as ground truth: shared training-data errors exist.

**Steps:**

1. **Extract atomic claims (you, before calling the council).** Decompose the draft into numbered, externally verifiable claims — one fact each: dates, statistics, names/titles, prices, rights/licensing ("X holds the rights through 2029"), version numbers, superlatives ("first/largest/only"), quotes and their attributions. **Exclude** opinions, experience markers ("in our testing"), and normative statements — those are voice, not facts.

2. **Classify volatility.** Mark each claim:
   - `STABLE` — historical/settled fact, unlikely to have changed
   - `VOLATILE` — prices, current rights-holders/broadcasters, schedules, "current" anything, claims plausibly changed after model training cutoffs

   VOLATILE claims **skip the council** and go straight to web verification (step 5) — polling offline models about them invites confident staleness.

3. **Construct the council question** for the STABLE claims:

```
You are fact-checking claims extracted from a machine-generated draft article. The draft may contain hallucinations — do NOT assume any claim is correct because it sounds plausible or appears in the draft.

For EACH numbered claim, give a verdict from your own knowledge:
- TRUE — confident it is correct
- FALSE — confident it is wrong (state the correction)
- UNCERTAIN — you don't know or can't verify

Rules: verdict each claim independently. If a name, date, number, or attribution is even slightly off, answer FALSE with the correction. Calibration matters more than confidence — UNCERTAIN is a good answer.

Claims:
C1. <claim>
C2. <claim>
...

Reply as a list: "C1: TRUE|FALSE|UNCERTAIN — one-line justification or correction".
```

   Run it with low temperature: `python3 council.py --temperature 0.2 "<question>"`.

4. **Score agreement across models** per claim:
   - `CONFIRMED` — all responding models say TRUE
   - `REFUTED` — majority FALSE with a consistent correction
   - `DISPUTED` — any disagreement, or UNCERTAIN votes

5. **Web-verify (you, after the council):** every `VOLATILE`, `REFUTED`, and `DISPUTED` claim via web search/fetch against authoritative sources (official sites, primary sources — not aggregators). Record the source URL per claim. `CONFIRMED` claims pass without search unless they're load-bearing for the piece's core argument — spot-check those too.

6. **Repair surgically.** Fix only the claims proven wrong or outdated, preserving the surrounding prose and the piece's voice — never rewrite paragraphs wholesale. A claim that can't be verified anywhere → flag it to the user as `UNVERIFIABLE` and ask whether to cut or keep; don't silently decide.

7. **Output a claim table:** `claim | volatility | council verdict | final verdict | source | fix applied`. If the page shows a visible `Updated:` date, confirm no VOLATILE fact predates it.

**Cost:** same as a normal deliberation (~$0.003–0.012) plus your web searches.

## Process

1. **Stage 1 - Diverge:** 5 models answer independently (parallel)
2. **Stage 2 - Rank:** Models anonymously rank each other's responses (parallel)
3. **Stage 3 - Synthesize:** Top model creates consensus from all responses

## Models

Authoritative list: the `MODELS` dict in `council.py` — this section mirrors it and must be updated together with it.

- **Gemini 3.1 Flash Lite** (ultra-cheap) - Google's fast model
- **GPT-4.1 Mini** (cost-efficient) - OpenAI's small model
- **DeepSeek V3** (ultra-cheap) - DeepSeek's flagship
- **Mistral Small 3.1** (ultra-cheap) - Mistral's efficient model, European perspective
- **Llama 3.3 70B** (ultra-cheap) - Meta's open-weights model
- **Synthesizer:** Gemini 3 Flash Preview (creates consensus from ranked responses)

3 AI ecosystems represented: US (Google, OpenAI, Meta), China (DeepSeek), Europe (Mistral).

## Cost

**~$0.003-$0.012 per deliberation** via OpenRouter (5 models, all cheap tier).

## Usage

```bash
# From Claude Code
/multi-llm-deliberation "Your question here"

# Direct
python3 skills/multi-llm-deliberation/council.py "Should we use Redis or Memcached?"
bash skills/multi-llm-deliberation/council.sh "Best database for time-series data?"
```

## Requirements

- `OPENROUTER_API_KEY` in environment or `~/.env.shared`
- Python 3.10+ (stdlib only, no pip install needed)

## Error Handling

**IMPORTANT:** If the script fails (exit code 2), report the error message to the user verbatim. Do NOT silently fall back to using Claude subagents or any alternative approach. Common errors:
- **HTTP 402**: OpenRouter has no credits — tell the user to top up at https://openrouter.ai/settings/credits
- **HTTP 401**: API key invalid — tell the user to check OPENROUTER_API_KEY
- **HTTP 429**: Rate limited — tell the user to wait and retry

## Output

1. Individual responses from all 5 models
2. Peer rankings (how models rated each other)
3. Synthesized consensus answer
4. Cost estimate
