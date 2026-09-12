# Humanizer

A Claude Code skill that rewrites AI-sounding text so it reads like the writer, without changing what it says. A craft tool for readability and voice, not an AI-detector-evasion tool.

## Installation

Part of the `wtf` plugin marketplace:

```
/plugin marketplace add We-The-Flywheel/skills
/plugin install wtf
```

Then invoke with `/wtf:humanizer`.

## Usage

```
/wtf:humanizer

[paste your text here]
```

Or ask Claude directly: "humanize this text", "humanize the prose in docs/launch-post.md".

Supply two or three writing samples to match a voice. The sample overrides the patterns below, including the dash rule.

## Overview

A language model writes whatever is most likely to come next, so by default it makes the choice that fits the widest range of readers and subjects. A human writer chooses for one reader and one subject, so their choices are uneven and specific. Every pattern in the skill is one form of that default choice.

Word habits change with every model release. Structural habits persist, so the patterns are ordered structure-first: vocabulary is group C, not group A.

### Severity

A tell counts in proportion to how rarely a careful writer would make it on purpose.

- **Act on sight.** Groups A and E, plus any pattern not marked otherwise.
- **Weak alone.** Patterns tagged *weak alone* (a lone em dash, triad, hedge, curly quote, repeated opening, hyphenated pair, passive construction, synonym cycle) need a second tell in the same passage. This is what stops the skill from over-editing deliberate prose.

### Fact guardrail

The rewrite may add no fact, name, number, date, quote, citation or ranking that is not in the source, and may drop none that is present. The three shape patterns that delete content most often (triads, stacked qualifiers, bold labels) carry an inline reminder.

### Output modes

- **Pasted text** (default): draft, a short list of remaining patterns, then the final rewrite.
- **File mode**: writes only the final text; leaves code, inline code, commands, paths, YAML frontmatter, data, and link targets unchanged.
- **Embedded mode**: returns only the final text, for when another skill or a pipeline step calls it.

## 31 patterns detected

### A. Staging instead of stating (act on sight)

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 1 | Not X but Y | "It's not merely a song, it's a statement" | "The heavy beat adds to the aggressive tone" |
| 2 | One-line closers and fragments | "That is the real win." / "No aesthetic prior. No nostalgia." | Cut the closer, merge the fragments into a claim |
| 3 | Sayings that sound deep | "At its core, what really matters is readiness" | "That depends on whether the organization changes its habits" |
| 4 | Staged run-up | "Let's dive in." / "In today's fast-paced world..." | Make the point |
| 5 | Arguing with no one | "A tempting approach would be... but" | State what actually happens |

### B. Rhythm by rule

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 6 | Forced triads | "innovation, inspiration, and industry insights" | Use the natural number of items |
| 7 | Repeated sentence openings *(weak alone)* | "She noted the door. She noted the lock." | "She noted the door and its lock" |
| 8 | Dashes as universal connector | "the policy — announced without warning — affects" | Commas, periods, colons, parentheses |
| 9 | Stacked qualifiers *(weak alone)* | "could potentially possibly be argued" | "may" |
| 10 | Hyphenated pairs everywhere *(weak alone)* | "the report is high-quality" | "the report is high quality" |
| 11 | Passive voice, missing subjects *(weak alone)* | "No configuration file needed" | "You do not need a configuration file" |
| 12 | Synonym cycling *(weak alone)* | "protagonist... main character... central figure... hero" | Repeat the clearest term |
| 13 | Uniform sentence length | Every sentence 15–25 words | Alternate short and long |
| 14 | Transition word overload | "Furthermore... Moreover... Nevertheless..." | Cut the density |

### C. Inflation and borrowed authority

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 15 | AI vocabulary | "testament... landscape... showcasing" | Plain words |
| 16 | Inflated significance | "marking a pivotal moment in the evolution of..." | "was established in 1989" |
| 17 | Vague connection | "associated with the leadership of ExampleCorp" | Name the relationship the source gives |
| 18 | Shallow -ing riders | "symbolizing... reflecting... showcasing..." | Keep the fact, drop the rider |
| 19 | Sales language | "nestled within the breathtaking region" | "is a town in the Gonder region" |
| 20 | Borrowed authority | "Experts believe" / a list of prestige outlets | Name the source or cut the claim |
| 21 | Copula avoidance | "serves as... features... boasts" | "is... has" |
| 22 | Abstract verb inflation | "leveraging our platform to unlock value" | Say what it does and by how much |
| 23 | False ranges | "from the Big Bang to dark matter" | List the topics |
| 24 | Filler phrases | "In order to", "Due to the fact that" | "To", "Because" |

### D. Formatting by rule

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 25 | Bold as decoration | "**OKRs**, **KPIs**, **BMC**" / "**Performance:** Performance improved" | Plain text, or prose |
| 26 | Decorative headings | "Strategic Negotiations And Partnerships" / "🚀 Launch Phase:" | Sentence case, no emoji |
| 27 | Curly quotes *(weak alone)* | `said “the project”` | `said "the project"` |

### E. Leftovers from the chat and the draft (act on sight)

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 28 | Chatbot residue and sycophancy | "Great question! I hope this helps!" | Remove the wrapper, keep the content |
| 29 | Cutoff disclaimers and filled-in guesses | "details are limited... it appears to have been" | State what the source does not show |
| 30 | Heading repeated in first sentence | "## Performance" then "Speed matters." | Delete the restatement |
| 31 | Writing about the previous version | "This replaces the previous approach of..." | Describe the current behavior |

## When not to act

A person can make any of these choices on purpose. Act on a *weak alone* tell only when several tells share a passage. Leave a watched phrase alone inside a quotation, a title, a proper name, or a passage that discusses the phrase rather than uses it. Salutations and sign-offs predate chatbots. Text written before 2022-11-30 is not AI-written.

No AI-detector score belongs in this process. Detectors measure origin, not craft, and the score does not tell you what to edit.

Keep the details that carry the writer's voice: a specific unusual detail, mixed feelings, era-bound references, a first-person choice the writer can explain, a genuine aside or self-correction.

## Voice profiles

If the repository has a `VOICE.md` (or `_VOICE.md` in a routed content directory), the skill resolves the nearest one by walking up from the edited file, cascades omitted sections upward, and treats it as the target voice: its lexicon extends the AI-vocabulary list, its tone axes and cadence replace generic inference, and its gold-standard examples become the rhythm target.

Precedence: a supplied writing sample, then `VOICE.md`, then the kind of text.

## References

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), primary source
- [WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)
- [blader/humanizer](https://github.com/blader/humanizer) v3.0.0 (MIT), source of the severity model, the structure-first ordering, the fact guardrail, the output modes, and patterns 2, 3, 4, 5, 7, 10, 11, 17, 30, 31

## Version history

- **3.0.0** - Severity model (act-on-sight vs *weak alone*), structure-first grouping into A–E, 8 new patterns (31 total), paragraph-scale detection, fact guardrail, output modes, prompt-injection line, "when not to act" exemptions
- **2.6.0** - `VOICE.md` resolution and cascade; AI-detector references removed
- **2.2.0** - Final "obviously AI generated" audit plus second-pass rewrite
- **2.1.0** - Before/after examples for all patterns
- **2.0.0** - Rewrite based on the Wikipedia article
- **1.0.0** - Initial release

## License

MIT
