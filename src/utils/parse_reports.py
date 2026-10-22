"""Parse filled-in survey worksheets (src/report.md copies) into tidy CSV tables.

Finds every ``agent_<n>/report.md`` under the given root(s). The participant ID is
the name of the directory holding the ``agent_<n>`` folders, e.g.
``data/participants/P01/agent_2/report.md`` -> participant ``P01``, agent ``2``.

Outputs (one row per participant x agent x item/row):
    items.csv          every numbered item, with its free text
    meta.csv           the header table (date, model, ...)
    <table>.csv        rows of each worksheet table, named via TABLE_NAMES
    claims.csv         all "Assumptions vs. evidence" closing tables, with a section column
    qc.csv             per-report counts of unfilled placeholders and parsed rows
    activity_hours.csv prompts per local hour of day, from each participant's
                       ``<ID>/activity_hours.csv`` (src/utils/activity_hours.py), if present

Lines of free text identical to the blank template's scaffolding (e.g. "1.", "-",
"**Hard rules:**") are dropped, so ``text`` holds only what the agent wrote.

Usage:
    python src/utils/parse_reports.py data/participants -o results/hci_analysis/parsed
"""

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

# Worksheet item number -> output table name.
TABLE_NAMES = {
    "1.2": "known_facts",
    "1.3": "environment",
    "1.4": "experience",
    "1.5": "guesses",
    "2.2": "expectations",
    "2.4": "values",
    "3.2": "axes",
    "3.3": "task_mix",
    "4.1": "pain_points",
    "4.2": "violations",
    "4.4": "responds_best",
    "5.1": "guess_verdicts",
    "6.3": "relationship_claims",
}
CLAIMS_TITLE = "assumptions vs. evidence"
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / "report.md"

PLACEHOLDER = re.compile(r"_<[^>]*>_")
COMMENT = re.compile(r"<!--.*?-->", re.S)
ITEM_HEADING = re.compile(r"^###\s+(\d+\.\d+)\s+(.*)$")
SECTION_HEADING = re.compile(r"^##\s+Section\s+(\d+)")
SEPARATOR_ROW = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")


def _clean(value):
    """Strip whitespace and treat placeholders as empty."""
    value = value.strip()
    return "" if PLACEHOLDER.fullmatch(value) or value == "%" else value


def _split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_tables(lines):
    """Split lines into (tables, text). Each table is a list of row dicts; rows
    whose cells are all empty or placeholders are dropped."""
    tables, text, block = [], [], []

    def flush():
        if len(block) >= 2 and SEPARATOR_ROW.match(block[1].strip()):
            header = _split_row(block[0])
            rows = []
            for line in block[2:]:
                cells = [_clean(c) for c in _split_row(line)]
                cells += [""] * (len(header) - len(cells))
                row = dict(zip(header, cells))
                # Columns pre-filled in the template (e.g. axis names, guess #)
                # don't count as an answer on their own.
                if sum(bool(v) for v in cells) > (1 if cells[0] else 0):
                    rows.append(row)
            tables.append(rows)
        else:
            text.extend(block)
        block.clear()

    for line in lines:
        if line.lstrip().startswith("|"):
            block.append(line)
        else:
            flush()
            text.append(line)
    flush()
    return tables, "\n".join(text).strip()


def _template_lines(template):
    """Per-item sets of non-blank text lines in the blank template."""
    if template is None:
        return {}
    items = parse_report(template)["items"]
    return {num: {l.strip() for l in item["text"].splitlines() if l.strip()}
            for num, item in items.items()}


def parse_report(path, scaffold=None):
    """Parse one worksheet into {'meta': rows, 'items': {num: {...}}, 'placeholders': n}.

    scaffold maps item number -> template text lines to drop from that item's text.
    """
    scaffold = scaffold or {}
    raw = Path(path).read_text()
    body = COMMENT.sub("", raw)
    placeholders = len(PLACEHOLDER.findall(body))

    preamble, items = [], {}
    current, section = None, None
    for line in body.splitlines():
        if m := SECTION_HEADING.match(line):
            section, current = m.group(1), None
            continue
        if m := ITEM_HEADING.match(line):
            current = m.group(1)
            items[current] = {"title": m.group(2).strip(), "section": section, "lines": []}
            continue
        if line.startswith("## ") or line.strip() == "---":
            continue
        if current:
            items[current]["lines"].append(line)
        elif section is None:
            preamble.append(line)

    meta_tables, _ = parse_tables(preamble)
    for item in items.values():
        item["tables"], item["text"] = parse_tables(item.pop("lines"))
    for num, item in items.items():
        lines = PLACEHOLDER.sub("", item["text"]).splitlines()
        drop = scaffold.get(num, set())
        item["text"] = "\n".join(l for l in lines if l.strip() not in drop).strip()

    return {"meta": meta_tables[0] if meta_tables else [], "items": items,
            "placeholders": placeholders}


def find_reports(roots):
    """Yield (participant, agent, path) for every agent_<n>/report.md under roots."""
    for root in roots:
        for path in sorted(Path(root).rglob("agent_*/report.md")):
            agent = path.parent.name.removeprefix("agent_")
            yield path.parent.parent.name, agent, path


def find_activity(roots):
    """Yield (participant, path) for every <ID>/activity_hours.csv under roots."""
    for root in roots:
        for path in sorted(Path(root).glob("*/activity_hours.csv")):
            yield path.parent.name, path


def build_tables(roots, template=DEFAULT_TEMPLATE):
    """Parse all reports under roots into {table_name: [row dicts]}."""
    scaffold = _template_lines(template)
    out = defaultdict(list)
    for participant, agent, path in find_reports(roots):
        report = parse_report(path, scaffold)
        key = {"participant": participant, "agent": agent}
        n_rows = 0

        for row in report["meta"]:
            out["meta"].append({**key, **row})

        for num, item in report["items"].items():
            out["items"].append({**key, "item": num, "section": item["section"],
                                 "title": item["title"], "text": item["text"]})
            if item["title"].lower() == CLAIMS_TITLE:
                name = "claims"
            else:
                name = TABLE_NAMES.get(num)
            if not name:
                continue
            for table in item["tables"]:
                for row in table:
                    out[name].append({**key, "item": num, "section": item["section"], **row})
                    n_rows += 1

        out["qc"].append({**key, "path": str(path), "placeholders_left": report["placeholders"],
                          "items_with_text": sum(bool(i["text"]) for i in report["items"].values()),
                          "table_rows": n_rows})

    for participant, path in find_activity(roots):
        with open(path) as f:
            out["activity_hours"].extend({"participant": participant, **row}
                                         for row in csv.DictReader(f))
    return out


def write_tables(tables, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        fields = list(dict.fromkeys(k for row in rows for k in row))
        with open(out_dir / f"{name}.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("roots", nargs="+", help="directories to search for agent_<n>/report.md")
    parser.add_argument("-o", "--out", required=True, help="output directory for CSVs")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE,
                        help="blank worksheet whose scaffolding is stripped (default: src/report.md)")
    args = parser.parse_args()

    tables = build_tables(args.roots, args.template)
    if not tables:
        parser.error(f"no agent_<n>/report.md found under {args.roots}")
    write_tables(tables, args.out)
    for name, rows in sorted(tables.items()):
        print(f"{name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
