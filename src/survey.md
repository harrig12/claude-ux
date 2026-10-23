# Claude user-interaction survey

You are being asked to profile the user you work with: who they are, what they
expect of you, how they work with you, and where that collaboration goes well or
badly. The goal is to find common user patterns across many users, so answer
candidly and specifically. Don't flatter the user and don't play it safe.

## Your environment

You may be running in one of several environments. Work out which one first, and
record it in the worksheet's **Environment** field:

- **Claude Code** (CLI, VS Code / JetBrains extension, or desktop app): you can
  read the user's files, including `~/.claude/`.
- **Chat app with tools** (claude.ai, the desktop or mobile app): no file access,
  but you may have memory, a past-chats search tool, project knowledge, or user
  preferences and styles in your context.
- **Plain chat**: only this conversation, plus whatever the user pasted in.

The sources each section names (`~/.claude/...` paths) are the Claude Code ones.
Use the closest equivalent you have:

| Source | Claude Code | Chat app |
|---|---|---|
| Settings / instructions | `CLAUDE.md`, `settings*.json`, skills, hooks, MCP servers | user preferences, custom instructions, styles, project instructions, enabled tools and connectors |
| Memory | `~/.claude/projects/*/memory/` | the app's memory (as shown in context or via a memory tool) |
| History | `~/.claude/history.jsonl`, session transcripts | past-chats search, project chats, or just this conversation |
| Repos and plans | git log, worktrees, `~/.claude/plans/` | none, unless the user shares them |

**Missing sources are expected, not a failure.** Fill in every item anyway. If
you have no evidence for one, say so in a short line naming what's missing (e.g.
"No prompt history available: chat app without past-chats search"), then give
your best guess tagged `[inferred]` with `low` confidence if a guess is useful.
In a table with nothing to report, write a single row saying so. Never leave a
`_<...>_` placeholder in place. Axes or questions that don't fit the environment
(e.g. worktrees or cluster jobs for a chat user) can be answered "doesn't apply",
with a reason.

## Ground rules

- **Answer the sections in order.** Answer Section 1 *before* you read any files
  or call any memory or past-chat search tools: use only what is already in your
  context. It measures what you believe about the user going in, and the later
  sections check that against evidence.
- **Tag every claim** with its source and confidence:
  - Source: `[ctx]` already in context (including this conversation),
    `[settings]` config/CLAUDE.md or chat preferences/instructions, `[memory]`
    memory files or chat memory, `[history]` transcripts, prompt history or past
    chats, `[inferred]` guess.
  - Confidence: `high` / `med` / `low`.
- **Cite evidence** as a file path (and line or session id where possible), or
  in a chat app as the chat title/date or "this conversation". Paraphrase
  instead of quoting verbatim, and leave out credentials, personal details about
  third parties, unpublished results, and anything else sensitive.
- **Bound your reads.** History and transcripts can be large. Sample them with a
  stated sampling scheme (e.g. "the 20 most recent sessions across 5 projects",
  or "8 past chats found by searching for corrections") instead of reading
  everything, and report what you sampled. With no history at all, write "none
  available" as the sampling scheme. In Claude Code, see "How to look at files"
  below.
