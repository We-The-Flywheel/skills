# Google Knowledge Panel / entity SEO

**Owns the entity layer: who Google and the LLMs think you *are*, as distinct
from how you rank.** Runnable standalone as `/wtf:knowledgepanel`. Split out from
the publishing gate the same way `og-meta-tags.md` was, because entity setup is
a per-*brand* job done once and maintained, not a per-*page* check.

Distilled from Jason Barnard's (Kalicube) entity-SEO method. Ranking is about
pages. This is about the thing the pages are *about*.

---

## Why this matters commercially

A wrong or absent Knowledge Panel leaks prospects at the bottom of the funnel,
where they are most expensive to have acquired. Someone who has already decided
to hire you searches your name to confirm you are real, sees Google confidently
assert something else, and quietly leaves. Barnard's own case: Google had him
classified as a cartoon voiceover artist, and he attributes a lost six-figure
deal to it.

The failure is silent. There is no bounce to attribute it to, no form
abandonment, no analytics event. This is why the check has to be run
deliberately rather than waited for.

---

## Step 1 — the Entity Home (the check that fails most often)

> **The Entity Home is the About page, not the homepage.**

Google and grounding LLMs need one URL to treat as the authoritative
reconciliation point for an entity: the place they go to settle what this thing
*is* when signals conflict. That page has to be dry, stable and factual.

The homepage is the wrong page for this. It is a marketing signpost: it changes
with campaigns, it sells rather than states, and its job is to route visitors
onward. An About page is the destination for bots because it holds the boring
durable facts.

**Hard rules:**

| Rule | Why |
|---|---|
| A real, routable About page must exist at its own URL | The reconciliation point must be linkable and citable on its own |
| A `#about` **anchor section on the homepage does not count** | It has no independent URL, so nothing external can point at it, so the loop in Step 2 cannot close |
| Exactly **one** Entity Home per entity, and every signal points at that one URL | Two candidate homes is the same failure as none |
| The Entity Home must be reachable from site navigation or prominent body links | An orphan page is not authoritative |
| It must answer, in plain prose: who you are, what you do, who you serve, why you are credible | These are the four facts every downstream system extracts |

**This is the single most common gap.** A site can have flawless homepage
JSON-LD and still fail here.

### Facet pages: keep the Entity Home lean

The machine has two jobs for a person: **separate** them from every namesake
and **unite** their many faces (the same person can be a founder, a podcaster,
and a marathon runner). The Entity Home handles the first. Facet pages handle
the second: each facet is a mini entity page the machine can go to when it
wants that aspect. Put everything on the Entity Home and it overwhelms the
machine, so keep only the fundamentals there and link to each facet and back.

**What stays on the Entity Home (the budget):** name and aliases, subtitle,
the 150-word summary, the disambiguation sentence, birth date/place, current
role(s) with the organization named, a short career line (most senior roles
only), education, 3+ real captioned photos, one line per facet linking to its
page, every `sameAs` profile as a visible link, and a contact route. Race
lists, press lists, publication lists, and full career histories do not
belong on it.

