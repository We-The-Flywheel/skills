# Full worked example

Moved verbatim from SKILL.md.

**Before (AI-sounding):**
> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools—nestled at the intersection of research and practice—are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.
>
> At its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts, from solo developers to cross-functional teams. The technology has been featured in The New York Times, Wired, and The Verge. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> - 💡 **Speed:** Code generation is significantly faster, reducing friction and empowering developers.
> - 🚀 **Quality:** Output quality has been enhanced through improved training, contributing to higher standards.
> - ✅ **Adoption:** Usage continues to grow, reflecting broader industry trends.
>
> While specific details are limited based on available information, it could potentially be argued that these tools might have some positive effect. Despite challenges typical of emerging technologies—including hallucinations, bias, and accountability—the ecosystem continues to thrive. In order to fully realize this potential, teams must align with best practices.
>
> In conclusion, the future looks bright. Exciting times lie ahead as we continue this journey toward excellence. Let me know if you’d like me to expand on any section!

**Draft rewrite:**
> AI coding assistants speed up some tasks. In a 2024 study by Google, developers using Codex completed simple functions 55% faster than a control group, but showed no improvement on debugging or architectural decisions.
>
> The tools are good at boilerplate: config files, test scaffolding, repetitive refactors. They are bad at knowing when they are wrong. I have mass-accepted suggestions that compiled, passed lint, and still did the wrong thing because I stopped paying attention.
>
> The productivity claims are hard to verify. GitHub says Copilot users "accept 30% of suggestions," but acceptance is not correctness, and correctness is not value.
>
> None of this means the tools are useless. It means they are tools. They do not replace judgment, and they do not eliminate the need for tests.

**What still sounds AI generated?**
- The rhythm is still too tidy: clean contrasts, evenly paced paragraphs, every sentence in the 15–25 word band (§13).
- "None of this means X. It means Y" is a §1 contrast split across sentences.
- The closer leans slogan-y rather than sounding like a person talking (§2).
- Fact guardrail: the Google study and the GitHub figure must be in the source. If they are not, cut them rather than keep a plausible-sounding number.

**Final version:**
> AI coding assistants can make you faster at the boring parts. Not everything. Definitely not architecture.
>
> They're great at boilerplate: config files, test scaffolding, repetitive refactors. They're also great at sounding right while being wrong. I've accepted suggestions that compiled, passed lint, and still missed the point because I stopped paying attention.
>
> People I talk to tend to land in two camps. Some use it like autocomplete for chores and review every line. Others disable it after it keeps suggesting patterns they don't want. Both feel reasonable.
>
> The productivity metrics are slippery. GitHub can say Copilot users "accept 30% of suggestions," but acceptance isn't correctness, and correctness isn't value. If you don't have tests, you're basically guessing.

**Changes made:**
- §28 chatbot residue ("Great question!", "I hope this helps!", "Let me know if...")
- §16 inflated significance ("testament", "pivotal moment", "evolving landscape", "vital role") and the §16 send-off ("the future looks bright")
- §19 sales language ("groundbreaking", "nestled", "seamless, intuitive, and powerful")
- §20 borrowed authority ("Industry observers", the outlet list)
- §18 -ing riders ("underscoring", "highlighting", "reflecting", "contributing to")
- §1 not-X-but-Y ("It's not just X; it's Y")
- §6 triads and §12 synonym cycling ("catalyst/partner/foundation")
- §23 false ranges ("from X to Y, from A to B")
- §8 dashes, §26 emojis and decorative headings, §25 bold labels, §27 curly quotes
- §21 copula avoidance ("serves as", "functions as", "stands as")
- §29 knowledge-cutoff hedging, §9 stacked qualifiers
- §24 filler ("In order to"), §3 pseudo-profound ("At its core")
- §13 burstiness: rewrote for varied sentence length