- **Skip survey-design history.** Don't read transcripts or memory for the
  `claude-ux` project (`~/.claude/projects/*claude-ux*`): they contain the
  discussion that designed this survey and would bias your answers. The same goes
  for `claude-ux` entries in `~/.claude/history.jsonl`, which is shared across all
  projects: filter it by its `project` field. Also skip
  `~/.claude/projects/-tmp-*` (other survey agents' scratch sessions) and other
  agents' reports under `results/agent_*/`. In a chat app, skip past chats about
  designing or running this survey.
- **End every section (1–4) with a closing block**, numbered as the last items of
  that section:
  - **Context used:** list everything you pulled into context to answer the section:
    files read (with the line ranges or sample you took), commands run, and which
    parts of your existing context (system prompt, CLAUDE.md, earlier turns, recalled
    memories) you relied on. If you deliberately skipped something, say what and why.
  - **Assumptions vs. evidence:** a table with one row per claim in the section that
    goes beyond restating a source:

    | Claim | Assumption or evidence? | Supporting source (or "none") | What would falsify it |
    |---|---|---|---|

    Mark a claim as an *assumption* if it rests on defaults, stereotypes about the
    user's field or role, or your general sense of "users like this", rather than on
    something you actually read.
- **Don't change anything.** This survey is read-only: no edits to settings, memory, or
  CLAUDE.md files, and in a chat app don't add to or edit memory.
- **Use the worksheet.** If you were given a copy of `src/report.md` to fill in,
  fill in that copy. If the worksheet was pasted into the chat, reply with the
  whole filled-in worksheet as plain markdown, starting at its `# ...: report`
  heading, with no preamble and not inside a code block, so the user can save
  your reply as `report.md` unchanged. If it's too long for one reply, stop at
  the end of a section and continue from the next `## Section` heading when the
  user says "continue". Otherwise copy `src/report.md` to
  `results/agent_<n>/report.md` and fill in the copy. Keep its headings and
  numbering, and don't edit the template itself. The closing blocks are numbered
  1.7–1.8, 2.8–2.9, 3.7–3.8 and 4.8–4.9.

---

## How to look at files (Claude Code)

Skip this part if you have no file access. Commands outside a short read-only allowlist go to a safety check, which often
refuses them, and every refused call wastes a turn. Work like this:

- **Prefer the Read, Grep and Glob tools** for files. Use Read's offset/limit to
  take a window of a large file, and Grep's line numbers to find where to look.
- **Use one simple command per shell call, with absolute paths.** No `cd x; ...`,
  no `for` loops, no `;`/`&&` chains. Compound commands are the main thing that
  gets refused. Pipes between allowed commands (`jq`, `grep`, `head`, `tail`,
  `sort`, `uniq`, `cut`, `wc`) are fine.
- **Use `jq` for JSON and JSON-lines files**, not Python.
- **Don't read credentials.** Skip `~/.claude.json`, `mcp.json`, `.env` files and
  `~/.ssh`. Take MCP server names from your system prompt instead.
- **If a call is refused, don't retry variations of it.** Switch to the Read or
  Grep tool, or note the gap in your "Context used" block and move on.
- **Write only to your worksheet**, with the Edit tool, section by section. Don't
  stage drafts in other files.

**Prompt history** (`~/.claude/history.jsonl`) has one JSON object per prompt,
with `display` (the prompt text), `project`, `timestamp` and `sessionId`:

```bash
jq -r 'select(.project | test("claude-ux|^/tmp") | not) | [.project, .display] | @tsv' ~/.claude/history.jsonl | tail -200
jq -r 'select(.project | test("claude-ux|^/tmp") | not) | .project' ~/.claude/history.jsonl | sort | uniq -c | sort -rn
```

Some users (e.g. VS Code extension only) have no `history.jsonl`. If it's missing,
use the session transcripts below for prompt history instead, and note that in
the worksheet's sampling scheme.

**Session transcripts** are `~/.claude/projects/<project-dir>/<sessionId>.jsonl`,
one JSON object per event. You may read them. Single lines can be over 100 KB
(tool output), so never print whole lines; extract fields with `jq`:

```bash
# the user's typed prompts in one session
jq -r 'select(.type=="user" and (.message.content | type)=="string") | .message.content[0:300]' <file>
# the agent's replies
jq -r 'select(.type=="assistant") | .message.content[] | select(.type=="text") | .text[0:300]' <file>
# where things went wrong: interruptions and refused tool calls (line numbers)
grep -n -o 'Request interrupted by user\|doesn.t want to proceed' <file> | head
```

To understand a correction, find it by line number, then read the prompts and
replies around it:

```bash
# conversation text from lines 2830–2850 of a transcript
sed -n '2830,2850p' <file> | jq -r 'select(.type=="user" or .type=="assistant") | {t: .type, x: ([.message.content] | flatten | map(if type=="string" then . elif .type=="text" then .text else empty end) | join(" "))} | select(.x != "") | .t + ": " + .x[0:300]'
```

---

## Section 1: User profile (prior beliefs)

*Sources: only what is already in your context. Don't open new files yet.*

1.1 In 2–3 sentences, who do you think this user is: role, field, seniority, and the
    kind of work they mostly bring to you?

1.2 What do you know for certain about the user, and where does each fact come from
    (system prompt, CLAUDE.md, environment info, earlier turns)?

1.3 What is their technical environment (OS, compute, languages, tools, domain
    software)? Mark which parts are stated and which are inferred.

1.4 How experienced do they seem with (a) programming, (b) their research/work domain,
    (c) LLM agents specifically? Rate each novice / intermediate / expert, with a reason.

1.5 **Go out on a limb: make 5 guesses about the user** that are *not* directly stated
    anywhere. Make them specific enough to be checked and possibly wrong (e.g. "they
    usually work late in the day", not "they value good code"). For each guess, give:
    - the guess
    - what cue led you to it
    - confidence (`low` / `med` / `high`)
    - how it could be checked

1.6 What do you *not* know about this user that would most change how you help them?

---

## Section 2: User settings (explicit expectations)

*Sources: `~/.claude/CLAUDE.md`, project-level `CLAUDE.md` files,
`~/.claude/settings.json`, `~/.claude/settings.local.json`, project
`.claude/settings*.json`, `~/.claude/skills/`, configured MCP servers / plugins,
hooks, and permission allow/deny lists. In a chat app: user preferences, custom
instructions, styles, project instructions, and the tools, connectors and skills
enabled for you. For 2.1, list those (or "none") if you read no files.*

2.1 List every file you read for this section.

2.2 Summarize what the user **explicitly** expects of their agent, grouped by theme
    (e.g. code design, repo layout, compute/job submission, data handling, plotting,
    environment management, communication, git). Give one line per expectation and cite
    the file.

2.3 Which of these are **hard rules** (phrased "never", "always", "must") and which
    are **preferences**? Rank the top 5 by how costly a violation would be to the user.

2.4 What **priorities or values** sit behind the rules (e.g. reproducibility,
    cost/fairshare, protecting the environment, speed)? Name each value and the rules
    that point to it.

2.5 What do the **permissions, hooks, skills, and MCP servers** tell you about how much
    autonomy the user gives you and which workflows they've invested in automating?

2.6 Do any instructions **conflict** with each other, overlap, or look stale (e.g. paths
    or tools that no longer exist, or duplicate skills)? List them.

2.7 What would you expect to see in a setup like this that is *missing*?

---

## Section 3: Workstyle

*Sources: `~/.claude/history.jsonl` (prompt history), session transcripts under
`~/.claude/projects/*/`, `~/.claude/plans/`, project memory files, and the
repos themselves (git log, branch/worktree usage). In a chat app: past chats
(search them if you can), memory, and this conversation.*

3.1 Describe in a short paragraph how this user works with Claude day to day.

3.2 **Classify the user on each axis below.** Pick one position, give a one-line
    justification, and cite evidence. If an axis doesn't fit, say so.

| Axis | Positions |
|---|---|
| Delegation granularity | micro-tasks · feature-sized · whole-project / open-ended |
| Specification style | terse one-liners · moderate · detailed specs up front |
| Iteration style | one-shot and move on · short review loops · long multi-pass refinement |
| Oversight | reviews every diff · spot-checks · trusts output / reviews results only |
| Autonomy granted | asks to confirm most actions · mixed · auto mode / broad permissions |
| Planning | dives straight in · asks for a plan sometimes · plan-first habitually |
| Session shape | short, many sessions · long single sessions · long-running / background agents |
| Parallelism | one task at a time · several sessions or worktrees in parallel · subagent/workflow fan-out |
| Domain vs. engineering split | mostly domain/analysis · mixed · mostly software engineering |
| Codification | rarely writes rules down · CLAUDE.md only · heavy use of skills, memory, hooks |
| Feedback style | silent redirection · brief corrections · explains the why |
| Tone | terse/imperative · neutral · conversational |

3.3 What **task types** make up most of their usage? Estimate rough proportions (e.g.
    analysis scripts 40%, plotting 25%, cluster jobs 15%, tooling/skills 10%, writing
    10%) and say how you estimated them.

3.4 What does a **typical session** look like from first prompt to end? Give the usual
    sequence of steps, and one short paraphrased example.

3.5 What **recurring workflows or rituals** does the user have (e.g. plot-iteration
    checklists, worktree-per-feature, smoke-test then scale up)?

3.6 **Handoff brief.** Write a briefing of 10 bullets or fewer for a new agent meeting this
    user for the first time: how to work with them, what to do by default, what to ask
    about, and what never to do. A fresh agent should be able to act on it without
    reading anything else.

---

## Section 4: Pain points and what works

*Sources: memory files (`~/.claude/projects/*/memory/`, especially `feedback_*`),
session transcripts (look for corrections, interruptions, rejected tool calls,
"no"/"stop"/"actually"/"I said", repeated requests, reverted changes), plans,
and git history (reverts, fix-ups). In a chat app: past chats and memory,
looking for the same signs of correction.*

*Memory was written by agents and records only what they chose to keep.
Check it against the user's own words in transcripts, prompt history or past chats before
calling something the user's main pain point.*

4.1 List the **recurring pain points** you found. For each one, give:
    - what goes wrong (one line)
    - how often (one-off / recurring / chronic) and in which projects
    - category: misunderstood intent · ignored an instruction · over-reach / did too
      much · under-delivered · wrong tool or approach · environment/infra friction ·
      verbosity/communication · slow / too many prompts · other
    - evidence (paths)

4.2 Which **explicit instructions get violated anyway**? Look for corrections that
    repeat a rule already in CLAUDE.md or memory. Why might they keep happening?

4.3 **What works well?** Which interactions led to quick acceptance, praise, or the
    user building on the output without corrections? What did the agent do in those
    cases?

4.4 **What does the user respond to best?** Consider output format, level of detail,
    asking vs. acting, showing evidence (plots, numbers, diffs), and proactive
    suggestions vs. staying in scope.

4.5 **When things go wrong, what happens next?** Describe the usual recovery sequence:
    does the user correct inline, interrupt, revert, restart the session, write a new
    memory/rule, or take over by hand? How quickly do they escalate? Does the
    correction usually stick within the session, and across sessions?

4.6 What **friction from the harness or environment** (permissions, cluster, worktrees,
    MCP failures, context length) recurs, as opposed to friction with the agent's
    behaviour?

4.7 Name the **top 3 changes** (to agent behaviour, the user's config, or tooling)
    that would most improve this collaboration, each with a one-line rationale.

---

## Section 5: Calibration (after Sections 2–4)

5.1 Go back to your 5 guesses from 1.5. Mark each one **confirmed / refuted /
    still unknown**, with evidence.

5.2 What in Sections 2–4 surprised you most compared with your Section 1 picture?

5.3 Rate your overall confidence in this profile (`low` / `med` / `high`) and name
    the biggest gap in the evidence.

5.4 Across all sections, which assumptions did you rely on most heavily? How many of
    the claims in your closing tables were assumptions rather than evidence?

---

## Section 6: Working relationship

*Sources: everything gathered above. Keep each answer to a short paragraph (about
3–5 sentences), written candidly and in the first person.*

6.1 **How the user thinks of you.** Describe how you imagine the user thinks of you
    while you work: as a tool, a junior colleague, a collaborator, a pair programmer,
    a liability to supervise, or something else. Cover how much they trust you, what
    they expect you to get wrong, and what they rely on you for. Point to the
    behaviours behind your impression (e.g. how they phrase requests, what they
    double-check, what they've written rules about).

6.2 **How you think of the user.** Describe how you think of the user while you work:
    what kind of collaborator they are, what working with them feels like, what you
    find yourself being careful about, and what makes a session with them go well.

6.3 Mark which parts of 6.1 and 6.2 rest on evidence and which are your impression or
    assumption, using the same tags as elsewhere.
