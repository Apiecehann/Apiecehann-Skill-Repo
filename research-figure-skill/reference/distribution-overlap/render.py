"""Render a two-panel overlapping histogram (distribution comparison).

MOCK data only: the shape is for layout/style review, not a scientific claim.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
DATA = HERE / "data.csv"
OUT = HERE / "figure.png"


def load():
    with DATA.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    return rows


def render():
    rows = load()
    panels = list(dict.fromkeys(r["panel"] for r in rows))
    fig, axes = plt.subplots(1, len(panels), figsize=(7.2, 3.6), dpi=200)
    if len(panels) == 1:
        axes = [axes]
    colors = {"correct": "#4C9BE8", "incorrect": "#F4C542"}
    labels = {"correct": "Correct", "incorrect": "Incorrect"}
    bins = np.linspace(0, 1, 21)
    for ax, panel in zip(axes, panels):
        panel_colors = dict(colors)
        if panel.startswith("CE"):
            panel_colors["correct"] = "#E85D8A"
        for series in ("correct", "incorrect"):
            values = [float(r["value"]) for r in rows if r["panel"] == panel and r["series"] == series]
            ax.hist(values, bins=bins, density=True, alpha=.78, color=panel_colors[series],
                    edgecolor="white", linewidth=.45, label=labels[series], zorder=2)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Maximum Predicted Probability", fontsize=8)
        ax.set_ylabel("Density", fontsize=8)
        ax.tick_params(labelsize=7, length=3, color="#6B7280")
        ax.grid(True, which="major", axis="both", color="#D9DEE3", linewidth=.6, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_color("#D9DEE3")
            ax.spines[side].set_linewidth(.6)
        for side in ("left", "bottom"):
            ax.spines[side].set_color("#9CA3AF")
            ax.spines[side].set_linewidth(.7)
        ax.legend(frameon=False, fontsize=7, loc="upper right", handlelength=1.3,
                  handletextpad=.4, borderaxespad=.2)
        ax.set_title(f"Figure 4 | {panel}", fontsize=9, pad=6)
    fig.subplots_adjust(left=.07, right=.99, top=.87, bottom=.17, wspace=.22)
    fig.patch.set_facecolor("white")
    fig.savefig(OUT, dpi=300, facecolor="white")
    fig.savefig(HERE / "figure.pdf", facecolor="white")
    fig.savefig(HERE / "figure.svg", facecolor="white")
    plt.close(fig)
    print("wrote", OUT)


if __name__ == "__main__":
    render()
