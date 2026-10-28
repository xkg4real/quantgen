import sys, yaml, datetime as dt
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
repo, out = sys.argv[1], sys.argv[2]
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
OPEN, CLOSED, ADDED, EARLY = "#eceae4", "#2a78d6", "#eb6834", "#1baf7a"
cals = ["KRX", "NYSE", "FED", "SIFMA"]
def kinds(path):
    d = yaml.safe_load(open(path)); m = {}
    for r in d["rows"]:
        if r["date"].startswith("2027"): m[r["date"]] = r["kind"]
    return m
old = {c: kinds(f"{repo}/core/calendars/data/holidays_{c}.yaml") for c in cals}
new = {c: kinds(f"{repo}/docs/audit/2026-10-27/calendar_T-CAL-02/proposed/holidays_{c}.yaml") for c in cals}
start = dt.date(2027, 1, 1); start_mon = start - dt.timedelta(days=start.weekday())
fig, axes = plt.subplots(len(cals), 1, figsize=(13, 8.8), facecolor=SURF)
for ax, c in zip(axes, cals):
    ax.set_facecolor(SURF)
    d = start
    while d.year == 2027:
        if d.weekday() < 5:
            w = (d - start_mon).days // 7; y = 4 - d.weekday(); k = new[c].get(d.isoformat())
            changed = k is not None and old[c].get(d.isoformat()) != k
            fc = OPEN if k is None else (ADDED if changed else (EARLY if k == "early_close" else CLOSED))
            ax.add_patch(Rectangle((w + 0.06, y + 0.06), 0.88, 0.88, facecolor=fc, edgecolor=SURF, linewidth=1.5,
                                   hatch="////" if changed else None))
        d += dt.timedelta(days=1)
    n_cl = sum(1 for v in new[c].values() if v == "closed"); n_ec = sum(1 for v in new[c].values() if v == "early_close")
    n_ch = sum(1 for k, v in new[c].items() if old[c].get(k) != v)
    pl = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")
    ax.set_title(f"{c}  -  2027: {pl(n_cl, 'weekday closure')}, {pl(n_ec, 'early close')}, "
                 f"{n_ch} added or changed by the audit", loc="left", fontsize=10.5, color=INK, pad=16)
    ax.set_xlim(0, 53); ax.set_ylim(0, 5); ax.set_aspect("equal")
    ax.set_yticks([4.5, 3.5, 2.5, 1.5, 0.5]); ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri"], fontsize=7.5, color=INK2)
    mt = [((dt.date(2027, m, 1) - start_mon).days // 7 + 0.5) for m in range(1, 13)]
    ax.set_xticks(mt); ax.set_xticklabels([dt.date(2027, m, 1).strftime("%b") for m in range(1, 13)], fontsize=8, color=INK2)
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    # direct labels for audit changes only (selective)
    for k, v in sorted(new[c].items()):
        if old[c].get(k) != v:
            dd = dt.date.fromisoformat(k); w = (dd - start_mon).days // 7
            ax.annotate(dd.strftime("%m-%d"), (w + 0.5, 5), xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, color=INK, weight="bold")
fig.legend(handles=[Patch(facecolor=CLOSED, label="closed (already in draft)"),
                    Patch(facecolor=EARLY, label="early close (already in draft)"),
                    Patch(facecolor=ADDED, hatch="////", edgecolor=SURF, label="added or changed by the audit"),
                    Patch(facecolor=OPEN, label="open weekday")],
           loc="lower center", ncol=4, frameon=False, fontsize=9, labelcolor=INK)
fig.suptitle("2027 holiday files proposed for signing (T-CAL-02) - weekdays only", x=0.012, ha="left",
             fontsize=13, color=INK, weight="bold")
fig.tight_layout(rect=(0, 0.05, 1, 0.97), h_pad=2.2)
fig.savefig(out, dpi=150, facecolor=SURF)
print("saved", out)
