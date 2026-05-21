# Feature Research

**Domain:** Agentic-CLI AI language tutor (SRS vocab + free writing), Slavic-L2 dogfood, OSS Claude plugin
**Researched:** 2026-05-19
**Confidence:** HIGH for SRS/writing patterns (well-studied); MEDIUM for agentic-CLI differentiators (novel surface); MEDIUM for Slavic evaluator concerns (verified via UA-GEC + grammar refs)

## Scope Framing

v1 surface = six skills: `tutor-setup`, `tutor-vocab`, `tutor-writing`, `tutor-feedback`, `tutor-progress`, `tutor-session-analyzer`. Anything outside that surface is deferred or anti-feature. The wedge is **own-your-data, terminal-native, LLM-as-judge with structured contracts** — not "another Anki" and not "another Duolingo." Feature decisions optimize for **daily dogfood by the author on Russian/Ukrainian**, not breadth of audience.

## Feature Landscape

### Smarter Vocabulary Engine

`tutor vocab start --json` now returns a deterministic due-first queue with
`effective_count`, `active_weak_tags`, `selection_reasons`, and
`selection_policy`. Weak tags are derived from the last 10 completed analyzed
sessions and limited to the top 5 signals; explicit tag filters remain hard
boundaries before weak targeting is applied.

Review intensity changes queue pressure only: `light` is 50%, `normal` is 100%,
and `heavy` is 150% of session length, with a final 60-card cap. SM-2 scheduling
does not read review intensity.

### Table Stakes (Users Expect These)

Missing any of these makes the product feel broken to a learner who has used Anki, Duolingo, italki, or ChatGPT-as-tutor.

