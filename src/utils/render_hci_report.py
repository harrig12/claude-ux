"""Render the cross-participant HCI report as a standalone HTML page.

Inputs:
    synthesis.json   written by the synthesis step (see src/hci_synthesis.md)
    qc.csv           from src/utils/parse_reports.py, for agent and model counts
    activity_hours.csv  from src/utils/parse_reports.py, prompts per hour of day (optional)

The page uses the Coastal Broadsheet theme (light mode): Bebas Neue headings,
Merriweather body, Inter labels, on parchment with crimson accents.

Usage:
    python src/utils/render_hci_report.py results/hci_analysis/synthesis.json \
        --qc results/hci_analysis/parsed/qc.csv --meta results/hci_analysis/parsed/meta.csv \
        --activity results/hci_analysis/parsed/activity_hours.csv \
        -o results/hci_analysis/hci_report.html
"""

import argparse
import csv
import json
import math
from collections import Counter
from html import escape
from pathlib import Path

CSS = """
:root {
  --bg: #F5F3F1; --fg: #292929; --accent: #A51228; --primary: #ACC8E5;
  --surface: #EDEAE6; --rule: #D4CDC5; --muted: #5E5A56;
  --head: 'Bebas Neue', 'Arial Narrow', sans-serif;
  --body: 'Merriweather', Georgia, serif;
  --label: 'Inter', system-ui, sans-serif;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.65 var(--body); }
main { max-width: 1040px; margin: 0 auto; padding: 0 16px 64px; }
header.masthead { border-bottom: 3px double var(--fg); padding: 40px 0 16px; margin-bottom: 8px; }
.eyebrow, .label { font: 600 11px/1.4 var(--label); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
h1, h2, h3 { font-family: var(--head); font-weight: 400; letter-spacing: .02em; margin: 0; }
h1 { font-size: clamp(44px, 8vw, 76px); line-height: .95; }
h2 { font-size: 32px; color: var(--accent); border-bottom: 1px solid var(--rule); padding-bottom: 4px; margin: 48px 0 16px; }
h3 { font-size: 22px; }
.dek { font-style: italic; color: var(--muted); max-width: 680px; margin: 12px 0 0; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); border-bottom: 1px solid var(--rule); }
.stat { padding: 16px 12px; border-right: 1px solid var(--rule); }
.stat:last-child { border-right: 0; }
.stat .num { font: 400 48px/1 var(--head); color: var(--accent); }
.stat .num.small { font-size: 28px; line-height: 1.7; }
ol.ranked { list-style: none; padding: 0; margin: 0; display: grid; gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
ol.ranked li { background: var(--surface); border-top: 3px solid var(--accent); padding: 16px; }
ol.ranked .rank { font: 400 40px/1 var(--head); color: var(--primary); -webkit-text-stroke: 1px var(--fg); }
ol.ranked h3 { margin: 4px 0 6px; }
ol.ranked p { margin: 0 0 8px; }
.participant { border-top: 1px solid var(--fg); padding-top: 16px; margin-top: 32px; }
.participant-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 16px; margin-bottom: 12px; }
.participant-head h3 { font-size: 30px; }
.grid4 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); }
.cell { background: var(--bg); padding: 14px 16px; }
.cell .label { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.cell .label .who { color: var(--accent); }
.cell p { margin: 0; }
.evidence { font: 12px/1.5 var(--label); color: var(--muted); margin-top: 6px !important; }
.support { font: 600 11px/1.4 var(--label); background: var(--primary); color: var(--fg); padding: 1px 6px; border-radius: 2px; white-space: nowrap; }
.unique { background: var(--surface); border-left: 3px solid var(--accent); padding: 12px 16px; margin-top: 12px; }
.notes { font: 13px/1.6 var(--label); color: var(--muted); border-top: 3px double var(--fg); margin-top: 56px; padding-top: 12px; }
.notes p { margin: 0 0 6px; }
.vibe-bar { display: flex; height: 28px; border: 1px solid var(--fg); margin: 8px 0 6px; }
.vibe-bar span { display: flex; align-items: center; justify-content: center; font: 600 11px/1 var(--label); letter-spacing: .08em; text-transform: uppercase; }
.vibe-positive { background: var(--primary); color: var(--fg); }
.vibe-neutral { background: var(--surface); color: var(--fg); }
.vibe-negative { background: var(--accent); color: var(--bg); }
.vibe-legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font: 12px/1.5 var(--label); color: var(--muted); }
.vibe-legend i { display: inline-block; width: 10px; height: 10px; border: 1px solid var(--fg); margin-right: 6px; vertical-align: -1px; }
.vibes { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 6px; }
.vibes li { font: 13px/1.5 var(--label); }
.workstyle { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 16px 24px; margin-top: 16px; }
.workstyle p { margin: 4px 0 10px; }
.workstyle ul.rituals { margin: 4px 0 10px; padding-left: 18px; }
.workstyle ul.rituals li { margin-bottom: 6px; }
.handoff { border-left: 3px solid var(--primary); padding-left: 12px; }
figure.pie { margin: 0; }
figure.pie svg { display: block; width: 160px; height: 160px; margin: 8px 0; }
figure.pie path, figure.pie circle { stroke: var(--bg); stroke-width: 2; }
figure.hours { margin: 20px 0 0; }
figure.hours svg { display: block; width: 100%; max-width: 360px; height: auto; margin-top: 6px; }
figure.hours rect.bar { fill: var(--muted); }
figure.hours rect.hit { fill: transparent; }
figure.hours g:hover rect.bar { fill: var(--accent); }
figure.hours text { font: 10px var(--label); fill: var(--muted); }
figure.hours line { stroke: var(--rule); }
.pie-legend { list-style: none; padding: 0; margin: 0; font: 12px/1.5 var(--label); }
.pie-legend li { display: flex; gap: 8px; align-items: baseline; }
.pie-legend i { flex: none; width: 10px; height: 10px; border-radius: 2px; }
.pie-legend .pct { margin-left: auto; color: var(--muted); font-variant-numeric: tabular-nums; }
.chip { display: inline-block; font: 600 10px/1.6 var(--label); letter-spacing: .08em; text-transform: uppercase; padding: 0 6px; border: 1px solid var(--fg); margin-right: 8px; }
@media (max-width: 640px) { .grid4, .workstyle { grid-template-columns: 1fr; } .stat { border-right: 0; border-bottom: 1px solid var(--rule); } }
"""

