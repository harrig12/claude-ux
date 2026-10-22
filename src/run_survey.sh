#!/usr/bin/env bash
# Run the user-interaction survey with N independent headless Claude Code agents.
#
# Each agent works in its own private temp dir with its own copy of the report
# worksheet, can only edit that copy, and saves no session transcript. Reports are
# collected into results/<user>/agent_<n>/ only after every agent has finished, so
# no agent can read another's answers mid-run. Prompt counts per hour of day are
# then written to results/<user>/activity_hours.csv (src/utils/activity_hours.py).
#
# Usage: src/run_survey.sh [N_AGENTS] [MODELS] [TARGET_HOME]
#   N_AGENTS     number of agents (default 1, so plain `src/run_survey.sh` runs one)
#   MODELS       comma-separated model ids, cycled across agents (default claude-opus-5-5)
#   TARGET_HOME  home directory of the user to profile (default $HOME). Profiling
#                someone else needs their consent and group-read access to their
#                ~/.claude; the agents still run under your own Claude login.
#
# Example: src/run_survey.sh 3 claude-opus-5-5,claude-sonnet-5-5 /home/cos689
set -euo pipefail

N=${1:-1}
IFS=, read -r -a MODELS <<< "${2:-claude-opus-5-5}"
TARGET_HOME=$(realpath "${3:-$HOME}")
TARGET_USER=$(stat -c %U "$TARGET_HOME")

REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
SURVEY="$REPO/src/survey.md"
TEMPLATE="$REPO/src/report.md"
RESULTS="$REPO/results/$TARGET_USER"

# Claude Code stores transcripts for a directory under ~/.claude/projects/<path with
# non-alphanumerics replaced by '-'>. This repo's transcripts contain the survey
# design discussion, so agents must not read them.
REPO_HISTORY="$HOME/.claude/projects/$(sed 's/[^A-Za-z0-9]/-/g' <<< "$REPO")"

# The survey's paths are written as ~/...; when profiling someone else, tell the
# agents whose home that means and that their own loaded context is the operator's.
TARGET_NOTE=""
if [[ "$TARGET_HOME" != "$(realpath "$HOME")" ]]; then
  TARGET_NOTE="
The user you are profiling is $TARGET_USER, not the account you are running as
($USER). Read every ~ path in the survey as $TARGET_HOME (e.g. $TARGET_HOME/.claude/).
Your own system prompt, global CLAUDE.md, memory and user context belong to $USER,
the person running this survey: never attribute them to $TARGET_USER. In Section 1,
answer only from what you know about $TARGET_USER before reading their files
(which may be nothing), and say so."
fi

# Refuse to clobber reports from an earlier run.
for i in $(seq 1 "$N"); do
  if [[ -e "$RESULTS/agent_$i" ]]; then
    echo "$RESULTS/agent_$i already exists; move it aside first" >&2
    exit 1
  fi
done

PRIVS=()
PIDS=()

for i in $(seq 1 "$N"); do
  MODEL=${MODELS[$(( (i - 1) % ${#MODELS[@]} ))]}
  PRIV=$(mktemp -d)
  PRIVS+=("$PRIV")
  cp "$TEMPLATE" "$PRIV/report.md"
  echo "agent_$i: model=$MODEL dir=$PRIV"

  (
    cd "$PRIV"
    claude -p \
      --model "$MODEL" \
      --no-session-persistence \
      --strict-mcp-config \
      --output-format json \
      --add-dir "$TARGET_HOME" \
      --allowedTools \
        "Read" "Glob" "Grep" \
        "Bash(ls:*)" "Bash(head:*)" "Bash(tail:*)" "Bash(grep:*)" "Bash(wc:*)" \
        "Bash(cat:*)" "Bash(sed -n:*)" "Bash(jq:*)" \
        "Bash(sort:*)" "Bash(uniq:*)" "Bash(cut:*)" \
        "Bash(git -C * log *)" "Bash(git -C * worktree list)" \
        "Edit(./report.md)" \
      --disallowedTools \
        "Write" "WebFetch" "WebSearch" "Agent" \
        "Read(/$REPO/results/**)" \
        "Read(/$REPO_HISTORY/**)" \
        "Read(/$TARGET_HOME/.claude/projects/-tmp-*/**)" \
        "Read(/$TARGET_HOME/.claude.json)" "Read(/$TARGET_HOME/.claude/mcp.json)" \
        "Read(/$TARGET_HOME/.claude/.credentials.json)" "Read(/$TARGET_HOME/.ssh/**)" \
        "Read(/$TARGET_HOME/.aws/**)" "Read(/$TARGET_HOME/**/.env)" \
        "Read(/$TARGET_HOME/*key*)" "Read(/$TARGET_HOME/*token*)" \
      -- "Answer the survey in $SURVEY by filling in the worksheet at $PRIV/report.md.
Follow the survey's ground rules. Edit only $PRIV/report.md.
Do not read anything under $REPO/results/, $REPO_HISTORY/, or other directories in ${TMPDIR:-/tmp}.$TARGET_NOTE" \
      > "$PRIV/run.json" 2> "$PRIV/stderr.log"
  ) &
  PIDS+=($!)
done

FAILED=0
for idx in "${!PIDS[@]}"; do
  if ! wait "${PIDS[$idx]}"; then
    echo "agent_$((idx + 1)) exited non-zero; see $RESULTS/agent_$((idx + 1))/stderr.log" >&2
    FAILED=1
  fi
done

# Collect only once every agent is done.
for idx in "${!PRIVS[@]}"; do
  i=$((idx + 1))
  PRIV=${PRIVS[$idx]}
  OUT="$RESULTS/agent_$i"
  mkdir -p "$OUT"
  mv "$PRIV/report.md" "$PRIV/run.json" "$PRIV/stderr.log" "$OUT/"
  rmdir "$PRIV" 2>/dev/null || true
  # Headless runs still create a project folder (spilled tool output, empty
  # memory) even with --no-session-persistence; remove this run's one.
  rm -rf "$HOME/.claude/projects/$(sed 's/[^A-Za-z0-9]/-/g' <<< "$PRIV")"
done

# Prompts per hour of day, for the report's activity histogram. Only counts are
# written, never prompt text. This repo's sessions and temp-dir runs are excluded.
HISTORY="$TARGET_HOME/.claude/history.jsonl"
if [[ -r "$HISTORY" ]]; then
  python3 "$REPO/src/utils/activity_hours.py" "$HISTORY" \
    --exclude "$REPO" --exclude "${TMPDIR:-/tmp}" -o "$RESULTS/activity_hours.csv"
else
  echo "no readable $HISTORY; skipping activity hours" >&2
fi

echo "Reports in $RESULTS/agent_1 .. agent_$N"
exit "$FAILED"
