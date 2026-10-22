#!/usr/bin/env bash
# Build the HCI report from participants' survey reports.
#
#   1. parse   reports -> CSV tables         (src/utils/parse_reports.py)
#   2. synth   CSVs + reports -> JSON        (headless Claude, src/hci_synthesis.md,
#                                             validated against src/utils/hci_synthesis_schema.json)
#   3. render  JSON + CSVs -> HTML           (src/utils/render_hci_report.py)
#
# Steps 1 and 3 are deterministic. Step 2 is not, so its output (synthesis.json,
# with provenance) is kept; rerun with --render-only to rebuild the HTML from it.
#
# Usage: src/build_hci_report.sh [--render-only] [PARTICIPANTS_DIR] [OUT_DIR] [MODEL]
#   PARTICIPANTS_DIR  holds <ID>/agent_<n>/report.md   (default data/participants)
#   OUT_DIR           output directory                  (default results/hci_analysis)
#   MODEL             model for the synthesis step       (default claude-opus-5-5)
set -euo pipefail

RENDER_ONLY=0
if [[ "${1:-}" == "--render-only" ]]; then RENDER_ONLY=1; shift; fi

REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
PARTICIPANTS=$(realpath "${1:-$REPO/data/participants}")
OUT=$(realpath -m "${2:-$REPO/results/hci_analysis}")
MODEL=${3:-claude-opus-5-5}

PROMPT="$REPO/src/hci_synthesis.md"
SCHEMA="$REPO/src/utils/hci_synthesis_schema.json"
PARSED="$OUT/parsed"
SYNTH="$OUT/synthesis.json"

if (( ! RENDER_ONLY )); then
  echo "[1/3] parsing reports in $PARTICIPANTS"
  python3 "$REPO/src/utils/parse_reports.py" "$PARTICIPANTS" -o "$PARSED"

  echo "[2/3] synthesising with $MODEL"
  WORK=$(mktemp -d)
  ln -s "$PARSED" "$WORK/parsed"
  ln -s "$PARTICIPANTS" "$WORK/participants"
  (
    cd "$WORK"
    claude -p \
      --model "$MODEL" \
      --no-session-persistence \
      --strict-mcp-config \
      --output-format json \
      --json-schema "$(cat "$SCHEMA")" \
      --add-dir "$PARSED" "$PARTICIPANTS" \
      --allowedTools "Read" "Glob" "Grep" \
      --disallowedTools "Bash" "Edit" "Write" "WebFetch" "WebSearch" "Agent" \
      -- "$(cat "$PROMPT")

Today's date is $(date +%F). The inputs are in ./parsed and ./participants." \
      > "$OUT/synthesis_run.json"
  )
  rm -rf "$WORK" "$HOME/.claude/projects/$(sed 's/[^A-Za-z0-9]/-/g' <<< "$WORK")"

  # Keep the structured output plus what produced it.
  jq --arg model "$MODEL" \
     --arg commit "$(git -C "$REPO" rev-parse --short HEAD)$(git -C "$REPO" diff --quiet -- src || echo '-dirty')" \
     --arg prompt_sha "$(sha256sum "$PROMPT" | cut -c1-12)" \
     --arg built "$(date -Iseconds)" \
     '(.structured_output // (.result | fromjson))
      + {provenance: {model: $model, commit: $commit, prompt_sha256: $prompt_sha,
                      built: $built, cost_usd: .total_cost_usd}}' \
     "$OUT/synthesis_run.json" > "$SYNTH"
fi

echo "[3/3] rendering"
python3 "$REPO/src/utils/render_hci_report.py" "$SYNTH" \
  --qc "$PARSED/qc.csv" --meta "$PARSED/meta.csv" -o "$OUT/hci_report.html"
