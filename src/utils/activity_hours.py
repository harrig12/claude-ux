"""Count a user's Claude Code prompts by local hour of day.

The source is either ~/.claude/history.jsonl or, for users without one (e.g. VS
Code extension only), the per-session transcripts in ~/.claude/projects/.

Each history line has a ``timestamp`` (ms since epoch) and the ``project`` it was
typed in. In transcripts, a prompt is a top-level ``user`` line with text content
(not a tool result, meta message or subagent turn), with an ISO ``timestamp`` and
its ``cwd``. Prompts from projects whose path contains any --exclude string are
dropped (the survey's own repo and /tmp scratch sessions). Hours are in the
machine's local timezone unless --tz is given. Only counts leave this script,
never prompt text.

Output: CSV with columns hour (0-23) and prompts.

Usage:
    python src/utils/activity_hours.py ~/.claude/history.jsonl \
        --exclude claude-ux --exclude /tmp -o results/activity_hours.csv
    python src/utils/activity_hours.py ~/.claude/projects \
        --exclude claude-ux --exclude /tmp -o results/activity_hours.csv
"""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def count_hours(history, exclude=(), tz=None):
    """Return a Counter of prompts per local hour (0-23)."""
    tzinfo = ZoneInfo(tz) if tz else None
    hours = Counter()
    with open(history) as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = entry["timestamp"] / 1000
            except (ValueError, KeyError, TypeError):
                continue
            if any(x in entry.get("project", "") for x in exclude):
                continue
            hours[datetime.fromtimestamp(ts, tzinfo).hour] += 1
    return hours


def _is_prompt(entry):
    """True for a transcript line the user typed (not tool output or a subagent turn)."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isSidechain"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, str):
        return not content.startswith("<local-command-stdout>")
    if isinstance(content, list):
        kinds = {c.get("type") for c in content if isinstance(c, dict)}
        return "text" in kinds and "tool_result" not in kinds
    return False


def count_transcript_hours(projects, exclude=(), tz=None):
    """Return a Counter of prompts per local hour (0-23) from session transcripts."""
    tzinfo = ZoneInfo(tz) if tz else None
    hours = Counter()
    # Top-level <project>/<session>.jsonl only; subagent transcripts sit deeper.
    for path in Path(projects).glob("*/*.jsonl"):
        with open(path, errors="replace") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if not _is_prompt(entry):
                        continue
                    ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue
                if any(x in entry.get("cwd", "") for x in exclude):
                    continue
                hours[ts.astimezone(tzinfo).hour] += 1
    return hours


def write_hours(hours, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hour", "prompts"])
        writer.writerows((h, hours.get(h, 0)) for h in range(24))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("history",
                        help="~/.claude/history.jsonl, or the ~/.claude/projects transcript dir")
    parser.add_argument("--exclude", action="append", default=[],
                        help="drop prompts whose project path contains this (repeatable)")
    parser.add_argument("--tz", help="IANA timezone, e.g. America/New_York (default: local)")
    parser.add_argument("-o", "--out", required=True, help="output CSV path")
    args = parser.parse_args()

    count = count_transcript_hours if Path(args.history).is_dir() else count_hours
    hours = count(args.history, args.exclude, args.tz)
    write_hours(hours, args.out)
    print(f"wrote {args.out}: {sum(hours.values())} prompts")


if __name__ == "__main__":
    main()
