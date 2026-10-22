#!/usr/bin/env bash
# Run the user-interaction survey with N independent headless Claude Code agents.
#
# Each agent works in its own private temp dir with its own copy of the report
# worksheet, can only edit that copy, and saves no session transcript. Reports are
# collected into results/agent_<n>/ only after every agent has finished, so no
# agent can read another's answers mid-run.
#
# Usage: src/run_survey.sh [N_AGENTS] [MODELS]
#   N_AGENTS  number of agents (default 1, so plain `src/run_survey.sh` runs one)
#   MODELS    comma-separated model ids, cycled across agents (default claude-opus-5-5)
#
# Example: src/run_survey.sh 3 claude-opus-5-5,claude-sonnet-5-5
set -euo pipefail

N=${1:-1}
IFS=, read -r -a MODELS <<< "${2:-claude-opus-5-5}"

REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
SURVEY="$REPO/src/survey.md"
TEMPLATE="$REPO/src/report.md"

# Claude Code stores transcripts for a directory under ~/.claude/projects/<path with
# non-alphanumerics replaced by '-'>. This repo's transcripts contain the survey
# design discussion, so agents must not read them.
REPO_HISTORY="$HOME/.claude/projects/$(sed 's/[^A-Za-z0-9]/-/g' <<< "$REPO")"

# Refuse to clobber reports from an earlier run.
for i in $(seq 1 "$N"); do
  if [[ -e "$REPO/results/agent_$i" ]]; then
    echo "$REPO/results/agent_$i already exists; move it aside first" >&2
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
      --add-dir "$HOME" \
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
        "Read(/$HOME/.claude/projects/-tmp-*/**)" \
        "Read(/$HOME/.claude.json)" "Read(/$HOME/.claude/mcp.json)" "Read(/$HOME/.ssh/**)" \
      -- "Answer the survey in $SURVEY by filling in the worksheet at $PRIV/report.md.
Follow the survey's ground rules. Edit only $PRIV/report.md.
Do not read anything under $REPO/results/, $REPO_HISTORY/, or other directories in ${TMPDIR:-/tmp}." \
      > "$PRIV/run.json" 2> "$PRIV/stderr.log"
  ) &
  PIDS+=($!)
done

FAILED=0
for idx in "${!PIDS[@]}"; do
  if ! wait "${PIDS[$idx]}"; then
    echo "agent_$((idx + 1)) exited non-zero; see $REPO/results/agent_$((idx + 1))/stderr.log" >&2
    FAILED=1
  fi
done

# Collect only once every agent is done.
for idx in "${!PRIVS[@]}"; do
  i=$((idx + 1))
  PRIV=${PRIVS[$idx]}
  OUT="$REPO/results/agent_$i"
  mkdir -p "$OUT"
  mv "$PRIV/report.md" "$PRIV/run.json" "$PRIV/stderr.log" "$OUT/"
  rmdir "$PRIV" 2>/dev/null || true
  # Headless runs still create a project folder (spilled tool output, empty
  # memory) even with --no-session-persistence; remove this run's one.
  rm -rf "$HOME/.claude/projects/$(sed 's/[^A-Za-z0-9]/-/g' <<< "$PRIV")"
done

echo "Reports in $REPO/results/agent_1 .. agent_$N"
exit "$FAILED"
