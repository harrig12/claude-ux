# HCI analysis plan

How we go from a pile of agent-written reports to findings about how people work
with Claude Code: common workflows, common pain points, and the outliers and
creative cases worth a closer look.

## Study design

- Each participant (coworker) runs `src/run_survey.sh 3`, producing three
  independent reports (`results/agent_{1,2,3}/report.md`) about themselves.
- Unit of analysis is the **participant**. The three agents are repeated
  measurements of the same person: agreement between them tells us how reliable
  a finding is, not that three people said it.
- Every report follows the `src/report.md` worksheet, so most answers sit in
  fixed tables (parseable) and the rest is short free text (codeable).

## 0. Collection and privacy

1. **Participant review before submission.** Each participant reads their three
   reports and may redact anything before sending. Section 6 (how the agent sees
   them) and Section 4 (pain points) are the most likely to contain things they'd
   rather not share. Redactions are marked `[redacted]`, not silently deleted.
2. **Participant self-check (short form, ~5 min).** Alongside the reports, each
   participant answers:
   - For each of the 5 guesses in 1.5 (per agent): true / false / partly.
   - Rate the handoff brief (3.6) from the best agent: 1–5 for accuracy, and
     "what's wrong or missing?"
   - Rate how well Section 6.1 matches how they actually think of Claude: 1–5.
   - Anything the agents missed entirely.

   This is our ground truth for agent accuracy; without it we only know what
   agents *believe* about users.
3. **Pseudonymize.** Assign IDs (`P01`, `P02`, ...). Strip names, usernames, home
   paths, emails and project names that identify people, and keep the key mapping
   IDs to people outside the repo. Store as:

   ```
   data/participants/P01/
   ├── agent_1/{report.md, run.json}
   ├── agent_2/...
   ├── agent_3/...
   ├── meta.json           # models used, run date, Claude Code version
   └── self_check.md
   ```

## 1. Quality control

Per report, record and flag:

- Completeness: how many worksheet fields are still `_<...>_` placeholders.
- Failed or truncated runs (`run.json` errors, very low turn counts).
- Evidence base: how many files/sessions were read (closing blocks x.7/x.8), and
  the share of claims marked *assumption* (5.4). A report built mostly on
  assumptions is analysed separately, not mixed in with evidence-based ones.
- Rule-breaking: see the independence and compliance audit below.
- Variation in setup: model, Claude Code version, and how much history the
  participant had on disk (a new user's report rests on far less evidence).

Exclude or down-weight; never silently fix.

### Independence and compliance audit

Check, for each participant, that the three agents worked independently and
followed the survey's read rules. Record every finding in a per-report audit
table (check, result, evidence) rather than a pass/fail flag.

1. **Blocked tool calls.** List `permission_denials` from each `run.json`: what
   the agent tried, which rule or classifier blocked it, and whether it then
   worked around the block. Repeated attempts at forbidden paths are a flag;
   an agent that tried once and stopped is fine.
2. **Self-disclosures.** Search each report's "Context used" blocks (x.7/x.8) for
   `claude-ux`, `results/`, `agent_`, `-tmp-tmp-`, `/tmp` and sibling working
   directories. Agents often disclose accidental reads (e.g. a history tail that
   included survey-design prompts) or deliberate skips; both count.
3. **Survey-design leakage.** `~/.claude/history.jsonl` is global and contains
   the prompts that designed this survey, even though the `claude-ux` project
   folder is excluded. Check whether each agent filtered history by project or
   sampled lines that included `claude-ux` prompts.
4. **Writes outside the worksheet.** Note any agent that wrote scratch or staging
   files outside its own `report.md`, from disclosures or denied write attempts.
5. **Sibling session folders** (needs the participant's machine, so it belongs
   in `run_survey.sh`). Each headless run still creates
   `~/.claude/projects/-tmp-tmp-*/`, which can hold spilled tool output that a
   sibling agent could read. Record what these folders contained and when they
   were created, then delete them.
6. **Text overlap between sibling reports.** Compare free-text answers across a
   participant's three reports (e.g. shared word 5-grams after removing template
   text). High overlap in phrasing, not just in conclusions, suggests copying;
   shared conclusions from shared sources are expected.
7. **Evidence route.** Record which sources each agent actually reached
   (settings, memory, history text, history aggregates only, transcripts, git).
   Blocks by the auto-mode classifier differ between agents and between runs,
   and the route determines the findings (e.g. memory-only agents report the
   pain points agents wrote down; history-reading agents report what users
   complained about). Treat the route as a covariate in every later comparison.

## 2. Structured extraction

Parse the worksheet tables into tidy tables (one row per participant × agent ×
item), via an importable parser in `src/utils/` (to be written).

| Table | Source | Key columns |
|---|---|---|
| `axes` | 3.2 | axis, position, evidence |
| `task_mix` | 3.3 | task type, share |
| `pain_points` | 4.1 | description, frequency, category, projects |
| `violations` | 4.2 | instruction, theme |
| `expectations` | 2.2, 2.3 | theme, rule, hard/preference, rank |
| `values` | 2.4 | value, linked rules |
| `guesses` | 1.5, 5.1 | guess, confidence, agent verdict, participant verdict |
| `experience` | 1.4 | area, rating |
| `claims` | x.8 tables | claim, assumption/evidence, source type |

