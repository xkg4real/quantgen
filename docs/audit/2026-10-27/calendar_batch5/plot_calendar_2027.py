"""2027 weekday closures of the five proposed batch-5 holiday files, coloured by evidence grade (report section 4).

    python docs/audit/2026-10-27/calendar_batch5/plot_calendar_2027.py <repo> <out.png>      (needs matplotlib)
"""
import datetime as dt
import sys

import matplotlib
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

repo, out = sys.argv[1], sys.argv[2]
SURF, INK, INK2 = "#fcfcfb", "#0b0b0b", "#52514e"
OPEN, CLOSED, INFERRED, EARLY = "#eceae4", "#2a78d6", "#eb6834", "#1baf7a"
cals = [("JPX", "Tokyo"), ("SSE", "Shanghai"), ("HKEX", "Hong Kong"), ("TWSE", "Taiwan"), ("CME", "CME equity futures")]


def rows(c):
    d = yaml.safe_load(open(f"{repo}/docs/audit/2026-10-27/calendar_batch5/proposed/holidays_{c}.yaml", encoding="utf-8"))
    return {r["date"]: (r["kind"], r["evidence"][0]) for r in d["rows"] if r["date"].startswith("2027")}


start = dt.date(2027, 1, 1)
start_mon = start - dt.timedelta(days=start.weekday())
fig, axes = plt.subplots(len(cals), 1, figsize=(13, 10.6), facecolor=SURF)
for ax, (c, label) in zip(axes, cals):
    m = rows(c)
    ax.set_facecolor(SURF)
    d = start
    while d.year == 2027:
        if d.weekday() < 5:
            w, y = (d - start_mon).days // 7, 4 - d.weekday()
            kind, grade = m.get(d.isoformat(), (None, None))
            fc = OPEN if kind is None else EARLY if kind == "early_close" else INFERRED if grade == "C" else CLOSED
            ax.add_patch(Rectangle((w + 0.06, y + 0.06), 0.88, 0.88, facecolor=fc, edgecolor=SURF, linewidth=1.5,
                                   hatch="////" if grade == "C" else None))
        d += dt.timedelta(days=1)
    n_cl = sum(1 for k, _ in m.values() if k == "closed")
    n_ec = sum(1 for k, _ in m.values() if k == "early_close")
    n_c = sum(1 for _, g in m.values() if g == "C")
    pl = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")
    ax.set_title(f"{c} ({label})  -  2027: {pl(n_cl, 'weekday closure')}, {pl(n_ec, 'early close')}, "
                 f"{n_c} inferred (grade C)", loc="left", fontsize=10.5, color=INK, pad=8)
    ax.set_xlim(0, 53)
    ax.set_ylim(0, 5)
    ax.set_aspect("equal")
    ax.set_yticks([4.5, 3.5, 2.5, 1.5, 0.5])
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri"], fontsize=7.5, color=INK2)
    ax.set_xticks([((dt.date(2027, mo, 1) - start_mon).days // 7 + 0.5) for mo in range(1, 13)])
    ax.set_xticklabels([dt.date(2027, mo, 1).strftime("%b") for mo in range(1, 13)], fontsize=8, color=INK2)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
fig.legend(handles=[Patch(facecolor=CLOSED, label="closed: exchange notice or government list (A/B)"),
                    Patch(facecolor=INFERRED, hatch="////", edgecolor=SURF, label="closed: inferred, re-check (C)"),
                    Patch(facecolor=EARLY, label="early close"),
                    Patch(facecolor=OPEN, label="trading weekday")],
           loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK)
fig.suptitle("2027 holiday files proposed for signing (calendar audit 5) - weekdays only", x=0.012, ha="left",
             fontsize=13, color=INK, weight="bold")
fig.tight_layout(rect=(0, 0.05, 1, 0.97), h_pad=2.2)
fig.savefig(out, dpi=150, facecolor=SURF)
print("saved", out)