#### Vocab / SRS

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| SM-2 review scheduling with ease factor + interval | Anki-equivalent baseline; no SRS app ships without it | MEDIUM | Pure math + DB write. 4 inputs (q, reps, EF, interval). Golden-test the math. |
| Quality rating per review (Again/Hard/Good/Easy or 0–5) | SM-2 needs `q`; user expects to grade recall difficulty | LOW | Map LLM evaluator verdict → q score deterministically (don't ask user twice). |
| Due-review queue surfacing on session start | Users expect "what's due today" as the first thing they see | LOW | `BootContext.due_srs_summary` already in design. Cap by `session_length` pref. |
| Add new card (manual + LLM-generated) | Even "LLM-generated content" projects need a way to capture an in-the-wild word | LOW | `tutor-vocab` add-flow; persist via DAL. Dedupe on lemma+L2. |
| Show correct answer after miss | Universal expectation; users learn from the correction not the failure | LOW | Already implied by `FeedbackEnvelope.corrected_answer`. |
| Lapse handling (reset interval on Again) | SM-2 standard: q<3 resets to 1 day | LOW | Part of SM-2 impl. |
| Per-card history visible on demand | Users want to see "why is this card hard" | LOW | Query `srs_reviews` by item_id. v1 = read-only text view. |
| Cards survive across sessions deterministically | If reviews disappear users abandon | LOW | SQLite transactional write on `StatePersisted`. |

#### Writing Practice

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Prompt at learner's CEFR level | LangCorrect/italki/ChatGPT all calibrate prompts to level | MEDIUM | LLM generation; pass CEFR target + interests from profile. |
| Error span identification (not just "rewrite this") | Research finding: localized correction outperforms holistic rewrite for L2 acquisition | MEDIUM | `FeedbackEnvelope.error_spans[]` already designed. Span = offset+length+tag. |
| Severity classification per error | Learners need to know "is this a typo or a fluency-blocker?" | LOW | 4-level: ✅🟡🟠🔴 already designed. |
| Corrected version alongside original | Standard L2 written-corrective-feedback (WCF) pattern | LOW | `corrected_answer` field. Render as diff or side-by-side. |
| Explanation of why it's wrong (not just what) | Research: explicit feedback > implicit recasts for adult L2 learners | MEDIUM | LLM produces `explanation`; render in L1 by default. |
| Submit a free-form passage (not fill-in-blank only) | "Free writing" is the whole point; controlled exercises are a different modality | LOW | Multi-line input via Claude Code skill prompt. |
| Tagged error categories (controlled vocabulary) | EGP/CEFR taxonomy work shows learners need consistent error labels to spot patterns | MEDIUM | `tags[]` field; enforce closed set (see Slavic section). |

#### Onboarding / Profile

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| L1 (native language) capture | Required to render explanations; non-negotiable | LOW | `profile.yaml` field; ISO 639-1 code. |
| L2 (target language) capture | Required for everything | LOW | Same as above. |
| CEFR target (A1–C2) | Required to calibrate prompt difficulty and evaluator strictness | LOW | Enum in profile. Default A2 if unknown. |
| Daily session length preference | SRS apps universally let users cap queue size | LOW | `preferences.yaml` minutes or item-count. |
| Interests / topics | Drives prompt content; users disengage from generic prompts | LOW | Free-form list in profile; LLM-consumed. |
| Re-runnable setup | Profile evolves; must be editable without DB surgery | LOW | YAML is human-editable by design; `/tutor-setup` re-runs. |

#### Feedback Rendering

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Markdown output (not plain text) | Claude Code terminal renders markdown; users expect bold/headers | LOW | Renderer layer; golden tests already in design. |
| Severity emoji or color mark | Visual scanning of long feedback; standard across tutoring apps | LOW | ✅🟡🟠🔴 mapping. |
| Deterministic feedback for same answer | If "the AI" gives different verdicts each run, trust collapses | HIGH | Hard problem with LLM judges. Mitigate: low temperature, structured output schema, golden tests on canonical answers. |
| Explanation in learner's L1 | Beginners can't read L2 grammar explanations | LOW | LLM prompt: "explain in {L1}". Already designed. |

#### Progress / Motivation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Current streak (days with ≥1 session) | Universal across SRS/learning apps; cheap psychological hook | LOW | Compute from `session_summaries.created_at`. |
| Due count (today / next 7 days) | Users plan around it | LOW | SQL aggregate over `srs_items`. |
| Recent weak patterns (top error tags) | The "what should I work on next" answer | MEDIUM | Aggregate `mistake_events.tag` over last N sessions. |
| Per-tag mastery rows | Learners need a ranked list of weak/strong tags, not only raw weak tags | MEDIUM | Derived from aggregate-safe review, mistake, and session-summary evidence. |
| Last-N recap with ASCII trends | Shows recent direction without adding charts or a dashboard | MEDIUM | `tutor progress --json` supports 1-30 completed-session windows and ASCII sparklines. |
| Markdown / JSON export | Progress should be shareable and contract-validatable | LOW | JSON is canonical; markdown renders from validated `ProgressReport`. |
| Item count by maturity (new / learning / mature) | Standard Anki/SRS overview | LOW | SQL aggregate by interval bucket. |
| Last-session summary recap | Boot context already produces it; show it for free | LOW | Read `session_summaries.summary_for_next_boot`. |

#### Session Analysis (BootContext input)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Severity counts (✅🟡🟠🔴 totals) | Single-number health snapshot | LOW | Count from session's `FeedbackEnvelope`s. |
| New vs repeated vs resolved error tags | Drives next-session focus | MEDIUM | Set diff against previous N sessions' tags. |
| Recommended next focus | The whole point of analysis | MEDIUM | LLM rationale + structured field. |
| SRS adjustments | If analyzer says "demote this card" core must execute | MEDIUM | `srs_adjustments[]` already designed; apply in `StatePersisted`. |
| Concise next-boot summary (token-budgeted) | Boot context has a budget; analyzer must respect it | MEDIUM | Enforce char/token cap in schema validation. |

### Differentiators (Competitive Advantage)

Where the agentic-CLI niche wins. Don't try to differentiate on SRS math — differentiate on **integration surface and data ownership**.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| YAML profile + SQLite state as plain files in `$HOME` | Own-your-data, grep-able, git-versionable, no vendor lock-in. Nothing competing in this niche offers it. | LOW | Already designed. Wedge feature. |
| Skill triggered by natural-language intent in Claude Code | "I want to practice Russian writing" → skill activates. No app to open, no context switch. | LOW | Frontmatter `description` drives discovery; already designed. |
| Structured `FeedbackEnvelope` + `SessionAnalysis` contracts | Reproducible feedback; testable with golden files; other tools (your shell, other LLM CLIs) can consume the same JSON | MEDIUM | Schemas in design. Differentiator vs ChatGPT-as-tutor (which produces unstructured prose). |
| Language-agnostic engine (LLM-generated content for any L2) | No bundled curriculum to maintain; switch L2 by editing one YAML field | LOW | Wedge vs Duolingo/Babbel/Mango which require per-language content investment. |
| Host-portable architecture (adapter layer, even if only Claude ships in v1) | Future-proofs against host churn; same pedagogy on Codex/OpenClaw when ready | LOW (v1) | Pay the design cost now; defer alternate adapters. |
| Composable with shell/CLI (cron-trigger reviews, pipe input from `pbpaste`, etc.) | Power-user wedge: scheduling and integration that web/mobile can't match | LOW | Free if skills accept piped stdin and YAML lives in $HOME. Don't formally promise; let it emerge. |
| Reproducible session via golden fixtures | "Why did the tutor say that?" → check the fixture. Trust for OSS contributors. | MEDIUM | Already in testing strategy. |
| No telemetry, no auth, no cloud | Privacy-conscious learners (lawyers, journalists, security folks) | LOW | "Local-only" is a one-liner promise; trivial to keep if you don't add anything. |

### Anti-Features (Commonly Requested, Often Problematic)

Document these explicitly so they don't sneak in during scope drift.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| XP / levels / leagues / leaderboards | "Duolingo does it" | Research (arXiv 2203.16175) shows leagues create anxiety and shift focus from learning to ranking. Single-user OSS tool has nobody to compete with. | Streak + due count as quiet feedback. No social comparison. |
| Push / desktop notifications | "Reminders drive habits" | Out of scope for CLI; OS-level cron + shell wrapper is the unix-native answer | Document a recipe: `crontab` + `tutor-vocab` skill trigger. Not a built-in. |
| Cloud sync across devices | "I want to study on my phone" | Forces auth, ops, backend, privacy story. Kills the local-first wedge. | YAML + SQLite in `~/Sync/` or dropbox. User chooses sync layer. |
| Multi-user accounts | "What if my partner wants to learn too" | Auth + permissions blow scope. Single-user is the wedge. | Second user runs second Claude Code profile with separate `$HOME` config. |
| Audio / TTS / speech recognition | "Listening + speaking matter" | Host I/O limits in Claude Code; SR/TTS quality varies wildly; v1 is text. | Defer to post-v1 (already in Out of Scope). |
| Built-in curated curriculum / language packs | "Anki has shared decks" | Curation burden; locks engine to specific languages; competes with the LLM-generated-content wedge | LLM generates exercises on demand. Optional: user-supplied seed-word list at setup. |
| Multi-L1 curated UI translations | "Localize the tool itself" | i18n strings + maintenance burden; doesn't move learning outcomes | LLM renders explanations in any L1; tool UI stays English. |
| FSRS / fancy SRS algorithms in v1 | "FSRS beats SM-2 in benchmarks" | YAGNI; SM-2 is sufficient and golden-testable; FSRS adds 19+ parameters and tuning complexity | SM-2 for v1. Re-evaluate after dogfood data. |
| Rich analytics dashboard / charts | "I want pretty graphs" | Terminal renders ASCII at best; over-engineering for single-user OSS | Plain markdown summary from `tutor-progress`. |
| Adaptive lesson sequencing across modalities | "Smart tutoring routes me through skills" | Whole research field; v1 = single-skill sessions | Defer to post-v1 (already in Out of Scope). |
| Real-time WebSocket / streaming feedback during typing | "Like Grammarly" | Hosts don't support it well; doubles complexity; no L2 acquisition evidence it helps | Submit-then-grade flow. |
| Telemetry / "anonymous usage stats" | "We need it to improve" | Contradicts privacy wedge; OSS users distrust it | Logs stay local; user can `cat` them if curious. |
| Voice of the AI / personality / mascot | "Duolingo has Duo" | Tone drift, prompt-injection risk, distracts from pedagogy | Plain, neutral feedback voice. |
| Inline AI chat ("ask the tutor a question") | "ChatGPT-as-tutor lets me ask anything" | The host already does this. Skills shouldn't reimplement freeform chat. | If learner wants to chat about grammar, they already have Claude Code. |

## Slavic-L2 Evaluator Concerns

Russian/Ukrainian dogfood will stress the evaluator more than English/Spanish would. The evaluator prompt and error-tag controlled vocabulary must explicitly cover:

| Concern | Why It Matters | Evaluator Requirement |
|---------|---------------|----------------------|
| **Case marking** (6 in Russian, 7 in Ukrainian) | Most frequent error type for English-L1 learners; word order doesn't disambiguate role | Tag set must include `case:nom`/`case:gen`/`case:dat`/`case:acc`/`case:ins`/`case:loc`/`case:voc` distinctions. Evaluator must identify which case was wrong AND which was required. |
| **Gender agreement** (3 genders) | Adjectives, past-tense verbs, possessives all agree | Tag `agreement:gender`; evaluator notes the noun whose gender governs the error. |
| **Verb aspect** (imperfective / perfective pairs) | The single hardest topic; not a "grammar rule" but a semantic choice | Tag `aspect:perfective-needed` / `aspect:imperfective-needed`. Evaluator must explain *why* (single completed action vs ongoing/habitual). |
| **Animacy** (affects accusative case for masc nouns) | Subtle but pervasive | Tag `case:acc-animacy`. |
| **Verbs of motion** (with/without prefix, unidirectional/multidirectional) | Famous learner trap | Tag `motion:directionality` / `motion:prefix`. |
| **Stress placement** (mobile in Russian/Ukrainian) | Affects pronunciation but also written forms occasionally (Ukrainian і vs ї, Russian ё marking) | Out of scope for v1 written eval; flag for post-v1. |
| **Word order / topicalization** | Free-but-not-really; carries information structure | Tag `wordorder:information-structure` — low severity by default; learners shouldn't be over-corrected on this. |
| **Punctuation** (Slavic comma rules differ from English) | Frequent minor errors; would dominate `🔴` counts if treated as blocking | Tag `punctuation:slavic-comma`; default severity 🟡. |
| **Cyrillic vs transliteration** | Learners may type Latin-transliterated forms | Profile preference `transliteration_allowed: bool`; evaluator respects it. |
| **Russian–Ukrainian interference** (learner of one may leak from the other) | Author is dogfooding both — common interference patterns | Tag `interference:ru-uk` / `interference:uk-ru`. |

**Evaluator prompt rule:** Must accept a `target_language` parameter and load a per-language tag set + correction style guide. Don't hardcode English-grammar assumptions in the prompt.

**Validation:** Build a golden test set of ~20 known-wrong Slavic sentences with expected tags. Re-run on every prompt change. (Reference: [UA-GEC corpus](https://arxiv.org/pdf/2103.16997) has real learner errors for Ukrainian — use as test-set inspiration.)

## L1-in-Feedback Pattern

| Profile Setting | Behavior |
|----------------|----------|
| `feedback_l1: en` (default) | Explanation in English; L2 forms rendered in L2 |
| `feedback_l1: ru` (learner of Ukrainian whose L1 is Russian) | Explanation in Russian |
| `feedback_l1: <any LLM-supported code>` | LLM renders in that L1 |

**Rules:**
- L2 forms always appear in L2 (don't translate the corrected answer).
- Error tags stay in English (controlled vocabulary = stable schema).
- Severity emojis are universal.
- LLM gets explicit instruction: "Render `explanation` and `next_drill_hint` in {L1}. Leave `corrected_answer`, `error_spans[].text`, and `tags[]` untouched."

Translanguaging research ([drpress.org/EHSS/17531](https://drpress.org/ojs/index.php/EHSS/article/view/17531)) supports L1-mediated feedback as cognitive scaffolding — reduces cognitive load and improves uptake for adult learners.

## Feature Dependencies

```
[Profile YAML]
    └──required by──> [BootContext]
                          └──required by──> [tutor-vocab session]
                          └──required by──> [tutor-writing session]

[SQLite migrations]
    └──required by──> [srs_items / srs_reviews]
                          └──required by──> [SM-2 algorithm]
                                                └──required by──> [tutor-vocab]

[FeedbackEnvelope schema]
    └──required by──> [tutor-feedback renderer]
    └──required by──> [mistake_events persistence]
                          └──required by──> [weak patterns aggregation]
                                                └──required by──> [tutor-progress]
                                                └──required by──> [BootContext.top_weak_patterns]

[SessionAnalysis schema]
    └──required by──> [tutor-session-analyzer]
                          └──required by──> [session_summaries.summary_for_next_boot]
                                                └──required by──> [BootContext.last_session_summary]

[Error tag controlled vocabulary]
    └──required by──> [tutor-writing evaluator prompt]
    └──required by──> [Slavic-specific tag set]
    └──required by──> [weak pattern aggregation correctness]

[L1 profile field]
    └──required by──> [feedback explanation rendering]

[Streak + due count]
    └──enhances──> [tutor-progress]
    └──conflicts with──> [XP/leagues] (skip them; keep motivation calm)
```

### Dependency Notes

- **Error-tag vocabulary must be defined before `tutor-writing` ships.** Without it, weak-pattern aggregation is garbage (free-form tags can't cluster).
- **`BootContext` depends on `session_summaries` row from the previous session.** First-ever session needs a deterministic empty state; design `BootContext` to handle `last_session_summary = None`.
- **SM-2 depends on a stable `quality` mapping from LLM verdict.** Decide the mapping before implementing SRS updates: `✅ → 5`, `🟡 → 4`, `🟠 → 3`, `🔴 → 1`. Then golden-test.
- **`tutor-progress` depends on at least one completed session.** First-run UX must say "no data yet, run `tutor-vocab` or `tutor-writing`."

## MVP Definition

### Launch With (v1)

- [ ] **YAML profile + preferences** — Without these no other feature works.
- [ ] **SQLite schema + migrations** — Without these no state survives.
- [ ] **`tutor-setup`** — First-run experience; writes L1/L2/CEFR/interests/session-length.
- [ ] **SM-2 scheduling** — Core SRS math, golden-tested.
- [ ] **`tutor-vocab`** — Due-review queue, present item, capture answer, evaluate, update SRS, persist.
- [ ] **`tutor-writing`** — Generate prompt, accept free-form L2 response, return `FeedbackEnvelope` with spans/tags/severity/explanation-in-L1.
- [ ] **`tutor-feedback` renderer** — Markdown + severity emojis; golden-tested.
- [ ] **Controlled error-tag vocabulary** (Slavic-aware) — Frozen for v1; documented.
- [ ] **`tutor-session-analyzer`** — Validated JSON output; persists `summary_for_next_boot`.
- [ ] **`get_boot_context()`** — Deterministic, token-budgeted, handles cold-start.
- [ ] **`tutor-progress`** — Validated JSON and terminal markdown: streak, due count, per-tag mastery, top weak tags, last-N recap, ASCII trends, skipped-data notices, and item counts by maturity.
- [ ] **Claude plugin manifest + skills frontmatter** — So it actually installs.
- [ ] **Adapter contract test suite** — Proves Claude adapter covers full lifecycle.

### Add After Validation (v1.x)

- [ ] **Manual card add flow** — User says "add `мова` (language, fem)" → `tutor-vocab` creates entry. (Trigger: dogfood reveals need to capture words encountered outside the tool.)
- [ ] **Per-card review history view** — "Why is this hard?" (Trigger: user wants to debug their own learning.)
- [ ] **Cloze deletion exercise type** — Anki-style fill-in-blank. (Trigger: pure recall feels insufficient; want recognition + production blend.)
- [ ] **Session length cap negotiation** — If queue > session-length, prompt: "review all or just top N?" (Trigger: queue overflow after a missed day.)
- [ ] **Tag-based filtered review** — "Drill only `case:gen` errors this session." (Trigger: enough weak-pattern data accumulated to make filtering useful.)
- [ ] **Cron / scheduled trigger recipe** — Docs for OS-level reminders. (Trigger: streak streak-drops on travel days.)

### Future Consideration (v2+)

- [ ] **Reading / listening / speaking skills** — Already in Out of Scope.
- [ ] **`tutor-lesson` compound session** — Sequence vocab → reading → writing in one flow.
- [ ] **Additional host adapters** (Codex, OpenClaw, Hermess) — Architecture supports it; ship when one of those hosts is worth shipping for.
- [ ] **FSRS upgrade** — If dogfood data shows SM-2 wastes review time.
- [ ] **User-supplied seed word lists** — Bridge between LLM-generated content and "Anki shared decks."
- [ ] **Image / audio cards** — Once a host supports rich I/O.
- [ ] **Cross-session pattern drift detection** — Beyond what `SessionAnalysis.pattern_drift` does in v1.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| YAML profile + SQLite migrations | HIGH (gating) | LOW | P1 |
| SM-2 scheduling | HIGH | MEDIUM | P1 |
| `tutor-vocab` end-to-end | HIGH | MEDIUM | P1 |
| `tutor-writing` end-to-end | HIGH | HIGH (LLM judge reliability) | P1 |
| Slavic-aware error tag vocabulary | HIGH (Slavic dogfood) | MEDIUM | P1 |
| `FeedbackEnvelope` + markdown renderer | HIGH | MEDIUM | P1 |
| `tutor-session-analyzer` | HIGH (BootContext input) | MEDIUM | P1 |
| `tutor-progress` | MEDIUM | LOW | P1 |
| `get_boot_context()` deterministic + budgeted | HIGH (token cost) | MEDIUM | P1 |
| L1-aware explanation rendering | HIGH (if learner's L1 ≠ English) | LOW | P1 |
| Adapter contract tests | MEDIUM (insurance for portability claim) | MEDIUM | P1 |
| Manual card add | MEDIUM | LOW | P2 |
| Per-card history view | LOW | LOW | P2 |
| Cloze cards | MEDIUM | MEDIUM | P2 |
| Tag-filtered drill | MEDIUM | LOW | P2 |
| FSRS | LOW (SM-2 sufficient) | HIGH | P3 |
| Other modalities (reading/listening/speaking) | HIGH but Out of Scope | HIGH | P3 |
| Other host adapters | LOW (no users on those hosts yet) | MEDIUM | P3 |
| Gamification (XP/leagues) | NEGATIVE | LOW | Anti |
| Cloud sync / multi-user | NEGATIVE (kills wedge) | HIGH | Anti |

## Competitor Feature Analysis

| Feature | Anki | Duolingo | LangCorrect / italki | ChatGPT-as-tutor | language-tutor (this) |
|---------|------|----------|----------------------|------------------|------------------------|
| SRS algorithm | SM-2 / FSRS | Custom non-SRS path | None | None | SM-2 (v1) |
| Free writing eval | None (cards only) | Limited templated | Human peers | Free-form prose | Structured `FeedbackEnvelope` |
| Error tagging | Card tags (user-defined) | None visible | Inline comments | Inconsistent | Closed controlled vocabulary |
| L1-rendered explanation | User builds | Limited locales | Peer-chosen | Yes (unstructured) | Yes (structured + LLM-rendered) |
| Local-first / own-your-data | Yes (.apkg files) | No | No | No | Yes (YAML + SQLite in $HOME) |
| Terminal-native | No (Qt app) | No (web/mobile) | No (web) | No (web/app) | Yes |
| Gamification | None | Heavy (anti) | Light | None | None (deliberate) |
| Curriculum dependency | User-built | Heavy | Peer-supplied | LLM-generated | LLM-generated |
| Reproducible feedback | N/A | N/A | No (peer variance) | No (sampling) | Goal (golden tests + low temp) |

## Phase 2 Vocabulary Depth

Implemented vocabulary depth adds local deck ownership without changing SM-2:

- Manual add: `tutor vocab add --json '<card>'` stores standard or cloze cards.
- Seed import: `tutor vocab import --json '{"path":"...json"}'` validates each entry independently, merges duplicate metadata additively, and keeps SQLite canonical after import.
- Tag drills: `tutor vocab start --json '{"tags":["greetings"]}'` uses inclusive OR matching and reports no-match versus not-due empty states.
- Cloze cards: `card_type:"cloze"` requires exactly one `{{answer}}` marker, hides it during drill, and reveals the full sentence in feedback.
- Review history: `tutor vocab history --json '{"item_id":"vocab_..."}'` returns current due status and chronological attempts.

## Sources

- [SM-2 Spaced Repetition Algorithm](https://github.com/cnnrhill/sm-2) — Reference implementation
- [SM-2 explainer (Tegaru)](https://tegaru.app/en/blog/sm2-algorithm-explained) — Interval logic
- [supermemo2 PyPI](https://pypi.org/project/supermemo2/) — Python reference
- [Anki — official](https://apps.ankiweb.net/) — Table-stakes feature set
- [LangCorrect](https://langcorrect.com/) and [italki review](https://www.alllanguageresources.com/langcorrect/) — Writing-feedback baseline
- [Eleven pitfalls in L2 written corrective feedback](https://gianfrancoconti.com/2025/04/01/eleven-common-pitfalls-in-l2-written-corrective-feedback-highlighted-by-research/) — WCF best practices
- [Evaluating Prompting Strategies for GEC by Proficiency](https://arxiv.org/pdf/2402.15930) — LLM-as-judge calibration
- [ChatGPT and L2 Chinese writing study](https://www.tandfonline.com/doi/full/10.1080/09588221.2025.2453205) — Prompt-language effects on feedback
- [When Gamification Spoils Your Learning](https://arxiv.org/pdf/2203.16175) — Anti-feature evidence for leagues/XP
- [Duolingo Gamification Case Study](https://medium.com/@flordaniele/duolingo-case-study-research-on-gamification-90b5bac3ada0) — Both sides of streaks/XP
- [UA-GEC: Ukrainian Grammatical Error Correction Corpus](https://arxiv.org/pdf/2103.16997) — Real Slavic learner errors for evaluator validation
- [Ukrainian grammar reference](https://en.wikipedia.org/wiki/Ukrainian_grammar) — Cases, aspect, gender
- [Common Russian Grammar Mistakes](https://www.polyglottistlanguageacademy.com/language-culture-travelling-blog/2025/4/5/common-russian-grammar-mistakes-and-how-to-avoid-them) — Error inventory
- [English Grammar Profile + LLMs](https://arxiv.org/pdf/2603.17171) — CEFR-aligned controlled error vocabulary
- [Bilingual feedback / translanguaging in L2 writing](https://www.tandfonline.com/doi/full/10.1080/2331186X.2025.2510010) — L1-in-feedback evidence
- [L1 in peer feedback for L2 writing](https://drpress.org/ojs/index.php/EHSS/article/view/17531) — Cognitive-scaffolding rationale
- [OpenAI Agents SDK — session memory](https://cookbook.openai.com/examples/agents_sdk/session_memory) — BootContext-equivalent patterns
- [LangChain context engineering](https://docs.langchain.com/oss/python/langchain/context-engineering) — Token-budget discipline for agent state
- [LinGo terminal language app](https://github.com/hsnborn22/LinGo) — Terminal-native prior art

---
## Phase 5 Addendum — Text Modalities (2026-05-22)

Three text-only practice features, all host-independent and terminal-readable:

- **Reading comprehension** (`tutor-reading`): validate a generated passage + questions,
  answer, receive `FeedbackEnvelope` feedback, persist safe signals.
- **Guided micro-lessons** (`tutor-lesson`): one bounded topic (weak tag or chosen topic) +
  one practice step.
- **Transcript drills**: a text-only submode of `tutor-reading` (`mode=transcript`) —
  reconstruction / correction / comprehension. **Not audio**, and not a separate skill.

Out of scope (anti-features for Phase 5): audio playback, speech recognition, images,
GUI/web/dashboards, new hosts/adapters, cloud sync, gamification, bundled curriculum, and
any new scheduler or persistence. Generated exercises are provisional until validated by
Python contracts; invalid candidates get one repair attempt then a clear learner-facing
refusal. Rendered exercise ≤ 1200 chars; rendered feedback ≤ 900 chars.

---
*Feature research for: agentic-CLI AI language tutor (vocab + writing MVP, Slavic dogfood)*
*Researched: 2026-05-19*
