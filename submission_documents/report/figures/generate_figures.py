"""
generate_figures.py
Run from the Report/ directory:
    python figures/generate_figures.py

Produces three PDF figures in Report/figures/:
  fig_time_comparison.pdf   — FR vs How-provenance time per query (log scale)
  fig_speedup.pdf           — Speedup ratio (FR / How) per query grouped by operator
  fig_space_annotation.pdf  — Annotation chars for Why and How semirings per query
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Raw data (from performance_analysis.md, median ms / annotation chars)
# ---------------------------------------------------------------------------

QUERIES = [
    ("Q01", "SELECT"),
    ("Q02", "SELECT"),
    ("Q03", "SELECT"),
    ("Q04", "SELECT"),
    ("Q05", "PROJECT"),
    ("Q06", "PROJECT"),
    ("Q07", "JOIN"),
    ("Q08", "JOIN"),
    ("Q09", "JOIN"),
    ("Q10", "JOIN"),
    ("Q15", "UNION-2"),
    ("Q16", "UNION-2"),
    ("Q17", "UNION-3"),
    ("Q18", "UNION+JOIN-2"),
    ("Q19", "UNION+JOIN-2"),
    ("Q20", "UNION+JOIN-3"),
]

FR_TIME = [87.3, 50.5, 50.2, 719.2, 129.7, 160.1,
           16449.6, 16415.2, 31322.0, 16475.5,
           141.8, 71.7, 82.7,
           32806.7, 60847.4, 47390.6]

BOOL_TIME  = [5.8, 3.2, 3.7, 247.0, 5.6, 3.1, 1567.5, 1507.7, 2847.3, 1481.1, 10.1,  5.4,  8.7, 3023.8, 5201.9, 4470.1]
BAG_TIME   = [5.1, 3.2, 3.7, 244.7, 5.5, 3.2, 1540.5, 1492.3, 2822.9, 1463.8, 10.4,  5.6,  9.0, 2993.7, 5217.5, 4487.6]
WHY_TIME   = [5.9, 3.4, 4.0, 375.7, 5.8, 3.4, 1743.3, 1689.5, 3003.0, 1595.7, 11.4,  5.9,  8.9, 3708.9, 5750.8, 5364.5]
HOW_TIME   = [5.5, 3.4, 3.8, 303.7, 5.7, 3.2, 1743.7, 1668.2, 2924.9, 1633.4, 10.9,  5.7,  9.1, 3591.7, 5708.2, 5204.7]

# annotation_chars (space, from performance_analysis.md)
WHY_CHARS = [208, 9015, 10855, 882464, 164, 9015,
             1154839, 199148, 35757, 176740,
             1758, 5000, 10602,
             1254452, 156982, 1588507]

HOW_CHARS = [168, 7055, 8495, 712048, 168, 7055,
             984423, 169644, 30845, 150548,
             1422, 3912, 8298,
             1069292, 135686, 1354147]

FR_CHARS  = [1298, 1172, 1217, 942, 1035532, 1240,
             1401, 1371, 1527, 1762,
             2292, 1994, 2941,
             2419, 2697, 3904]

labels    = [q[0] for q in QUERIES]
op_types  = [q[1] for q in QUERIES]

# colour per operator category
OP_COLOUR = {
    "SELECT":       "#4C72B0",
    "PROJECT":      "#DD8452",
    "JOIN":         "#55A868",
    "UNION-2":      "#C44E52",
    "UNION-3":      "#C44E52",
    "UNION+JOIN-2": "#8172B3",
    "UNION+JOIN-3": "#8172B3",
}

# ---------------------------------------------------------------------------
# Figure 1 — Time comparison (log scale bar chart)
# ---------------------------------------------------------------------------

x      = np.arange(len(labels))
width  = 0.35

fig, ax = plt.subplots(figsize=(14, 5))
bars_fr = ax.bar(x - width/2, FR_TIME,  width, label="Firing Rules",    color="#E8735A", edgecolor="white")
bars_hw = ax.bar(x + width/2, HOW_TIME, width, label="Semiring (How)",  color="#5A9BD5", edgecolor="white")

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Time (ms, log scale)")
ax.set_title("Execution Time: Firing Rules vs. How-Provenance Semiring")
ax.legend(loc="upper left")
ax.yaxis.grid(True, which="both", linestyle="--", alpha=0.4)
ax.set_axisbelow(True)

# colour x-tick labels by operator
for tick, op in zip(ax.get_xticklabels(), op_types):
    tick.set_color(OP_COLOUR.get(op, "black"))

# operator legend patches
unique_ops = dict.fromkeys(op_types)
op_patches = [mpatches.Patch(color=OP_COLOUR[op], label=op) for op in unique_ops]
ax.legend(handles=[
    mpatches.Patch(color="#E8735A", label="Firing Rules"),
    mpatches.Patch(color="#5A9BD5", label="Semiring (How)"),
] + op_patches, loc="upper left", fontsize=8, ncol=2)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_time_comparison.pdf"), bbox_inches="tight")
plt.close()
print("Saved fig_time_comparison.pdf")

# ---------------------------------------------------------------------------
# Figure 2 — Speedup ratio (FR / How)
# ---------------------------------------------------------------------------

speedup = [fr / hw for fr, hw in zip(FR_TIME, HOW_TIME)]

fig, ax = plt.subplots(figsize=(14, 4))
bar_colours = [OP_COLOUR.get(op, "#888") for op in op_types]
ax.bar(x, speedup, color=bar_colours, edgecolor="white", linewidth=0.5)
ax.axhline(y=1, color="black", linewidth=0.8, linestyle="--")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Speedup (FR time / Semiring time)")
ax.set_title("Semiring Speedup over Firing Rules (FR / How-Provenance)")
ax.yaxis.grid(True, linestyle="--", alpha=0.4)
ax.set_axisbelow(True)

for tick, op in zip(ax.get_xticklabels(), op_types):
    tick.set_color(OP_COLOUR.get(op, "black"))

op_patches = [mpatches.Patch(color=OP_COLOUR[op], label=op) for op in unique_ops]
ax.legend(handles=op_patches, loc="upper right", fontsize=8)

plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_speedup.pdf"), bbox_inches="tight")
plt.close()
print("Saved fig_speedup.pdf")

# ---------------------------------------------------------------------------
# Figure 3 — Annotation space (chars, log scale)
# ---------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(14, 5))
bars_fr  = ax.bar(x - width,     FR_CHARS,  width, label="FR (JSON)",       color="#E8735A", edgecolor="white")
bars_why = ax.bar(x,             WHY_CHARS, width, label="Why-Provenance",   color="#5A9BD5", edgecolor="white")
bars_how = ax.bar(x + width,     HOW_CHARS, width, label="How-Provenance",   color="#70AD47", edgecolor="white")

ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
ax.set_ylabel("Annotation size (characters, log scale)")
ax.set_title("Annotation / Explanation Size: FR JSON vs. Why vs. How")
ax.legend(loc="upper left", fontsize=9)
ax.yaxis.grid(True, which="both", linestyle="--", alpha=0.4)
ax.set_axisbelow(True)

for tick, op in zip(ax.get_xticklabels(), op_types):
    tick.set_color(OP_COLOUR.get(op, "black"))

plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig_space_annotation.pdf"), bbox_inches="tight")
plt.close()
print("Saved fig_space_annotation.pdf")

print("All figures generated in", OUT)