FONTS = ("https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600"
         "&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap")


def _support(obs):
    """Badge for how many of a participant's agents reported an observation."""
    n, of = obs.get("agents"), obs.get("of")
    if n is None:
        return ""
    return f'<span class="support">{n}/{of} agents</span>' if of else f'<span class="support">{n} agents</span>'


def _evidence(obs):
    ev = obs.get("evidence")
    return f'<p class="evidence">{escape(ev)}</p>' if ev else ""


def _cell(who, what, obs):
    return (f'<div class="cell"><div class="label"><span><span class="who">{who}</span> · {what}</span>'
            f'{_support(obs)}</div><p>{escape(obs["text"])}</p>{_evidence(obs)}</div>')


def _ranked(items):
    out = []
    for i, item in enumerate(items, 1):
        prev = item.get("prevalence")
        prev_html = f'<p class="label">{escape(prev)}</p>' if prev else ""
        out.append(f'<li><div class="rank">{i:02d}</div><h3>{escape(item["title"])}</h3>'
                   f'<p>{escape(item["description"])}</p>{prev_html}{_evidence(item)}</li>')
    return '<ol class="ranked">' + "".join(out) + "</ol>"


VIBES = ("positive", "neutral", "negative")


def _vibe_section(participants, summary):
    """Overall sentiment distribution across every agent report."""
    counts = Counter(v["label"] for p in participants for v in p.get("vibe", []))
    total = sum(counts.values())
    if not total:
        return ""
    bar = "".join(f'<span class="vibe-{k}" style="flex:{counts[k]}">{counts[k]}</span>'
                  for k in VIBES if counts[k])
    legend = "".join(f'<span><i class="vibe-{k}"></i>{k} {counts[k]}/{total} '
                     f'({100 * counts[k] / total:.0f}%)</span>' for k in VIBES)
    return (f'<h2>Vibe check</h2><p class="label">Sentiment of each agent report toward the user '
            f'and the collaboration</p><div class="vibe-bar">{bar}</div>'
            f'<div class="vibe-legend">{legend}</div><p>{escape(summary)}</p>')


def _vibe_list(p):
    items = "".join(f'<li><span class="chip vibe-{escape(v["label"])}">{escape(v["label"])}</span>'
                    f'<b>{escape(v["report"])}</b> · {escape(v["rationale"])}</li>'
                    for v in p.get("vibe", []))
    return f'<ul class="vibes">{items}</ul>' if items else ""


# Colourblind-safe categorical set (validated against --bg); "Other" stays grey.
CATEGORICAL = ["#0072B2", "#E69F00", "#8F17CF", "#009E73", "#D55E00", "#56B4E9"]
OTHER = "#999999"


