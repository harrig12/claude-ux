# CLAUDE user interaction profiling

This repo develops a survey on how people work with Claude Code. Claude agents
answer a series of questions to profile the user's workflow style, habits, and
common pain points.

- `src/survey.md`: the survey questions
- `src/report.md`: blank worksheet the agents fill in
- `src/run_survey.sh`: runs the survey with independent headless agents
- `src/hci_analysis.md`: plan for analysing everyone's reports
- `src/utils/parse_reports.py`: parses filled-in worksheets into CSV tables

## Taking the survey (participants)

You need Claude Code installed and logged in (`claude --version` should work).
The agents only read files; they don't change your settings, memory, or code.
Taking part is voluntary.

### Risks to know before you run it

1. **The agents can read your whole home directory, and anything they read is sent
   to Anthropic.** That includes credentials (`~/.ssh`, `.env`, tokens) and your
   past Claude Code history across all projects, which may contain pasted secrets,
   patient or sample identifiers, or unpublished results. If your work falls under
   a data use agreement or involves PHI, check that before running.
2. **Reports can contain sensitive material.** Despite instructions to paraphrase,
   an agent may name colleagues, describe confidential work, or make speculative
   guesses about you personally. Agents also write candid judgments of your
   experience level and working habits.
3. **A coworker reads your reports.** Cait will see your pain points and the agents'
   assessments of you. Reports are pseudonymized for analysis, but in a small group
   your projects and tools may still identify you. You can redact anything, and you
   can withdraw at any time.
4. **It uses your Claude usage and shared compute.** Three long agent sessions run
   in parallel and use a noticeable share of your plan's limits. Don't run it on a
   shared login node; use a workstation or an interactive job.

1. **Clone the repo and run the survey.**

   ```bash
   git clone <url tbd> claude-ux
   cd claude-ux
   src/run_survey.sh
   ```

   This runs three agents in parallel, each independently filling in its own
   copy of the worksheet. It takes a while; leave it running in its own terminal.
   When it's done, the reports are in `results/agent_1/`, `results/agent_2/` and
   `results/agent_3/`.

2. **Review your reports.** Read the three `report.md` files before sending
   them. Replace anything you'd rather not share with `[redacted]` (Sections 4
   and 6 are the most personal).

3. **Send the results to Cait.**

   ```bash
   tar czf claude-ux_$(whoami).tar.gz results/agent_*
   ```

   Send `claude-ux_<you>.tar.gz` to Cait Harrigan (<how to send: tbd>).
