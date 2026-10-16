# POlaris — Complete Project Spec

## CSE 311 Software & CSE 321 Data Systems | Fall 2026 | Acıbadem University

| | |
|---|---|
| **Product** | POlaris: a web system that manages and maintains every student's Program Outcome (PO) scores |
| **Name** | "POlaris" is a working name (PO + Polaris, the star you navigate by). Rename it whenever the team agrees |
| **Team** | 3 people: Person A, Person B, Person C (fill in names in [§0.3](#03-who-owns-what)) |
| **Team size warning** | The guidelines say *exactly 4 members, not 3, not 5*. Get written confirmation from the TA (Doruk Düz) that a 3-person team is accepted. Do this before Sprint 1 starts |
| **Stack** | Python 3.13 · Django 6.1 · PostgreSQL 17 · Redis · Celery · HTMX · Bootstrap 5.3 · Claude API |
| **Repo** | `https://github.com/<org>/<repo>` (fill in) |
| **Spec version** | v1.0, written 16 Oct 2026. Living document: update it in the same PR as the change it describes |

**Key dates**

| Date | What |
|---|---|
| Fri 16 – Sun 18 Oct | Sprint 0: setup |
| Thu 12 Nov | **CSE 321 checkpoint**: Data & System Architecture presentation + report, in class |
| Tue 17 Nov | **CSE 311 checkpoint**: Tooling & Tasking presentation + report, in class |
| 10 Nov, 22 Dec | CSE 311 midterms |
| 19 Nov, 24 Dec | CSE 321 midterms |
| **Sun 6 Dec** | **Our target: feature-complete (Baseline + Tier 1)** |
| Mon 21 Dec | Feature freeze. Only bug fixes after this |
| Tue 29 – Wed 30 Dec | **Final demo + printed reports (one per course)** |

---

## How to use this document

This is the single source of truth for what we build and how we build it. It has three kinds of content:

1. **Decisions** (Parts 1–8): what the product is, how scores are calculated, the architecture, the data model, every feature with acceptance criteria. If code and spec disagree, one of them is wrong. Fix whichever one is wrong in the same PR.
2. **Process** (Parts 9–10): how we work as a Scrum team, Git, testing, CI/CD, local setup. CSE 311 grades this part directly.
3. **Plan** (Parts 11–15): sprint-by-sprint work, the full backlog, checkpoint deliverables, risks, gotchas. Appendices hold the official POs, the demo data and the change log.

Read Part 0 every time you sit down to work. Read Parts 1–3 once, carefully, before writing any code. Everything else is reference: jump to the part you need.

> **Getting Real says specs are bad.** Chapter 11, *There's Nothing Functional about a Functional Spec*, argues that big up-front specs lead to "an illusion of agreement". We take the warning seriously in three ways. This spec is short on prose and long on decisions and acceptance criteria. It lives in the repo and changes with the code (*Don't Do Dead Documents*, Ch. 11). And we race to running software anyway: the baseline is demoable by 8 Nov (*Race to Running Software*, Ch. 6). Cite this tension in report Section 6. Graders like seeing that we read the book critically.

---

# PART 0: START HERE

## 0.1 Where the project stands

> Update this block at the end of every sprint review. It is the first thing a teammate reads.

**Current sprint:** Sprint 0 (16 – 18 Oct): setup
**Last updated:** 16 Oct 2026

| Area | Status |
|---|---|
| Spec | ✅ v1.0 written, awaiting team review |
| TA confirmation of 3-person team | ⏳ not yet asked |
| GitHub repo + branch protection | ⏳ |
| Backlog in GitHub Projects | ⏳ |
| Django skeleton + Docker + CI | ⏳ |
| Staging deployment | ⏳ (Sprint 2) |
| Baseline features | ⏳ (Sprints 1–3) |
| Tier 1 features | ⏳ (Sprints 4–7) |

**Blockers:** none yet.

## 0.2 Decisions to review before Sprint 1

These were decided while writing the spec. The team has not discussed them yet. Read each one, then either accept it or raise it at the Sprint 1 planning meeting. Once accepted, tick it.

| # | Decision | Where it's explained |
|---|---|---|
| D1 | LO→PO weights are integers 1–5 everywhere. Assessment→LO weights are percentages 1–100 with no "must sum to 100" rule | [§2.3](#23-calculation-policies) |
| D2 | Grades are draft until the instructor publishes the assessment. Only published grades count anywhere students or the department can see | [§2.3](#23-calculation-policies), [§6 B7](#b7-publish-grades-and-audit-trail) |
| D3 | A missing grade is *skipped*, not counted as zero. The score is computed from what exists and shows a coverage %. An instructor who wants a zero enters 0 | [§2.3](#23-calculation-policies) |
| D4 | A student's PO score across courses is one flat weighted average over every LO→PO link they have, as drawn on the professor's slides. No per-course averaging step, no credit weighting | [§2.3](#23-calculation-policies) |
| D5 | If a student retakes a course, only the latest completed attempt counts | [§2.3](#23-calculation-policies) |
| D6 | Roles live in a `ProgramMembership` table, not a single field on the user, because a department head usually also teaches | [§3.2](#32-how-roles-are-modelled) |
| D7 | PostgreSQL from day one, even locally (in Docker). No SQLite | [§4.1](#41-technology-stack) |
| D8 | Celery + Redis for background jobs. Django 6's built-in Tasks framework ships no production worker yet | [§4.1](#41-technology-stack) |
| D9 | Server-rendered Django templates + HTMX. No React, no separate frontend | [§4.1](#41-technology-stack) |
| D10 | Our own small audit table instead of `django-simple-history`, which does not yet declare Django 6.1 support | [§5.4](#54-audit-trail) |
| D11 | The AI only ever reads syllabi. It never sees student names or grades | [§7.8](#78-privacy-and-safety) |
| D12 | Claude model: `claude-opus-5-5`, with automatic fallback on refusal turned on. About 20–30 US cents per syllabus | [§7.5](#75-calling-claude), [§7.7](#77-cost) |
| D13 | Department head does **not** have to approve mapping changes in the baseline. They can view and override any mapping. Formal approval is Tier 2 | [§3.3](#33-permission-matrix) |
| D14 | Hosting on one small Linux VPS with Docker Compose, staging + production side by side, deployed by GitHub Actions | [§9.10](#910-cd-pipeline-and-hosting) |
| D15 | One-week sprints, Monday to Sunday | [§9.1](#91-scrum-for-a-team-of-three) |

## 0.3 Who owns what

Three ownership areas. Owning an area means you are the default assignee and the reviewer of last resort for that code, not that nobody else touches it. Every PR is still reviewed by someone else.

| Person | Area | Owns | Scrum role |
|---|---|---|---|
| **A**: `<name>` | **Engine & Data** | Data model, migrations, scoring engine, snapshots, seed data, Claude extraction service (`apps/ingestion/extraction.py`), CSE 321 data diagrams | Product Owner (keeps the backlog ordered, talks to the TA) |
| **B**: `<name>` | **Instructor Experience** | Course setup, LO and assessment editors, both weight matrices, grade sheet, publish flow, bulk upload, syllabus wizard screens | Developer |
| **C**: `<name>` | **Platform & Insights** | Auth, roles, permissions, Docker, CI/CD, hosting, student profile, department dashboards, exports, design system | Scrum Master (runs ceremonies, keeps the board and velocity log honest) |

Why this split: each area is a vertical slice that one person can hold in their head, and each has visible UI so everyone has something to show at demos. The heaviest unknown, the AI extraction, sits with the person who owns the data model, because the hard part is mapping messy syllabus text onto our tables.

**Report Section 2 needs "who carried out what explicitly".** Keep the owner field on every GitHub issue accurate. At each checkpoint, the issue list filtered by assignee *is* that section.

## 0.4 Codebase conventions (read before writing code)

Match these so we don't end up with a Frankenstein.

| Convention | Value | Why |
|---|---|---|
| Python | 3.13, managed by `uv` | Fast, one lockfile, same versions on every machine |
| Django apps | Live in `apps/` (`apps.accounts`, `apps.catalog`, …) | One place to look |
| Views | Function-based views + decorators | Same style as CSE 220. Easy to read, easy to test |
| Business logic | In `services.py` (writes) and `selectors.py` (reads) per app. **Never in views or templates** | Views stay thin. Logic is testable without HTTP |
| Scoring math | Only in `apps/scoring/engine.py`. Pure Python, **no Django imports** | One source of truth for every number, tested to 100% |
| Money-like numbers | `Decimal` everywhere for scores and weights. Never `float` | Floats make 0.1 + 0.2 ≠ 0.3. Grades must be exact |
| Rounding | Only at display time, 1 decimal, half-up, via the `|score` template filter | [§2.3](#23-calculation-policies) |
| URL params | `<int:offering_id>`, `<int:assessment_id>`, etc. Named after the model | Predictable |
| Templates | `apps/<app>/templates/<app>/<page>.html`. Partials via Django 6 `{% partialdef %}` | Namespaced, HTMX-friendly |
| Forms | `forms.py` per app | |
| Permissions | Only via `apps/accounts/permissions.py` helpers and the `@require_role` / `@require_offering_access` decorators | One place to audit. Matrix-tested |
| Settings | `config/settings/{base,dev,test,prod}.py`, secrets from environment via `django-environ` | Nothing secret in Git |
| Lint/format | `ruff check` + `ruff format`, enforced in CI and pre-commit | No style debates in reviews |
| Tests | `pytest` + `pytest-django` + `factory_boy`, in `apps/<app>/tests/` | |
| Branches | `feature/<issue#>-short-slug`, `fix/<issue#>-slug` off `develop` | [§9.6](#96-branching-model) |
| Commits | Imperative, human, mentions the issue: `Add grade sheet inline editing (#42)` | Readable history for the report |
| PRs | Small (< 400 changed lines where possible), one issue each, `Closes #42` in description | Fast reviews, clean board automation |
| Language | UI copy, code, comments and commits in English. Turkish via i18n later (Tier 2) | |

## 0.5 Daily workflow in one screen

```bash
git switch develop && git pull                 # 1. start fresh
git switch -c feature/42-grade-sheet           # 2. branch per issue
docker compose up -d                           # 3. Postgres + Redis
uv run python manage.py migrate                # 4. apply teammates' migrations
uv run python manage.py runserver              # 5. work
uv run pytest                                  # 6. tests green before every push
uv run ruff check . && uv run ruff format .    # 7. lint
git push -u origin feature/42-grade-sheet      # 8. open PR → develop, request review
```

Move your card on the board when you start (In Progress), when you open the PR (In Review), and the PR merge moves it to Done automatically.

---

# PART 1: THE PRODUCT

## 1.1 The problem

Engineering departments must prove to accreditation bodies (in Turkey, MÜDEK) that graduates achieve the department's Program Outcomes. Acıbadem CSE has 11 POs. Today the evidence lives in spreadsheets: every instructor maps their course's learning outcomes to POs, and someone in the department stitches grades from dozens of courses into PO numbers by hand, once a year, under deadline pressure. It is slow, error-prone, and nobody can see a student's PO profile until it is too late to act on it.

## 1.2 Punchline and key ingredient (report Section 1)

> **Punchline:** *Upload a syllabus, get a PO-ready course in two minutes. Publish grades, and every student's PO profile updates itself.*
>
> **Key ingredient:** a small, exhaustively tested scoring engine that every number flows through, fed by an AI syllabus reader that turns a PDF or a phone photo into learning outcomes, assessments and weights, which the instructor reviews before anything is saved.

## 1.3 Who uses it

Fictional personas used throughout this spec, in the seed data and in the demo.

| Persona | Role | What they need |
|---|---|---|
| **Elif Yıldız** | 3rd-year CSE student | See her PO profile, understand which courses drove each score, download a PO transcript |
| **Dr. Can Aydın** | Instructor, teaches CSE 311 and CSE 321 | Set up his courses fast, enter or upload grades, publish when ready, see how his class did per LO |
| **Prof. Deniz Kara** | Department head, also teaches | Own the PO list and course catalog, see PO attainment per cohort, find under-covered POs, export accreditation evidence, chase instructors who haven't published |
| **Admin** | Technical superuser | Create programs and accounts, fix data via Django admin |

## 1.4 Glossary

| Term | Meaning |
|---|---|
| **Program Outcome (PO)** | A skill the whole program promises, e.g. *PO 6: work effectively in teams*. 11 of them, owned by the department |
| **PO set** | A versioned list of POs for a program (curricula change; old students keep the set they enrolled under) |
| **Course** | A catalog entry, e.g. CSE 311 Software. Exists across terms |
| **Offering** | One run of a course in one term, e.g. CSE 311 in Fall 2026. LOs, assessments, grades all hang off the offering |
| **Learning Outcome (LO)** | A course-level skill, e.g. *LO 2: apply agile practices in a team project*. Defined per offering |
| **Assessment** | Anything graded: midterm, project, quiz, homework, lab, presentation |
| **Assessment→LO weight** | How much an assessment counts toward an LO, a percentage (1–100) |
| **LO→PO weight** | How strongly an LO contributes to a PO, an integer 1–5 |
| **Mapping** | The set of all weights for an offering |
| **Draft / Published** | A grade is visible to students and counts toward scores only after the instructor publishes that assessment |
| **Coverage** | How much of a score's inbound weight actually has data. 100% = everything graded |
| **Attainment** | A student *attains* a PO when their PO score ≥ the program threshold (default 60) |
| **Attainment rate** | Share of a cohort that attains a PO. The headline accreditation number |
| **Cohort** | Students grouped by entry year, e.g. "2023 entry" |

## 1.5 Answers to the instructor's eight design questions

The brief lists open questions our design must answer. These are our answers. Put this table on a slide at both checkpoints.

| Question | Our answer |
|---|---|
| Who provides the POs? | The department head, per program, as a versioned PO set. Seeded with Acıbadem CSE's official 11 |
| Who creates the courses? | The head creates catalog courses and per-term offerings, and assigns instructors |
| Who creates the learning outcomes? | The offering's instructor: by hand, by cloning last term (Tier 2), or by approving what the syllabus wizard extracted (Tier 1) |
| Who enters the percentages? | The instructor, in two grids: assessment→LO in %, LO→PO on 1–5. The head can view and override any mapping |
| Who enters the grades? When and how? | The instructor (later also a TA, Tier 2), any time during the term, via the grade sheet or bulk upload. Grades stay draft until published in one atomic action. The head can close a term, which locks it |
| Relationship between syllabi and POs? | The syllabus file is stored on the offering and is the source of its LOs, assessments and mappings. Many Bologna syllabi already contain a course→PO contribution table on a 1–5 scale, which the wizard reads |
| What user roles exist? What can each see and do? | Student, Instructor, Department Head, Admin (+ TA in Tier 2). See the matrix in [§3.3](#33-permission-matrix) |
| 3rd-party integrations? UI/UX? | Claude API (syllabus reading), email (reminders, password reset), Excel/CSV in and out, PDF export, later university SSO and an OBS course-page import. UI: server-rendered, fast, works on a phone |

## 1.6 Scope tiers

Baseline is what the brief literally asks for. Basic functionality only = average grade, so **Baseline is necessary but not sufficient**. Tier 1 is committed scope: we are not done without it. Tier 2 is planned and goes in by velocity. Tier 3 is stretch.

### Baseline (Sprints 1–3, demoable by Sun 8 Nov)

| ID | Feature | Primary user |
|---|---|---|
| B1 | Accounts: email login, logout, password reset, role-aware navigation | All |
| B2 | Program and PO management (versioned PO sets, seeded with the official 11) | Head |
| B3 | Terms, course catalog, offerings, instructor assignment, enrollment (manual + CSV import) | Head |
| B4 | Course setup: learning outcomes and assessments per offering | Instructor |
| B5 | The two weight matrices (assessment→LO %, LO→PO 1–5) with live validation | Instructor |
| B6 | Grade sheet: spreadsheet-like inline grade entry | Instructor |
| B7 | Publish grades per assessment + audit trail of every change | Instructor |
| B8 | Student PO profile v1: 11 PO scores, coverage, contributing courses | Student |
| B9 | Instructor course results: per-student LO scores, class averages | Instructor |
| B10 | Department overview v1: average score per PO, per term | Head |
| B11 | Mapping lint: warnings for broken or suspicious mappings | Instructor, Head |
| B12 | Django admin for every model, demo seed command | Admin, Team |

### Tier 1 (Sprints 4–7, committed, done by Sun 6 Dec)

| ID | Feature | Why it's worth it |
|---|---|---|
| T1.1 | **Bulk grade upload**: CSV/Excel from the gradebook, column mapping, dry run that lists every problem before anything is saved | Instructors already have grades in Excel. Typing 80 students × 6 assessments is 480 chances to make a typo |
| T1.2 | **Syllabus ingestion wizard**: upload PDF, Word or phone photo → Claude extracts course info, LOs, assessments, weights → instructor reviews and edits → one click applies it | Turns 30–60 minutes of setup into 2. The flagship feature. Explicitly suggested by the instructor |
| T1.3 | **AI-suggested LO→PO weights**: when a syllabus has no LO-level mapping, suggest 1–5 weights against the 11 PO descriptions, each with a one-line reason | Mapping is the step instructors find hardest |
| T1.4 | **Audit history viewer**: who changed which grade or weight, when, from what to what | Trust. Accreditation auditors ask exactly this |
| T1.5 | **Student profile v2**: radar chart, per-course breakdown, trend across terms | Students understand a picture faster than a table |
| T1.6 | **Department dashboard**: PO attainment rate per cohort and term with threshold, course × PO coverage heat map that flags under-covered POs | This *is* the accreditation evidence |
| T1.7 | **Exports**: dashboard and course reports to PDF and Excel | The head has to submit something. The instructor suggested "generating a report on student performance" |

### Tier 2 (Sprints 8–9, by velocity, ordered)

| ID | Feature |
|---|---|
| T2.1 | Clone last term's course setup in one click |
| T2.2 | Term completion tracker for the head + email reminders to instructors who haven't published |
| T2.3 | Precomputed score tables (PostgreSQL materialized view) refreshed by the worker on publish. Feeds CSE 321 report Section 4 |
| T2.4 | PO transcript PDF a student can download |
| T2.5 | Turkish / English toggle (Django i18n) |
| T2.6 | Multi-program support in the UI (the data model supports it from day one) |
| T2.7 | Head approval workflow for mapping changes |
| T2.8 | Teaching Assistant role: enters draft grades, cannot publish |
| T2.9 | Import a course from its public OBS Bologna page URL (same extraction pipeline, HTML instead of PDF) |
| T2.10 | Error monitoring (Sentry free tier) and uptime check |

### Tier 3 (stretch)

| ID | Feature |
|---|---|
| T3.1 | What-if simulator: preview how PO scores change before committing new weights |
| T3.2 | Anonymous cohort comparison on the student profile ("you are above the cohort median on PO 4") |
| T3.3 | Course recommendations targeting a student's weakest PO |
| T3.4 | University single sign-on (Microsoft Entra ID / Google) |
| T3.5 | REST API with OpenAPI docs for future OBS/LMS integration |

## 1.7 Non-goals

Saying no is a feature (*Start With No*, Getting Real Ch. 5). We will **not** build:

- Letter grades, GPA or a full student information system. OBS already does that.
- Writing anything back to OBS.
- A native mobile app. The site is responsive instead.
- Real student data, ever. All demo data is synthetic (KVKK, Turkey's data-protection law).
- Chat with an AI about your grades. Useless for the actual users and a privacy risk.
- Custom per-instructor formulas. One formula, explained, tested, trusted.

---

# PART 2: THE SCORING METHOD

Every number POlaris shows comes from this part. Every team member must be able to explain it at the demo without notes. Read it slowly.

## 2.1 The idea in plain language

Scores flow left to right through two layers of weighted arrows:

```
 ASSESSMENTS              LEARNING OUTCOMES             PROGRAM OUTCOMES
 (graded by instructor)   (per course offering)         (per program, across all courses)

 Midterm  ──60%──►  LO 1  ──weight 4──►  PO 1
          ──40%──►  LO 2  ──weight 2──►  PO 1
 Project  ──40%──►  LO 1                 ──weight 5──►  PO 2
          ──100%─►  LO 2
```

At every node the rule is the same:

> **score = Σ (weight × score of each source) ÷ Σ (weights of those sources)**

That is a **weighted average**. A source with twice the weight pulls the result twice as hard. Because we divide by the sum of the weights, the weights never need to add up to 100 and the scale does not matter: weights of 60 and 40 behave exactly like 0.6 and 0.4, and LO→PO weights of 4 and 2 behave exactly like 1.0 and 0.5. Only the *ratios* between weights matter. This is called **scale invariance**, and it is why we can safely use percentages on one layer and a 1–5 scale on the other.

## 2.2 Worked example: Elif (from the professor's slides)

Elif scored 90 on the midterm and 80 on the project in CSE 311.

**Layer 1: assessments → learning outcomes**

| LO | Inputs | Calculation | Score |
|---|---|---|---|
| LO 1 | Midterm 90 @ 60%, Project 80 @ 40% | (90×60 + 80×40) ÷ (60+40) = 8600 ÷ 100 | **86.0** |
| LO 2 | Midterm 90 @ 40%, Project 80 @ 100% | (90×40 + 80×100) ÷ (40+100) = 11600 ÷ 140 | **82.857… → 82.9** |

**Layer 2: learning outcomes → program outcomes**

The slide uses 100% and 50% for LO 1→PO 1 and LO 2→PO 1. On our 1–5 scale the same 2:1 ratio is weights 4 and 2.

| PO | Inputs | Calculation | Score |
|---|---|---|---|
| PO 1 | LO 1 86.0 @ 4, LO 2 82.857… @ 2 | (86×4 + 82.857…×2) ÷ 6 | **84.952… → 85.0** |
| PO 2 | LO 2 82.857… @ 5 | (82.857…×5) ÷ 5 | **82.857… → 82.9** |

These match the guidelines slide (*Worked example: Elif's PO scores*: 85.0 and 82.9) exactly. Our engine reproduces them in a test ([§2.6](#26-engine-tests)).

> **Why the brief says 84 and the guidelines say 85.** The earlier brief (the "Cato" slides) rounded LO 2 down to 82 *before* computing PO 1, then dropped the decimals: (86×1 + 82×0.5) ÷ 1.5 = 84.67 → "84". The later guidelines deck keeps full precision and gets 85.0. Rounding in the middle of a calculation compounds error, so **POlaris never rounds intermediate values**. It rounds once, for display. Be ready to explain this at the demo: it shows we understand the method, not just the formula.

**Across many courses.** Elif also takes CSE 321 and MAT 241. Each course's LOs link to POs with their own 1–5 weights. Her PO 1 score is one weighted average over *every* LO→PO 1 link from *every* course she has taken, exactly as drawn on the brief's multi-course slides (lines go directly from each course's LOs to the PO).

## 2.3 Calculation policies

Each policy below was a real choice. The *why* is what you defend at the demo.

| # | Policy | Why |
|---|---|---|
| P1 | **Assessment→LO weights are percentages, 1–100.** They do not need to sum to 100 per LO or per assessment | The slides themselves don't sum: LO 2 receives 40% + 100% = 140%. The formula divides by the sum anyway. Forcing 100 would add friction for zero mathematical benefit. Mapping lint (B11) warns about unusual patterns instead |
| P2 | **LO→PO weights are integers 1–5.** No link = no contribution (we store no row, never a 0) | The guidelines' multi-course slide says "weight 1–5". It matches the 1–5 contribution scale used in Bologna syllabi, so instructors already think this way |
| P3 | **Raw marks are normalised to 0–100** before anything else: `normalised = raw ÷ max_score × 100` | A quiz out of 20 and a midterm out of 100 must be comparable |
| P4 | **Only published grades count** toward any score a student or the head sees | Instructors need to fix mistakes before students see them (D2) |
| P5 | **Missing grades are skipped, not zero.** The weighted average uses only the sources that have a value, and the result carries a **coverage** = (weight of sources present) ÷ (weight of all sources) | Mid-term, most assessments aren't graded yet. Counting them as 0 would show every student failing in October. An instructor who wants a real zero (no-show) enters 0 |
| P6 | **Excused grades** (`is_excused`) are skipped like missing ones but not flagged as missing | A student with a medical report shouldn't show "incomplete" forever |
| P7 | **No intermediate rounding.** Store and compute with `Decimal`. Round once, for display: 1 decimal, half-up (84.95 → 85.0) | See the 84 vs 85 box above |
| P8 | **Cross-course aggregation is flat** over all LO→PO links (no per-course average step, no ECTS weighting) | It is what the slides draw. A 2-credit course with five LOs strongly mapped to PO 7 *does* provide more evidence for PO 7 than one weak link elsewhere. Credit weighting can be added later as a program setting if the department asks |
| P9 | **Retakes: latest completed attempt counts.** Earlier offerings of the same catalog course are excluded from PO scores (still visible in history) | Mirrors how transcripts treat retakes. Avoids double-counting the same course |
| P10 | **In-progress courses are included with their coverage.** The student profile marks them "in progress". Department attainment defaults to **closed terms only**, with a toggle | Students want early signal. Accreditation numbers should only use final data |
| P11 | **Attainment threshold** is a program setting, default 60. A student *attains* a PO when their score ≥ threshold. **Attainment rate** = students attaining ÷ students with any score for that PO | 60 is a placeholder. The head sets the real target |
| P12 | A node whose inbound weights sum to zero, or that has no sources with data, has score **None** (shown "—"), never 0 | "No evidence" and "failed" are different things |

## 2.4 The engine contract

The engine is a pure Python module, `apps/scoring/engine.py`. It takes plain data in and returns plain data out. It imports nothing from Django. Views and services never compute a score themselves; they call a loader that reads the database into these dataclasses, call the engine, and display what comes back.

```
           ┌────────────────────────┐      ┌──────────────────────┐      ┌────────────────────────┐
 Database ─┤ apps/scoring/loaders.py├─────►│ apps/scoring/engine.py├────►│ views / templates /    │
 (ORM)     │ builds StudentInputs   │      │ pure functions        │      │ exports / snapshots    │
           └────────────────────────┘      └──────────────────────┘      └────────────────────────┘
               applies P4, P9, P10            applies P1–P3, P5–P8, P12        applies P7 display rounding
```

Why pure: the engine is where a bug would silently corrupt every number in the product. Pure functions can be tested exhaustively and fast (hundreds of tests in under a second), with no database. This is also the cleanest place in the codebase to practise **TDD** (CSE 311 Week 11): write the test from the professor's example first, watch it fail, then make it pass. Keep those commits separate so the history shows red → green.

## 2.5 Reference implementation

This code was run against the worked example while writing the spec. It reproduces 86.0, 82.9, 85.0 and 82.9. Person A types it in test-first in Sprint 1. Don't paste it blindly: write the tests in §2.6 first, then make them pass, then compare.

```python
# apps/scoring/engine.py
"""Pure scoring engine. No Django imports. Every score in POlaris comes from here."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Hashable, Iterable, Mapping

ZERO = Decimal("0")
HUNDRED = Decimal("100")


@dataclass(frozen=True)
class Edge:
    """A weighted arrow from a source node (assessment or LO) to a target node (LO or PO)."""
    source: Hashable
    target: Hashable
    weight: Decimal


@dataclass(frozen=True)
class NodeScore:
    score: Decimal | None  # None = no source feeding this node has a value (P12)
    coverage: Decimal      # share of inbound weight that had a value, 0..1 (P5)


def weighted_average(pairs: Iterable[tuple[Decimal, Decimal]]) -> Decimal | None:
    """score = sum(weight * score) / sum(weights). None when the weights sum to zero."""
    num = ZERO
    den = ZERO
    for score, weight in pairs:
        num += score * weight
        den += weight
    return None if den == ZERO else num / den


def propagate(source_scores: Mapping[Hashable, Decimal],
              edges: Iterable[Edge]) -> dict[Hashable, NodeScore]:
    """Compute one layer. Sources without a score are skipped and the remaining
    weights renormalise (P5). Coverage records how much inbound weight was present."""
    inbound: dict[Hashable, list[Edge]] = defaultdict(list)
    for e in edges:
        if e.weight <= ZERO:
            raise ValueError(f"weight must be positive: {e}")
        inbound[e.target].append(e)

    result: dict[Hashable, NodeScore] = {}
    for target, es in inbound.items():
        total = sum((e.weight for e in es), ZERO)
        present = [(source_scores[e.source], e.weight) for e in es if e.source in source_scores]
        covered = sum((w for _, w in present), ZERO)
        result[target] = NodeScore(score=weighted_average(present), coverage=covered / total)
    return result


def normalise(raw: Decimal, max_score: Decimal) -> Decimal:
    """Convert a raw mark (e.g. 17 out of 20) to the 0-100 scale (P3)."""
    if max_score <= ZERO:
        raise ValueError("max_score must be positive")
    return raw / max_score * HUNDRED


def display(value: Decimal | None) -> str:
    """Round only for display: 1 decimal, half-up (P7). None -> an em dash (P12)."""
    if value is None:
        return "—"
    return str(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


# ---------- whole-student calculation ----------

@dataclass(frozen=True)
class OfferingInputs:
    """Everything the engine needs about one course offering for one student."""
    offering_id: int
    grades: Mapping[int, Decimal]            # assessment_id -> raw mark (published, not excused)
    max_scores: Mapping[int, Decimal]        # assessment_id -> max_score
    assessment_lo_edges: tuple[Edge, ...]    # source=assessment_id, target=lo_id, weight=%
    lo_po_edges: tuple[Edge, ...]            # source=lo_id, target=po_id, weight=1..5


@dataclass(frozen=True)
class StudentProfile:
    lo_scores: dict[tuple[int, int], NodeScore]   # (offering_id, lo_id) -> score
    po_scores: dict[int, NodeScore]               # po_id -> score
    po_contributors: dict[int, list[tuple[int, int, Decimal]]] = field(default_factory=dict)
    # po_id -> [(offering_id, lo_id, weight)], used for "why is my PO 3 this number?"


def compute_student_profile(offerings: Iterable[OfferingInputs]) -> StudentProfile:
    lo_scores: dict[tuple[int, int], NodeScore] = {}
    lo_values: dict[tuple[int, int], Decimal] = {}
    po_edges: list[Edge] = []
    contributors: dict[int, list[tuple[int, int, Decimal]]] = defaultdict(list)

    for off in offerings:
        normalised = {a: normalise(raw, off.max_scores[a]) for a, raw in off.grades.items()}
        for lo_id, ns in propagate(normalised, off.assessment_lo_edges).items():
            key = (off.offering_id, lo_id)
            lo_scores[key] = ns
            if ns.score is not None:
                lo_values[key] = ns.score
        for e in off.lo_po_edges:
            key = (off.offering_id, e.source)
            po_edges.append(Edge(source=key, target=e.target, weight=e.weight))
            contributors[e.target].append((off.offering_id, e.source, e.weight))

    return StudentProfile(
        lo_scores=lo_scores,
        po_scores=propagate(lo_values, po_edges),
        po_contributors=dict(contributors),
    )
```

LO keys are `(offering_id, lo_id)` because LOs are per offering: "LO 1" of CSE 311 and "LO 1" of MAT 241 are different things.

**Class-level and cohort-level numbers** (class average per LO, department average per PO) are averages of the per-student results, computed in `apps/scoring/aggregates.py`, never a separate formula applied to pooled grades. A class average LO score is the plain mean of the students' LO scores that are not None.

## 2.6 Engine tests

Write these first (TDD). `apps/scoring/tests/test_engine.py`. Target: **100% line and branch coverage** of `engine.py`.

**Golden tests (exact numbers from the slides)**

| Test | Expect |
|---|---|
| `test_elif_lo1` | 86.0 |
| `test_elif_lo2` | display 82.9 (exact 82.857142…) |
| `test_elif_po1_on_1_to_5_scale` | weights 4 and 2 → display 85.0 |
| `test_elif_po2` | 82.9 |
| `test_brief_rounding_discrepancy` | feeding the rounded 82 gives 84.7, not 85.0: documents why we never round intermediates |

**Policy tests**

| Test | Expect |
|---|---|
| `test_missing_grade_is_skipped_not_zero` | project ungraded → LO 2 = 90.0 from the midterm alone, coverage 40/140 = 28.6% |
| `test_no_data_gives_none` | no grades → score None, coverage 0 |
| `test_zero_or_negative_weight_raises` | `ValueError` |
| `test_normalise_out_of_20` | 17/20 → 85 |
| `test_normalise_rejects_zero_max` | `ValueError` |
| `test_display_half_up` | 84.95 → "85.0", 84.94 → "84.9", None → "—" |
| `test_two_courses_feed_one_po` | flat average across offerings (P8), with a hand-computed expected value |
| `test_lo_keys_do_not_collide_across_offerings` | LO id 1 in two offerings stays separate |
| `test_contributors_list` | PO 1 lists exactly the (offering, LO, weight) triples that feed it |

**Property tests with Hypothesis** (random inputs, hundreds of cases each)

| Property | Statement |
|---|---|
| Bounded | A weighted average always lies between the smallest and largest source score |
| Scale invariant | Multiplying every weight on a layer by the same positive constant leaves scores unchanged (compare with a tolerance of 1e-20: `Decimal` keeps 28 significant digits, so the last digit can differ) |
| Order independent | Shuffling the edge list does not change any score |
| Neutral addition | Adding a source whose score equals the current average leaves the average unchanged |
| Coverage range | Coverage is always in [0, 1], and 1 exactly when every source has a score |

```python
# apps/scoring/tests/test_engine.py (excerpt)
from decimal import Decimal as D

from hypothesis import given, strategies as st

from apps.scoring.engine import Edge, display, propagate

GRADES = {"midterm": D(90), "project": D(80)}
A_TO_LO = [
    Edge("midterm", "LO1", D(60)), Edge("project", "LO1", D(40)),
    Edge("midterm", "LO2", D(40)), Edge("project", "LO2", D(100)),
]


def test_elif_po1_on_1_to_5_scale():
    lo = {k: v.score for k, v in propagate(GRADES, A_TO_LO).items()}
    po = propagate(lo, [Edge("LO1", "PO1", D(4)), Edge("LO2", "PO1", D(2))])
    assert display(po["PO1"].score) == "85.0"


def test_missing_grade_is_skipped_not_zero():
    lo = propagate({"midterm": D(90)}, A_TO_LO)
    assert display(lo["LO2"].score) == "90.0"
    assert display(lo["LO2"].coverage * 100) == "28.6"


scores = st.decimals(min_value=0, max_value=100, places=2)
weights = st.decimals(min_value=1, max_value=100, places=0)


@given(st.lists(st.tuples(scores, weights), min_size=1, max_size=12))
def test_weighted_average_is_bounded(pairs):
    src = {i: s for i, (s, _) in enumerate(pairs)}
    edges = [Edge(i, "T", w) for i, (_, w) in enumerate(pairs)]
    result = propagate(src, edges)["T"].score
    assert min(src.values()) <= result <= max(src.values())
```

---

# PART 3: ROLES AND PERMISSIONS

## 3.1 Roles

| Role | Who | One-line summary |
|---|---|---|
| **Student** | Enrolled students | Sees only their own published grades, LO scores and PO profile |
| **Instructor** | Faculty assigned to offerings | Configures and grades their own offerings, publishes, sees their own classes' results |
| **Department Head** | Usually also an instructor | Everything an instructor can do on *any* offering of the program, plus POs, catalog, terms, enrollment, dashboards |
| **Admin** | Technical superuser (`is_superuser`) | Programs, accounts, Django admin. Not a product persona |
| **Teaching Assistant** (Tier 2) | Assigned to an offering | Enters draft grades. Cannot publish, cannot change weights |

## 3.2 How roles are modelled

A department head usually teaches too, and one person can in principle belong to two programs. A single `role` field on the user can't express that. So:

- `User` holds identity only (email, name, student number).
- `ProgramMembership(user, program, role)` says what someone is *in a program*: `student`, `instructor` or `head`. One user can hold several rows.
- Which offerings an instructor teaches is a separate fact: `CourseOffering.instructors` (many-to-many).
- Which offerings a student takes is `Enrollment`.
- Admin is Django's `is_superuser`.

Permission helpers combine these: "can edit offering X" = superuser, OR head of X's program, OR instructor listed on X. This lives in one module, `apps/accounts/permissions.py`.

## 3.3 Permission matrix

✓ = allowed. "own" = only offerings they teach (instructor) or their own record (student). Anything not listed is denied. **When the term is closed, every write below is denied for everyone except Admin** (the head can reopen a term; reopening is audited).

| Action | Student | Instructor | Head | Admin |
|---|---|---|---|---|
| View own PO profile, own published grades | ✓ | — | — | ✓ |
| View another student's PO profile | — | — | ✓ | ✓ |
| View students' LO scores in a course | — | own | ✓ | ✓ |
| Manage programs | — | — | — | ✓ |
| Manage PO sets and POs | — | view | ✓ | ✓ |
| Manage terms; close / reopen a term | — | — | ✓ | ✓ |
| Manage catalog courses and offerings; assign instructors | — | view own | ✓ | ✓ |
| Import enrollments | — | — | ✓ | ✓ |
| Edit LOs, assessments, both weight matrices | — | own | ✓ | ✓ |
| Run the syllabus wizard | — | own | ✓ | ✓ |
| Enter / upload draft grades | — | own | ✓ | ✓ |
| Publish an assessment's grades | — | own | ✓ | ✓ |
| View audit history | — | own | ✓ | ✓ |
| Department dashboard, heat map, attainment | — | — | ✓ | ✓ |
| Export course report | — | own | ✓ | ✓ |
| Export department report | — | — | ✓ | ✓ |
| Download own PO transcript (T2.4) | ✓ | — | — | ✓ |
| Approve mapping changes (T2.7) | — | — | ✓ | ✓ |
| Django admin | — | — | — | ✓ |

Decision D13: in the baseline the head does **not** approve mappings. They can view and override any mapping, and every change is in the audit trail. A formal approval step is T2.7.

## 3.4 Enforcement rules

1. **Every view** is decorated: `@login_required` plus `@require_role(...)` or `@require_offering_access(edit=True)`. No view checks permissions by hand.
2. **Every query that returns student data** goes through a selector that takes `user` as its first argument and scopes the queryset. Example: `selectors.visible_enrollments(user, offering)`.
3. **Objects you may not see return 404, not 403.** A 403 tells an attacker the object exists.
4. **Templates hide buttons** with `{% if perms_for.offering.can_edit %}`, but hiding is cosmetic. The decorator is the real check.
5. **The permission matrix test** (`apps/accounts/tests/test_permission_matrix.py`) is parametrised over every URL × every role and asserts the expected status code (200 / 302 / 404). Adding a URL without adding it to the matrix fails the test. This is how we prove in the report that students cannot see each other's grades.

---

# PART 4: ARCHITECTURE

## 4.1 Technology stack

Versions were checked on 16 Oct 2026. Pin exact versions in `uv.lock`; upgrade deliberately, never by accident.

| Layer | Choice | Version | Why this, not something else |
|---|---|---|---|
| Language | Python | 3.13 | Django 6.1 needs ≥ 3.12. 3.13 has the widest library support today |
| Package manager | uv | 0.13.x | One tool for Python versions, virtualenvs, lockfile. 10–100× faster than pip. `uv sync` gives every teammate identical packages |
| Web framework | Django | 6.1.x | Mandated. 6.x adds template partials, which pair perfectly with HTMX |
| Database | PostgreSQL | 17 | Real constraints, transactions with selectable isolation levels, partial indexes, materialized views, `EXPLAIN ANALYZE`: everything CSE 321 asks about. SQLite can't show any of that (D7) |
| DB driver | psycopg | 3.3.x | Current driver; Django's recommended one |
| Cache + message broker | Redis | 7 | One service for two jobs: Django cache and Celery broker |
| Background jobs | Celery | 5.6.x | Syllabus extraction takes 20–90 s; exports and recomputation must not block a web request. Django 6's built-in `django.tasks` framework ships only development backends and no worker (D8) |
| Frontend | Django templates + HTMX | htmx 2.0.x | Inline grade editing, live validation, job-status polling, all without writing a JavaScript app. One codebase, one language for three people (D9) |
| UI kit | Bootstrap | 5.3.x | The team knows it from CSE 220. Built-in dark mode, responsive grid |
| Charts | Chart.js | 4.5.x | Radar, bar, line charts from JSON in a `<script>` tag. No build step |
| AI | Anthropic Python SDK + Claude | `anthropic` 1.x, `claude-opus-5-5` | Reads PDFs and images natively, returns schema-validated JSON (structured outputs) |
| Excel / CSV | openpyxl + stdlib `csv` | 3.1.x | Read and write `.xlsx` without pandas |
| Word files | python-docx | 1.2.x | Extract text from `.docx` syllabi |
| PDF export | WeasyPrint | current | HTML + CSS → PDF. Reuses our templates, so exports look like the site |
| Config | django-environ | 0.14.x | Twelve-factor settings from environment variables |
| Static files | WhiteNoise | 6.x | Serve static files from gunicorn without a separate server |
| App server | gunicorn | current | Standard WSGI server |
| Reverse proxy + HTTPS | Caddy | 2 | Automatic Let's Encrypt certificates with a 5-line config |
| Containers | Docker + Docker Compose | current | Same Postgres/Redis on every laptop; same images in staging and production |
| Testing | pytest, pytest-django, factory_boy, Hypothesis, coverage | current | Fixtures, factories, property-based tests for the engine |
| Lint / format | Ruff | 0.17.x | One fast tool replaces flake8, isort and black |
| CI/CD | GitHub Actions | — | Required by report Section 5 |
| Backlog | GitHub Projects | — | Lives next to the code, links issues to PRs automatically, has iteration fields and charts. Report Section 1 asks which tool we used |

**Vendor the frontend files.** Download Bootstrap, HTMX and Chart.js into `static/vendor/` instead of loading them from a CDN. University Wi-Fi on demo day is not something to depend on.

## 4.2 System diagram

```mermaid
flowchart LR
    subgraph Client
        B[Browser<br/>Django templates + HTMX + Chart.js]
    end
    subgraph Server["VPS (Docker Compose)"]
        C[Caddy<br/>HTTPS reverse proxy]
        W[web<br/>gunicorn + Django 6.1]
        K[worker<br/>Celery]
        R[(Redis<br/>cache + broker)]
        P[(PostgreSQL 17)]
        M[/media volume<br/>syllabi, uploads, exports/]
    end
    subgraph External["3rd-party services"]
        A[Claude API<br/>syllabus extraction]
        E[SMTP provider<br/>email]
    end
    B -- HTTPS --> C --> W
    W --> P
    W --> R
    W --> M
    W -- enqueue job --> R
    R -- deliver job --> K
    K --> P
    K --> M
    K -- PDF / image / text --> A
    K --> E
```

Put this diagram (rendered) in the CSE 321 report, Section 2. GitHub renders Mermaid in Markdown automatically.

## 4.3 Repository layout

```
polaris/                              ← repo root
├── POLARIS-PROJECT-SPEC.md           ← this file
├── README.md                         ← what it is, how to run it, screenshots
├── pyproject.toml                    ← dependencies + ruff + pytest config
├── uv.lock                           ← exact versions (committed)
├── .python-version                   ← 3.13
├── .env.example                      ← every env var, no real secrets
├── .pre-commit-config.yaml
├── compose.yml                       ← dev: postgres + redis only
├── compose.prod.yml                  ← staging/prod: caddy, web, worker, postgres, redis
├── Dockerfile
├── Caddyfile
├── manage.py
├── .github/
│   ├── workflows/ci.yml
│   ├── workflows/cd.yml
│   ├── ISSUE_TEMPLATE/user_story.yml
│   ├── ISSUE_TEMPLATE/bug.yml
│   └── pull_request_template.md
├── config/
│   ├── settings/base.py  dev.py  test.py  prod.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py  asgi.py
├── apps/
│   ├── core/          ← base templates, design system, template filters (|score), audit model, mixins
│   ├── accounts/      ← User, ProgramMembership, login, permissions.py, decorators
│   ├── catalog/       ← Program, ProgramOutcomeSet, ProgramOutcome, Term, Course, CourseOffering, Enrollment
│   ├── outcomes/      ← LearningOutcome, Assessment, AssessmentLOWeight, LOPOWeight, lint.py
│   ├── grading/       ← Grade, publish service, grade sheet, bulk upload
│   ├── scoring/       ← engine.py (pure), loaders.py, aggregates.py, snapshots (T2.3)
│   ├── ingestion/     ← IngestionJob, extraction.py (Claude), schemas.py, tasks.py, wizard views
│   └── reports/       ← student profile, course results, department dashboard, exports
├── templates/         ← base.html, 404.html, 500.html, includes/
├── static/            ← css/polaris.css, js/polaris.js, vendor/ (bootstrap, htmx, chart.js)
├── docs/
│   ├── process/       ← sprint-NN/ folders: board screenshots, burndown, retro notes; velocity.md
│   ├── diagrams/      ← exported architecture, class, ER diagrams
│   ├── reports/       ← CSE 311 + CSE 321 report sources
│   └── adr/           ← architecture decision records (one page each, optional)
└── seed/
    ├── syllabi/       ← sample syllabus PDFs for tests and the demo
    └── grades/        ← sample gradebook CSV/XLSX files
```

## 4.4 Layering rules

```
templates  →  views  →  services (writes) / selectors (reads)  →  models
                                    ↓
                            scoring.loaders → scoring.engine (pure)
```

1. **Views** parse the request, call one service or selector, render. No ORM queries beyond `get_object_or_404`, no business rules.
2. **Services** (`services.py`) perform every write: they validate, run inside `transaction.atomic()`, write audit events, and enqueue background jobs with `transaction.on_commit(...)` so a job never runs against a rolled-back transaction.
3. **Selectors** (`selectors.py`) perform every read that involves permissions or non-trivial queries, and always take `user`.
4. **The engine** never touches the database.
5. **Templates** never compute. They display what the view passed in, through the `|score` filter for numbers.

## 4.5 Key flows

### Publishing an assessment

```mermaid
sequenceDiagram
    actor I as Instructor
    participant V as grading.views.publish
    participant S as grading.services.publish_assessment
    participant DB as PostgreSQL
    participant Q as Celery (T2.3)
    I->>V: POST /offerings/7/assessments/3/publish/
    V->>S: publish_assessment(user, assessment)
    S->>DB: BEGIN
    S->>DB: SELECT … FROM assessment WHERE id=3 FOR UPDATE
    S->>DB: UPDATE grade SET published_score = score, published_at = now() WHERE assessment_id=3
    S->>DB: UPDATE assessment SET published_at = now(), published_by = I
    S->>DB: INSERT audit_event (action='publish', before/after counts)
    S->>DB: COMMIT
    S-->>Q: on_commit → refresh_scores(offering 7)
    V-->>I: 302 → grade sheet, "Midterm I published to 84 students"
```

`FOR UPDATE` locks the assessment row so two clicks (or two people) can't publish half-and-half. All-or-nothing: either every grade becomes visible or none does.

### Syllabus ingestion

```mermaid
sequenceDiagram
    actor I as Instructor
    participant W as ingestion views
    participant DB as PostgreSQL
    participant K as Celery worker
    participant C as Claude API
    I->>W: Upload syllabus.pdf for offering 7
    W->>DB: INSERT ingestion_job (status=PENDING, file)
    W-->>K: on_commit → extract_syllabus(job_id)
    W-->>I: "Reading your syllabus…" page (HTMX polls status every 2 s)
    K->>DB: status=PROCESSING
    K->>C: messages.create(PDF + PO list + JSON schema)
    C-->>K: JSON matching SyllabusExtraction
    K->>K: validate (Pydantic) + domain checks → warnings
    K->>DB: result=JSON, status=READY_FOR_REVIEW, tokens, cost
    I->>W: Poll → READY → editable preview
    I->>W: Edit, then "Apply to course"
    W->>DB: BEGIN; create LOs, assessments, both weight sets; audit; status=APPLIED; COMMIT
```

### Bulk grade upload

Upload file → parse (no DB writes) → match columns to assessments and rows to enrolled students → **dry-run report** (matched, unknown student numbers, duplicates, out-of-range, empty cells) → instructor confirms → one transaction writes draft grades + audit events. Nothing is published by an upload.

## 4.6 Settings and environment variables

| Variable | Example | Used for |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | Which settings file |
| `SECRET_KEY` | (50 random chars) | Sessions, CSRF. Different per environment |
| `DEBUG` | `False` | Never `True` outside dev |
| `ALLOWED_HOSTS` | `polaris.example.com` | Comma-separated |
| `CSRF_TRUSTED_ORIGINS` | `https://polaris.example.com` | Needed behind HTTPS proxy |
| `DATABASE_URL` | `postgres://polaris:pw@db:5432/polaris` | |
| `REDIS_URL` | `redis://redis:6379/0` | Cache + Celery broker |
| `ANTHROPIC_API_KEY` | `sk-ant-…` | Claude. **Never committed. Never in client-side code** |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | Overridable without a code change |
| `EMAIL_URL` | `smtp+tls://user:pw@smtp.provider.com:587` | Prod email. Dev uses the console backend |
| `DEFAULT_FROM_EMAIL` | `POlaris <noreply@…>` | |
| `SENTRY_DSN` | (optional, T2.10) | Error monitoring |

`.env.example` lists every variable with a dummy value. Real `.env` files are in `.gitignore`. CI uses GitHub Actions secrets.

## 4.7 Environments

| Environment | Where | Branch | Database | Purpose |
|---|---|---|---|---|
| Local | Each laptop | any | Postgres in Docker (`compose.yml`) | Development |
| CI | GitHub Actions runner | every PR + push | Postgres service container | Lint, tests, migration check |
| Staging | VPS, `staging.<host>` | `develop` (auto-deploy) | Own Postgres, demo seed data | Integration, sprint reviews, the TA can poke at it |
| Production | VPS, `<host>` | `main` (auto-deploy after approval) | Own Postgres, curated demo data | Checkpoints and final demo |

---

# PART 5: DATA MODEL

## 5.1 Entity-relationship diagram

```mermaid
erDiagram
    USER ||--o{ PROGRAM_MEMBERSHIP : has
    PROGRAM ||--o{ PROGRAM_MEMBERSHIP : has
    PROGRAM ||--o{ PROGRAM_OUTCOME_SET : versions
    PROGRAM_OUTCOME_SET ||--|{ PROGRAM_OUTCOME : contains
    PROGRAM ||--o{ COURSE : catalogs
    COURSE ||--o{ COURSE_OFFERING : "runs as"
    TERM ||--o{ COURSE_OFFERING : schedules
    USER }o--o{ COURSE_OFFERING : teaches
    COURSE_OFFERING ||--o{ ENROLLMENT : has
    USER ||--o{ ENROLLMENT : "enrolls in"
    COURSE_OFFERING ||--o{ LEARNING_OUTCOME : defines
    COURSE_OFFERING ||--o{ ASSESSMENT : defines
    ASSESSMENT ||--o{ ASSESSMENT_LO_WEIGHT : "feeds (%)"
    LEARNING_OUTCOME ||--o{ ASSESSMENT_LO_WEIGHT : "fed by"
    LEARNING_OUTCOME ||--o{ LO_PO_WEIGHT : "feeds (1-5)"
    PROGRAM_OUTCOME ||--o{ LO_PO_WEIGHT : "fed by"
    ASSESSMENT ||--o{ GRADE : has
    ENROLLMENT ||--o{ GRADE : has
    COURSE_OFFERING ||--o{ INGESTION_JOB : has
    USER ||--o{ AUDIT_EVENT : performs
```

The whole scoring graph is four tables: `ASSESSMENT_LO_WEIGHT` and `LO_PO_WEIGHT` are the weighted arrows from [Part 2](#part-2-the-scoring-method), `GRADE` holds the values at the left edge, and `PROGRAM_OUTCOME` is the right edge.

## 5.2 Models

Field names are final. Person A writes these in Sprint 1; anyone changing them later updates this section in the same PR.

### `apps/accounts/models.py`

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra["is_staff"] = True
        extra["is_superuser"] = True
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Identity only. What someone *is* lives in ProgramMembership (decision D6)."""
    username = None
    email = models.EmailField(unique=True)
    student_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"


class ProgramMembership(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"
        HEAD = "head", "Department Head"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    program = models.ForeignKey("catalog.Program", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=Role.choices)
    cohort_year = models.PositiveSmallIntegerField(null=True, blank=True)  # students only, e.g. 2023

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "program", "role"], name="uniq_membership"),
            models.CheckConstraint(
                condition=~Q(role="student") | Q(cohort_year__isnull=False),
                name="student_has_cohort",
            ),
        ]
```

`AUTH_USER_MODEL = "accounts.User"` must be in settings **before the first `migrate`**. Changing the user model after the first migration is one of the most painful things in Django. This is why it's Sprint 1, story 1.

### `apps/catalog/models.py`

```python
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Program(models.Model):
    code = models.CharField(max_length=16, unique=True)              # "CSE"
    name = models.CharField(max_length=200)                           # "Computer Science and Engineering"
    attainment_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("60"))

    def __str__(self):
        return self.code


class ProgramOutcomeSet(models.Model):
    """A versioned list of POs. Curricula change; students keep the set of their cohort."""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="po_sets")
    label = models.CharField(max_length=100)                          # "2023 curriculum"
    effective_from_year = models.PositiveSmallIntegerField()          # first cohort it applies to
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["program", "label"], name="uniq_po_set_label"),
            # partial unique index: at most one active set per program
            models.UniqueConstraint(fields=["program"], condition=Q(is_active=True),
                                    name="one_active_po_set_per_program"),
        ]


class ProgramOutcome(models.Model):
    po_set = models.ForeignKey(ProgramOutcomeSet, on_delete=models.CASCADE, related_name="outcomes")
    number = models.PositiveSmallIntegerField()                       # 1..11
    short_name = models.CharField(max_length=80)                      # "Teamwork"
    description = models.TextField()                                 # official wording

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["po_set", "number"], name="uniq_po_number"),
            models.CheckConstraint(condition=Q(number__gte=1) & Q(number__lte=30), name="po_number_range"),
        ]

    def __str__(self):
        return f"PO {self.number}"


class Term(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    code = models.CharField(max_length=10, unique=True)               # "2026F"
    name = models.CharField(max_length=40)                            # "Fall 2026"
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNED)

    class Meta:
        ordering = ["-starts_on"]
        constraints = [
            models.CheckConstraint(condition=Q(ends_on__gt=F("starts_on")), name="term_dates_ordered"),
        ]


class Course(models.Model):
    program = models.ForeignKey(Program, on_delete=models.PROTECT, related_name="courses")
    code = models.CharField(max_length=16)                            # "CSE 311"
    title = models.CharField(max_length=200)
    credits = models.DecimalField(max_digits=4, decimal_places=1)
    ects = models.DecimalField(max_digits=4, decimal_places=1)

    class Meta:
        ordering = ["code"]
        constraints = [models.UniqueConstraint(fields=["program", "code"], name="uniq_course_code")]


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="offerings")
    term = models.ForeignKey(Term, on_delete=models.PROTECT, related_name="offerings")
    section = models.CharField(max_length=8, default="1")
    instructors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="teaching", blank=True)
    syllabus = models.FileField(upload_to="syllabi/%Y/", null=True, blank=True)
    cloned_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "term", "section"], name="uniq_offering"),
        ]


class Enrollment(models.Model):
    class Status(models.TextChoices):
        ENROLLED = "enrolled", "Enrolled"
        DROPPED = "dropped", "Dropped"

    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="enrollments")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ENROLLED)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["offering", "student"], name="uniq_enrollment"),
        ]
        indexes = [models.Index(fields=["student"], name="enrollment_student_idx")]
```

### `apps/outcomes/models.py`

```python
from django.db import models
from django.db.models import Q


class Source(models.TextChoices):
    MANUAL = "manual", "Entered by hand"
    SYLLABUS = "syllabus", "Read from syllabus"
    AI_SUGGESTED = "ai_suggested", "Suggested by AI"
    CLONED = "cloned", "Cloned from a previous term"


class LearningOutcome(models.Model):
    offering = models.ForeignKey("catalog.CourseOffering", on_delete=models.CASCADE,
                                 related_name="learning_outcomes")
    number = models.PositiveSmallIntegerField()
    description = models.TextField()
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)

    class Meta:
        ordering = ["number"]
        constraints = [models.UniqueConstraint(fields=["offering", "number"], name="uniq_lo_number")]

    def __str__(self):
        return f"LO {self.number}"


class Assessment(models.Model):
    class Kind(models.TextChoices):
        MIDTERM = "midterm", "Midterm"
        FINAL = "final", "Final exam"
        PROJECT = "project", "Project"
        QUIZ = "quiz", "Quiz"
        HOMEWORK = "homework", "Homework"
        LAB = "lab", "Lab"
        PRESENTATION = "presentation", "Presentation"
        PARTICIPATION = "participation", "Attendance / participation"
        OTHER = "other", "Other"

    offering = models.ForeignKey("catalog.CourseOffering", on_delete=models.CASCADE,
                                 related_name="assessments")
    name = models.CharField(max_length=100)                           # "Midterm I"
    kind = models.CharField(max_length=16, choices=Kind.choices)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=100)
    course_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # share of the course grade, e.g. 25 (%). Informational; also the AI's default for assessment→LO weights
    due_date = models.DateField(null=True, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey("accounts.User", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["offering", "name"], name="uniq_assessment_name"),
            models.CheckConstraint(condition=Q(max_score__gt=0), name="max_score_positive"),
        ]


class AssessmentLOWeight(models.Model):
    """Arrow from an assessment to an LO. Weight in percent, 0 < w ≤ 100 (policy P1)."""
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="lo_weights")
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE,
                                         related_name="assessment_weights")
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assessment", "learning_outcome"], name="uniq_a_lo"),
            models.CheckConstraint(condition=Q(weight__gt=0) & Q(weight__lte=100), name="a_lo_weight_range"),
        ]


class LOPOWeight(models.Model):
    """Arrow from an LO to a PO. Integer 1..5 (policy P2). No row = no contribution."""
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, related_name="po_weights")
    program_outcome = models.ForeignKey("catalog.ProgramOutcome", on_delete=models.PROTECT,
                                        related_name="lo_weights")
    weight = models.PositiveSmallIntegerField()
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)
    rationale = models.TextField(blank=True)                          # filled by the AI suggestion (T1.3)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["learning_outcome", "program_outcome"], name="uniq_lo_po"),
            models.CheckConstraint(condition=Q(weight__gte=1) & Q(weight__lte=5), name="lo_po_weight_range"),
        ]
```

### `apps/grading/models.py`

```python
from django.conf import settings
from django.db import models
from django.db.models import Q


class Grade(models.Model):
    """One student's mark on one assessment.
    `score` is the instructor's working (draft) value. `published_score` is what students
    and every score calculation see. Publishing copies score → published_score (decision D2)."""
    assessment = models.ForeignKey("outcomes.Assessment", on_delete=models.CASCADE, related_name="grades")
    enrollment = models.ForeignKey("catalog.Enrollment", on_delete=models.CASCADE, related_name="grades")
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    is_excused = models.BooleanField(default=False)
    published_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    published_is_excused = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                   related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assessment", "enrollment"], name="uniq_grade"),
            models.CheckConstraint(condition=Q(score__isnull=True) | Q(score__gte=0), name="score_non_negative"),
        ]
        indexes = [models.Index(fields=["enrollment"], name="grade_enrollment_idx")]

    @property
    def has_unpublished_change(self) -> bool:
        return (self.score, self.is_excused) != (self.published_score, self.published_is_excused)
```

### `apps/core/models.py` (audit) and `apps/ingestion/models.py`

```python
# apps/core/models.py
from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)           # "grade.update", "assessment.publish", "lo_po.update", ...
    entity_type = models.CharField(max_length=40)      # "grade", "assessment", "lo_po_weight", ...
    entity_id = models.BigIntegerField()
    offering = models.ForeignKey("catalog.CourseOffering", null=True, on_delete=models.SET_NULL)
    before = models.JSONField(null=True)
    after = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["offering", "-created_at"], name="audit_offering_time_idx"),
            models.Index(fields=["entity_type", "entity_id"], name="audit_entity_idx"),
        ]


# apps/ingestion/models.py
class IngestionJob(models.Model):
    class Kind(models.TextChoices):
        SYLLABUS = "syllabus", "Syllabus"
        GRADES = "grades", "Grade file"

    class Status(models.TextChoices):
        PENDING = "pending", "Waiting"
        PROCESSING = "processing", "Reading"
        READY = "ready", "Ready for review"
        APPLIED = "applied", "Applied"
        FAILED = "failed", "Failed"
        DISCARDED = "discarded", "Discarded"

    offering = models.ForeignKey("catalog.CourseOffering", on_delete=models.CASCADE, related_name="ingestion_jobs")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    file = models.FileField(upload_to="uploads/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    result = models.JSONField(null=True, blank=True)    # validated extraction / parsed rows
    warnings = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)
    model = models.CharField(max_length=40, blank=True)
    request_id = models.CharField(max_length=64, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
```

## 5.3 Rules the database can't enforce (enforced in services, each with a test)

| Rule | Where |
|---|---|
| An `AssessmentLOWeight` connects an assessment and an LO **of the same offering** | `outcomes.services.save_assessment_lo_matrix` |
| An `LOPOWeight` points at a PO from **the active PO set of the offering's program** | `outcomes.services.save_lo_po_matrix` |
| A `Grade`'s assessment and enrollment belong to **the same offering** | `grading.services` (sheet save, bulk upload) |
| `score ≤ assessment.max_score` | Same. Over-max is rejected with a clear message ("Max for Midterm I is 100") |
| Nothing in a **closed term** changes | Every service calls `ensure_term_open(offering)` first |
| Deleting an assessment that has **published** grades is blocked | `outcomes.services.delete_assessment`. Instructor must un-publish first (audited) |
| Changing max_score after grades exist asks for confirmation and re-validates every grade | `outcomes.services.update_assessment` |
| Every change to a grade, weight, LO, assessment, or publish state writes an `AuditEvent` in the same transaction | All services, via `core.audit.record(...)` |

## 5.4 Audit trail

Decision D10: our own `AuditEvent` table rather than `django-simple-history`. Reasons: that package does not yet declare Django 6.1 support; all our writes already go through services, so recording an event is one line; and we control exactly what's stored (for a weight matrix save we record the whole before/after matrix as one event, which is what an auditor wants to read).

```python
# apps/core/audit.py
from .models import AuditEvent


def record(actor, action, entity, *, before=None, after=None, offering=None):
    AuditEvent.objects.create(
        actor=actor, action=action,
        entity_type=entity._meta.model_name, entity_id=entity.pk,
        offering=offering, before=before, after=after,
    )
```

`before` / `after` are JSON-safe dicts: convert `Decimal` to `str`, dates to ISO strings. Never store passwords or file contents.

## 5.5 Reporting tables (Tier 2, T2.3)

Normal pages compute scores on request through the engine. At department scale that's fast enough (≈ 400 students × 8 courses × 5 LOs). Precomputed tables make the dashboard instant and give CSE 321 Sections 3–4 real material:

| Table / view | Grain | Written by |
|---|---|---|
| `scoring_studentloscore` | one row per (enrollment, LO): score, coverage, computed_at | Celery task `refresh_scores(offering_id)` after publish or mapping change, using **the same engine** |
| `scoring_studentposcore` | one row per (student, PO, scope = cumulative or term) | Same task |
| `mv_course_po_coverage` (PostgreSQL **materialized view**) | one row per (offering, PO): Σ LO→PO weights, number of LOs | `REFRESH MATERIALIZED VIEW CONCURRENTLY` after mapping changes. Pure SQL aggregation of mapping tables, no scoring logic |
| `mv_po_attainment` (materialized view) | one row per (program, cohort, term, PO): students scored, students attaining, rate | Refreshed after `refresh_scores` |

The score tables are written by Python, not SQL, on purpose: scoring logic lives in exactly one place (the engine). The materialized views only *aggregate* already-computed numbers.

Seen as a warehouse, the reporting side is a **star schema**: the fact is a student's score on an outcome; the dimensions are student (with cohort), term, course/offering, learning outcome, program outcome. The operational tables (5.2) are normalised to 3NF. Say exactly this in CSE 321 Section 3.

## 5.6 CSE 321 hooks

These are implemented as we go, then written up for the CSE 321 report (Sections 3–5). Owner: Person A.

**Indexes**

| Index | Type | Serves |
|---|---|---|
| Every FK | B-tree (Django default) | Joins |
| `uniq_grade (assessment, enrollment)` | Unique B-tree | Grade sheet load, upsert on bulk upload |
| `grade_enrollment_idx` | B-tree | "All grades of this student" (profile) |
| `enrollment_student_idx` | B-tree | "All courses of this student" |
| `one_active_po_set_per_program` | **Partial** unique index (`WHERE is_active`) | Integrity + fast lookup of the active set |
| `audit_offering_time_idx (offering, created_at DESC)` | Composite B-tree | Audit viewer, newest first |
| `ingestion_job.result` | (optional) GIN on JSONB | Only if we ever query inside results. Probably not; say so |

Prove each with `EXPLAIN ANALYZE` on the seeded demo database and paste the plans into the report.

**Transactions and isolation levels**

| Operation | Transaction | Isolation / locking | Why |
|---|---|---|---|
| Publish an assessment | `atomic()` | READ COMMITTED + `SELECT … FOR UPDATE` on the assessment row | All grades flip together. Two concurrent publishes serialise on the lock |
| Save a weight matrix | `atomic()` | READ COMMITTED + `FOR UPDATE` on the offering row | The matrix is replaced as a whole. Concurrent saves by instructor and head can't interleave |
| Bulk grade upload commit | `atomic()` | READ COMMITTED | Whole file or nothing |
| Apply a syllabus extraction | `atomic()` | READ COMMITTED + `FOR UPDATE` on the offering | Creates LOs, assessments and two weight sets together |
| Close a term | `atomic()` | `FOR UPDATE` on the term row | No grade save can sneak in mid-close |
| Generate a department export | `atomic()` | **REPEATABLE READ** (`SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` as the first statement) | An export runs dozens of queries; all must see one consistent snapshot even if someone publishes meanwhile |

PostgreSQL's default isolation is READ COMMITTED. Explain in the report why that default is enough for writes once we add row locks, and why the export is the one place we need a stronger level.

**Scale, partitioning, replication, fault tolerance** (mostly discussion, with numbers)

- Acıbadem CSE: ≈ 400 students × ≈ 8 courses/term × ≈ 6 assessments ≈ 19,000 grades per term, ≈ 400,000 over 10 years. Indexes handle this easily, so we **don't partition**. Show the arithmetic and state the point where we would: the `grade` table partitioned by term (declarative range/list partitioning) once a whole university (≈ 15,000 students) uses it.
- Replication: describe a PostgreSQL streaming read replica for dashboards and exports. Not built.
- Fault tolerance we *do* build: Celery tasks retry with exponential backoff on Claude rate limits and 5xx; tasks are idempotent (re-running an extraction just overwrites `result`); Docker health checks restart dead containers; nightly `pg_dump` backup of production with a tested restore.

**Table sizes for CSE 321 Section 3** ("each table's final rows, columns and raw size"):

```sql
-- exact row counts: run SELECT count(*) per table for the final numbers
SELECT c.relname                                         AS table_name,
       s.n_live_tup                                      AS approx_rows,
       (SELECT count(*) FROM information_schema.columns col
         WHERE col.table_name = c.relname)               AS columns,
       pg_size_pretty(pg_relation_size(c.oid))           AS data_size,
       pg_size_pretty(pg_total_relation_size(c.oid))     AS total_with_indexes
FROM pg_class c
JOIN pg_stat_user_tables s ON s.relid = c.oid
ORDER BY pg_total_relation_size(c.oid) DESC;
```

---

# PART 6: FEATURE SPECIFICATIONS

Each feature lists: the user story, what the screen does, the rules, and **acceptance criteria (AC)**. A story is Done only when every AC passes, has a test, and works on staging ([Definition of Done](#92-definition-of-ready-and-done)). Story IDs (e.g. `S1-03`) refer to the backlog in [Part 12](#part-12-product-backlog).

## Baseline

### B1. Accounts and navigation

*As any user, I log in with my university email so that I see only what my role allows.*

- Email + password login (Django auth views, custom templates). Logout. Password reset by email (console backend in dev, SMTP in prod).
- No public sign-up. Accounts come from the head (enrollment import creates student accounts) or the admin.
- After login, redirect by role: student → My PO profile; instructor → My courses; head → Department overview. Multiple roles → a role switcher in the navbar.
- Navbar items are role-aware.

**AC**
1. A student logging in lands on their own profile; an instructor on their course list; a head on the department overview.
2. Wrong password shows a generic "Email or password is incorrect" (doesn't reveal whether the email exists).
3. Password reset email arrives (dev: printed in console) and the link works once.
4. A user with both instructor and head memberships can switch views without logging out.
5. Visiting any page while logged out redirects to login, then back to the requested page.

### B2. Program and PO management (Head)

*As the head, I maintain the program's POs so every score in the system refers to the official outcomes.*

- Data migration seeds program **CSE** with PO set "2023 curriculum" (active) containing the official 11 POs ([Appendix A](#appendix-a-the-11-program-outcomes)).
- Head can edit short names and descriptions, create a new PO set version (copy of the active one), and activate a version.
- POs that already have LO→PO weights cannot be deleted, only edited.

**AC**
1. Fresh install shows 11 POs with official wording.
2. Creating a new version copies all POs; activating it deactivates the old one (the partial unique index guarantees one active set).
3. Deleting a referenced PO is refused with a message naming the courses that use it.

### B3. Terms, catalog, offerings, enrollment (Head)

*As the head, I set up the term so instructors can start configuring their courses.*

- Terms: create, open, close, reopen (reopen asks for a reason, stored in the audit trail).
- Catalog: courses with code, title, credits, ECTS.
- Offerings: pick course + term (+ section), assign one or more instructors.
- Enrollment: add students manually, or **import a CSV** with columns `student_number,email,first_name,last_name,cohort_year`. Unknown students are created as accounts (with a student membership and an emailed set-password link in prod); known ones are matched by student number. Dry-run preview before commit, same pattern as T1.1.

**AC**
1. A head can go from empty term to an offering with an instructor and 30 enrolled students in under 5 minutes using the CSV import.
2. Import preview lists: new accounts, existing matches, rows with errors (missing email, duplicate student number in file). Nothing is written until "Confirm".
3. Closing a term makes every page of its offerings read-only, including for instructors.
4. The same student number twice in one offering is impossible (unique constraint) and the importer reports it as a duplicate instead of crashing.

### B4. Course setup: LOs and assessments (Instructor)

*As an instructor, I define my course's learning outcomes and assessments.*

- Offering setup page with two cards: Learning Outcomes (numbered list, add / edit / reorder / delete) and Assessments (name, kind, max score, course weight %, due date).
- A setup checklist at the top: ☐ LOs ☐ Assessments ☐ Assessment→LO weights ☐ LO→PO weights ☐ Students enrolled. Each item links to its section. Empty states explain what to do first (*The Blank Slate*, Getting Real Ch. 9).
- "Upload syllabus instead" button (T1.2) appears in the empty state.

**AC**
1. LO numbers are unique per offering; renumbering on reorder keeps them contiguous (1, 2, 3…).
2. Assessment course weights that don't sum to 100 show a warning, not an error.
3. Deleting an LO or assessment that has weights asks for confirmation and lists what will be removed.
4. Deleting an assessment with published grades is blocked (5.3).

### B5. The two weight matrices (Instructor)

*As an instructor, I connect assessments to LOs and LOs to POs so the system can compute scores.*

Two grid editors on the offering's **Mapping** tab.

```
Assessment → LO weights (%)            LO → PO weights (1–5, blank = none)
            LO1   LO2   LO3                     PO1 PO2 PO3 PO4 PO5 PO6 PO7 PO8 PO9 PO10 PO11
Midterm I   [60]  [40]  [  ]           LO1      [4] [ ] [2] [ ] [ ] [ ] [ ] [ ] [ ] [  ] [  ]
Project     [40]  [100] [50]           LO2      [2] [5] [ ] [ ] [ ] [3] [ ] [ ] [ ] [  ] [  ]
Final       [  ]  [  ]  [50]           LO3      [ ] [ ] [ ] [4] [ ] [ ] [ ] [ ] [ ] [  ] [  ]
            ───   ───   ───            PO cov.   6   5   2   4   0   3   0   0   0    0    0
```

- Blank cell = no arrow (no row stored). Typing a number creates it.
- Validation inline: A→LO 1–100, LO→PO integer 1–5. Invalid cells turn red with the reason in a tooltip; the Save button stays disabled.
- One Save button per grid; the whole grid saves in one transaction and one audit event (5.6).
- Hovering a PO column header shows the PO's full description, so instructors map against the real wording.
- Bottom row on the LO→PO grid: total weight per PO for this course (a mini coverage view).
- The head sees the same grids for any offering and can edit them (D13).

**AC**
1. Entering the Elif example (60/40, 40/100; 4/2 to PO1, 5 to PO2) and grades 90/80 produces LO1 86.0, LO2 82.9, PO1 85.0, PO2 82.9 on the results page.
2. Entering 0, 6, 2.5 or "abc" in the LO→PO grid is rejected with a clear message.
3. Saving after a teammate (the head) changed the grid in another tab shows "This mapping changed since you opened it" instead of silently overwriting (compare a version number / `updated_at` sent with the form).
4. After saving, mapping lint (B11) re-runs and shows its warnings above the grid.

### B6. Grade sheet (Instructor)

*As an instructor, I type grades into a spreadsheet-like table so data entry is fast.*

- Rows = enrolled students (student number, name). Columns = assessments. Cells = draft score.
- **HTMX inline save:** each cell posts on change (`hx-post`, `hx-trigger="change"`), the server validates and returns the cell partial (green tick or red error). Arrow keys and Enter move between cells (small JS in `polaris.js`).
- Per-cell "excused" toggle via a context menu or typing `EX`.
- Column header shows: max score, published / draft state, number of unpublished changes, **Publish** button.
- Cells with unpublished changes have a coloured dot.
- Sticky header and first column so an 80-student sheet stays usable.

**AC**
1. Typing 105 in a column with max 100 shows "Max for Midterm I is 100" and nothing is saved.
2. A saved draft grade is **not** visible to the student and does not affect any score.
3. 80 students × 6 assessments loads in under 1 second on the seeded staging database (one query for grades, no N+1: verify with `django-debug-toolbar` locally or `assertNumQueries` in a test).
4. Keyboard-only entry works: type, Enter, next row.

### B7. Publish grades and audit trail

*As an instructor, I publish an assessment when I'm sure of its grades, so students never see half-finished data.*

- Publish button per assessment column → confirmation modal: "Publish Midterm I to 84 students? 3 students have no grade (they will be skipped, not counted as zero)."
- Publishing copies `score → published_score` for every grade of that assessment in one transaction (4.5). Later edits are drafts again until the next publish ("3 unpublished changes").
- Unpublish (rare, e.g. wrong file uploaded) requires a reason; audited.
- Every write records an `AuditEvent` (5.4). The audit viewer UI is T1.4; in the baseline, events are visible in Django admin.

**AC**
1. Student view before publish: assessment shows "Not published yet". After: the score appears.
2. A crash halfway through publish (simulated in a test by raising inside the transaction) leaves zero grades published.
3. Editing a published grade does not change what the student sees until re-publish.
4. Every grade change, publish and unpublish appears in `AuditEvent` with actor, before and after.

### B8. Student PO profile v1

*As a student, I see my score for each PO and where it comes from.*

- Table of the 11 POs: number, short name (full description on hover/tap), score (`|score` filter), coverage bar, attainment badge (✓ ≥ threshold).
- Horizontal bar chart of the 11 scores (Chart.js), threshold line.
- Click a PO → drawer listing contributing (course, LO, LO score, weight) rows from `po_contributors`, so the student can answer "why is my PO 3 only 61?"
- Courses list: each enrolled offering with published assessments and LO scores; in-progress courses labelled.

**AC**
1. Elif (seed data) sees PO1 85.0 and PO2 82.9 for the slide example.
2. A PO with no evidence shows "—" and "No courses have contributed to this outcome yet", never 0.
3. A student requesting another student's profile URL gets 404.
4. Draft grades never appear.

### B9. Instructor course results

*As an instructor, I see how my class is doing on each LO.*

- Table: students × LOs with scores and coverage; class average row; distribution mini-histogram per LO.
- "This course's contribution to POs" panel: class-average PO scores computed from this offering only.

**AC**
1. Class average equals the mean of non-None student LO scores (test with seed data).
2. Only the instructor(s) of the offering and the head can open it.

### B10. Department overview v1 (Head)

*As the head, I see where the program stands on each PO.*

- Term selector (default: latest closed term, with "include open terms" toggle per P10).
- Per PO: average score across students, number of students with evidence, attainment rate vs. threshold.
- Offerings list with setup checklist status (which courses have no mapping or unpublished assessments).

**AC**
1. Numbers on the overview match a hand computation on a 3-student test fixture.
2. Toggling "include open terms" changes the numbers and the label says so.

### B11. Mapping lint

*As an instructor or head, I'm warned when a mapping is broken or suspicious.*

Rules (each a pure function in `apps/outcomes/lint.py`, each tested):

| Code | Severity | Rule |
|---|---|---|
| L001 | Error | An LO has no assessment feeding it (its score can never exist) |
| L002 | Error | An LO has no PO link (it contributes nothing to the program) |
| L003 | Warning | An assessment feeds no LO (its grades are ignored by every score) |
| L004 | Warning | An assessment's course weights don't sum to 100 across the offering |
| L005 | Warning | A single PO receives more than 60% of the course's total LO→PO weight (possible over-claiming) |
| L006 | Info | The course links to fewer than 2 POs |
| L007 | Warning | An LO→PO weight was AI-suggested and never edited or confirmed by a human |

**AC**
1. Each rule has a passing and a failing test case.
2. Lint results appear on the Mapping tab and as a badge on the course list.

### B12. Django admin and seed data

- Every model registered with sensible `list_display`, `list_filter`, `search_fields`, and inlines (LOs and assessments inline on offering).
- `manage.py seed_demo` builds the full demo dataset ([Appendix B](#appendix-b-demo-seed-data)). Idempotent: `--reset` wipes and rebuilds.

---

## Tier 1

### T1.1. Bulk grade upload

*As an instructor, I upload my gradebook file instead of typing 480 numbers.*

**Flow:** Upload (`.csv`, `.xlsx`) → **Map columns** → **Dry run** → Confirm → done.

1. **Upload.** Max 5 MB. The first sheet of an `.xlsx`, or a CSV (UTF-8 or Windows-1254 / Turkish Excel export: detect and decode).
2. **Map columns.** We auto-detect the student-number column (header contains "no", "number", "öğrenci" or values look like student numbers) and match other headers to assessment names (case/space-insensitive, then fuzzy with `difflib`). The instructor confirms or changes each mapping with dropdowns. Unmapped columns are ignored.
3. **Dry run.** No writes. Show a summary and a row-level table:
   - ✅ N grades will be created, M updated (show old → new), K unchanged
   - ⚠️ Students in the file not enrolled in this offering (listed)
   - ⚠️ Enrolled students missing from the file
   - ❌ Invalid values: non-numeric, negative, above max (cell reference like `C14`)
   - ❌ Duplicate student numbers in the file
   - Values `EX`, `M` (muaf), `excused` → excused
   - Turkish decimal commas (`85,5`) parsed as 85.5
4. **Confirm.** One transaction writes all valid rows as **drafts** + one audit event per changed grade. Errors block confirm unless the instructor ticks "skip invalid rows".
5. The uploaded file and the dry-run report are stored on an `IngestionJob(kind=GRADES)` for traceability.

**AC**
1. The sample files in `seed/grades/` (one clean, one messy with every error type) produce exactly the expected dry-run reports (golden tests).
2. Nothing is written before Confirm; nothing is published by an upload.
3. Re-uploading the same file is a no-op ("0 changes").
4. A 200-row file processes in under 2 seconds.

### T1.2. Syllabus ingestion wizard (flagship)

*As an instructor, I upload my syllabus and get my course set up in two minutes, reviewing everything before it's saved.*

Full design in [Part 7](#part-7-ai-syllabus-ingestion). Screens:

1. **Upload.** Drag-and-drop PDF, DOCX, PNG, JPG or WEBP (phone photo of a printed syllabus), max 20 MB. Shown in the empty state of a new offering and as a button on the setup page.
2. **Reading…** A progress page that polls job status every 2 s (`hx-trigger="every 2s"` on a status partial that stops polling once the job leaves PROCESSING). Typical 20–60 s. Shows "You can leave this page; we'll keep working."
3. **Review.** Four editable sections, pre-filled from the extraction:
   - Course info (code, title, credits, ECTS): compared with the offering's catalog data; mismatches highlighted.
   - Learning outcomes: editable list. Each has a "source" link that shows the quoted text from the syllabus.
   - Assessments: name, kind, max score, course weight %.
   - Both weight grids, same editors as B5. Cells are colour-coded: **from the document**, **derived** (rule in §7.6), **AI-suggested** (with a rationale tooltip).
   - Warnings from the extraction and from validation at the top ("Course weights sum to 90%", "LO 4 is not assessed by anything").
4. **Apply.** One transaction creates everything ([§4.5](#syllabus-ingestion)). If the offering already has LOs or assessments: allowed only when it has **no grades**, and the instructor must tick "Replace current setup". Otherwise refused with an explanation.
5. **Discard** at any point.

**AC**
1. On the 5 sample syllabi in `seed/syllabi/`, extraction finds every LO and every assessment (checked by the eval script, §7.9). Course weights are correct to the percent.
2. Nothing is written to the course until Apply.
3. A failed extraction (bad file, API down, refusal) ends in FAILED with a human message and a "Set up manually instead" link, never a 500.
4. Uploading an unrelated PDF (e.g. a restaurant menu) produces a FAILED job with "This doesn't look like a course syllabus", not invented outcomes.
5. Every created LO and weight carries `source` = `syllabus` or `ai_suggested`, visible in the UI and audit trail.
6. Each job records model, tokens, cost and the Claude `request_id`.

### T1.3. AI-suggested LO→PO weights

*As an instructor whose syllabus has no LO-level PO mapping, I get a suggested mapping with reasons I can accept or change.*

- Runs as part of the extraction (same Claude call, §7.4) when the document has no LO→PO table. Also available as a standalone button "Suggest PO weights" on the Mapping tab for courses set up by hand (separate small call with the LOs as text input).
- If the syllabus has a **course-level** PO contribution table (common in Bologna syllabi: "Contribution of the course to program outcomes, 1–5"), suggestions respect it: no LO→PO weight exceeds the course's stated level for that PO, and POs with level 0 get no links.
- Each suggested cell shows its one-sentence rationale on hover. Suggested cells stay flagged (lint L007) until a human edits or confirms them ("Accept all suggestions" button exists but is a deliberate click).

**AC**
1. Suggestions never use weights outside 1–5 or POs outside the active set (validated after the call; invalid entries dropped with a warning).
2. With a course-level table present, no suggestion exceeds it (test with a fixture extraction).
3. Accepting changes `source` to `manual`-confirmed; lint L007 clears.

### T1.4. Audit history viewer

*As an instructor or head, I see who changed what and when.*

- Per offering: a timeline filterable by type (grades, weights, setup, publish) and by person. Each entry: who, when, what, before → after.
- Per grade cell: right-click → "History" shows that grade's events.
- Head: program-wide audit view with the same filters.

**AC**
1. Changing a grade from 75 to 78 and publishing shows two events in order with the right actor.
2. Instructors only see their offerings' events.

### T1.5. Student profile v2

- **Radar chart** of the 11 POs with the threshold ring.
- **Per-course breakdown**: stacked contribution of each course to each PO (from `po_contributors`: weight × LO score share).
- **Trend**: PO scores per term (cumulative up to each term) as a line chart.
- Plain-language summary at the top, written by template logic (not AI): "Your strongest outcome is PO 2 (Problem solving, 88.4). PO 7 (Communication) has the least evidence so far: 1 course."

**AC**
1. Radar and table show identical numbers.
2. Trend for a student with 3 terms of seed data has 3 points per PO, each equal to a hand-checked cumulative calculation for one PO.

### T1.6. Department dashboard

*As the head, I see PO attainment by cohort and term, and which POs our curriculum under-covers.*

- **Attainment table and chart**: rows = POs, columns = cohorts (or terms); cell = attainment rate (% of students ≥ threshold), coloured against a target (default 70% of students attaining; head can change it). Click a cell → student list (head only).
- **Coverage heat map**: rows = courses, columns = POs, cell = Σ LO→PO weight for that course (from `mv_course_po_coverage` in T2.3, or a query before that). Column totals at the bottom. POs whose column total is below a threshold, or which are covered by only one course, are flagged "under-covered".
- **Completion panel**: per offering in the selected term, "% assessments published", "mapping complete?". (Reminder emails are T2.2.)
- Filters: term range, cohort, closed-terms-only toggle.

**AC**
1. Attainment rate for a fixture of 10 students (6 above threshold) shows 60%.
2. A PO linked by no course appears in the heat map with an "Not covered by any course" flag.
3. The dashboard loads in under 1.5 s on the seed dataset (otherwise do T2.3 earlier).

### T1.7. Exports

- **Course report** (instructor/head): PDF + Excel. Course info, mapping grids, per-LO class statistics, per-PO course contribution, lint status.
- **Department report** (head): PDF + Excel. Attainment table, coverage heat map, completion status, generated timestamp, filters used. Generated in a **REPEATABLE READ** transaction (5.6) so all numbers are from one snapshot.
- PDFs are rendered from HTML templates with WeasyPrint in a Celery task (can take a few seconds); the user gets a download link when ready. Excel via openpyxl with one sheet per section.

**AC**
1. Every number in the PDF equals the same number on screen (test: render both from the same context and compare a sample of values).
2. Opening the Excel file in Excel/LibreOffice shows numeric cells as numbers, not text.

---

## Tier 2 (short specs; expanded when pulled into a sprint)

| ID | Spec |
|---|---|
| T2.1 Clone setup | On a new offering: "Copy setup from Fall 2025" copies LOs, assessments (without dates) and both weight sets; `cloned_from` set; `source=cloned`. No grades copied |
| T2.2 Completion tracker + reminders | Head picks a deadline; Celery beat sends a daily email to instructors with unpublished assessments or incomplete mappings after the deadline. Opt-out per instructor. Every email logged |
| T2.3 Precomputed scores | Tables and materialized views from 5.5; `refresh_scores` task after publish / mapping save; dashboard reads from them; a management command rebuilds everything; a test asserts snapshot == live engine result for the seed data |
| T2.4 PO transcript PDF | Student downloads a one-page PDF: PO table, radar, courses contributing, generation date, verification code. Same WeasyPrint pipeline |
| T2.5 TR / EN | `{% translate %}` / `gettext` everywhere, `LocaleMiddleware`, language switcher, Turkish `.po` file. PO descriptions in both languages (second field) |
| T2.6 Multi-program UI | Program switcher; head of one program can't see another's data; seed a second program (e.g. Biomedical Engineering) to prove it |
| T2.7 Mapping approval | Changing a mapping on a course with published grades puts it into "pending approval"; scores keep using the last approved version until the head approves. Needs a mapping version table: bigger change, plan carefully |
| T2.8 TA role | `OfferingAssistant` relation; TAs enter drafts, cannot publish or change weights; matrix test extended |
| T2.9 OBS import | Paste an OBS Bologna course URL; the worker fetches the page, extracts text, runs the same extraction with an HTML/text input. Verify early that OBS pages are reachable from the server |
| T2.10 Monitoring | Sentry SDK in web + worker; uptime check pinging `/healthz` |

## Tier 3 (stretch; only with spare velocity)

What-if simulator (T3.1), anonymous cohort comparison (T3.2), course recommendations for a weak PO (T3.3), university SSO via OIDC (T3.4), read-only REST API with OpenAPI docs (T3.5).

---

# PART 7: AI SYLLABUS INGESTION

The flagship feature. Owner: Person A (extraction service, schemas, eval), Person B (wizard screens). Built in Sprints 5–6.

## 7.1 What it does

An instructor uploads a syllabus (PDF, Word, or phone photo). Claude reads it and returns structured data: course info, learning outcomes, assessments with weights, which assessments measure which LOs, any PO mapping the document contains, and suggested LO→PO weights where it contains none. Our code validates the result, the instructor reviews and edits it, and only then is anything saved.

**Design principle: the AI proposes, a human disposes.** Nothing the model returns is ever written to the course without an explicit Apply click on a screen that shows every value and where it came from.

## 7.2 Pipeline

```
upload ──► IngestionJob(PENDING) ──on_commit──► Celery: extract_syllabus(job_id)
                                                   │
                                                   ├─ 1. load file, detect type, build content blocks
                                                   ├─ 2. call Claude (structured output = SyllabusExtraction)
                                                   ├─ 3. handle stop reasons (refusal, max_tokens)
                                                   ├─ 4. domain validation → warnings / dropped items
                                                   ├─ 5. derive missing assessment→LO weights (§7.6)
                                                   └─ 6. save result + tokens + cost → READY (or FAILED)
wizard review (human edits) ──Apply──► one transaction: LOs, assessments, weights, audit ──► APPLIED
```

## 7.3 Input handling

| File type | How it's sent to Claude |
|---|---|
| PDF | Native `document` block, base64. Claude sees text *and* page images, so tables and scanned pages work. Limits: 32 MB request, 600 pages. We cap uploads at 20 MB |
| PNG / JPG / WEBP | `image` block, base64. Phone photos: we downscale to max 2000 px on the long side with Pillow first (cheaper, same accuracy) |
| DOCX | `python-docx` extracts paragraphs **and tables** to text in reading order; sent as a `text` block wrapped in `<syllabus>` tags |
| Anything else (HEIC, DOC, PPTX…) | Rejected at upload with "Please export as PDF or JPG" |

Validate type by content (magic bytes via the file header), not by extension.

## 7.4 Output schema

`apps/ingestion/schemas.py`. These Pydantic models are both the instruction to Claude (structured outputs turn them into a JSON schema the response must match) and the validator of what comes back.

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict

AssessmentKind = Literal["midterm", "final", "project", "quiz", "homework", "lab",
                         "presentation", "participation", "other"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")   # → additionalProperties: false


class ExtractedLO(Strict):
    number: int
    description: str
    source_quote: str               # verbatim text from the document supporting this LO


class ExtractedAssessment(Strict):
    name: str                       # "Midterm I"
    kind: AssessmentKind
    course_weight_percent: float | None   # share of the course grade, e.g. 25.0
    max_score: float | None         # usually None (→ 100)
    measures_lo_numbers: list[int]  # LOs this assessment measures, if the document says so
    measures_stated_in_document: bool
    source_quote: str


class ExtractedLOPOLink(Strict):
    lo_number: int
    po_number: int                  # 1..11
    weight: int                     # 1..5
    stated_in_document: bool        # True: read from a table. False: suggested by the model
    rationale: str                  # one sentence; required when suggested


class CoursePOContribution(Strict):
    po_number: int
    level: int                      # 0..5 as printed in a Bologna "contribution to program outcomes" table


class SyllabusExtraction(Strict):
    is_course_syllabus: bool        # False → we fail the job with a friendly message
    course_code: str | None
    course_title: str | None
    credits: float | None
    ects: float | None
    language: str | None
    learning_outcomes: list[ExtractedLO]
    assessments: list[ExtractedAssessment]
    course_po_contributions: list[CoursePOContribution]
    lo_po_links: list[ExtractedLOPOLink]
    warnings: list[str]             # ambiguities the model noticed, in plain English
```

Numeric ranges (1–5, 1–11, 0–100) are deliberately **not** in the schema: structured outputs don't support `minimum`/`maximum`, so we check them in step 4 instead.

## 7.5 Calling Claude

`apps/ingestion/extraction.py`. Model `claude-opus-5-5` (configurable via `ANTHROPIC_MODEL`), adaptive thinking (always on for this model), effort `high` because mapping outcomes to POs is judgment, not just copying. **Refusal fallback is on** (`fallbacks: "default"`): if a safety classifier declines a request by mistake, the API retries it on a fallback model inside the same call instead of failing.

```python
import base64
from pathlib import Path

import anthropic
from django.conf import settings

from .schemas import SyllabusExtraction
from .prompts import SYSTEM_PROMPT, build_instruction

_client = anthropic.Anthropic(timeout=300.0, max_retries=2)   # SDK retries 429/5xx/connection errors


class ExtractionError(Exception):
    """Non-retryable: shown to the instructor as a friendly message."""


def _content_blocks(path: Path, media_type: str, po_list_text: str) -> list[dict]:
    data = path.read_bytes()
    if media_type == "application/pdf":
        doc = {"type": "document",
               "source": {"type": "base64", "media_type": "application/pdf",
                          "data": base64.standard_b64encode(data).decode()}}
    elif media_type in {"image/png", "image/jpeg", "image/webp"}:
        doc = {"type": "image",
               "source": {"type": "base64", "media_type": media_type,
                          "data": base64.standard_b64encode(data).decode()}}
    else:  # DOCX already converted to text by the caller
        doc = {"type": "text", "text": f"<syllabus>\n{data.decode('utf-8')}\n</syllabus>"}
    return [doc, {"type": "text", "text": build_instruction(po_list_text)}]


def extract_syllabus(path: Path, media_type: str, po_list_text: str):
    response = _client.beta.messages.parse(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _content_blocks(path, media_type, po_list_text)}],
        output_format=SyllabusExtraction,
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        extra_body={"fallbacks": "default"},
    )
    if response.stop_reason == "refusal":
        raise ExtractionError("The document could not be processed. Please set up the course manually.")
    if response.stop_reason == "max_tokens":
        raise ExtractionError("This document is too long to read in one pass. Upload only the syllabus pages.")
    return response.parsed_output, response
```

The caller (the Celery task) stores `response.usage.input_tokens`, `response.usage.output_tokens`, `response.model` and `response._request_id` on the job.

> **Sprint 5 spike, first hour:** run this against one real syllabus from a Django shell before building anything around it. Confirm (1) the helper accepts `output_config={"effort": ...}` together with `output_format=…` (if it raises, drop the effort line; the model then uses its default effort), (2) the fallback parameter is accepted on the account's API key, (3) `parsed_output` validates. Record what you found in the PR description.

**Celery task and retries** (`apps/ingestion/tasks.py`):

```python
@shared_task(bind=True, autoretry_for=(anthropic.RateLimitError, anthropic.InternalServerError,
                                      anthropic.APIConnectionError, anthropic.APITimeoutError),
             retry_backoff=30, retry_backoff_max=600, max_retries=4)
def run_syllabus_extraction(self, job_id: int):
    job = IngestionJob.objects.get(pk=job_id)
    if job.status not in {IngestionJob.Status.PENDING, IngestionJob.Status.PROCESSING}:
        return                                    # idempotent: already done or discarded
    job.status = IngestionJob.Status.PROCESSING
    job.save(update_fields=["status", "updated_at"])
    try:
        extraction, response = extract_syllabus(...)
        result, warnings = validate_and_derive(extraction, job.offering)   # §7.6
    except ExtractionError as e:
        mark_failed(job, str(e)); return
    except anthropic.BadRequestError as e:
        mark_failed(job, "The file could not be read. Is it a valid PDF or image?", detail=str(e)); return
    save_ready(job, result, warnings, response)
```

The SDK already retries quick blips twice; Celery retries longer outages with backoff (30 s, 60 s, 120 s… capped at 10 min). After the last retry the job is marked FAILED with "The AI service is unavailable right now. Try again later or set up the course manually."

**System prompt** (`apps/ingestion/prompts.py`, version it with a constant `PROMPT_VERSION` stored on each job):

```text
You extract structured course information from a university course syllabus so that a
department can track Program Outcome scores. The syllabus may be in English or Turkish;
always answer in the syllabus's own language for descriptions and quotes.

Rules:
- Only report learning outcomes and assessments that the document actually contains.
  Never invent them. Every learning outcome and assessment must have a verbatim
  source_quote from the document.
- If the document is not a course syllabus, set is_course_syllabus to false and leave
  the lists empty.
- Number learning outcomes in the order the document lists them, starting at 1.
- course_weight_percent is the assessment's share of the final course grade as printed.
- measures_lo_numbers: fill it only from an explicit statement or table in the document,
  and set measures_stated_in_document to true. If the document is silent, propose the
  learning outcomes each assessment most plausibly measures and set it to false.
- course_po_contributions: copy the "contribution of the course to program outcomes"
  table if the document has one (levels 0-5). Otherwise return an empty list.
- lo_po_links: if the document maps learning outcomes to program outcomes, copy that
  mapping with stated_in_document true. Otherwise suggest links with
  stated_in_document false, using weights 1-5 where 5 means the learning outcome is a
  central, directly assessed part of the program outcome. Suggest only clear links,
  usually 1-3 per learning outcome. Never exceed the course-level contribution level
  for that program outcome when one is given. Give a one-sentence rationale per link.
- Put anything ambiguous or contradictory in warnings, in plain English.
```

The user turn carries the document, then the instruction with the program's active POs listed as `PO 1: <full description>` … `PO 11: …` so the model maps against the official wording.

## 7.6 Validation and derivation (step 4–5)

Pure functions in `apps/ingestion/validation.py`, fully unit-tested with recorded extraction fixtures (no API calls in tests).

| Check | Action |
|---|---|
| `is_course_syllabus` is false | FAIL: "This doesn't look like a course syllabus" |
| No learning outcomes found | FAIL: "We couldn't find learning outcomes. Set up manually or upload the page that lists them" |
| LO numbers duplicated or not 1..n | Renumber in document order; warning |
| Assessment references an LO number that doesn't exist | Drop that reference; warning |
| PO number outside the active PO set | Drop the link; warning |
| LO→PO weight outside 1–5 | Clamp to 1–5; warning |
| Suggested link exceeds course-level contribution level | Lower it to the level; drop it if level is 0; warning |
| Course weights don't sum to 100 (±1) | Keep; warning |
| `max_score` missing | 100 |

**Deriving assessment→LO weights.** Syllabi say *which* LOs an assessment measures, almost never *what percentage*. Our rule: **the weight of the arrow from assessment *a* to LO *l* is *a*'s course weight.** So a midterm worth 25% of the grade contributes with weight 25 to every LO it measures, and a project worth 40% contributes with weight 40. The effect: each LO's score is an average of the assessments that measure it, weighted the same way they are in the course grade. That's the most defensible default without extra information, it's easy to explain, and the instructor can change any cell before applying. If course weights are missing, every arrow gets weight 100 (equal). Derived cells are coloured differently in the review screen.

## 7.7 Cost

Pricing for `claude-opus-5-5`: $4 per million input tokens, $20 per million output tokens (thinking is billed as output).

| Item | Estimate |
|---|---|
| Typical 4–6 page PDF syllabus | ≈ 10,000–20,000 input tokens (PDF pages cost roughly 1,500–3,000 tokens each, text plus image) |
| Output: JSON + thinking | ≈ 4,000–12,000 tokens |
| **Per syllabus** | **≈ $0.15–0.35, typically $0.20–0.30** |
| Development + eval runs + demo (≈ 150 calls) | ≈ $30–45 for the semester |

These are estimates; the job table records real token counts, so we'll know the true cost after the first week. Put a **monthly spend limit** on the Anthropic Console workspace (e.g. $50) so a bug can't burn money. The key belongs to the team account, stored only in GitHub secrets and the server's `.env`.

If cost becomes a problem: switch `ANTHROPIC_MODEL` to `claude-sonnet-5-5` ($2 / $10) and re-run the eval to check accuracy holds. One env var, no code change.

## 7.8 Privacy and safety

- **Claude only ever sees syllabi** (decision D11). Student names, numbers and grades are never sent. Bulk grade upload (T1.1) is parsed by our own code, no AI.
- Syllabi are public course documents, so there's no personal data in them beyond the instructor's name.
- The API key lives only on the server and in CI secrets. It is never in the repo, in templates or in browser JavaScript.
- **Prompt injection** (a document containing "ignore your instructions and…"): the model has no tools, its output is forced into our schema, every value is shown to a human before saving, and nothing it returns is ever executed or rendered as HTML (Django auto-escapes). The worst a malicious document can do is propose wrong outcomes that the instructor then sees.
- Uploaded files are stored under random names; the original name is kept only for display.

## 7.9 Evaluation

LLM features need measurement, not vibes. `apps/ingestion/evals/`:

- `syllabi/`: 5 real syllabi with different shapes. Start with our own **CSE 311 syllabus** (4 LOs, an assessment table, no PO mapping), plus public Acıbadem course pages saved as PDF, ideally one Turkish, one with a Bologna PO contribution table, one scanned/photographed.
- `expected/<name>.json`: hand-labelled correct answers (Person A + one other person agree on each).
- `manage.py eval_extraction --runs 3`: runs each syllabus 3 times and prints:

| Metric | Definition | Target |
|---|---|---|
| LO recall | expected LOs found (text similarity ≥ 0.8) | 100% |
| LO precision | found LOs that are real | 100% |
| Assessment recall | expected assessments found by name | 100% |
| Course weight accuracy | assessments with the right % | ≥ 95% |
| Stated mapping accuracy | document-stated LO→PO links copied exactly | 100% |
| Suggestion agreement | suggested links within ±1 of a human mapping, on POs both chose | report only |
| Stability | identical LO lists across the 3 runs | report only |

Run it when the prompt or model changes, before each checkpoint, and before the demo. **Not in CI** (costs money, needs the key). Paste a results table into the CSE 311 final report: it's strong evidence for "test in the wild".

## 7.10 Tests (no network)

- `test_validation.py`: every row of the §7.6 table, using fixture `SyllabusExtraction` objects.
- `test_derivation.py`: course weights → arrow weights; missing weights → 100.
- `test_tasks.py`: `extract_syllabus` monkeypatched to return a fixture, raise `ExtractionError`, raise `anthropic.RateLimitError` (retries) and `BadRequestError` (fails). Job ends in the right status every time.
- `test_apply.py`: applying a reviewed extraction creates exactly the expected rows in one transaction, and a failure midway leaves the offering untouched.

---

# PART 8: UI AND UX

Owner of the design system: Person C. Everyone builds screens with it.

## 8.1 Principles (with the Getting Real chapters they come from)

1. **Interface first** (*Interface First*, Ch. 9). Sketch every screen on paper or in a shared Excalidraw board before writing its view. The wireframes below are the starting point.
2. **Epicenter first** (*Epicenter Design*, Ch. 9). Build the core of each page first: the grade grid, the weight grid, the PO table. Navigation, headers and footers come after.
3. **Three states for every screen** (*Three State Solution*, Ch. 9): regular (data), blank (first use: say what to do next, with a button), error (what went wrong, what to do). Every template has all three; reviewers check for them.
4. **Copy is interface** (*Copywriting is Interface Design*, Ch. 9). Short, specific, human. "Midterm I published to 84 students" beats "Operation successful".
5. **Real words in seed data** (*Use Real Words*, Ch. 11). Turkish names, real-looking course codes, realistic grade distributions. Never "Lorem ipsum" or "Student 1".
6. **Numbers are always explainable.** Any score can be clicked to show where it came from.

## 8.2 Design system

- Bootstrap 5.3 with a small override file `static/css/polaris.css`. Light + dark mode via `data-bs-theme`.
- **Colour tokens** (CSS custom properties): `--pl-primary` (navy, actions), `--pl-accent` (amber, highlights), and fixed semantic colours: attained (green), below threshold (red), no evidence (grey), draft/unpublished (amber dot), AI-suggested (violet), derived (teal), from document (blue). Never use colour alone: every coloured state also has an icon or label (accessibility).
- **Typography**: system font stack; tabular numerals (`font-variant-numeric: tabular-nums`) for every score column so digits line up.
- **Components** (`templates/includes/`): `score_badge`, `coverage_bar`, `empty_state`, `lint_list`, `confirm_modal`, `po_tooltip`, `toast`, `setup_checklist`, `weight_grid`, `job_status`.
- **The `|score` template filter** is the only way a score is printed: 1 decimal, half-up, "—" for None (P7, P12).
- Every interactive element is reachable by keyboard; every form field has a `<label>`; contrast meets WCAG AA. Check with Lighthouse before each checkpoint.
- Responsive: student pages must work on a phone (students will check on their phones). Instructor grids are desktop-first but scroll horizontally on tablets.

## 8.3 Page and URL map

| URL | Page | Roles |
|---|---|---|
| `/login/`, `/logout/`, `/password-reset/…` | Auth | all |
| `/` | Role-based redirect | all |
| `/me/` | My PO profile (B8, T1.5) | student |
| `/me/courses/<offering_id>/` | My grades and LO scores in one course | student |
| `/me/transcript.pdf` | PO transcript (T2.4) | student |
| `/teaching/` | My courses (current term first) with setup checklist badges | instructor, head |
| `/offerings/<id>/` | Offering home: checklist, quick stats | instructor (own), head |
| `/offerings/<id>/setup/` | LOs + assessments (B4) | instructor (own), head |
| `/offerings/<id>/mapping/` | Both weight grids + lint (B5, B11) | instructor (own), head |
| `/offerings/<id>/grades/` | Grade sheet (B6, B7) | instructor (own), head |
| `/offerings/<id>/grades/upload/` | Bulk upload flow (T1.1) | instructor (own), head |
| `/offerings/<id>/syllabus/` and `/ingestion/<job_id>/…` | Syllabus wizard (T1.2) | instructor (own), head |
| `/offerings/<id>/results/` | Course results (B9) | instructor (own), head |
| `/offerings/<id>/history/` | Audit viewer (T1.4) | instructor (own), head |
| `/offerings/<id>/export/{pdf,xlsx}/` | Course report (T1.7) | instructor (own), head |
| `/department/` | Department overview / dashboard (B10, T1.6) | head |
| `/department/students/<user_id>/` | Any student's profile | head |
| `/department/outcomes/` | PO sets and POs (B2) | head |
| `/department/terms/`, `/department/courses/`, `/department/offerings/` | Catalog management (B3) | head |
| `/department/enrollments/import/` | Enrollment CSV import (B3) | head |
| `/department/export/{pdf,xlsx}/` | Department report (T1.7) | head |
| `/healthz` | Health check (returns 200 + DB/Redis status) | public |
| `/admin/` | Django admin | admin |

This table is also the input list for the permission matrix test (§3.4).

## 8.4 Key screens (wireframes)

**Student profile (`/me/`)**

```
┌────────────────────────────────────────────────────────────────────────────┐
│ POlaris                         My profile   My courses        Elif Y. ▾  │
├────────────────────────────────────────────────────────────────────────────┤
│ Your strongest outcome is PO 2 Problem solving (88.4).                     │
│ PO 7 Communication has the least evidence so far: 1 course.                │
│                                                                            │
│   ┌──────── radar of 11 POs ────────┐   PO   Outcome           Score  Cov. │
│   │        (threshold ring at 60)   │   1    Math & science     85.0  ████ │
│   │                                 │   2    Problem solving    88.4  ████ │
│   │                                 │   …                                 │
│   └─────────────────────────────────┘   7    Communication      71.2  █░░░ │
│                                         11   Health & safety       —  ░░░░ │
│  [ Terms ▾ Cumulative ]    click any row → "where this number comes from"  │
├────────────────────────────────────────────────────────────────────────────┤
│ Courses  CSE 311 Software (Fall 2026, in progress) · CSE 321 … · MAT 241 … │
└────────────────────────────────────────────────────────────────────────────┘
```

**Syllabus review (T1.2, step 3)**

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Review what we read from CSE311_syllabus.pdf          [Discard] [Apply ▶] │
│ ⚠ Course weights sum to 100% ✓   ⚠ LO 4 is not measured by any assessment │
├────────────────────────────────────────────────────────────────────────────┤
│ Learning outcomes                                     legend: ■ document   │
│  1 [Learn design choices & philosophy behind …]  ⓘ source   ■ derived     │
│  2 [Learn agile-SD methodology & best practices…] ⓘ source  ■ AI-suggested │
│  + add                                                                     │
│ Assessments            kind      max   course %                            │
│  [Midterm I]          [midterm]  [100]  [25]                               │
│  [Project]            [project]  [100]  [40]                               │
│ Assessment → LO (%)        LO→PO (1–5)            PO1 PO2 PO3 PO4 … PO11  │
│            LO1 LO2 LO3      LO1                    [ ] [ ] [3] [4]        │
│  Midterm I [25][25][  ]     LO2   hover: "Agile    [ ] [ ] [ ] [ ] [2]…   │
│  Project   [40][40][40]           practice is …"                           │
└────────────────────────────────────────────────────────────────────────────┘
```

**Department dashboard (T1.6)**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Department · CSE        Terms [2025F – 2026S ▾]  Cohort [All ▾]  ☑ closed only│
├──────────────────────────────────────────────────────────────────────────────┤
│ PO attainment (≥ 60)      2022    2023    2024     target 70%                │
│ PO 1 Math & science        82%     78%     74%                               │
│ PO 7 Communication         61% ▼   58% ▼   —        ← below target           │
├──────────────────────────────────────────────────────────────────────────────┤
│ Coverage heat map  (Σ LO→PO weight)    PO1 PO2 PO3 … PO9 PO10 PO11           │
│ CSE 311 Software                         2   5   6     3    9    0           │
│ CSE 321 Data Systems                     4   8   7     0    2    0           │
│ …                                                                            │
│ Total                                   31  44  39     4   18    0  ⚠ PO 11  │
│                                                         ⚠ PO 9 only 1 course │
├──────────────────────────────────────────────────────────────────────────────┤
│ Fall 2026 completion: 14/22 courses fully published   [Export PDF] [Excel]   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 8.5 HTMX patterns we use (and only these)

| Pattern | Where | How |
|---|---|---|
| Inline cell save | Grade sheet, weight grids | `hx-post` on `change`, server returns the cell partial (`{% partialdef cell %}`), `hx-swap="outerHTML"` |
| Live validation | Forms | `hx-post` to a `?validate=1` variant, returns the field partial with errors |
| Polling | Ingestion job status, export status | Status partial with `hx-trigger="every 2s"`; when done the server returns a partial without the trigger, so polling stops |
| Modal content | Confirm publish, history drawer | `hx-get` into a Bootstrap modal body |

`django-htmx` adds `request.htmx` so one view can return either the full page or just the partial. Include the CSRF token via `hx-headers` on `<body>`.

---

# PART 9: HOW WE WORK (the CSE 311 part)

CSE 311 grades *how* we work: backlog, sprints, velocity, branching, CI/CD, testing. Most of it is invisible unless we **capture evidence while we work**. Every rule below exists for one of two reasons: it makes us faster, or it produces something a report section needs. Each rule says which.

## 9.1 Scrum for a team of three

| Element | How we do it | Report section it feeds |
|---|---|---|
| **Sprint length** | 1 week, Monday 00:00 → Sunday 23:59. Sprint 1 starts Mon 19 Oct | S2 sprint duration and count |
| **Product Owner** | Person A. Orders the backlog, writes acceptance criteria, says "done or not done" at review | S2 division of work |
| **Scrum Master** | Person C. Runs the meetings, guards the board, updates `velocity.md`, removes blockers | S2 |
| **Sprint planning** | Monday evening, 45 min, online is fine. Pull stories from the top of the backlog until the forecast (§9.4) is reached. Split each story into tasks (checkboxes in the issue). Assign owners | S1 backlog management, S2 |
| **Daily stand-up** | **Async**, by 11:00 every day, in the team chat's `#standup` thread: *Yesterday · Today · Blockers*, one line each. Plus a 10-minute in-person sync after the Tuesday lecture | S1 "team meetings" |
| **Backlog refinement** | Thursday, 20 min. Next sprint's top stories get acceptance criteria and a planning-poker estimate | S2 difficulty assessment |
| **Sprint review** | Sunday, 30 min. Demo the sprint's stories **on staging**, not on a laptop. Record a 2–3 min screen capture of the new features | S1, presentation |
| **Retrospective** | Right after review, 15 min. *Start · Stop · Continue*. Pick **one** action item and put it in the next sprint as a task | S6 Getting Real (*Rinse and Repeat*, Ch. 6) |
| **Release** | After review: merge `develop` → `main` (a release PR), tag `v0.<sprint>.0`, production deploys | S4, S5 |

Why async stand-ups: three students with different timetables can't meet daily. *Meetings Are Toxic* (Getting Real, Ch. 7) argues for exactly this. The written thread is also evidence.

## 9.2 Definition of Ready and Done

**Ready** (a story may enter a sprint only if):
- [ ] Written as a user story: *As a … I want … so that …*
- [ ] Acceptance criteria listed (copy from Part 6 where they exist)
- [ ] Estimated in story points by planning poker
- [ ] Small enough: ≤ 8 points. 13 means split it
- [ ] Dependencies are done or in the same sprint

**Done** (a story counts toward velocity only if all are true):
- [ ] Every acceptance criterion passes
- [ ] Tests written and green in CI; coverage did not drop below 85%
- [ ] Ruff clean
- [ ] Reviewed and approved by another team member
- [ ] Merged to `develop` and **working on staging**
- [ ] Blank and error states exist for any new screen (§8.1)
- [ ] Spec updated if behaviour differs from this document
- [ ] Issue closed, card in Done

Partly done stories count **zero** points this sprint and carry over with their full estimate. This keeps velocity honest.

## 9.3 Backlog tool: GitHub Projects

**Why GitHub Projects** (report Section 1 asks which tool and why): it lives next to the code, issues link to PRs and close automatically on merge, it has iteration and number fields for sprints and points, and its history *is* our evidence. Trello or Jira would need manual syncing.

**Set up once in Sprint 0 (Person C):**

1. Create an organization-level or repo-level Project named **POlaris Backlog**.
2. Fields:

| Field | Type | Values |
|---|---|---|
| Status | Single select | Backlog · Ready · In Progress · In Review · Done |
| Sprint | Iteration | 1 week, first iteration starts Mon 19 Oct 2026 (create Sprint 0 manually for 16–18 Oct) |
| Points | Number | 1, 2, 3, 5, 8 (13 = must split) |
| Area | Single select | Engine & Data · Instructor · Platform & Insights · Process |
| Tier | Single select | Baseline · Tier 1 · Tier 2 · Tier 3 · Chore |
| Priority | Single select | P0 · P1 · P2 |

3. Views: **Board** (grouped by Status, filtered to the current Sprint), **Backlog** (table sorted by Priority, then Tier), **By person** (table grouped by Assignee, current Sprint), **Roadmap** (by Sprint).
4. Built-in workflows: *Item added → Backlog*, *Pull request merged → Done*, *Item closed → Done*.
5. Labels: `story`, `bug`, `chore`, `spike`, `docs`.
6. Milestones (dates): *CSE 321 checkpoint* 12 Nov, *CSE 311 checkpoint* 17 Nov, *Feature complete* 6 Dec, *Final demo* 29 Dec.
7. Import the backlog from [Part 12](#part-12-product-backlog) as issues (a small script with `gh issue create` per row, or by hand: about an hour).

**Issue template** `.github/ISSUE_TEMPLATE/user_story.yml`:

```yaml
name: User story
description: A feature from the user's point of view
labels: ["story"]
body:
  - type: input
    id: story_id
    attributes:
      label: Story ID (from the spec backlog)
      placeholder: S2-04
  - type: textarea
    id: story
    attributes:
      label: User story
      value: "As a <role>, I want <capability> so that <benefit>."
    validations:
      required: true
  - type: textarea
    id: ac
    attributes:
      label: Acceptance criteria
      value: |
        - [ ] 
        - [ ] 
    validations:
      required: true
  - type: textarea
    id: tasks
    attributes:
      label: Tasks
      value: |
        - [ ] Tests
        - [ ] Implementation
        - [ ] Blank + error states
        - [ ] Spec updated if needed
  - type: textarea
    id: notes
    attributes:
      label: Notes / links to spec sections
```

**PR template** `.github/pull_request_template.md`:

```markdown
Closes #

## What changed
<!-- one or two sentences -->

## How to test
1.

## Checklist
- [ ] Tests added / updated, `uv run pytest` green
- [ ] `uv run ruff check . && uv run ruff format --check .` clean
- [ ] Migrations included (if models changed)
- [ ] Blank and error states (if new screen)
- [ ] Screenshot / GIF (if UI)
- [ ] Spec updated (if behaviour differs)
```

## 9.4 Estimating difficulty

Report Section 2 asks *how we assessed the difficulty of features*. Our answer: **relative estimation in story points with planning poker**, calibrated against reference stories.

- Scale: Fibonacci **1, 2, 3, 5, 8**. 13 or more means split the story.
- Points measure size and uncertainty together, not hours.
- **Planning poker:** everyone picks a card privately (physical cards, or planningpokeronline.com), reveals at once. If the spread is more than two steps (e.g. 2 vs 8), the highest and lowest explain their reasoning and we vote again. Record the final number **and** the first-round spread in the issue: the spread is great report material ("the syllabus wizard started at 5 / 8 / 13 because…").

**Reference stories** (our ruler):

| Points | Reference |
|---|---|
| 1 | Register a model in the admin with list filters |
| 2 | A simple CRUD form, e.g. terms (B3 part) |
| 3 | A read-only page with a non-trivial query, template, three states and tests, e.g. course results (B9) |
| 5 | An interactive HTMX feature with validation, e.g. one weight grid (B5) |
| 8 | A multi-step flow with file parsing and a dry run, e.g. bulk upload (T1.1) |

**Capacity and forecast.** About 10 focused hours per person per normal sprint, about 5 in light sprints (exam / checkpoint weeks). Sprint 1's forecast is a guess (≈ 24 points). From Sprint 2 on, use **yesterday's weather**: forecast = average velocity of the last 3 sprints, halved for light sprints.

## 9.5 Velocity and evidence capture

`docs/process/velocity.md`:

```markdown
| Sprint | Dates | Forecast | Committed | Completed | Carried over | Notes |
|---|---|---|---|---|---|---|
| 0 | 16–18 Oct | – | 12 | | | setup |
| 1 | 19–25 Oct | 24 | | | | |
```

**Velocity** = sum of points of stories that met the Definition of Done by Sunday 23:59.

**End-of-sprint evidence checklist** (Scrum Master, Sunday, 10 minutes). Save into `docs/process/sprint-NN/`:

- [ ] Screenshot of the Board view (current sprint) at start (Monday) and end (Sunday)
- [ ] Screenshot of the Project's Insights chart for the sprint (burn-up)
- [ ] Link to the review screen recording
- [ ] `retro.md`: start / stop / continue + the action item
- [ ] Row added to `velocity.md`
- [ ] Release PR merged and tag pushed; link to the green CD run

At the checkpoint and in the final report, this folder becomes Section 2 almost by copy-paste, and the presentation gets a velocity chart (completed points per sprint, bar chart, forecast line).

## 9.6 Branching model

Report Section 4 asks for our branching model and any development / release / deployment branches. We use a **simplified Git Flow** with one long-lived branch per environment.

```mermaid
gitGraph
    commit id: "init"
    branch develop
    checkout develop
    commit id: "skeleton"
    branch feature/12-engine
    checkout feature/12-engine
    commit id: "test: Elif golden"
    commit id: "engine passes"
    checkout develop
    merge feature/12-engine id: "squash #12"
    branch feature/15-grade-sheet
    checkout feature/15-grade-sheet
    commit id: "grade sheet"
    checkout develop
    merge feature/15-grade-sheet id: "squash #15"
    checkout main
    merge develop id: "release v0.1.0" tag: "v0.1.0"
    checkout develop
    commit id: "sprint 2 work"
    checkout main
    branch hotfix/31-login
    commit id: "fix"
    checkout main
    merge hotfix/31-login tag: "v0.1.1"
    checkout develop
    merge hotfix/31-login
```

| Branch | Purpose | Deploys to | Rules |
|---|---|---|---|
| `main` | What's in production. Every commit on it is a release | Production | No direct pushes. Only release PRs from `develop` and hotfix PRs. 1 approval, CI green |
| `develop` | Integration branch. **Set as the repo's default branch** | Staging | No direct pushes. PRs from feature/fix branches. 1 approval, CI green |
| `feature/<issue>-<slug>` | One story | — | Branch from `develop`, short-lived (≤ 3 days), deleted after merge |
| `fix/<issue>-<slug>` | A bug found on staging | — | Same as feature |
| `hotfix/<issue>-<slug>` | A bug in production that can't wait for the next release | — | Branch from `main`, PR into `main`, then merge `main` back into `develop` |
| `release/<version>` (optional) | Stabilise before a checkpoint (e.g. `release/0.4` before 12 Nov) | Staging | Only bug fixes. Merged into `main` and back into `develop` |

**Merge strategy.** Feature → `develop`: **squash merge** (one clean commit per story, titled with the issue number). `develop` → `main`: **merge commit** (keeps the history, marks the release point).

**Branch protection (Settings → Branches → add rule)** for `main` and `develop`: require a pull request, 1 approval, dismiss stale approvals on new commits, require status checks `lint` and `test` to pass, require branches to be up to date, no force pushes, no deletions.

> **The contribution chart trap (report Section 3).** GitHub's *Contributors* graph and *Code frequency* only count commits on the **default branch**, and only commits whose author email matches a GitHub account. So: (1) make `develop` the default branch so the charts update every day, not once a week; (2) every member runs `git config --global user.email` and checks it matches an email verified on their GitHub account **before the first commit**; (3) squash merges are attributed to the PR author, so whoever writes the code opens the PR. When pair programming, rotate who drives and add `Co-authored-by:` trailers.

## 9.7 Code review

Every PR gets one reviewer who isn't the author. Review within 24 hours; if you can't, say so in chat. Reviewers check:

1. Does it do what the issue's acceptance criteria say? Pull the branch and click through if it has UI.
2. Are there tests, and do they test behaviour (not implementation details)?
3. Is logic in services/selectors, not views/templates? Any score computed outside the engine?
4. Permissions: decorator on every new view? New URL added to the permission matrix test?
5. Any `float` for a score or weight? Any rounding outside `|score`?
6. Blank and error states?
7. Migrations: reversible, no data loss, committed?

Comment kindly and specifically. "Nit:" prefix for optional style points. Approve when it's good enough, not perfect (*Done!*, Getting Real Ch. 6).

## 9.8 Testing strategy

| Layer | Tool | What we test | Target |
|---|---|---|---|
| Engine (`scoring/engine.py`) | pytest + Hypothesis | Every policy P1–P12, golden numbers from the slides, properties (§2.6). **Written test-first (TDD)** | 100% line + branch |
| Validation / parsing (lint, bulk upload parser, extraction validation) | pytest | Every rule, with good and bad fixtures. Golden-file tests for upload dry-run reports | ≥ 95% |
| Services | pytest-django + factory_boy | Writes, transactions (rollback on failure), audit events, permission and term-lock rules | ≥ 90% |
| Views | Django test client | Status codes, redirects, right template, HTMX partial responses, query counts on heavy pages (`django_assert_max_num_queries`) | ≥ 80% |
| Permissions | Parametrised matrix test | Every URL × every role (§3.4) | every URL |
| End-to-end (Sprint 7) | `pytest-playwright` | 3 golden paths: instructor sets up course and publishes; student sees profile; head exports report | 3 tests, run nightly + before releases |
| AI extraction | Eval script (§7.9) | Accuracy on real syllabi | Not in CI |

Overall coverage gate: **85%** (`fail_under` in `pyproject.toml`). CI fails below it.

**TDD for the engine.** For each policy: (1) write the failing test and commit (`test: missing grades are skipped (red)`), (2) write the minimal code and commit (`engine: skip missing sources (green)`), (3) refactor. These commits are evidence for the Week 11 TDD topic and make a good presentation slide.

**Factories** (`apps/<app>/tests/factories.py`): one per model. A `scenario` helper builds the Elif example in one line, used by many tests:

```python
def elif_scenario():
    """Offering with 2 assessments, 2 LOs, 2 POs, weights and grades from the professor's slide."""
    ...
    return SimpleNamespace(offering=..., student=..., midterm=..., project=..., lo1=..., lo2=..., po1=..., po2=...)
```

## 9.9 CI pipeline

`.github/workflows/ci.yml`. Runs on every pull request, and is called by the CD workflow on every push to `develop` and `main` (so pushes aren't tested twice).

```yaml
name: CI

on:
  pull_request:
  workflow_call:

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
      - run: uv sync --locked
      - name: Ruff lint
        run: uv run ruff check --output-format=github .
      - name: Ruff format
        run: uv run ruff format --check .

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_USER: polaris
          POSTGRES_PASSWORD: polaris
          POSTGRES_DB: polaris
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U polaris"
          --health-interval 5s --health-timeout 5s --health-retries 10
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 5s --health-timeout 3s --health-retries 10
    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      DATABASE_URL: postgres://polaris:polaris@localhost:5432/polaris
      REDIS_URL: redis://localhost:6379/0
      SECRET_KEY: ci-not-a-secret
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
      - run: uv sync --locked
      - name: Django system checks
        run: uv run python manage.py check
      - name: Migrations are committed
        run: uv run python manage.py makemigrations --check --dry-run
      - name: Tests with coverage
        run: uv run pytest --cov --cov-report=xml --cov-report=term-missing --junitxml=junit.xml
      - name: Coverage summary on the run page
        if: always()
        run: uv run coverage report --format=markdown >> "$GITHUB_STEP_SUMMARY"
      - uses: actions/upload-artifact@v7
        if: always()
        with:
          name: test-reports
          path: |
            coverage.xml
            junit.xml

  deploy-check:
    runs-on: ubuntu-latest
    env:
      DJANGO_SETTINGS_MODULE: config.settings.prod
      SECRET_KEY: ci-only-but-long-enough-to-pass-the-deploy-check-0123456789abcdef
      DATABASE_URL: sqlite:///tmp/check.db
      REDIS_URL: redis://localhost:6379/0
      ALLOWED_HOSTS: example.com
      CSRF_TRUSTED_ORIGINS: https://example.com
      EMAIL_URL: consolemail://
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10
      - run: uv sync --locked --no-dev
      - name: Production settings pass Django's deployment checklist
        run: uv run --no-dev python manage.py check --deploy --fail-level WARNING

  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: docker/setup-buildx-action@v4
      - name: Image builds
        uses: docker/build-push-action@v7
        with:
          context: .
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

In GitHub branch protection, mark `lint`, `test`, `deploy-check` and `docker-build` as required checks.

## 9.10 CD pipeline and hosting

### Hosting decision (D14)

One small Linux VPS (Ubuntu 24.04, 2 vCPU, 2–4 GB RAM) running Docker Compose, with **staging and production side by side** and one Caddy in front of both. Why: it's cheap (≈ €5/month, or free with student credits: check the current GitHub Student Developer Pack offers), we control the whole stack (needed for Celery, Redis, WeasyPrint system libraries, and the CSE 321 architecture discussion), and the CD pipeline is real: build an image, push it, deploy it, migrate, smoke-test. Free platform tiers tend to lack background workers or expire databases after a few weeks.

Hostnames: a cheap domain (≈ $10/year) or a free DuckDNS subdomain, e.g. `polaris-cse.duckdns.org` and `staging-polaris-cse.duckdns.org`. Caddy gets HTTPS certificates automatically.

### Server layout

```
/srv/edge/compose.yml           ← Caddy only, ports 80/443, joins the "edge" network
/srv/edge/Caddyfile
/srv/polaris/staging/           ← compose.prod.yml + .env (STACK=staging)
/srv/polaris/production/        ← compose.prod.yml + .env (STACK=production)
/srv/backups/                   ← nightly pg_dump files
```

`/srv/edge/Caddyfile`:

```
staging-polaris-cse.duckdns.org {
    encode zstd gzip
    reverse_proxy staging-web:8000
}

polaris-cse.duckdns.org {
    encode zstd gzip
    reverse_proxy production-web:8000
}
```

Uploaded files (syllabi, grade files, exports) are **not** served by Caddy. Django serves them through views that check permissions (`FileResponse`), because a grade file must never be downloadable by URL guessing.

### `.github/workflows/cd.yml`

```yaml
name: CD

on:
  push:
    branches: [develop, main]
  workflow_dispatch:

concurrency:
  group: cd-${{ github.ref }}
  cancel-in-progress: false

permissions:
  contents: read
  packages: write

jobs:
  ci:
    uses: ./.github/workflows/ci.yml

  build:
    needs: ci
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.meta.outputs.image }}
    steps:
      - uses: actions/checkout@v7
      - id: meta
        run: echo "image=ghcr.io/${GITHUB_REPOSITORY,,}" >> "$GITHUB_OUTPUT"
      - uses: docker/setup-buildx-action@v4
      - uses: docker/login-action@v4
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v7
        with:
          context: .
          push: true
          tags: |
            ${{ steps.meta.outputs.image }}:${{ github.sha }}
            ${{ steps.meta.outputs.image }}:${{ github.ref_name }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.ref_name == 'main' && 'production' || 'staging' }}
      url: https://${{ vars.SITE_HOST }}
    steps:
      - name: Deploy over SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            set -euo pipefail
            cd /srv/polaris/${{ vars.STACK }}
            echo "${{ secrets.GHCR_READ_TOKEN }}" | docker login ghcr.io -u "${{ secrets.GHCR_USER }}" --password-stdin
            sed -i "s|^IMAGE=.*|IMAGE=${{ needs.build.outputs.image }}|; s|^IMAGE_TAG=.*|IMAGE_TAG=${{ github.sha }}|" .env
            docker compose -f compose.prod.yml pull web worker
            docker compose -f compose.prod.yml run --rm web python manage.py migrate --noinput
            docker compose -f compose.prod.yml up -d --remove-orphans
            docker image prune -f
      - name: Smoke test
        run: |
          for i in $(seq 1 20); do
            curl -fsS "https://${{ vars.SITE_HOST }}/healthz" && exit 0
            sleep 6
          done
          echo "Health check failed" && exit 1
```

**GitHub setup for CD (Person C, Sprint 2):**

- Settings → Environments: create `staging` and `production`. Each gets variables `STACK` (`staging` / `production`) and `SITE_HOST`, and the secrets `SSH_HOST`, `SSH_USER`, `SSH_KEY` (a deploy key made only for this), `GHCR_USER`, `GHCR_READ_TOKEN` (a fine-grained token with *read packages* only).
- On `production`, add a required reviewer if the repo plan allows it (public repos, or GitHub Pro/Team). Otherwise the protection is the approved release PR into `main`.

**Rollback:** set `IMAGE_TAG` in the server's `.env` back to the previous commit SHA and run `docker compose -f compose.prod.yml up -d`. Migrations must therefore be backwards-compatible for one release (add columns nullable first, remove them a release later).

**Report Section 5** needs these two YAML files plus "a summary of particular runs". At each sprint's end, the Scrum Master copies one CI run (with its coverage summary table) and one CD run (with deploy duration and smoke test result) into `docs/process/sprint-NN/runs.md`. Include at least one **failed** run and how we fixed it. A red build caught by CI is the best possible evidence that CI is doing its job.

---

# PART 10: SETUP GUIDE

## 10.1 Prerequisites (everyone, before Sprint 0 ends)

| Tool | Install (macOS) | Check |
|---|---|---|
| Git | comes with Xcode command-line tools | `git --version` |
| uv | `brew install uv` (or `curl -LsSf https://astral.sh/uv/install.sh \| sh`) | `uv --version` |
| Docker Desktop | docker.com | `docker compose version` |
| GitHub CLI (optional, handy) | `brew install gh` | `gh auth status` |
| Editor | VS Code or PyCharm with the Ruff extension | |

Windows teammates: use WSL2 (Ubuntu) for everything above. It avoids line-ending and path problems.

**Git identity (do this first, see §9.6):**

```bash
git config --global user.name  "Your Name"
git config --global user.email "the-email-verified-on-your-github-account@example.com"
```

## 10.2 Repository bootstrap (Person C, once, Sprint 0)

```bash
# 1. Clone the empty repo registered on 13 Oct
git clone https://github.com/<org>/<repo>.git polaris && cd polaris

# 2. Python project with uv
uv init --bare --python 3.13
uv python pin 3.13
uv add "django~=6.1" "psycopg[binary]~=3.3" django-environ "celery[redis]~=5.6" \
       django-htmx anthropic pydantic openpyxl python-docx pillow weasyprint \
       whitenoise gunicorn
uv add --dev pytest pytest-django pytest-cov factory-boy hypothesis faker \
       ruff pre-commit django-debug-toolbar pytest-playwright

# 3. Django project + apps
uv run django-admin startproject config .
mkdir -p apps && touch apps/__init__.py
for app in core accounts catalog outcomes grading scoring ingestion reports; do
  mkdir apps/$app && uv run python manage.py startapp $app apps/$app
done
# then in every apps/<app>/apps.py change   name = "<app>"   to   name = "apps.<app>"

# 4. Split settings (see 10.3), add compose.yml, .env.example, .gitignore, pre-commit
mkdir config/settings && git mv config/settings.py config/settings/base.py 2>/dev/null || mv config/settings.py config/settings/base.py
touch config/settings/__init__.py

# 5. First commit on main, then create develop and make it the default branch
git add -A && git commit -m "Bootstrap Django 6.1 project with uv"
git push -u origin main
git switch -c develop && git push -u origin develop
gh repo edit --default-branch develop
```

Copy this spec into the repo root as `POLARIS-PROJECT-SPEC.md` in the same first PR.

## 10.3 Key configuration files

### `pyproject.toml` (tool sections; dependencies are written by `uv add`)

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
extend-exclude = ["*/migrations/*"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "DJ", "S", "SIM"]

[tool.ruff.lint.per-file-ignores]
"**/tests/**" = ["S101", "S106"]   # assert and hard-coded test passwords are fine in tests

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"

[tool.coverage.run]
source = ["apps"]
branch = true
omit = ["*/migrations/*", "*/tests/*"]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = true
```

### `config/settings/base.py` (the parts that differ from the generated file)

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent      # three levels now: settings/ → config/ → repo
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.outcomes",
    "apps.grading",
    "apps.scoring",
    "apps.ingestion",
    "apps.reports",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {"default": env.db("DATABASE_URL")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"           # BEFORE the first migrate. Never change later.
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"

CACHES = {"default": {
    "BACKEND": "django.core.cache.backends.redis.RedisCache",
    "LOCATION": env("REDIS_URL"),
}}

CELERY_BROKER_URL = env("REDIS_URL")
CELERY_TASK_ACKS_LATE = True                 # a crashed worker's task is redelivered
CELERY_TASK_TIME_LIMIT = 15 * 60

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024

ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", default="claude-opus-5-5")
# ANTHROPIC_API_KEY is read by the SDK directly from the environment
```

### `config/settings/dev.py`, `test.py`, `prod.py`

```python
# dev.py
from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_EAGER", default=True)  # noqa: F405  run tasks inline until Sprint 5
```

```python
# test.py
from .base import *  # noqa: F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]   # fast tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
STORAGES = {**STORAGES, "staticfiles": {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
```

```python
# prod.py
from .base import *  # noqa: F403

DEBUG = False
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")  # noqa: F405
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")   # Caddy terminates HTTPS
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600                   # raise to 1 year once everything works
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SILENCED_SYSTEM_CHECKS = ["security.W021"]   # HSTS preload list: not appropriate for a student project domain
vars().update(env.email_url("EMAIL_URL"))  # noqa: F405  sets EMAIL_BACKEND, EMAIL_HOST, ...
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="POlaris <noreply@example.com>")  # noqa: F405
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

### `config/celery.py` and `config/__init__.py`

```python
# config/celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
app = Celery("polaris")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ("celery_app",)
```

Also change `manage.py`, `config/wsgi.py` and `config/asgi.py` to default to `config.settings.dev` / `config.settings.prod` respectively (wsgi/asgi → prod).

### `compose.yml` (local development: only the services, Django runs on your machine)

```yaml
services:
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: polaris
      POSTGRES_PASSWORD: polaris
      POSTGRES_DB: polaris
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U polaris"]
      interval: 5s
      retries: 10
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
volumes:
  pgdata:
```

Why Django runs outside Docker locally: instant auto-reload, debugger works, no rebuilds. Postgres and Redis in Docker: same versions as production, nothing to install.

### `.env.example`

```bash
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=dev-only-change-me
DEBUG=True
DATABASE_URL=postgres://polaris:polaris@localhost:5432/polaris
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-opus-5-5
CELERY_EAGER=True
# production / staging only:
# ALLOWED_HOSTS=polaris-cse.duckdns.org
# CSRF_TRUSTED_ORIGINS=https://polaris-cse.duckdns.org
# EMAIL_URL=smtp+tls://user:password@smtp.provider.com:587
# STACK=production
# COMPOSE_PROJECT_NAME=polaris-production
# IMAGE=ghcr.io/<org>/<repo>
# IMAGE_TAG=<commit sha>
```

### `.gitignore` (additions to GitHub's Python template)

```
.env
media/
staticfiles/
*.sqlite3
.coverage
coverage.xml
junit.xml
.DS_Store
```

### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.17.1
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: check-merge-conflict
      - id: check-added-large-files
        args: [--maxkb=5000]
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

### Health check view (`apps/core/views.py`)

```python
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    status = {"db": "ok", "cache": "ok"}
    try:
        connection.ensure_connection()
    except Exception:  # noqa: BLE001
        status["db"] = "down"
    try:
        cache.set("healthz", "1", 5)
    except Exception:  # noqa: BLE001
        status["cache"] = "down"
    code = 200 if all(v == "ok" for v in status.values()) else 503
    return JsonResponse(status, status=code)
```

## 10.4 Teammate setup (everyone else, ~15 minutes)

```bash
git clone https://github.com/<org>/<repo>.git polaris && cd polaris
uv sync                                   # installs Python 3.13 if needed + all packages
cp .env.example .env                      # then ask the team for the shared dev ANTHROPIC_API_KEY (Sprint 5+)
docker compose up -d                      # Postgres + Redis
uv run python manage.py migrate
uv run python manage.py seed_demo         # demo program, courses, students, grades (Sprint 1+)
uv run python manage.py createsuperuser
uv run pre-commit install                 # ruff runs on every commit
uv run python manage.py runserver         # http://localhost:8000
uv run pytest                             # everything green?
```

From Sprint 5 on, run the Celery worker in a second terminal when working on background jobs:

```bash
CELERY_EAGER=False uv run celery -A config worker -l info
```

## 10.5 Production image and stack

### `Dockerfile`

```dockerfile
FROM python:3.13-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# WeasyPrint needs Pango and HarfBuzz
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN DJANGO_SETTINGS_MODULE=config.settings.prod SECRET_KEY=build-only \
    DATABASE_URL=sqlite:////tmp/build.db REDIS_URL=redis://localhost:6379/0 \
    CSRF_TRUSTED_ORIGINS=https://build.local EMAIL_URL=consolemail:// \
    python manage.py collectstatic --noinput

RUN useradd --create-home app && mkdir -p /app/media && chown -R app /app
USER app
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
```

### `compose.prod.yml` (same file for staging and production; the `.env` next to it differs)

```yaml
services:
  web:
    image: ${IMAGE}:${IMAGE_TAG}
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
    volumes: [media:/app/media]
    depends_on:
      db: {condition: service_healthy}
      redis: {condition: service_healthy}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"]
      interval: 30s
      retries: 3
    networks:
      default: {}
      edge:
        aliases: ["${STACK}-web"]

  worker:
    image: ${IMAGE}:${IMAGE_TAG}
    command: celery -A config worker -l info --concurrency 2
    env_file: .env
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.prod
    volumes: [media:/app/media]
    depends_on:
      db: {condition: service_healthy}
      redis: {condition: service_healthy}
    restart: unless-stopped

  db:
    image: postgres:17
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes: [pgdata:/var/lib/postgresql/data]
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10

volumes:
  media:
  pgdata:

networks:
  edge:
    external: true
```

The server `.env` also sets `COMPOSE_PROJECT_NAME=polaris-staging` (or `-production`) so the two stacks never share containers or volumes. A Celery beat service for scheduled reminders is added with T2.2.

## 10.6 Server setup (Person C, Sprint 2, about 2 hours)

1. Create the VPS (Ubuntu 24.04). Add your SSH key. Point both hostnames at its IP.
2. `ssh root@<ip>`, then: create a user `deploy`, add it to the `docker` group, disable password SSH login, enable the firewall (`ufw allow 22,80,443/tcp && ufw enable`).
3. Install Docker Engine with the official instructions for Ubuntu (docs.docker.com → Install → Ubuntu).
4. `docker network create edge`, then create `/srv/edge/` with a compose file running `caddy:2` on ports 80/443, joined to `edge`, mounting the Caddyfile from §9.10 and a volume for certificates. `docker compose up -d`.
5. Create `/srv/polaris/staging/` and `/srv/polaris/production/`, each with `compose.prod.yml` and a real `.env` (strong random `SECRET_KEY`, `POSTGRES_PASSWORD`, `ANTHROPIC_API_KEY`, hosts).
6. Generate a deploy SSH key pair; add the public key to `deploy`'s `authorized_keys`; put the private key in the GitHub environments as `SSH_KEY`.
7. Push to `develop`; watch CD deploy staging. Then `docker compose -f compose.prod.yml exec web python manage.py seed_demo`.
8. **Backups** (production): a cron job as `deploy` at 03:00:

```bash
cd /srv/polaris/production && docker compose -f compose.prod.yml exec -T db \
  pg_dump -U polaris polaris | gzip > /srv/backups/polaris-$(date +\%F).sql.gz \
  && find /srv/backups -name 'polaris-*.sql.gz' -mtime +14 -delete
```

Do one **restore drill** before the CSE 321 checkpoint (restore the dump into staging) and write down how long it took. That's CSE 321 "fault tolerance" material.

---

# PART 11: SPRINT-BY-SPRINT PLAN

Each sprint lists its goal, the stories (IDs from [Part 12](#part-12-product-backlog), ordered: **the bottom ones drop first** if velocity is lower than the forecast), key how-to notes, and a checkpoint of what must work on staging by Sunday.

```
Oct            Nov                                      Dec
16  19   26    2    9    16   23   30    7    14   21   28
│S0 │ S1 │ S2 │ S3 │ S4 │ S5 │ S6 │ S7 │ S8 │ S9 │ S10│Demo
│set│core│inst│base│lite│lite│ AI │dash│buf │ T2 │frz │29-30
          ▲         ▲    ▲    ▲         ▲          ▲
          │   baseline│  12 Nov│  17 Nov│  feature  │ freeze
          │   8 Nov   │  CSE321│  CSE311│  complete │ 21 Dec
          │           │  ckpt  │  ckpt  │  6 Dec    │
```

## Sprint 0 — Setup (Fri 16 – Sun 18 Oct)

**Goal:** everyone can run the project locally, CI is green, the backlog exists.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S0-01 | Repo: `develop` default, branch protection, git identities verified | 1 | C |
| S0-02 | GitHub Project: fields, views, templates, milestones | 2 | C |
| S0-03 | Django 6.1 skeleton with uv, apps, split settings, `.env` | 3 | C |
| S0-04 | Dev `compose.yml`; setup verified on all three laptops | 2 | A |
| S0-05 | CI workflow (lint, test, migrations check, deploy check) green | 3 | C |
| S0-06 | Spec read by all; D1–D15 accepted or changed; backlog imported as issues | 1 | A + all |

**How-to notes**
- Follow §10.2 exactly. `AUTH_USER_MODEL` goes in now even though the model is written in Sprint 1, and **nobody runs `migrate` until S1-01 is merged**. (If someone did: drop the local database with `docker compose down -v`.)
- Ask the TA about the 3-person team **this weekend**, by email, and save the reply in `docs/process/`.

**Checkpoint:** `uv run pytest` passes on all three machines (even with zero tests); a PR shows green checks; the board shows Sprint 1 stories in Ready.

## Sprint 1 — Domain core (Mon 19 – Sun 25 Oct)

**Goal:** the whole data model exists, the 11 POs are seeded, and the engine reproduces the professor's numbers.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S1-01 | Custom `User` (email login) + `ProgramMembership` + manager | 3 | C |
| S1-02 | Catalog models with constraints + admin | 3 | A |
| S1-03 | Outcome models (LO, Assessment, both weight tables) + admin | 3 | B |
| S1-04 | `Grade` (draft/published) + `AuditEvent` + `audit.record` | 2 | B |
| S1-05 | Data migration: CSE program + official 11 POs | 1 | A |
| S1-06 | Scoring engine, test-first: golden + policy + property tests | 5 | A |
| S1-07 | Loaders: ORM → `OfferingInputs` (P4 published only, P9 retakes, P10 in-progress) | 3 | A |
| S1-08 | Factories for every model + `elif_scenario()` | 2 | B |
| S1-09 | Base template, design tokens, `|score` filter, `empty_state` / `score_badge` includes | 3 | C |
| S1-10 | `seed_demo` v1: program, terms, 4 courses, 30 students, Elif's slide example | 3 | B |

**How-to notes**
- S1-01 merges first (day 1–2). Everyone else waits for it before generating their first migration.
- Models: copy from §5.2, then run `makemigrations`. Review migration files in the PR.
- S1-06: commit the red test, then the green code (§9.8). Aim for 100% coverage of `engine.py` before moving on.
- S1-07 loader rule for retakes: for each catalog course, keep only the latest offering (by term start date) in which the student has an enrollment with status `enrolled`.

**Checkpoint:** in the Django shell, `compute_student_profile(load_student_inputs(elif))` gives PO 1 = 85.0, PO 2 = 82.9. Admin shows all models with seed data.

## Sprint 2 — Instructor flows (Mon 26 Oct – Sun 1 Nov)

**Goal:** an instructor can log in, set up a course, map it, and type grades. Staging is live.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S2-01 | Login / logout, role-based redirect, role switcher, navbar | 2 | C |
| S2-02 | `permissions.py`, decorators, selector pattern, permission matrix test scaffold | 5 | C |
| S2-03 | Head: terms, catalog, offerings CRUD, instructor assignment | 3 | A |
| S2-04 | Instructor: LO and assessment editors + setup checklist | 3 | B |
| S2-05 | Both weight grids (HTMX), validation, stale-edit detection | 5 | B |
| S2-06 | Grade sheet with HTMX inline save + keyboard navigation | 5 | A |
| S2-07 | Mapping lint rules L001–L006 + display | 2 | A |
| S2-08 | Dockerfile, `compose.prod.yml`, VPS, CD to **staging** | 5 | C |
| S2-09 | Password reset by email | 1 | B |

**How-to notes**
- HTMX grids: one `{% partialdef cell %}` per grid cell; the view returns `render(request, "outcomes/mapping.html#cell", ctx)` for HTMX requests (`request.htmx`).
- Stale edits (B5 AC 3): the grid form carries a hidden `version` = the offering's last mapping `AuditEvent` id; the service refuses a save if a newer event exists.
- Grade sheet query: one query for enrollments, one for assessments, one for grades (`Grade.objects.filter(assessment__offering=o)`), build a dict in Python. Test with `django_assert_max_num_queries(6)`.
- S2-08 is the riskiest story of the sprint; start it Monday (*Test in the Wild*, Getting Real Ch. 6: put it online early).

**Checkpoint:** on **staging**, log in as Dr. Can Aydın → create LOs and assessments → fill both grids → type grades. Matrix test covers every URL that exists so far.

## Sprint 3 — Baseline complete (Mon 2 – Sun 8 Nov)

**Goal:** every Baseline feature works end-to-end on staging and production. **Baseline done by Sun 8 Nov.**

| ID | Story | Pts | Owner |
|---|---|---|---|
| S3-01 | Publish / unpublish service + confirmation modal + audit | 5 | B |
| S3-02 | Student PO profile v1 (table, bar chart, contributors drawer) | 5 | C |
| S3-03 | Instructor course results | 3 | A |
| S3-04 | Department overview v1 | 3 | C |
| S3-05 | Enrollment CSV import with dry run | 5 | A |
| S3-06 | Production stack, first release `v0.3.0`, nightly backup cron | 2 | C |
| S3-07 | `seed_demo` v2: 3 terms, 12 courses, 120 students, realistic distributions (Appendix B) | 2 | B |
| S3-08 | Bulk upload spike: parse CSV/XLSX, Turkish decimals and encodings, column matching | 3 | B |

**Checkpoint (the "baseline demo"):** in production, the full loop works: head creates an offering → instructor sets it up and enters grades → publishes → student sees PO profile → head sees the overview. Record this as a 3-minute video. It's the fallback demo if anything breaks later, and it goes into both checkpoint presentations.

## Sprint 4 — Light: CSE 321 checkpoint (Mon 9 – Sun 15 Nov)

CSE 311 midterm Tue 10 Nov. **CSE 321 presentation + report Thu 12 Nov.** Forecast: half velocity.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S4-01 | Diagrams: architecture (§4.2), class diagram, ER diagram (§5.1) exported to `docs/diagrams/` | 3 | A |
| S4-02 | CSE 321 checkpoint report + slides ([§13.1](#131-cse-321-checkpoint-thu-12-nov)) | 3 | A + all |
| S4-03 | Bulk upload: dry run report + confirm + golden-file tests | 5 | B |
| S4-04 | Baseline bug fixes from the Sprint 3 review | 2 | C |
| S4-05 | CSE 311 checkpoint evidence: velocity chart, board screenshots, run summaries | 2 | C |

## Sprint 5 — Light: CSE 311 checkpoint (Mon 16 – Sun 22 Nov)

**CSE 311 presentation + report Tue 17 Nov.** CSE 321 midterm Thu 19 Nov.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S5-01 | CSE 311 checkpoint report + slides ([§13.2](#132-cse-311-checkpoint-tue-17-nov)) | 3 | C + all |
| S5-02 | Celery worker in prod compose; eager mode in tests; `on_commit` enqueue helper | 2 | C |
| S5-03 | Extraction spike → `schemas.py`, `prompts.py`, `extract_syllabus()` (§7.4–7.5) | 5 | A |
| S5-04 | Validation and derivation pure functions + fixture tests (§7.6, §7.10) | 3 | B |
| S5-05 | Eval set: 5 syllabi + hand-labelled expected JSON + `eval_extraction` command | 2 | A |

**How-to notes:** S5-03 starts with the one-hour spike in §7.5. Get the team's Anthropic API key set up (Console → workspace → spend limit) before Monday.

## Sprint 6 — The AI wizard (Mon 23 – Sun 29 Nov)

**Goal:** an instructor uploads a syllabus and gets a configured course after review.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S6-01 | `IngestionJob`, upload view, Celery task with retries, status polling page | 5 | A |
| S6-02 | Review screen: editable LOs, assessments, both grids, source colours, warnings | 8 | B |
| S6-03 | Apply service: one transaction, replace rules, audit, `source` fields | 3 | A |
| S6-04 | "Suggest PO weights" button for hand-made courses + lint L007 + accept-all | 3 | C |
| S6-05 | Attainment aggregates service + department attainment table (T1.6 part 1) | 5 | C |

**Checkpoint:** upload `seed/syllabi/cse311.pdf` on staging → review → apply → the course is configured. Eval script run recorded in `docs/process/sprint-06/eval.md`.

## Sprint 7 — Dashboards and polish: FEATURE COMPLETE (Mon 30 Nov – Sun 6 Dec)

**Goal:** every Tier 1 feature done. Tag `v0.7.0` = feature complete.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S7-01 | Coverage heat map + under-covered flags | 3 | C |
| S7-02 | Dashboard filters (term range, cohort, closed-only) + completion panel | 2 | C |
| S7-03 | Exports: course + department, PDF (WeasyPrint, Celery) + Excel, REPEATABLE READ | 5 | A |
| S7-04 | Student profile v2: radar, per-course breakdown, trend, summary sentence | 5 | B |
| S7-05 | Audit history viewer (offering timeline, per-grade history, head view) | 3 | B |
| S7-06 | Playwright smoke tests: 3 golden paths | 3 | A |
| S7-07 | Accessibility + Lighthouse pass on key pages | 2 | C |

**Checkpoint:** run the full demo script (§13.3) on production without touching the admin. If anything fails, Sprint 8 fixes it before any Tier 2 work.

## Sprint 8 — Buffer, then Tier 2 (Mon 7 – Sun 13 Dec)

Order: (1) carry-overs from Sprints 6–7, (2) bugs from the Sprint 7 demo run, (3) Tier 2 by priority.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S8-01 | T2.1 Clone last term's setup | 2 | B |
| S8-02 | T2.3 Precomputed score tables + materialized views + `refresh_scores` | 5 | A |
| S8-03 | T2.2 Completion tracker + reminder emails (Celery beat) | 5 | C |
| S8-04 | T2.4 PO transcript PDF | 3 | B |

## Sprint 9 — Tier 2 continued, reports drafted (Mon 14 – Sun 20 Dec)

| ID | Story | Pts | Owner |
|---|---|---|---|
| S9-01 | Final CSE 311 report first draft (Sections 1–6) | 3 | C + all |
| S9-02 | Final CSE 321 report first draft (Sections 1–6) | 3 | A + all |
| S9-03 | T2.5 Turkish / English | 5 | B |
| S9-04 | T2.10 Sentry + uptime check | 1 | C |
| S9-05 | T2.8 TA role | 3 | A |
| S9-06 | T2.9 OBS course page import | 3 | A |
| S9-07 | T2.6 Multi-program UI + second seeded program | 3 | C |

## Sprint 10 — Freeze (Mon 21 – Sun 27 Dec)

**Mon 21 Dec: feature freeze.** CSE 311 midterm 22 Dec, CSE 321 midterm 24 Dec. Only bug fixes, demo data, reports.

| ID | Story | Pts | Owner |
|---|---|---|---|
| S10-01 | Final bug fixes from a full-team test session (each person tests someone else's area) | 3 | all |
| S10-02 | Final demo dataset on production + backup video of the full demo | 2 | B |
| S10-03 | Final reports: edit, figures at full size, print test, print 1 copy per course | 2 | A + C |
| S10-04 | Final release `v1.0.0`, README with screenshots, tag | 1 | C |

**Mon 28 Dec:** full rehearsal with a timer. **Tue 29 – Wed 30 Dec:** demo.

---

# PART 12: PRODUCT BACKLOG

The master list. Import each row as a GitHub issue (title = ID + story; body from the issue template; Points, Sprint, Area, Tier fields set). Points are **initial estimates**: re-estimate at refinement and record changes.

| ID | Story | Feature | Tier | Pts | Owner | Sprint |
|---|---|---|---|---|---|---|
| S0-01 | As a team, we have a protected repo with `develop` as default so nobody breaks shared branches | Process | Chore | 1 | C | 0 |
| S0-02 | As a team, we manage the backlog in GitHub Projects so planning and evidence live with the code | Process | Chore | 2 | C | 0 |
| S0-03 | As a developer, I run a Django 6.1 skeleton with uv and split settings | Platform | Chore | 3 | C | 0 |
| S0-04 | As a developer, I get Postgres and Redis with one command | Platform | Chore | 2 | A | 0 |
| S0-05 | As a team, every PR is linted and tested automatically | CI | Chore | 3 | C | 0 |
| S0-06 | As a team, we agree on the spec decisions and import the backlog | Process | Chore | 1 | A | 0 |
| S1-01 | As any user, I log in with my email; one person can hold several roles | B1 | Baseline | 3 | C | 1 |
| S1-02 | As the head, programs, PO sets, terms, courses, offerings and enrollments are stored with integrity rules | B2, B3 | Baseline | 3 | A | 1 |
| S1-03 | As an instructor, LOs, assessments and both weight sets are stored with range checks | B4, B5 | Baseline | 3 | B | 1 |
| S1-04 | As an instructor, grades have a draft and a published value and every change is audited | B6, B7 | Baseline | 2 | B | 1 |
| S1-05 | As the head, the official 11 POs exist from the first deploy | B2 | Baseline | 1 | A | 1 |
| S1-06 | As everyone, every score is computed by one tested engine that reproduces the professor's example | Engine | Baseline | 5 | A | 1 |
| S1-07 | As the engine, I receive only published, latest-attempt data from the database | Engine | Baseline | 3 | A | 1 |
| S1-08 | As a developer, I build realistic test data in one line | Testing | Chore | 2 | B | 1 |
| S1-09 | As any user, pages share one look, and scores always print the same way | Design system | Baseline | 3 | C | 1 |
| S1-10 | As a team, `seed_demo` fills a fresh database with a believable department | B12 | Baseline | 3 | B | 1 |
| S2-01 | As any user, I land on the right home page and can switch roles | B1 | Baseline | 2 | C | 2 |
| S2-02 | As the department, nobody can see or change data their role doesn't allow | Permissions | Baseline | 5 | C | 2 |
| S2-03 | As the head, I set up terms, the catalog and offerings, and assign instructors | B3 | Baseline | 3 | A | 2 |
| S2-04 | As an instructor, I define my LOs and assessments with a setup checklist | B4 | Baseline | 3 | B | 2 |
| S2-05 | As an instructor, I fill both weight grids with live validation | B5 | Baseline | 5 | B | 2 |
| S2-06 | As an instructor, I type grades into a fast spreadsheet-like sheet | B6 | Baseline | 5 | A | 2 |
| S2-07 | As an instructor, I'm warned when my mapping is broken | B11 | Baseline | 2 | A | 2 |
| S2-08 | As a team, every merge to `develop` deploys to staging automatically | CD | Chore | 5 | C | 2 |
| S2-09 | As any user, I can reset a forgotten password by email | B1 | Baseline | 1 | B | 2 |
| S3-01 | As an instructor, I publish an assessment so students see it all at once | B7 | Baseline | 5 | B | 3 |
| S3-02 | As a student, I see my 11 PO scores and where each comes from | B8 | Baseline | 5 | C | 3 |
| S3-03 | As an instructor, I see my class's LO scores and averages | B9 | Baseline | 3 | A | 3 |
| S3-04 | As the head, I see the program's average and attainment per PO | B10 | Baseline | 3 | C | 3 |
| S3-05 | As the head, I import a class list from CSV with a preview | B3 | Baseline | 5 | A | 3 |
| S3-06 | As a team, `main` deploys to production and the database is backed up nightly | CD | Chore | 2 | C | 3 |
| S3-07 | As a team, the demo dataset spans 3 terms, 12 courses and 120 students | B12 | Baseline | 2 | B | 3 |
| S3-08 | As an instructor, my gradebook file is understood whatever Excel export I use (spike) | T1.1 | Tier 1 | 3 | B | 3 |
| S4-01 | As the team, our architecture, class and ER diagrams are current and exported | CSE 321 | Chore | 3 | A | 4 |
| S4-02 | As the team, we present our data and system architecture on 12 Nov | CSE 321 | Chore | 3 | A | 4 |
| S4-03 | As an instructor, I upload a gradebook, see every problem first, then confirm | T1.1 | Tier 1 | 5 | B | 4 |
| S4-04 | As users, baseline bugs found in review are fixed | Quality | Baseline | 2 | C | 4 |
| S4-05 | As the team, our process evidence is ready for the CSE 311 checkpoint | CSE 311 | Chore | 2 | C | 4 |
| S5-01 | As the team, we present our tooling and tasking on 17 Nov | CSE 311 | Chore | 3 | C | 5 |
| S5-02 | As the system, slow work runs in a background worker | Platform | Tier 1 | 2 | C | 5 |
| S5-03 | As the system, I turn a syllabus file into validated structured data with Claude | T1.2 | Tier 1 | 5 | A | 5 |
| S5-04 | As the system, extracted data is checked, repaired and completed before anyone sees it | T1.2 | Tier 1 | 3 | B | 5 |
| S5-05 | As the team, we measure extraction accuracy on real syllabi | T1.2 | Tier 1 | 2 | A | 5 |
| S6-01 | As an instructor, I upload a syllabus and watch it being read | T1.2 | Tier 1 | 5 | A | 6 |
| S6-02 | As an instructor, I review and edit everything that was extracted before saving | T1.2 | Tier 1 | 8 | B | 6 |
| S6-03 | As an instructor, one click applies the reviewed setup to my course | T1.2 | Tier 1 | 3 | A | 6 |
| S6-04 | As an instructor with a hand-made course, I get suggested PO weights with reasons | T1.3 | Tier 1 | 3 | C | 6 |
| S6-05 | As the head, I see PO attainment rates per cohort and term | T1.6 | Tier 1 | 5 | C | 6 |
| S7-01 | As the head, I see which POs our curriculum under-covers | T1.6 | Tier 1 | 3 | C | 7 |
| S7-02 | As the head, I filter the dashboard and see which courses are incomplete | T1.6 | Tier 1 | 2 | C | 7 |
| S7-03 | As the head or an instructor, I export reports to PDF and Excel | T1.7 | Tier 1 | 5 | A | 7 |
| S7-04 | As a student, I see a radar, a per-course breakdown and my trend over terms | T1.5 | Tier 1 | 5 | B | 7 |
| S7-05 | As an instructor or head, I see who changed what and when | T1.4 | Tier 1 | 3 | B | 7 |
| S7-06 | As a team, the three most important user journeys are tested end to end | Testing | Tier 1 | 3 | A | 7 |
| S7-07 | As any user, key pages are accessible and fast | Quality | Tier 1 | 2 | C | 7 |
| S8-01 | As an instructor, I copy last term's setup in one click | T2.1 | Tier 2 | 2 | B | 8 |
| S8-02 | As the head, dashboards load instantly from precomputed scores | T2.3 | Tier 2 | 5 | A | 8 |
| S8-03 | As the head, instructors who haven't published are reminded automatically | T2.2 | Tier 2 | 5 | C | 8 |
| S8-04 | As a student, I download a one-page PO transcript | T2.4 | Tier 2 | 3 | B | 8 |
| S9-01 | As the team, the final CSE 311 report is drafted | CSE 311 | Chore | 3 | C | 9 |
| S9-02 | As the team, the final CSE 321 report is drafted | CSE 321 | Chore | 3 | A | 9 |
| S9-03 | As any user, I use POlaris in Turkish or English | T2.5 | Tier 2 | 5 | B | 9 |
| S9-04 | As the team, we hear about production errors before users do | T2.10 | Tier 2 | 1 | C | 9 |
| S9-05 | As a TA, I enter draft grades for my assigned course | T2.8 | Tier 2 | 3 | A | 9 |
| S9-06 | As an instructor, I import my course from its OBS page | T2.9 | Tier 2 | 3 | A | 9 |
| S9-07 | As an admin, a second program runs side by side with its own POs | T2.6 | Tier 2 | 3 | C | 9 |
| S10-01 | As users, the final product has no known bugs in the demo paths | Quality | Chore | 3 | all | 10 |
| S10-02 | As the team, the demo data and a backup video are ready | Demo | Chore | 2 | B | 10 |
| S10-03 | As the team, both final reports are printed | Reports | Chore | 2 | A + C | 10 |
| S10-04 | As the team, `v1.0.0` is tagged with a polished README | Release | Chore | 1 | C | 10 |
| — | T2.7 Head approval workflow for mapping changes | T2.7 | Tier 2 | 8 | — | if time |
| — | T3.1 What-if simulator | T3.1 | Tier 3 | 5 | — | if time |
| — | T3.2 Anonymous cohort comparison | T3.2 | Tier 3 | 3 | — | if time |
| — | T3.3 Course recommendations for a weak PO | T3.3 | Tier 3 | 5 | — | if time |
| — | T3.4 University SSO (OIDC) | T3.4 | Tier 3 | 8 | — | if time |
| — | T3.5 Read-only REST API with OpenAPI docs | T3.5 | Tier 3 | 5 | — | if time |

**Points per sprint (planned):**

| Sprint | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Planned points | 12 | 28 | 31 | 28 | 15 | 15 | 24 | 23 | 15 | 21 | 8 |
| Per person (A / B / C) | 3/0/9 | 12/10/6 | 10/9/12 | 8/10/10 | 6/5/4 | 7/3/5 | 8/8/8 | 8/8/7 | 5/5/5 | 9/5/7 | shared |

Sprints 1–3 are planned above a 24-point guess on purpose: the bottom stories of each are the first to slip into the light Sprints 4–5, which is where the slack is. If Sprint 1's real velocity is below 20, move S1-10 and S1-09 to Sprint 2 and re-plan at Sprint 2 planning.

---

# PART 13: CHECKPOINTS, DEMO AND REPORTS

Both courses use the same rules for every report: **printed**, **no separate title page** (top of page 1: team name, members, GitHub repo URL), and every figure and code snippet readable at **125%** (if you have to squint at the printout, enlarge it). Do a print test of one page with a diagram and one with YAML before printing the whole thing.

## 13.1 CSE 321 checkpoint (Thu 12 Nov)

**Theme: Data & System Architecture.** Owner: Person A. Everyone presents a part.

**Slides (≈ 10–12, ≈ 10 minutes):**

| # | Slide | Source |
|---|---|---|
| 1 | Title: team, members, repo, punchline | §1.2 |
| 2 | The problem and the scoring chain (Elif example in one picture) | §1.1, §2.2 |
| 3 | Answers to the eight design questions | §1.5 |
| 4 | **Architecture diagram**: browser, Caddy, Django, Celery, Redis, PostgreSQL, Claude API, SMTP | §4.2 |
| 5 | Why each component (one line each: why Postgres, why Redis, why a worker) | §4.1 |
| 6 | **Class diagram**: models and relationships, generated then cleaned up | §5.2 |
| 7 | **Data model / ER diagram** with keys and constraints | §5.1 |
| 8 | Integrity: unique, check and partial-unique constraints; rules enforced in services | §5.2–5.3 |
| 9 | Transactions: publish with `FOR UPDATE`, export with REPEATABLE READ | §5.6 |
| 10 | Planned: snapshot tables, materialized views, star schema for reporting | §5.5 |
| 11 | Live: 60-second demo of publish → student profile on production | Sprint 3 video as backup |
| 12 | Questions | |

**Generate the class diagram** instead of drawing it: install `django-extensions` (dev only) and run `uv run python manage.py graph_models accounts catalog outcomes grading core ingestion -o docs/diagrams/classes.png` (needs Graphviz: `brew install graphviz`). Tidy it in draw.io if it's crowded.

**Checkpoint report:** short (4–6 pages). Use the CSE 321 final section headings that already apply: 1 Introduction, 2 System design (architecture + class diagram), 3 Data model (ER diagram, tables, normalisation). Mark Sections 4–6 "planned" with two or three sentences each.

## 13.2 CSE 311 checkpoint (Tue 17 Nov)

**Theme: Tooling & Tasking.** Owner: Person C. By 17 Nov we will have completed Sprints 0–4 (five sprints).

**Slides (≈ 10, ≈ 10 minutes):**

| # | Slide | Source |
|---|---|---|
| 1 | Title + punchline | §1.2 |
| 2 | How we formed the backlog: from the brief to 70 stories in tiers | §1.6, Part 12 |
| 3 | The tool: GitHub Projects board screenshot, fields, automation | §9.3 |
| 4 | Our meetings: planning, async stand-ups, review, retro | §9.1 |
| 5 | Who does what: three areas, owners, Scrum roles | §0.3 |
| 6 | How we rate difficulty: planning poker, reference stories, one real example with its first-round spread | §9.4 |
| 7 | Sprint length (1 week) and why | §9.1 |
| 8 | **Velocity chart**: completed points per sprint, Sprints 0–4, with the forecast line | `velocity.md` |
| 9 | What we learned: one retro action item that changed how we work | `sprint-NN/retro.md` |
| 10 | Teaser: CI/CD pipeline already running, AI wizard next | §9.9–9.10 |

**Checkpoint report:** use the final CSE 311 headings. Sections 1–2 in full, Section 3 with the charts so far, Sections 4–5 short but real (the branching model and CI/CD already exist), Section 6 "planned" with the chapters we're following.

## 13.3 Final demo (Tue 29 – Wed 30 Dec)

**Before the demo**
- [ ] Production reseeded with the final demo dataset the day before; nobody touches production after that.
- [ ] Logins for each persona written on a card: head, instructor, student.
- [ ] Three browser profiles (or one normal and two private windows) already logged in as the three personas.
- [ ] One syllabus extraction already done (backup), and one ready to run live.
- [ ] Backup video of the whole script on a laptop **and** a USB stick.
- [ ] Phone hotspot ready in case university Wi-Fi fails.
- [ ] Printed reports in hand, one per course.

**Script (≈ 10 minutes, rehearse with a timer):**

| Min | Who presents | Persona on screen | What happens |
|---|---|---|---|
| 0:00 | A | — | The problem in one sentence; the scoring chain on one slide (Elif example, 85.0) |
| 1:00 | B | Dr. Can Aydın | New offering is empty → **uploads the CSE 311 syllabus** → "Reading…" (talk over the wait) |
| 2:30 | B | Dr. Can Aydın | Review screen: LOs with source quotes, derived weights, AI-suggested PO links with reasons → edit one cell → Apply |
| 4:00 | B | Dr. Can Aydın | **Bulk upload** a messy gradebook → dry run catches errors → fix → confirm → **publish** the midterm |
| 5:30 | C | Elif Yıldız | Profile updates: radar, "why is my PO 6 this number?" drawer, trend over terms |
| 6:30 | C | Prof. Deniz Kara | Dashboard: attainment by cohort, heat map flags **PO 11 not covered by any course**, completion panel |
| 7:30 | C | Prof. Deniz Kara | Export the department report to PDF; open it |
| 8:00 | A | Prof. Deniz Kara | Audit history: who changed which grade, before and after |
| 8:30 | A | — | Behind the scenes: CI run with coverage, CD deploy, test counts, eval accuracy table |
| 9:30 | all | — | Questions |

If the live extraction is slow or fails, say "this takes about a minute, here's one we ran earlier" and open the finished job. Never debug in front of the graders.

## 13.4 Final CSE 311 report: where each section comes from

| Section | Asks for | Evidence we already collect | Owner |
|---|---|---|---|
| 1 | Punchline and key ingredient; backlog tool | §1.2; §9.3 with board screenshots | C |
| 2 | Who did what (explicitly); difficulty assessment; sprint length; sprints completed; velocity | Issue list by assignee; planning poker records; `velocity.md` and its chart | C |
| 3 | Contributors chart per member; code frequency chart | GitHub Insights screenshots taken on 27 Dec | A |
| 4 | Branching model; development / release / deployment branches | §9.6 with the diagram; real examples (a hotfix, a release branch) | A |
| 5 | GitHub Actions YAML for CI and CD; summary of particular runs | `ci.yml`, `cd.yml`; `docs/process/sprint-NN/runs.md`, including at least one failed run and its fix | C |
| 6 | Getting Real principles adopted, with chapters | §13.6 table, each row with a concrete example from our project | B |

## 13.5 Final CSE 321 report: where each section comes from

| Section | Asks for | Evidence | Owner |
|---|---|---|---|
| 1 | Introduction: key features | §1.2, §1.6 | B |
| 2 | Architecture diagram (databases, web apps, cache, notification services, 3rd-party integrations); class/object diagram | §4.2; generated class diagram | A |
| 3 | Data model diagram; each table's final rows, columns and raw size; star or snowflake; normalised or denormalised | §5.1; the SQL in §5.6 run on production on 27 Dec; §5.5 star schema discussion | A |
| 4 | Index types, materialized views or cubes, partitioning and replication, fault tolerance | §5.6 index table with `EXPLAIN ANALYZE` output; T2.3 materialized views; partitioning arithmetic; backups and restore drill; Celery retries | A |
| 5 | Where and how transactions are used, and their isolation level | §5.6 transactions table, with the tests that prove rollback | B |
| 6 | Teamwork: who did which task, explicitly | Same issue list as CSE 311 Section 2 | C |

## 13.6 Getting Real principles (CSE 311 report Section 6)

Chapter numbers and titles follow the online edition at basecamp.com/gettingreal.

| Principle we adopted | Chapter | What it looked like in our project |
|---|---|---|
| Build less | Ch. 2, *Build Less* | A non-goals list (§1.7) instead of competing on feature count |
| Fixed deadline, flexible scope | Ch. 2, *Fix Time and Budget, Flex Scope* | Demo date fixed; scope tiered so lower tiers can drop without missing the deadline |
| Embrace constraints | Ch. 3, *Embrace Constraints* | Three people, ten weeks: one framework, one language, no separate frontend |
| Scale later | Ch. 4, *Scale Later* | We computed scores on request first and precomputed only when the dashboard needed it (T2.3) |
| Opinionated software | Ch. 4, *Make Opinionated Software* | One formula, one weight scale, no per-instructor formulas |
| Half, not half-assed | Ch. 5, *Half, Not Half-Assed* | Baseline finished and solid before any extra started |
| Start with no | Ch. 5, *Start With No* | Requests we turned down, listed with reasons |
| Race to running software | Ch. 6, *Race to Running Software* | Staging live in Sprint 2, baseline in production by 8 Nov |
| Rinse and repeat | Ch. 6, *Rinse and Repeat* | One-week sprints with a retro action item each time |
| Test in the wild | Ch. 6, *Test in the Wild* | Every sprint review on staging; the extraction eval on real syllabi |
| Meetings are toxic | Ch. 7, *Meetings Are Toxic* | Async written stand-ups; only two short meetings a week |
| Celebrate small victories | Ch. 7, *Seek and Celebrate Small Victories* | A visible release tag every Sunday |
| Interface first, epicenter first | Ch. 9, *Interface First*; *Epicenter Design* | Wireframes (§8.4) before views; the grid built before the page around it |
| Three states, blank slate | Ch. 9, *Three State Solution*; *The Blank Slate* | Every screen has regular, blank and error states; empty courses offer the syllabus upload |
| Get defensive | Ch. 9, *Get Defensive* | Dry runs before bulk writes; friendly failure messages from the AI pipeline |
| Copy is interface | Ch. 9, *Copywriting is Interface Design* | "Midterm I published to 84 students", not "Success" |
| Less software, manage debt | Ch. 10, *Less Software*; *Manage Debt* | A small pure engine; a `tech-debt` label reviewed at each retro |
| Specs: the warning, and our answer | Ch. 11, *There's Nothing Functional about a Functional Spec*; *Don't Do Dead Documents* | Our spec is decisions plus acceptance criteria, lives in the repo, and changes in the same PR as the code |
| Use real words | Ch. 11, *Use Real Words* | Realistic Turkish names and grade distributions in the seed data |

Only claim the ones we actually practised. Delete rows that turned out not to be true by December.

---

# PART 14: RISKS

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | A 3-person team is not accepted (the guidelines say exactly 4) | Medium | Severe: score 0 | Written confirmation from the TA in Sprint 0. If refused, recruit a fourth member immediately and give them T2 features plus testing | A |
| R2 | One member becomes unavailable for a week or more | Medium | High | Every area has a second person who reviews its PRs and can take over; the spec and small PRs make handover possible | C |
| R3 | The AI extraction is inaccurate on real syllabi | Medium | High | The eval set measures it early (Sprint 5); human review before apply; manual setup always works | A |
| R4 | Anthropic API outage or rate limits during the demo | Low | High | A pre-run job ready to open; backup video; retries with backoff | A |
| R5 | API cost overrun from a bug or loop | Low | Medium | Workspace spend limit; costs logged per job; the eval is never in CI | A |
| R6 | Velocity much lower than forecast | Medium | Medium | Tiers: drop from the bottom; light sprints 4–5 absorb overflow; re-plan at every planning meeting | A |
| R7 | Midterms and other courses crowd out project work | High | Medium | Light sprints planned in advance; nothing important due the week of an exam | C |
| R8 | Deployment problems late in the semester | Low | High | Staging from Sprint 2, so deploys are routine by December; rollback procedure documented | C |
| R9 | Contribution charts misrepresent who did what | Medium | Medium | Git emails verified in Sprint 0; authors open their own PRs | C |
| R10 | Data loss on the VPS | Low | High | Nightly backups; restore drill done; the demo can be reseeded in minutes | C |
| R11 | Merge conflicts in migrations | Medium | Low | Pull `develop` before `makemigrations`; one person merges model changes at a time; resolve by deleting your migration and regenerating it | A |
| R12 | Scope creep from "one more cool feature" | High | Medium | New ideas go to the bottom of the backlog; nothing enters a running sprint | A |

---

# PART 15: GOTCHAS AND TIPS

**Django**
- `AUTH_USER_MODEL` must exist before the first `migrate`. If someone migrated too early locally: `docker compose down -v`, then migrate again.
- Two people adding migrations to the same app at once creates conflicting migration numbers. Delete your own unmerged migration, pull, and regenerate it. Never edit a migration that's already on `develop`.
- `Decimal("0.1")`, never `Decimal(0.1)`: the second one inherits float error.
- Template `{{ score }}` prints full precision. Always use `{{ score|score }}`.
- HTMX POSTs need the CSRF token. Put `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` on `<body>` once.
- `select_for_update()` only works inside `transaction.atomic()`. Outside it, it raises an error.
- Enqueue Celery jobs with `transaction.on_commit(lambda: task.delay(job.id))`, or the worker may read the row before it's committed.
- N+1 queries hide in templates that loop over related objects. Use `select_related`/`prefetch_related` and test query counts on heavy pages.

**Git and GitHub**
- Pull `develop` before you branch, and again before you open the PR.
- Never commit `.env`, real data or API keys. If a key leaks: revoke it in the Anthropic Console first, then clean the history.
- Keep PRs small. A 1,500-line PR doesn't get a real review.

**Docker**
- "Port 5432 already in use": a local Postgres is running (`brew services stop postgresql`).
- After changing `pyproject.toml`, run `uv sync` locally and rebuild the image for production.

**Process**
- Move your own card. A board that's two days stale is useless as evidence.
- Take the end-of-sprint screenshots on Sunday. You can't take them retroactively.
- Write down estimates and their spread when you vote. You'll need them in November.

---

# QUICK REFERENCE CARD

```bash
# daily
git switch develop && git pull && git switch -c feature/<issue>-<slug>
docker compose up -d
uv run python manage.py migrate
uv run python manage.py runserver

# before pushing
uv run pytest
uv run ruff check . && uv run ruff format .

# models changed
uv run python manage.py makemigrations && uv run python manage.py migrate

# data
uv run python manage.py seed_demo --reset
uv run python manage.py createsuperuser

# background jobs (Sprint 5+)
CELERY_EAGER=False uv run celery -A config worker -l info

# AI extraction accuracy (costs money: about $1–2 per run)
uv run python manage.py eval_extraction --runs 3

# reset local database completely
docker compose down -v && docker compose up -d && uv run python manage.py migrate
```

| Need | Where |
|---|---|
| How a score is calculated | Part 2 |
| Who may do what | §3.3 |
| Model fields | §5.2 |
| A feature's acceptance criteria | Part 6 |
| What to do this sprint | Part 11 |
| Report section sources | §13.4, §13.5 |

---

# APPENDIX A: THE 11 PROGRAM OUTCOMES

The official wording, from Acıbadem OBS (`obs.acibadem.edu.tr/oibs/bologna/progLearnOutcomes.aspx?lang=en&curSunit=6246`). Seed these verbatim in S1-05. The short names come from the guidelines deck.

| # | Short name | Official description |
|---|---|---|
| 1 | Math, science & engineering knowledge | Gain adequate knowledge in mathematics, science and related engineering discipline subjects; ability to use theoretical and applied knowledge in these fields in complex engineering problems. |
| 2 | Problem solving | Gain ability to identify, formulate and solve complex engineering problems; gain ability to choose and apply appropriate analysis and modeling methods for this purpose. |
| 3 | System design | Gain ability to design a complex system, process, device or product to meet certain requirements under realistic constraints and Conditions; ability to apply modern design methods for this purpose. |
| 4 | Modern tools & IT | Analyze and create solutions to complex problems encountered in engineering applications of modern techniques and tools for development, have skills, gain the ability to use information technology effectively. |
| 5 | Experiments & data | Gain ability to design experiments, conduct experiments, collect data, analyze and interpret results for the study of complex engineering problems or discipline-specific research topics. |
| 6 | Teamwork | Gain ability to work effectively in interdisciplinary and multidisciplinary teams; work individually. |
| 7 | Communication | Gain ability to communicate effectively in Turkish oral and written; knowledge of at least one foreign language; ability to write effective reports and understand written report, design and production reports, make effective presentations, give and receive clear and understandable instructions. |
| 8 | Lifelong learning | Gain awareness of of the need for lifelong learning; the ability to access information, monitor developments in science and technology, and constantly renew oneself. |
| 9 | Ethics & standards | Act in accordance with ethical principles, awareness of professional and ethical responsibility; gain knowledge of standards used in engineering applications |
| 10 | Project, risk & change management | Gain knowledge of business practices such as Project Management, risk Management and change management; gain awareness about entrepreneurship, innovation; have information about sustainable development. |
| 11 | Health, safety, environment & law | Gain knowledge of the effects of engineering practices on health, environment and safety in Universal and social dimensions and the problems reflected in the field of engineering of the era; gain awareness of the legal consequences of engineering solutions. |

(Typos such as "of of" are in the official source; keep them verbatim in the seed and fix them only if the department publishes a corrected text.)

# APPENDIX B: DEMO SEED DATA

`uv run python manage.py seed_demo [--reset]`. Owner: Person B. It uses a **fixed random seed**, so every run produces identical data, and the tests can rely on it.

| What | Content |
|---|---|
| Program | CSE, threshold 60, active PO set "2023 curriculum" with the 11 POs from Appendix A |
| Terms | 2025F (closed), 2026S (closed), 2026F (open) |
| People | Head: Prof. Deniz Kara (also teaches). Instructors: Dr. Can Aydın, Dr. Ayşe Demir, Dr. Mehmet Şahin. Students: 120 in cohorts 2023, 2024 and 2025 (40 each), realistic Turkish names from Faker's `tr_TR` locale, student numbers like `2023-0001` |
| Courses | 12, e.g. CSE 101, CSE 102, CSE 211, CSE 221, CSE 231, CSE 311, CSE 321, CSE 331, CSE 341, MAT 141, MAT 241, PHY 101 |
| Setup per offering | 3–6 LOs with realistic wording; 3–5 assessments (midterm, final, project, quizzes); weights that look like a real instructor's |
| Grades | Each student gets a hidden ability per PO plus noise, so profiles differ in believable ways. Values are clipped to 0–100 and rounded to whole numbers or halves. About 5% of grades are missing and 2% are excused |
| Elif Yıldız | CSE 311 in 2026F with exactly the slide example: midterm 90, project 80, weights 60/40 and 40/100, PO weights 4 and 2 to PO 1 and 5 to PO 2. Her profile must show 85.0 and 82.9 |
| Deliberate flaws for the demo | One 2026F offering with no mapping (lint and completion panel show it); PO 11 linked by no course (the heat map flags it); PO 9 covered by only one course; one assessment with unpublished changes |
| Logins | Every persona's password is printed by the command. Seeding refuses to run when `DEBUG=False` unless you pass `--allow-production`, so demo passwords never end up in a real deployment by accident |

---

# APPENDIX C: SPEC CHANGE LOG

| Version | Date | Change | By |
|---|---|---|---|
| 1.0 | 16 Oct 2026 | First complete version | Team |
