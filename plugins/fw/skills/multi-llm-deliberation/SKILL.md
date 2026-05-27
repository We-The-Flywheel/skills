---
name: multi-llm-deliberation
description: Use when you need diverse AI perspectives on architecture decisions, code review, or complex questions - runs a 3-stage deliberation (diverge, rank, synthesize) across 4 models for consensus answers. Triggers on "ask multiple models", "get consensus", "llm council", or any request for multi-model review.
---

# Multi-LLM Deliberation - Multi-Model Consensus

Get diverse AI perspectives through a 3-stage consensus process with 4 models via OpenRouter.

Self-contained — no external backend or dependencies beyond Python 3 and an OpenRouter API key.

## When to Use

- **Architecture decisions:** "Should we use PostgreSQL or MongoDB?"
- **Code review:** "Review this authentication implementation"
- **Design debates:** "Best approach for handling user sessions?"
- **Complex questions:** When you want multiple AI perspectives
- **Reduce bias:** Get consensus from diverse models (open-source + commercial)
- **Plan review:** After a planning exercise, get multi-model critique and improvement

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

## Process

1. **Stage 1 - Diverge:** 4 models answer independently (parallel)
2. **Stage 2 - Rank:** Models anonymously rank each other's responses (parallel)
3. **Stage 3 - Synthesize:** Top model creates consensus from all responses

## Models

- **Gemini 3 Flash** (ultra-cheap) - Google's fast model
- **Grok 4.1 Fast** (cost-efficient) - xAI's latest
- **GPT-4.1 Mini** (cost-efficient) - OpenAI's small model
- **DeepSeek V3** (ultra-cheap) - DeepSeek's flagship
- **Mistral Small 3.1** (ultra-cheap) - Mistral's efficient model, European perspective
- **Synthesizer:** Gemini 3 Flash (creates consensus from ranked responses)

3 AI ecosystems represented: US (Google, xAI, OpenAI), China (DeepSeek), Europe (Mistral).

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

1. Individual responses from all 4 models
2. Peer rankings (how models rated each other)
3. Synthesized consensus answer
4. Cost estimate
