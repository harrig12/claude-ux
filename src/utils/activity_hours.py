"""Count a user's Claude Code prompts by local hour of day from ~/.claude/history.jsonl.

Each history line has a ``timestamp`` (ms since epoch) and the ``project`` it was
typed in. Prompts from projects whose path contains any --exclude string are
dropped (the survey's own repo and /tmp scratch sessions). Hours are in the
machine's local timezone unless --tz is given. Only counts leave this script,
never prompt text.

Output: CSV with columns hour (0-23) and prompts.

Usage:
    python src/utils/activity_hours.py ~/.claude/history.jsonl \
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


def write_hours(hours, out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hour", "prompts"])
        writer.writerows((h, hours.get(h, 0)) for h in range(24))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("history", help="path to ~/.claude/history.jsonl")
    parser.add_argument("--exclude", action="append", default=[],
                        help="drop prompts whose project path contains this (repeatable)")
    parser.add_argument("--tz", help="IANA timezone, e.g. America/New_York (default: local)")
    parser.add_argument("-o", "--out", required=True, help="output CSV path")
    args = parser.parse_args()

    hours = count_hours(args.history, args.exclude, args.tz)
    write_hours(hours, args.out)
    print(f"wrote {args.out}: {sum(hours.values())} prompts")


if __name__ == "__main__":
    main()