def task_colours(participants):
    """Fixed category -> colour map, ordered by total share across participants,
    so a category keeps its colour in every participant's pie."""
    totals = Counter()
    for p in participants:
        for t in p.get("task_mix", []):
            if t["category"].lower() != "other":
                totals[t["category"]] += t["share"]
    cats = [c for c, _ in totals.most_common()]
    return {c: CATEGORICAL[i] if i < len(CATEGORICAL) else OTHER for i, c in enumerate(cats)}


def _pie(task_mix, colours):
    """Task-type mix as an SVG pie with a labelled legend."""
    total = sum(t["share"] for t in task_mix)
    if not total:
        return ""
    cx = cy = r = 80
    slices, legend, angle = [], [], -math.pi / 2
    for t in task_mix:
        frac = t["share"] / total
        colour = colours.get(t["category"], OTHER)
        tip = f'<title>{escape(t["category"])}: {100 * frac:.0f}%</title>'
        if frac >= 0.9999:
            slices.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{colour}">{tip}</circle>')
        elif frac > 0:
            end = angle + 2 * math.pi * frac
            x0, y0 = cx + r * math.cos(angle), cy + r * math.sin(angle)
            x1, y1 = cx + r * math.cos(end), cy + r * math.sin(end)
            large = 1 if frac > 0.5 else 0
            slices.append(f'<path d="M{cx},{cy} L{x0:.2f},{y0:.2f} A{r},{r} 0 {large} 1 {x1:.2f},{y1:.2f} Z" '
                          f'fill="{colour}">{tip}</path>')
            angle = end
        legend.append(f'<li><i style="background:{colour}"></i><span>{escape(t["category"])}</span>'
                      f'<span class="pct">{100 * frac:.0f}%</span></li>')
    return (f'<figure class="pie"><div class="label">Task-type mix (mean of agent estimates)</div>'
            f'<svg viewBox="0 0 160 160" role="img" aria-label="Task-type mix pie chart">{"".join(slices)}</svg>'
            f'<ul class="pie-legend">{"".join(legend)}</ul></figure>')


def _hours(counts):
    """Prompts per local hour of day as an SVG bar histogram."""
    if not counts or not any(counts):
        return ""
    w, h, left, bottom, top = 360, 140, 30, 20, 8
    bw = (w - left) / 24
    peak = max(counts)
    plot_h = h - bottom - top
    bars = []
    for hour, n in enumerate(counts):
        x = left + hour * bw
        bh = plot_h * n / peak
        bars.append(f'<g><title>{hour:02d}:00–{hour:02d}:59 · {n:,} prompts</title>'
                    f'<rect class="hit" x="{x:.1f}" y="{top}" width="{bw:.1f}" height="{plot_h}"/>'
                    f'<rect class="bar" x="{x + 1:.1f}" y="{top + plot_h - bh:.1f}" width="{bw - 2:.1f}" '
                    f'height="{bh:.1f}" rx="1"/></g>')
    ticks = "".join(f'<text x="{left + hour * bw:.1f}" y="{h - 6}" text-anchor="middle">{hour:02d}:00</text>'
                    for hour in (0, 6, 12, 18))
    axis = (f'<line x1="{left}" x2="{w}" y1="{top + plot_h}" y2="{top + plot_h}"/>'
            f'<text x="{left - 4}" y="{top + 8}" text-anchor="end">{peak:,}</text>'
            f'<text x="{left - 4}" y="{top + plot_h}" text-anchor="end">0</text>')
    return (f'<figure class="hours"><div class="label">Prompts by hour of day (local time, '
            f'{sum(counts):,} total)</div><svg viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="Histogram of prompts by hour of day">{axis}{"".join(bars)}{ticks}</svg></figure>')


def _workstyle(p, colours, hours=None):
    if not hours and not any(p.get(k) for k in ("day_to_day", "rituals", "handoff", "task_mix")):
        return ""
    text = ""
    if d := p.get("day_to_day"):
        text += (f'<div class="label">Day to day and typical session {_support(d)}</div>'
                 f'<p>{escape(d["text"])}</p>{_evidence(d)}')
    if rituals := p.get("rituals"):
        items = "".join(f'<li>{escape(r["text"])} {_support(r)}{_evidence(r)}</li>' for r in rituals)
        text += f'<div class="label">Recurring workflows and rituals</div><ul class="rituals">{items}</ul>'
    if h := p.get("handoff"):
        text += f'<div class="label">Handoff</div><p class="handoff">{escape(h)}</p>'
    charts = _pie(p.get("task_mix", []), colours) + _hours(hours)
    return f'<div class="workstyle"><div>{text}</div><div>{charts}</div></div>'