**What each facet page carries:** the complete, dated, sourced list for that
facet (every race with time and date, every publication with outlet and URL,
every role change or award with date and announcement link), an opening
sentence that names the entity and the facet ("Jane Doe's marathon race
results"), a link back to the Entity Home in the first paragraph, a real image
specific to the facet, and schema whose `about` / `mainEntity` references the
entity `@id`, never a second Person node.

**Typical person facets:** competition results, publications, press coverage,
career announcements, speaking, podcast appearances, patents, photos (a
captioned photos page of the person; Edward Sturm reports it supplied about a
quarter of his Google Images results for his name, ahead of namesakes). Create a facet
only when there is real, dated material to list. A facet page with one item is
weaker than a line on the Entity Home.

**Placement:** nest facets under the Entity Home (`/about/<name>/results/`,
`/about/<name>/publications/`) or in a real category, never at root. Surface
them in the top menu where the chrome allows. Footer links count for less.

**Facet data is single-sourced.** A facet's list lives in one data file that
every page repeating it imports. The same date typed into two templates is
how an entity ends up with three founding dates.

---

## Step 2 — the corroboration loop

Google is described in the source material as behaving like an ambitious but
untrained child: eager to conclude, poor at knowing when it is wrong. You do
not persuade it, you train it, by making the same statement in enough places
that the conclusion is unavoidable.

The mechanism is a closed loop:

```
Entity Home  ──sameAs──▶  External profile
     ▲                          │
     └──── links back to ───────┘
        the SAME Entity Home URL
```

Both directions are required. A `sameAs` pointing outward with no link back is
an assertion. A link back completes the corroboration and makes it a fact.

**The most common way this breaks silently:** the external profile links to the
**homepage** instead of the Entity Home. The loop looks closed on casual
inspection and is not.

**Corroboration platforms**, in rough order of weight. All URLs verified live.

| Platform | URL | Why it carries weight |
|---|---|---|
| Wikidata | https://www.wikidata.org/ | Structured, open, directly ingested into knowledge graphs. **Only once notable**, see below |
| Crunchbase | https://www.crunchbase.com/ | Trusted company and founder data |
| LinkedIn | https://www.linkedin.com/ | Highest-confidence person↔organization employment link |
| The Org | https://theorg.com/ | Trusted organizational charts and role data |
| Muck Rack | https://muckrack.com/ | Trusted journalist and author profiles |
| Trustpilot | https://www.trustpilot.com/ | Trusted review-entity profile. A national review platform works too; have at least one, including persons who sell a service |
| X | https://x.com/ | Fast-indexed, widely cross-referenced |

Barnard on this set: with the Entity Home, these profiles and one review
platform, "you would expect to get a knowledge panel in a few months, three
months to a year", no guarantee.

**Industry and government databases** count too, where the entity qualifies:
IMDb, ORCID, a national library record (Barnard's is at the French BNF),
company registers. "Government ones are the really strong ones."

**Wikidata timing.** "One big mistake people make is to create a Wikidata page
too early", before there is proof the entity is notable. A deleted item is a
worse signal than none. Create it once the identifiers exist (Crunchbase,
IMDb/ORCID, a registry or library record, press), and fill its identifiers
section carefully: that section is what makes the item worth having. Until
then, a missing Wikidata id is an expected state, not an audit failure.
**Wikipedia** is more dangerous: no self-editing, only through an editor with
community standing, disclosed.

**Keep every source current.** When the story changes (new title, new company,
new summary), update the profile, the page and the Crunchbase record in the
same pass. Barnard calls this the most important maintenance step.

**Personal brands use personal profiles.** For a person entity, the
corroboration set is the person's own accounts: LinkedIn, X, Instagram,
Facebook, YouTube, GitHub, Medium, plus the sites they founded. The Org and
Crunchbase are secondary for a person. Each account's website/link field must
be the Entity Home URL (`/about/<name>/`), not the homepage. That field is the
cheapest loop to close and the one most often left pointing at `/`.

**Temporal proof.** Third-party citations spread across many years show a claim
is long-standing, which a burst of recent mentions cannot. When the Entity Home
frames experience ("since 2004"), link proof from across that span, not only
the latest coverage.

**Checking the loop:** fetch each `sameAs` target and confirm it links back to
the Entity Home URL. Two hosts must be special-cased — **LinkedIn returns `999`
and Crunchbase returns `403` to automated requests**. Those are bot-blocks, not
missing profiles. Report them as `MANUAL` and check them in a browser. Scoring
them FAIL produces a permanent false negative.

---

## Step 3 — schema

One JSON-LD node per entity. **Merge into the existing node, never append a
second `<script>` for the same thing** — two unlinked nodes for one entity is
the exact split this whole exercise prevents.

| Property | Requirement |
|---|---|
| `@id` | **The load-bearing one.** A stable, permanent URI (e.g. `https://example.com/#jane-doe`). Never change it. Every site that references this entity uses this same string — that is what makes one identity out of several sites |
| `url` | Absolute URL of the Entity Home |
| `name`, `givenName`, `familyName` | Exact, consistently capitalized |
| `description` | The 150-word executive summary from Step 4 |
| `disambiguatingDescription` | **Required if any namesake exists.** One explicit sentence separating you from them |
| `sameAs` | Every corroborating profile from Step 2 |
| `image` | **≥3 distinct real images.** One is not enough to build visual confidence |
| `jobTitle`, `worksFor` | Person→Organization link. `worksFor` should target the org's `@id` where one exists |
| `alumniOf`, `hasCredential`, `award`, `memberOf` | Credibility signals — the "why trust you" facts, in structured form |
| `logo`, `address`, `telephone` | Organization only. `logo` should be **raster (PNG), not SVG** — Google's logo validation has historically rejected SVG. Put an SVG in `image` instead |

Wire the page itself:

```
AboutPage  ──mainEntity──▶  { "@id": "<the entity @id>" }
WebPage    ──about──────▶   { "@id": "<the entity @id>" }
```

---

## Step 4 — copywriting for machines

Two things distinguish entity copy from marketing copy.

### Do the reasoning for the machine

Indexing systems and grounding LLMs digest facts at ingestion time. They are
not reasoning over your prose to derive implications. So state the implication
explicitly, using an actual logical connective:

> Jason Barnard has been doing SEO since 1998, **therefore** he is an SEO expert.

The inference you leave implicit is the inference that does not get indexed.
Write `therefore`, `because`, `which means`, `as a result`. Do not imply.

### Name entities the machine already knows

Inside the summary, deliberately reference concepts already in the knowledge
graph — named cities, established industries, defined markets, known
organizations. Each one is an anchor point that maps your new entity onto
existing structure. An entity described only in novel terms has nothing to
attach to.

### Claim, Frame, Proof

Kalicube's stated method for every piece of copy: make the **claim** (who you
are, what you are best at), **frame** it in the words you want the machine to
repeat, then link the **proof** (third-party page, award, press, registry
record). A claim with no linked proof is self-declaration, which has a
stability ceiling that third-party proof does not.

Barnard's extension of E-E-A-T is **N-E-E-A-T-T**: Experience, Expertise,
Authoritativeness, Trustworthiness plus **Notability** and **Transparency**.
Notability is third-party proof and the source set in Step 2. Transparency is
contact, registration and legal facts on the Entity Home.

### The 150-word executive summary

150 words because that is what fits Crunchbase's primary description field.
That constraint makes it the reusable anchor of a modular system:

| Destination | Use |
|---|---|
| Crunchbase | The 150-word summary as the primary description; append the modular paragraphs lower down if the profile allows |
| LinkedIn | The same 150 words verbatim, plus the modular paragraphs appended |
| X / short bios | The one exception — condense further |
| Entity Home + schema `description` | The 150 words, unchanged |

Identical wording across platforms is the point. Variation is noise the machine
has to reconcile.

**Open with a semantic triple** (subject-verb-object, no hedging) and answer
four questions in order:

1. **Who you are** — the exact entity name, spelled and capitalized as everywhere else.
2. **What you do** — state the industry outright. If the brand name is
   non-descriptive ("Kalicube"), the machine cannot infer the sector, so say
   "digital brand engineering company" explicitly.
3. **Who and where you serve** — target audience and location.
4. **Why you are credible** — founding year, years of experience, a named
   credential. A checkable fact, not an adjective.

### Capitalization traps

NLP is highly sensitive to capitalization, because capitalization is the signal
that separates a named proper noun (an entity) from a generic action.

| Trap | Effect | Fix |
|---|---|---|
| Opening a sentence with a generic-word brand name ("Car Sales is…") | The sentence-initial capital is always required by grammar, so the parser reads it as grammatical, not as a proper noun, and may assume the word should have been lowercase | **Prepend a preposition**: "At Car Sales, …". Pushing the name off position one forces the capital to be read as deliberate |
| Writing the brand lowercase ("car sales") | Loses entity status entirely — parsed as the generic event "cars are being sold" | Always capitalize the brand exactly as registered |
| Brand names that are also verbs ("Engineers", "Sales") | Part-of-speech ambiguity; the parser picks the verb | Avoid where you can, and always surround with structure that forces the noun reading |
| Inconsistent casing across platforms | Each variant is a candidate distinct entity | One canonical casing everywhere, including `name` and `alternateName` |

---

## Step 5 — measuring it

| What you want to know | How | Cost |
|---|---|---|
| Does Google's graph hold my entity, under what KGMID, at what confidence, and pointing at which URL? | Google Knowledge Graph Search API — `kgmid_lookup.py` | Free |
| What does the panel actually *render* in the SERP? | DataForSEO SERP `knowledge_graph` item — `kgmid_lookup.py --source serp` | Paid per call |
| Manual KGMID lookup and confidence score | Kalicube Knowledge Graph Explorer, below | Free |
| What do AI engines say about the entity? | Ask ChatGPT, Google AI Mode, Gemini, Perplexity, Copilot "who is <entity>", then the follow-ups below | Manual |

**Follow the due-diligence chain.** A prospect rarely stops at "who is X". AI
interfaces suggest follow-ups ("is X legit", "X vs <competitor>", "X reviews")
and buyers take them; Barnard calls this the rabbit hole of due diligence. Run
the entity question, then the three or four follow-ups the engine itself
suggests, and record any answer that is wrong, vague or pulls in a namesake.
Each one points at a missing fact on the Entity Home or a missing proof link.

Barnard's model for why one setup serves every surface: the **algorithmic
trinity**, search engines, knowledge graphs and LLM chatbots, all read the same
underlying data. Control the Entity Home and the source set and you control
what all three repeat. His funnel stages: understandability (the Knowledge
Graph gets the facts right) gives control, credibility gives influence,
deliverability gives visibility. Fix understandability first.

The two APIs answer different questions and disagreement between them is
itself the finding. The graph can hold an entity that Google declines to render
a panel for; the rendered panel can show facts sourced from outside the graph.

**The single most diagnostic field** in the KG API response is `url` — the URL
Google associates with the entity. If that is not your Entity Home, the loop in
Step 2 is broken, and no amount of additional schema fixes it.

`resultScore` is a relevance score for the query, not a stable "confidence"
percentage. Track it over time on a fixed query rather than reading one value
as an absolute grade.

### Tools

| Tool | URL | Answers |
|---|---|---|
| Kalicube Knowledge Graph Explorer | https://kalicube.pro/tools/knowledge-graph-explorer | Search Google's graph directly; find your KGMID and confidence |
| Kalicube free tools hub | https://kalicube.pro/tools/free-resources | Schema builders, entity-recognition sandbox, optimization assets |
| Kalicube | https://kalicube.com/ | The method and its author |
| Google Rich Results Test | https://search.google.com/test/rich-results | Validates the JSON-LD actually parses |
| Schema Markup Validator | https://validator.schema.org/ | Validates properties Google's tester ignores |
| Wikidata | https://www.wikidata.org/ | Where a structured entity record can be created directly |

Background on the source material: Edward Sturm's show, episode 1,149 —
https://edwardsturm.com/the-edward-show/ — and his SEO course at
https://edwardsturm.com/compact-keywords/ (note: `compactkeywords.com` 301s
here; cite the destination).

