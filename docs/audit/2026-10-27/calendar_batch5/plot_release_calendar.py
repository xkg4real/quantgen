"""Figure for the release_calendar audit: days from the end of each reference period to its release, per release,
coloured and shaped by evidence grade (docs/audit/2026-10-27/12_release_calendar.md).

    python docs/audit/2026-10-27/calendar_batch5/plot_release_calendar.py
"""
from __future__ import annotations

import calendar
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
import yaml  # noqa: E402

HERE = Path(__file__).resolve().parent
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
GRADE = {"A": ("#2a78d6", "o", "A: two records agree"), "B": ("#eb6834", "s", "B: one official record"),
         "C": ("#1baf7a", "^", "C: weekly rule (no 2027 DOL dates yet)")}
PANELS = (("CPI", "CPI (BLS)"), ("EMPSIT", "Employment Situation (BLS)"), ("PIO", "Personal Income and Outlays (BEA)"),
          ("CLAIMS", "Weekly claims (DOL)"))
SHUTDOWNS = ((date(2025, 10, 1), date(2025, 11, 12), "2025 lapse"), (date(2026, 1, 31), date(2026, 2, 3), "2026 lapse"))
TODAY = date(2026, 10, 28)


def period_end(release: str, period: date) -> date:
    if release == "CLAIMS":
        return period                                   # week-ending Saturday
    return period.replace(day=calendar.monthrange(period.year, period.month)[1])


def main() -> None:
    doc = yaml.safe_load((HERE / "proposed" / "release_calendar.yaml").read_text(encoding="utf-8"))
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "text.color": INK})
    fig, axes = plt.subplots(4, 1, figsize=(10, 9.2), sharex=True, facecolor=SURFACE)
    for ax, (rel, title) in zip(axes, PANELS):
        ax.set_facecolor(SURFACE)
        rows = [r for r in doc["rows"] if r["release"] == rel]
        for lo, hi, label in SHUTDOWNS:
            ax.axvspan(lo, hi, color="#d9d8d3", alpha=0.6, lw=0, zorder=0)
        ax.axvline(TODAY, color=INK2, lw=1, ls=(0, (3, 3)), zorder=1)
        for g, (color, marker, label) in GRADE.items():
            pts = [(date.fromisoformat(r["release_date"]),
                    (date.fromisoformat(r["release_date"]) - period_end(rel, date.fromisoformat(r["period"]))).days)
                   for r in rows if r["evidence"].startswith(g)]
            if pts:
                xs, ys = zip(*pts)
                ax.scatter(xs, ys, s=26 if rel != "CLAIMS" else 16, c=color, marker=marker, edgecolors=SURFACE,
                           linewidths=1.0, zorder=3, label=label)
        for r in rows:
            if r["time"] != "08:30":
                x = date.fromisoformat(r["release_date"])
                y = (x - period_end(rel, date.fromisoformat(r["period"]))).days
                ax.annotate(f"{r['time']} ET", (x, y), xytext=(6, 4), textcoords="offset points", fontsize=7.5,
                            color=INK2)
        ax.set_ylim(top=ax.get_ylim()[1] * 1.12)
        ax.set_title(title, loc="left", fontsize=10, color=INK, pad=4)
        ax.set_ylabel("days after period end")
        ax.grid(axis="y", color=GRID, lw=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    axes[3].annotate("2027: rule-derived, replace when DOL publishes", (date(2027, 6, 1), 5), xytext=(0, 14),
                     textcoords="offset points", fontsize=7.5, color=INK2, ha="center")
    handles, labels = [], []
    for ax in axes:
        h, lab = ax.get_legend_handles_labels()
        for hh, ll in zip(h, lab):
            if ll not in labels:
                handles.append(hh)
                labels.append(ll)
    handles += [Patch(color="#d9d8d3", alpha=0.6, lw=0),
                Line2D([], [], color=INK2, lw=1, ls=(0, (3, 3)))]
    labels += ["federal funding lapses (2025-10-01..11-12, 2026-01-31..02-03)",
               "audit date 2026-10-28: released (left), scheduled (right)"]
    fig.legend(handles, labels, loc="upper left", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.005, 0.968))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    axes[-1].set_xlim(date(2024, 12, 15), date(2028, 1, 15))
    fig.suptitle("release_calendar v1.0.0 (proposed): 264 release dates, 2025-2027", x=0.01, ha="left", fontsize=11.5,
                 color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.925))
    fig.savefig(HERE / "release_calendar.png", dpi=130, facecolor=SURFACE)


if __name__ == "__main__":
    main()