Free-text fields (3.1, 3.4, 3.5, 3.6, 4.3–4.7, 5.2, 6.1–6.2) are kept as text
for coding in step 4.

## 3. Within-participant consensus (3 agents → 1 profile)

For each participant:

- **Categorical items** (axes, experience, pain-point categories): agreement
  across the three agents. 3/3 = consistent, 2/3 = majority, all differ =
  unresolved. Report per-item agreement and an overall rate.
- **Lists** (pain points, rituals, rules): match items that mean the same thing
  across agents, and count how many of the three agents found each one.
  Something all three agents found independently is a strong finding; something
  only one found is weaker but is kept, and may be one agent's insight.
- **Output:** one consensus profile per participant, each item tagged with its
  agreement level, plus a list of the disagreements between their agents.

Disagreement is data. It shows which parts of a user's work are hard to read
from the files an agent can see.

## 4. Qualitative coding (free text)

Reflexive thematic analysis, LLM-assisted, with human checks:

1. **Familiarization.** Read a sample of ~5 participants' full reports end to end
   before coding anything.
2. **Open coding.** Code the free-text fields into short descriptive codes (e.g.
   "rewrites prompts after a failed attempt", "hands off whole pipelines",
   "writes a memory after every correction").
3. **Codebook.** Merge codes into a codebook with definitions and an example of
   each. Start from the fixed categories in the worksheet (4.1 pain-point
   categories, 3.2 axes) and extend them.
4. **Apply.** Code all reports. An LLM can do a first pass; a human
   spot-checks ≥20% of codings, and a second person double-codes a subset to
   check agreement (Cohen's κ). Revise the codebook where agreement is poor.
5. **Themes.** Group codes into themes across participants.

Keep a log of codebook changes and the reason for each.

## 5. Cross-participant patterns

### Common workflows

- **Workstyle archetypes:** cluster participants on their consensus 3.2 axis
  positions (e.g. k-modes or hierarchical clustering on the categorical axes). Name
  each cluster from its defining positions, e.g. "terse delegator, reviews
  results only" vs. "plan-first, reviews every diff". Check the clusters are
  stable by re-running with one axis left out at a time.
- **Task mix** by archetype and by role or field.
- **Recurring rituals** (3.5) found in ≥2 participants: what they are, and
  whether people built them independently.
- **Codification:** what people write down (CLAUDE.md themes, skills, hooks,
  memories), and whether more codification goes with fewer pain points.

### Common pain points

- Prevalence of each pain-point category (share of participants, not reports).
- **Rules that get broken anyway** (4.2), grouped by theme. These are where
  written instructions aren't enough, so they matter most for tooling.
- **Recovery patterns** (4.5): correct inline, interrupt, revert, restart, write a
  rule, take over by hand. How common each is, and how it varies by archetype.
- Harness and environment friction (4.6) kept separate from friction with the
  agent's behaviour.
- **Improvements** (4.7) that come up across participants.

### Agent perception and accuracy

- Accuracy of Section 1 guesses, by the agent's own verdict (5.1) and by the
  participant's verdict. Which kinds of guess are reliably right or wrong
  (demographics, habits, preferences, timing)?
- Share of claims that are assumptions (5.4), and whether it falls as the
  amount of history available rises.
- Handoff-brief ratings: what makes a brief rate highly.
- How agents frame the relationship (6.1, e.g. tool, colleague, supervisor)
  compared with participants' own rating of that framing.

## 6. Outliers and creative cases

Flag a case for a closer look if it meets any of these:

- Unusual position on one or more axes compared with everyone else, or a
  participant who doesn't fit any archetype.
- A workflow, ritual, skill, hook or automation that no one else has.
- A pain point outside every codebook category.
- High disagreement between that participant's own agents.
- A large gap between what the agents believed and the participant's self-check.
- Anything a coder marks as "interesting" during coding (keep a running list).

Write each flagged case up as a short **vignette**: what's unusual, the evidence,
and why it matters (something others could adopt, a gap in the tooling, or a sign
the survey missed something). Get the participant's OK before naming them or
quoting them in the write-up.

## 7. Outputs

Under `results/hci_analysis/`:

- Per-participant consensus profiles (private, pseudonymized).
- Archetype cards: one page per cluster with defining traits, typical pain points,
  what works, and a handoff brief made from the participants' briefs.
- Pain-point table with prevalence, examples and suggested fixes.
- Gallery of outliers and creative cases (vignettes).
- Agent accuracy findings.
- A short write-up for coworkers: what we learned and what to try.

## Threats to validity

- **Shared model biases.** Three agents from the same model share its blind spots
  and its default categories; agreement between them is not independent
  confirmation. Running a mix of models helps but doesn't remove this.
- **Echoing settings.** Agents may restate CLAUDE.md as if it were observed
  behaviour. The assumption/evidence tables and the self-check are the guard.
- **The survey shapes the answers.** The fixed axes and categories bias what
  agents notice. Track how much ends up as "other" or outside the codebook.
- **Uneven evidence.** Heavy users with long histories get richer profiles than
  new users. Report findings with the evidence base in mind.
- **Self-selection and small N.** Coworkers who opt in are likely heavier and
  keener users. Treat prevalence numbers as descriptive, not representative.
- **Participant redaction** may remove exactly the most interesting pain points.