---

## Sequencing

Order matters. Doing these out of order wastes the corroboration.

1. **Build or fix the Entity Home** — nothing else works until one URL is the
   answer.
2. **Write the 150-word summary** to Step 4's rules.
3. **Ship the schema** with a permanent `@id`, pointing `url` at the Entity Home.
4. **Populate external profiles** with the identical summary, each linking back
   to the Entity Home URL.
5. **Add `sameAs`** for each profile, closing the loop.
6. **Wait.** Weeks to months. This is corroboration accumulating, not a
   deploy taking effect. A brand-new, unique brand name takes roughly 6 months
   before AI engines hold it at all. Barnard treats the panel as the leading
   indicator: AI engines start recommending the entity roughly 3 months after
   it appears.
7. **Measure** with Step 5, re-measure periodically, and never change the `@id`.

---

## Common mistakes

| Mistake | Consequence |
|---|---|
| Homepage `#about` anchor treated as the Entity Home | No independent URL, loop cannot close |
| External profiles link to the homepage, not the Entity Home | Loop looks closed, is not |
| `@id` changed during a redesign or migration | The accumulated entity is orphaned; corroboration restarts from zero |
| A second `<script>` with a duplicate entity added instead of merging | Two entities where there was one |
| No `disambiguatingDescription` despite a known namesake | Google merges you with them, or picks them |
| One image | Insufficient for visual confidence |
| Inconsistent bio wording per platform | Each variant is noise to reconcile |
| Different `@id` per site for the same person | The split this method exists to prevent |
| Expecting results in days | It is corroboration over time, not a ranking change |
| Scoring a LinkedIn `999` or Crunchbase `403` as a broken link | Permanent false negative |
| Creating a Wikidata item before notability can be proven | Deletion, a worse signal than no item |
| Self-declared "best X" lists and "we beat competitor Y" pages | Barnard's opinion, not proven: no longer carry weight and may hurt the brand in LLMs. Earned best-of mentions on third-party sites are the goal |

