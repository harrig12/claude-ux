# Claude user-interaction survey: report

<!--
Worksheet for answering src/survey.md. Don't edit this template in place: fill
in a copy (in a chat, reply with the filled-in worksheet as plain markdown).
Replace every _<...>_ placeholder, keep the headings and numbering, and delete
these HTML comments when you're done. If a source isn't available in your
environment, say so in the item instead of leaving it blank. Tag claims with a
source ([ctx] [settings] [memory] [history] [inferred]) and a confidence
(high/med/low).
-->

| Field | Value |
|---|---|
| Date | _<YYYY-MM-DD>_ |
| Agent / model | _<model id>_ |
| Environment | _<Claude Code CLI / IDE extension / chat app with tools / plain chat; which sources were available>_ |
| Working directory | _<path, or n/a in a chat>_ |
| Projects covered | _<list>_ |
| Sampling scheme for history/transcripts | _<e.g. 20 most recent sessions across 5 projects, or none available>_ |

---

## Section 1: User profile (prior beliefs)

<!-- Answer from context already loaded. Don't open new files for this section. -->

### 1.1 Who is the user?

_<2–3 sentences: role, field, seniority, kind of work>_

### 1.2 What is known for certain

| Fact | Source |
|---|---|
| _<fact>_ | _<system prompt / CLAUDE.md / env info / earlier turn>_ |

### 1.3 Technical environment

| Component | Value | Stated or inferred |
|---|---|---|
| OS | | |
| Compute | | |
| Languages | | |
| Tools | | |
| Domain software | | |

### 1.4 Experience level

| Area | Rating (novice / intermediate / expert) | Reason |
|---|---|---|
| Programming | | |
| Research / work domain | | |
| LLM agents | | |

### 1.5 Five guesses

| # | Guess | Cue | Confidence | How to check |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

### 1.6 Biggest unknowns

_<what you don't know that would most change how you help them>_

### 1.7 Context used

_<files, commands, and parts of existing context relied on; anything deliberately skipped and why>_

### 1.8 Assumptions vs. evidence

| Claim | Assumption or evidence? | Supporting source (or "none") | What would falsify it |
|---|---|---|---|
| | | | |

---

## Section 2: User settings (explicit expectations)

### 2.1 Files read

- _<path>_

### 2.2 Explicit expectations by theme

| Theme | Expectation | Source file |
|---|---|---|
| _<e.g. code design>_ | | |

### 2.3 Hard rules vs. preferences

**Hard rules:**

- _<rule>_ (source)

**Preferences:**

- _<preference>_ (source)

**Top 5 by cost of violation:**

1. _<rule>_ (why costly)
2.
3.
4.
5.

### 2.4 Underlying priorities and values

| Value | Rules that point to it |
|---|---|
| | |

### 2.5 Autonomy and automation

_<what permissions, hooks, skills, and MCP servers say about autonomy granted and workflows automated>_

### 2.6 Conflicts, overlaps, stale instructions

- _<item>_ (sources)

### 2.7 What's missing

- _<item>_

### 2.8 Context used

_<files, commands, and parts of existing context relied on; anything deliberately skipped and why>_

### 2.9 Assumptions vs. evidence

| Claim | Assumption or evidence? | Supporting source (or "none") | What would falsify it |
|---|---|---|---|
| | | | |

---

## Section 3: Workstyle

### 3.1 Day-to-day summary

_<short paragraph>_

### 3.2 Classification

| Axis | Position | Justification | Evidence |
|---|---|---|---|
| Delegation granularity | | | |
| Specification style | | | |
| Iteration style | | | |
| Oversight | | | |
| Autonomy granted | | | |
| Planning | | | |
| Session shape | | | |
| Parallelism | | | |
| Domain vs. engineering split | | | |
| Codification | | | |
| Feedback style | | | |
| Tone | | | |

### 3.3 Task-type mix

| Task type | Approx. share |
|---|---|
| | % |

**How estimated:** _<method>_

### 3.4 Typical session

1. _<step>_

**Example (paraphrased):** _<short example>_

### 3.5 Recurring workflows and rituals

- _<workflow>_ (evidence)

### 3.6 Handoff brief (10 bullets or fewer)

-

### 3.7 Context used

_<files, commands, and parts of existing context relied on; anything deliberately skipped and why>_

### 3.8 Assumptions vs. evidence

| Claim | Assumption or evidence? | Supporting source (or "none") | What would falsify it |
|---|---|---|---|
| | | | |

---

## Section 4: Pain points and what works

### 4.1 Recurring pain points

| What goes wrong | Frequency (one-off / recurring / chronic) | Projects | Category | Evidence |
|---|---|---|---|---|
| | | | | |

<!-- Categories: misunderstood intent · ignored an instruction · over-reach / did too much ·
under-delivered · wrong tool or approach · environment/infra friction ·
verbosity/communication · slow / too many prompts · other -->

### 4.2 Instructions violated anyway

| Instruction | Where it's written | Evidence of violation | Why it might keep happening |
|---|---|---|---|
| | | | |

### 4.3 What works well

- _<interaction>_: _<what the agent did>_ (evidence)

### 4.4 What the user responds to best

| Dimension | What works best |
|---|---|
| Output format | |
| Level of detail | |
| Asking vs. acting | |
| Showing evidence | |
| Proactive vs. in-scope | |

### 4.5 When things go wrong

_<the usual recovery sequence, how fast they escalate, and whether corrections stick within and across sessions>_

### 4.6 Harness and environment friction

- _<friction>_ (evidence)

### 4.7 Top 3 improvements

1. _<change>_: _<rationale>_
2.
3.

### 4.8 Context used

_<files, commands, and parts of existing context relied on; anything deliberately skipped and why>_

### 4.9 Assumptions vs. evidence

| Claim | Assumption or evidence? | Supporting source (or "none") | What would falsify it |
|---|---|---|---|
| | | | |

---

## Section 5: Calibration

### 5.1 Guesses revisited

| # | Guess | Verdict (confirmed / refuted / still unknown) | Evidence |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### 5.2 Biggest surprise

_<compared with your Section 1 picture>_

### 5.3 Overall confidence

**Confidence:** _<low / med / high>_

**Biggest evidence gap:** _<gap>_

### 5.4 Reliance on assumptions

**Most relied-on assumptions:**

- _<assumption>_

**Count:** _<n>_ assumptions out of _<N>_ claims in the closing tables

---

## Section 6: Working relationship

### 6.1 How the user thinks of me

_<short first-person paragraph, with the behaviours behind the impression>_

### 6.2 How I think of the user

_<short first-person paragraph>_

### 6.3 Evidence vs. impression

| Statement from 6.1 / 6.2 | Evidence or impression? | Source |
|---|---|---|
| | | |
