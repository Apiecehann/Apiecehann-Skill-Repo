"""Render the distribution-overlap chart family.

The compiler writes a small config and a normalized long table; this module only
draws it. Data are observations, not pre-binned counts.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np


def render(config, rows, out_stem):
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    panels = config["panels"]
    series = config["series_order"]
    colors = config["colors"]
    labels = config.get("series_labels", {})
    x_min, x_max = config.get("x_min", 0.0), config.get("x_max", 1.0)
    bins = np.linspace(x_min, x_max, int(config.get("bins", 20)) + 1)
    width, height = config.get("size_pt", [504, 252])
    fig, axes = plt.subplots(1, len(panels), figsize=(width / 72, height / 72), dpi=200)
    if len(panels) == 1:
        axes = [axes]
    for ax, panel in zip(axes, panels):
        for name in series:
            values = [float(r["value"]) for r in rows
                      if r["panel"] == panel and r["series"] == name]
            ax.hist(values, bins=bins, density=True, alpha=.78, color=colors[name],
                    edgecolor="white", linewidth=.45, label=labels.get(name, name), zorder=2)
        ax.set_xlim(x_min, x_max)
        ax.set_xlabel(config.get("x_label", "Value"), fontsize=8)
        ax.set_ylabel(config.get("y_label", "Density"), fontsize=8)
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
        prefix = config.get("title_prefix", "Figure 4 | ")
        ax.set_title(f"{prefix}{panel}", fontsize=9, pad=6)
    fig.subplots_adjust(left=.07, right=.99, top=.87, bottom=.17, wspace=.22)
    fig.patch.set_facecolor("white")
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]
