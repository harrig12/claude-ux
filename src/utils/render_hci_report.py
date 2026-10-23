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
import re
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
.participant { border-top: 1px solid var(--fg); padding-top: 8px; margin-top: 16px; font-size: 13px; }
.participant > summary { cursor: pointer; list-style-position: outside; margin-left: 16px; }
.participant[open] > summary { margin-bottom: 8px; }
.cohort-pies { margin-top: 16px; }
.hours-legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font: 12px/1.5 var(--label); color: var(--muted); margin-top: 6px; }
.hours-legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }
.participant-head { display: inline-flex; flex-wrap: wrap; align-items: baseline; gap: 4px 16px; }
.participant-head h3 { font-size: 22px; }
.grid4 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); }
.cell { background: var(--bg); padding: 14px 16px; }
.cell .label { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.cell .label .who { color: var(--accent); }
.cell p { margin: 0; }
.unique { background: var(--surface); border-left: 3px solid var(--accent); padding: 10px 14px; margin: 8px 0 4px; font-size: 14px; }
.unique .label { color: var(--accent); }
.cohort-grid { margin-top: 16px; }
figure.models { margin: 0; }
.stat-models { grid-column: span 2; }
figure.models .models { margin-top: 6px; }
.compiled { font: 11px/1.6 var(--label); color: var(--muted); border-top: 3px double var(--fg); margin-top: 56px; padding-top: 12px; }
.prev { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.prev .track { flex: 1; height: 8px; background: var(--rule); border-radius: 4px; overflow: hidden; }
.prev .fill { height: 100%; background: var(--accent); border-radius: 4px; }
.prev .label { white-space: nowrap; }
.models { display: grid; grid-template-columns: minmax(0, max-content) minmax(80px, 1fr) max-content; gap: 6px 12px;
  align-items: center; max-width: 640px; font: 12px/1.5 var(--label); }
.models .track { height: 12px; }
.models .fill { height: 100%; background: var(--muted); border-radius: 0 4px 4px 0; }
.models .track:hover .fill { background: var(--accent); }
.models .n { color: var(--muted); font-variant-numeric: tabular-nums; }
.vibe-bar { display: flex; height: 28px; border: 1px solid var(--fg); margin: 8px 0 6px; }
.vibe-bar span { display: flex; align-items: center; justify-content: center; font: 600 11px/1 var(--label); letter-spacing: .08em; text-transform: uppercase; }
.vibe-positive { background: var(--primary); color: var(--fg); }
.vibe-neutral { background: var(--surface); color: var(--fg); }
.vibe-negative { background: var(--accent); color: var(--bg); }
.vibe-legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font: 12px/1.5 var(--label); color: var(--muted); }
.vibe-legend i { display: inline-block; width: 10px; height: 10px; border: 1px solid var(--fg); margin-right: 6px; vertical-align: -1px; }
.vibes { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 6px; }
.vibes li { font: 13px/1.5 var(--label); }
.workstyle { margin-top: 16px; max-width: 760px; }
.workstyle p { margin: 4px 0 10px; }
.workstyle ul.rituals { margin: 4px 0 10px; padding-left: 18px; }
.workstyle ul.rituals li { margin-bottom: 6px; }
.handoff { border-left: 3px solid var(--primary); padding-left: 12px; }
figure.pie { margin: 0; }
figure.pie svg { display: block; width: 84px; height: 84px; margin: 4px 0 0; }
figure.pie.main svg { width: 200px; height: 200px; margin: 6px 0 10px; }
.pie-layout { display: flex; flex-wrap: wrap; align-items: flex-start; gap: 24px 48px; margin: 8px 0 12px; }
.pies { display: grid; grid-template-columns: repeat(3, max-content); gap: 14px 22px; }
figure.pie path, figure.pie circle { stroke: var(--bg); stroke-width: 2; }
figure.hours { margin: 0; }
figure.hours svg { display: block; width: 100%; max-width: 560px; height: auto; margin-top: 6px; }
figure.hours rect.bar { stroke: var(--bg); stroke-width: 1; }
figure.hours rect.hit { fill: transparent; }
figure.hours rect.bar:hover { opacity: .75; }
figure.hours text { font: 10px var(--label); fill: var(--muted); }
figure.hours line { stroke: var(--rule); }
.pie-legend { list-style: none; padding: 0; margin: 0 0 4px; max-width: 360px; font: 12px/1.5 var(--label); }
.pie-legend li { display: flex; gap: 8px; align-items: baseline; }
.pie-legend i { flex: none; width: 10px; height: 10px; border-radius: 2px; }
.pie-legend .pct { margin-left: auto; color: var(--muted); font-variant-numeric: tabular-nums; }
.chip { display: inline-block; font: 600 10px/1.6 var(--label); letter-spacing: .08em; text-transform: uppercase; padding: 0 6px; border: 1px solid var(--fg); margin-right: 8px; }
@media (max-width: 640px) { .grid4 { grid-template-columns: 1fr; } .stat { border-right: 0; border-bottom: 1px solid var(--rule); } .stat-models { grid-column: auto; } }
"""

FONTS = ("https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600"
         "&family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap")


def _text(obs):
    """Observation text, whether given as a plain string or an observation object."""
    return obs["text"] if isinstance(obs, dict) else obs


def _cell(who, what, obs):
    return (f'<div class="cell"><div class="label"><span><span class="who">{who}</span> · {what}</span></div>'
            f'<p>{escape(_text(obs))}</p></div>')


def _grid4(src):
    """Doing well / could improve square for users and agents."""
    return '<div class="grid4">' + "".join([
        _cell("User", "doing well", src["user_strength"]),
        _cell("User", "could improve", src["user_improvement"]),
        _cell("Agents", "doing well", src["agent_strength"]),
        _cell("Agents", "could improve", src["agent_improvement"]),
    ]) + "</div>"


def _prevalence(prev):
    """'k of N users' as a filled bar; any other wording falls back to text."""
    if not prev:
        return ""
    m = re.search(r"(\d+)\s*(?:of|/)\s*(\d+)", prev)
    if not m or not int(m[2]):
        return f'<p class="label">{escape(prev)}</p>'
    k, n = int(m[1]), int(m[2])
    return (f'<div class="prev" title="{escape(prev)}"><div class="track">'
            f'<div class="fill" style="width:{100 * k / n:.0f}%"></div></div>'
            f'<span class="label">{k}/{n} users</span></div>')


def _ranked(items):
    out = []
    for i, item in enumerate(items, 1):
        out.append(f'<li><div class="rank">{i:02d}</div><h3>{escape(item["title"])}</h3>'
                   f'<p>{escape(item["description"])}</p>{_prevalence(item.get("prevalence"))}</li>')
    return '<ol class="ranked">' + "".join(out) + "</ol>"


def _models(models):
    """Agent reports per model as horizontal bars."""
    if not models:
        return ""
    peak = max(models.values())
    rows = "".join(f'<span>{escape(m)}</span><div class="track" title="{escape(m)}: {n} report{"s" * (n != 1)}">'
                   f'<div class="fill" style="width:{100 * n / peak:.0f}%"></div></div>'
                   f'<span class="n">{n}</span>' for m, n in models.most_common())
    return f'<figure class="models"><div class="label">Agent reports by model</div><div class="models">{rows}</div></figure>'


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


def _palette(keys):
    """Fixed key -> colour map in the given order; keys past the palette and
    'Other' share the grey."""
    keys = [k for k in keys if k.lower() != "other"]
    return {k: CATEGORICAL[i] if i < len(CATEGORICAL) else OTHER for i, k in enumerate(keys)}


def cohort_mix(participants, categories=None):
    """Mean task share per category across participants (missing = 0), in the
    synthesis's shared category order, Other last, rescaled to sum to 100."""
    if not categories:
        totals = Counter()
        for p in participants:
            for t in p.get("task_mix", []):
                totals[t["category"]] += t["share"]
        categories = [c for c, _ in totals.most_common()]
    categories = sorted(categories, key=lambda c: c.lower() == "other")
    mean = Counter()
    for p in participants:
        total = sum(t["share"] for t in p.get("task_mix", [])) or 1
        for t in p.get("task_mix", []):
            mean[t["category"]] += 100 * t["share"] / total / len(participants)
    scale = 100 / (sum(mean[c] for c in categories) or 1)
    return [{"category": c, "share": mean[c] * scale} for c in categories if mean[c] > 0]


def _pie(task_mix, colours, label, main=False):
    """One task-type mix as a small SVG pie; shares are in the slice tooltips."""
    total = sum(t["share"] for t in task_mix)
    if not total:
        return ""
    cx = cy = r = 80
    slices, angle = [], -math.pi / 2
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
    return (f'<figure class="pie{" main" if main else ""}"><div class="label">{escape(label)}</div>'
            f'<svg viewBox="0 0 160 160" role="img" aria-label="{escape(label)} task-type mix pie chart">'
            f'{"".join(slices)}</svg></figure>')


def _pies(participants, categories=None):
    """Task-type mix: a large cohort-mean pie with the shared legend, beside small
    multiples per participant. Colours are keyed to category so they match."""
    mix = cohort_mix(participants, categories)
    if not mix:
        return ""
    order = [m["category"] for m in mix]
    colours = _palette(order)
    small = "".join(_pie(cohort_mix([p], order), colours, p["id"]) for p in participants)
    legend = "".join(f'<li><i style="background:{colours.get(m["category"], OTHER)}"></i>'
                     f'<span>{escape(m["category"])}</span><span class="pct">{m["share"]:.0f}%</span></li>'
                     for m in mix)
    return (f'<div class="pie-layout">'
            f'<div>{_pie(mix, colours, "Task-type mix (mean across users)", main=True)}'
            f'<ul class="pie-legend">{legend}</ul></div>'
            f'<div><div class="label">By participant (hover a slice for its share)</div>'
            f'<div class="pies">{small}</div></div></div>')


def _hours(activity, colours):
    """Prompts per local hour of day, stacked by participant, as an SVG histogram."""
    activity = {p: c for p, c in activity.items() if any(c)}
    if not activity:
        return ""
    w, h, left, bottom, top = 560, 160, 34, 20, 8
    bw = (w - left) / 24
    totals = [sum(c[hour] for c in activity.values()) for hour in range(24)]
    peak = max(totals)
    plot_h = h - bottom - top
    bars = []
    for hour in range(24):
        x, y = left + hour * bw, top + plot_h
        for pid, counts in activity.items():
            bh = plot_h * counts[hour] / peak
            if not bh:
                continue
            y -= bh
            bars.append(f'<rect class="bar" x="{x + 1:.1f}" y="{y:.1f}" width="{bw - 2:.1f}" height="{bh:.1f}" '
                        f'fill="{colours.get(pid, OTHER)}"><title>{escape(pid)} · {hour:02d}:00–{hour:02d}:59 · '
                        f'{counts[hour]:,} prompts</title></rect>')
    ticks = "".join(f'<text x="{left + hour * bw:.1f}" y="{h - 6}" text-anchor="middle">{hour:02d}:00</text>'
                    for hour in (0, 6, 12, 18))
    axis = (f'<line x1="{left}" x2="{w}" y1="{top + plot_h}" y2="{top + plot_h}"/>'
            f'<text x="{left - 4}" y="{top + 8}" text-anchor="end">{peak:,}</text>'
            f'<text x="{left - 4}" y="{top + plot_h}" text-anchor="end">0</text>')
    legend = "".join(f'<span><i style="background:{colours.get(pid, OTHER)}"></i>{escape(pid)} '
                     f'({sum(c):,})</span>' for pid, c in activity.items())
    total = sum(totals)
    return (f'<figure class="hours"><div class="label">Prompts by hour of day (local time, {total:,} total)</div>'
            f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Histogram of prompts by hour of day, '
            f'stacked by participant">{axis}{"".join(bars)}{ticks}</svg>'
            f'<div class="hours-legend">{legend}</div></figure>')


def _cohort(synthesis):
    """Cohort-level summary: text, doing well / could improve square and pooled
    task mix."""
    participants = synthesis["participants"]
    pie = _pies(participants, synthesis.get("task_categories"))
    summary = f'<p>{escape(synthesis["cohort_summary"])}</p>' if synthesis.get("cohort_summary") else ""
    grid = f'<div class="cohort-grid">{_grid4(synthesis["cohort_grid"])}</div>' if synthesis.get("cohort_grid") else ""
    return (f'<h2>Cohort</h2>{summary}{grid}'
            f'<div class="cohort-pies">{pie}</div>')


def _activity(participants, activity):
    """Prompts by hour of day, stacked by participant, as its own section."""
    hours = _hours({p["id"]: activity[p["id"]] for p in participants if p["id"] in activity},
                   _palette(p["id"] for p in participants))
    return f'<h2>Activity</h2>{hours}' if hours else ""


def _workstyle(p):
    if not any(p.get(k) for k in ("day_to_day", "rituals", "handoff")):
        return ""
    text = ""
    if d := p.get("day_to_day"):
        text += f'<div class="label">Day to day and typical session</div><p>{escape(_text(d))}</p>'
    if rituals := p.get("rituals"):
        items = "".join(f'<li>{escape(_text(r))}</li>' for r in rituals)
        text += f'<div class="label">Recurring workflows and rituals</div><ul class="rituals">{items}</ul>'
    if h := p.get("handoff"):
        text += f'<div class="label">Handoff</div><p class="handoff">{escape(h)}</p>'
    return f'<div class="workstyle">{text}</div>'


def _participant(p):
    archetype = f'<span class="label">{escape(p["archetype"])}</span>' if p.get("archetype") else ""
    return (f'<details class="participant"><summary><span class="participant-head"><h3>{escape(p["id"])}</h3>'
            f'{archetype}</span><div class="unique"><div class="label">Unique</div>'
            f'{escape(_text(p["unique"]))}</div></summary>'
            f'{_grid4(p)}{_workstyle(p)}{_vibe_list(p)}</details>')


def count_runs(qc_path=None, meta_path=None):
    """Return (Counter of agent reports per participant, Counter of models) from
    parse_reports.py output."""
    agents = Counter()
    if qc_path:
        with open(qc_path) as f:
            agents.update(row["participant"] for row in csv.DictReader(f))
    models = Counter()
    if meta_path:
        with open(meta_path) as f:
            for row in csv.DictReader(f):
                if row.get("Field", "").lower().startswith("agent / model") and row.get("Value"):
                    models[row["Value"]] += 1
    return agents, models


def load_activity(path):
    """{participant: [prompts for hours 0-23]} from parsed activity_hours.csv."""
    activity = {}
    if path and Path(path).exists():
        with open(path) as f:
            for row in csv.DictReader(f):
                activity.setdefault(row["participant"], [0] * 24)[int(row["hour"])] = int(row["prompts"])
    return activity


def render(synthesis, agents, models, activity=None):
    participants = synthesis["participants"]
    activity = activity or {}
    n_users = len(participants)
    n_agents = sum(agents.values())
    stats = "".join([
        f'<div class="stat"><div class="label">Users</div><div class="num">{n_users}</div></div>',
        f'<div class="stat"><div class="label">Agent reports</div><div class="num">{n_agents}</div></div>',
        f'<div class="stat stat-models">{_models(models)}</div>' if models else "",
    ])
    compiled = f'<footer class="compiled">Compiled {escape(synthesis["date"])}</footer>' if synthesis.get("date") else ""
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

{_cohort(synthesis)}

{_vibe_section(participants, synthesis.get("vibe_summary", ""))}

<h2>Top 3 common interaction patterns</h2>
{_ranked(synthesis["common_interactions"])}

<h2>When things go wrong: top 3 recovery strategies</h2>
{_ranked(synthesis["recovery_strategies"])}

<h2>Participants</h2>
<p class="label">What sets each participant apart; click for the deep dive</p>
{"".join(_participant(p) for p in participants)}

{_activity(participants, activity)}

{compiled}
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
    agents, models = count_runs(args.qc, args.meta)

    if args.qc:
        with open(args.qc) as f:
            qc_ids = {row["participant"] for row in csv.DictReader(f)}
        syn_ids = {p["id"] for p in synthesis["participants"]}
        if qc_ids != syn_ids:
            print(f"warning: participants differ between qc.csv {sorted(qc_ids)} "
                  f"and synthesis {sorted(syn_ids)}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(synthesis, agents, models, load_activity(args.activity)))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
