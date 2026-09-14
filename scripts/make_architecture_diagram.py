#!/usr/bin/env python3
"""Regenerate the architecture / workflow diagram from the project's own metrics.

The version embedded in the report carries figures from an earlier run -- "~50
UAE government apps", "52,498 raw reviews", "19,916 reviews" in the modelling
set -- against the 136 / 74,412 / 48,930 reported everywhere else. Reading the
counts from ``results/metrics.json`` means the diagram cannot fall out of step
with the pipeline again.

    python scripts/make_architecture_diagram.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parents[1]
M = json.loads((REPO / "results" / "metrics.json").read_text())
OUT = REPO / "results" / "figures" / "fig4_architecture.png"

ds, eda = M["dataset"], M["eda"]
splits = {r["split"]: r for r in M["split"]["summary"]}

# Palette taken from the capstone presentation template's theme so the diagram
# sits inside the deck rather than on top of it.
NAVY   = "#1C3678"
TEAL   = "#1A9988"
GOLD   = "#C79212"
RED    = "#B3373C"
INK    = "#1A1A1A"
GREY   = "#5A6472"
LINE   = "#7A8595"

STAGES = [
    # (row, index, title, lines, colour)
    (0, 0, "1. Data Ingestion",
     ["Google Play + App Store",
      f"{ds['apps']} UAE government apps",
      f"{ds['raw_rows']:,} raw reviews",
      "Notebook 01"], NAVY),
    (0, 1, "2. Preprocessing",
     ["Normalisation, dedup,", "Arabic orthography,",
      "language detection", "Notebook 02"], NAVY),
    (0, 2, "3. Weak Labelling",
     ["4–5 stars = Satisfied", "1–2 stars = Dissatisfied",
      "3 stars excluded", "Notebook 04"], NAVY),
    (0, 3, "4. EDA",
     ["Length bands,", "class balance,",
      "language split", "Notebook 03"], NAVY),
    (0, 4, "5. Modelling Set",
     [f"{ds['modelling_rows']:,} reviews",
      "(≥ 6 words,", "Arabic + English)",
      "70 / 15 / 15 split"], TEAL),

    (1, 0, "6. Feature Engineering",
     ["TF-IDF word 1–2 + char 3–5", "grams (clean_text)",
      "Raw text for transformer", "tokenisers"], GOLD),
    (1, 1, "7. Model Development",
     ["Classical: LR, linear SVM, NB", "Cross-lingual: XLM-R, mBERT",
      "Arabic subset: AraBERT,", "MARBERT — Notebooks 06–07"], GOLD),
    (1, 2, "8. Evaluation",
     ["Macro-F1, per-class recall", "McNemar + effect size",
      "Per-language kappa", "Notebooks 05, 08"], GOLD),
    (1, 3, "9. Aspect Analysis",
     ["Bilingual lexicon + BERTopic", "Aspect-to-dissatisfaction",
      "association ranking", "Notebooks 09–10"], GOLD),

    (2, 0, "10. Decision Outputs",
     ["Satisfaction score per review", "Ranked aspect drivers",
      "Segment breakdowns"], TEAL),
    (2, 1, "11. Serving Layer",
     ["Batch scoring service", "REST endpoint",
      "Weekly refresh"], TEAL),
    (2, 2, "12. Target Users",
     ["Service and product teams", "Chief Happiness Officers",
      "Policy and strategy units"], RED),
]

ROW_N = {0: 5, 1: 4, 2: 3}          # boxes per row
BOX_W, BOX_H = 3.30, 1.80
GAP_X, GAP_Y = 0.42, 0.85
FIG_W = ROW_N[0] * BOX_W + (ROW_N[0] - 1) * GAP_X + 1.0


def row_origin(row: int) -> float:
    """Right-align each row under the previous one, as in the original."""
    n = ROW_N[row]
    used = n * BOX_W + (n - 1) * GAP_X
    return 0.5 + (FIG_W - 1.0 - used)


def draw():
    rows = 3
    fig_h = rows * BOX_H + (rows - 1) * GAP_Y + 1.0
    fig, ax = plt.subplots(figsize=(FIG_W, fig_h), dpi=200)
    ax.set_xlim(0, FIG_W)
    ax.set_ylim(0, fig_h)
    ax.axis("off")

    centres = {}
    for row, idx, title, lines, colour in STAGES:
        x = row_origin(row) + idx * (BOX_W + GAP_X)
        y = fig_h - 0.5 - (row + 1) * BOX_H - row * GAP_Y

        # body
        ax.add_patch(FancyBboxPatch(
            (x, y), BOX_W, BOX_H,
            boxstyle="round,pad=0,rounding_size=0.09",
            linewidth=1.6, edgecolor=colour, facecolor="white", zorder=2))
        # header band
        ax.add_patch(FancyBboxPatch(
            (x, y + BOX_H - 0.42), BOX_W, 0.42,
            boxstyle="round,pad=0,rounding_size=0.09",
            linewidth=0, facecolor=colour, zorder=3))
        ax.add_patch(plt.Rectangle((x, y + BOX_H - 0.50), BOX_W, 0.10,
                                   linewidth=0, facecolor=colour, zorder=3))

        ax.text(x + BOX_W / 2, y + BOX_H - 0.21, title, ha="center",
                va="center", fontsize=10.5, fontweight="bold", color="white",
                zorder=4)
        for i, ln in enumerate(lines):
            ax.text(x + BOX_W / 2, y + BOX_H - 0.78 - i * 0.245, ln,
                    ha="center", va="center", fontsize=8.2, color=INK, zorder=4)
        centres[(row, idx)] = (x, y)

    def arrow(p1, p2, rad=0.0):
        ax.add_patch(FancyArrowPatch(
            p1, p2, arrowstyle="-|>", mutation_scale=13, linewidth=1.5,
            color=LINE, connectionstyle=f"arc3,rad={rad}",
            shrinkA=0, shrinkB=0, zorder=1))

    # within-row arrows
    for row, n in ROW_N.items():
        for i in range(n - 1):
            x, y = centres[(row, i)]
            arrow((x + BOX_W, y + BOX_H / 2),
                  (x + BOX_W + GAP_X, y + BOX_H / 2))

    # row hand-offs: last box of a row down to the first of the next
    for row in (0, 1):
        xs, ys = centres[(row, ROW_N[row] - 1)]
        xd, yd = centres[(row + 1, 0)]
        mid = ys - GAP_Y / 2
        ax.plot([xs + BOX_W / 2, xs + BOX_W / 2], [ys, mid],
                color=LINE, linewidth=1.5, zorder=1)
        ax.plot([xs + BOX_W / 2, xd + BOX_W / 2], [mid, mid],
                color=LINE, linewidth=1.5, zorder=1)
        arrow((xd + BOX_W / 2, mid), (xd + BOX_W / 2, yd + BOX_H))

    # governance note
    gx, gy = 0.5, centres[(2, 0)][1] + 0.12
    ax.add_patch(FancyBboxPatch(
        (gx, gy), 2.55, 1.32, boxstyle="round,pad=0,rounding_size=0.08",
        linewidth=1.4, edgecolor=RED, facecolor="white",
        linestyle=(0, (4, 3)), zorder=2))
    ax.text(gx + 1.275, gy + 1.02, "Governance and audit", ha="center",
            va="center", fontsize=9.5, fontweight="bold", color=RED, zorder=3)
    for i, ln in enumerate(["Every filtering rule logged",
                            "and reversible; raw archive",
                            "immutable. Seed 42; splits",
                            "leakage-checked."]):
        ax.text(gx + 1.275, gy + 0.72 - i * 0.20, ln, ha="center", va="center",
                fontsize=7.6, color=GREY, zorder=3)

    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white",
                pad_inches=0.12)
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    p = draw()
    print(f"wrote {p}")
    print(f"  apps {ds['apps']}   raw {ds['raw_rows']:,}   "
          f"modelling {ds['modelling_rows']:,}   test {splits['test']['n']:,}")