---

## Per-site checklist

```
ENTITY AUDIT — <entity name> @ <site>
 1  Entity Home exists at its own URL         PASS/FAIL  <url>
 2  Entity Home is substantive (4 questions)  PASS/FAIL
 3  Entity Home reachable from nav/body       PASS/FAIL
 4  Single entity node, no duplicates         PASS/FAIL  <count>
 5  Stable @id present                        PASS/FAIL  <@id>
 6  url → Entity Home                         PASS/FAIL
 7  sameAs complete                           PASS/FAIL  <n profiles>
 8  Corroboration loop closed                 PASS/FAIL/MANUAL  <n/n>
 9  disambiguatingDescription                 PASS/FAIL/N-A
10  image ≥ 3                                 PASS/FAIL  <count>
11  AboutPage.mainEntity → @id                PASS/FAIL
12  Description follows Step 4 rules          PASS/FAIL
13  KGMID present                             FOUND/NOT-FOUND  <kgmid, score>
14  Google's url == Entity Home               PASS/FAIL  <what Google holds>
15  Entity Home within budget, facets single-sourced  PASS/FAIL/N-A
16  Source set: Crunchbase, The Org, review platform, industry/gov databases, Wikidata-when-notable  PASS/FAIL/MANUAL

VERDICT: <n> failing
```

**Scope.** Applies to any brand, person, or organization that should be a
recognized entity: personal brands, company sites, portfolio brands. Does not
apply to individual article or product pages — those are ranking surface, not
entity surface.

**Gate enforcement.** Rows 1, 5 and 6 are structural: everything downstream
depends on them, so a FAIL on any of the three makes the rest of the audit
moot. Report it as:

> "Entity setup incomplete. `<entity>` fails: [rows]. Entity Home and a stable
> `@id` have to be right before corroboration is worth building — fix these
> first, or the external profile work is wasted."

Never soften a structural FAIL into a suggestion.