def _participant(p, colours, hours=None):
    cells = "".join([
        _cell("User", "doing well", p["user_strength"]),
        _cell("User", "could improve", p["user_improvement"]),
        _cell("Agents", "doing well", p["agent_strength"]),
        _cell("Agents", "could improve", p["agent_improvement"]),
    ])
    archetype = f'<span class="label">{escape(p["archetype"])}</span>' if p.get("archetype") else ""
    u = p["unique"]
    return (f'<section class="participant"><div class="participant-head"><h3>{escape(p["id"])}</h3>{archetype}</div>'
            f'<div class="grid4">{cells}</div>'
            f'<div class="unique"><div class="label"><span class="who" style="color:var(--accent)">Unique</span></div>'
            f'<p>{escape(u["text"])}</p>{_evidence(u)}</div>{_workstyle(p, colours, hours)}'
            f'{_vibe_list(p)}</section>')


def count_runs(qc_path=None, meta_path=None):
    """Return (n_agents, Counter of models) from parse_reports.py output."""
    n_agents = 0
    if qc_path:
        with open(qc_path) as f:
            n_agents = sum(1 for _ in csv.DictReader(f))
    models = Counter()
    if meta_path:
        with open(meta_path) as f:
            for row in csv.DictReader(f):
                if row.get("Field", "").lower().startswith("agent / model") and row.get("Value"):
                    models[row["Value"]] += 1
    return n_agents, models


def load_activity(path):
    """{participant: [prompts for hours 0-23]} from parsed activity_hours.csv."""
    activity = {}
    if path and Path(path).exists():
        with open(path) as f:
            for row in csv.DictReader(f):
                activity.setdefault(row["participant"], [0] * 24)[int(row["hour"])] = int(row["prompts"])
    return activity


def render(synthesis, n_agents, models, activity=None):
    participants = synthesis["participants"]
    colours = task_colours(participants)
    n_users = len(participants)
    model_text = ", ".join(f"{m} ×{n}" for m, n in models.most_common()) or "n/a"
    stats = "".join([
        f'<div class="stat"><div class="label">Users</div><div class="num">{n_users}</div></div>',
        f'<div class="stat"><div class="label">Agent reports</div><div class="num">{n_agents}</div></div>',
        f'<div class="stat"><div class="label">Agents per user</div>'
        f'<div class="num">{n_agents / n_users:.0f}</div></div>' if n_users else "",
        f'<div class="stat"><div class="label">Models</div><div class="num small">{escape(model_text)}</div></div>',
        f'<div class="stat"><div class="label">Compiled</div>'
        f'<div class="num small">{escape(synthesis.get("date", ""))}</div></div>',
    ])
    notes = "".join(f"<p>{escape(n)}</p>" for n in synthesis.get("notes", []))
    if prov := synthesis.get("provenance"):
        notes += "<p>Synthesis: " + escape(", ".join(f"{k} {v}" for k, v in prov.items() if v is not None)) + "</p>"
    title = escape(synthesis.get("title", "Working with Claude Code"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>{CSS}</style>
</head>
<body>
<main>
<header class="masthead">
  <div class="eyebrow">HCI survey · Claude Code user interaction</div>
  <h1>{title}</h1>
  <p class="dek">{escape(synthesis.get("dek", ""))}</p>
</header>
<div class="stats">{stats}</div>

{_vibe_section(participants, synthesis.get("vibe_summary", ""))}

<h2>Top 3 common interaction patterns</h2>
{_ranked(synthesis["common_interactions"])}

<h2>When things go wrong: top 3 recovery strategies</h2>
{_ranked(synthesis["recovery_strategies"])}

<h2>Participants</h2>
{"".join(_participant(p, colours, (activity or {}).get(p["id"])) for p in participants)}

<footer class="notes">{notes}</footer>
</main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("synthesis", help="synthesis.json from the synthesis step")
    parser.add_argument("--qc", help="qc.csv from parse_reports.py (agent count)")
    parser.add_argument("--meta", help="meta.csv from parse_reports.py (model counts)")
    parser.add_argument("--activity", help="activity_hours.csv from parse_reports.py (optional)")
    parser.add_argument("-o", "--out", required=True, help="output HTML path")
    args = parser.parse_args()

    synthesis = json.loads(Path(args.synthesis).read_text())
    n_agents, models = count_runs(args.qc, args.meta)

    if args.qc:
        with open(args.qc) as f:
            qc_ids = {row["participant"] for row in csv.DictReader(f)}
        syn_ids = {p["id"] for p in synthesis["participants"]}
        if qc_ids != syn_ids:
            print(f"warning: participants differ between qc.csv {sorted(qc_ids)} "
                  f"and synthesis {sorted(syn_ids)}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(synthesis, n_agents, models, load_activity(args.activity)))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
