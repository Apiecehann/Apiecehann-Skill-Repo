"""P0 2D chart renderers: dot plot and dumbbell.

These renderers consume the compiler's small config; they do not read IR directly.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np


def _setup(config):
    width, height = config.get("size_pt", [360, 240])
    fig, ax = plt.subplots(figsize=(width / 72, height / 72), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.grid(True, axis="x", color="#D9DEE3", linewidth=.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#9CA3AF")
        ax.spines[side].set_linewidth(.7)
    ax.tick_params(labelsize=7, length=3, color="#6B7280")
    return fig, ax


def _reference(ax, config):
    for ref in config.get("reference", []):
        value = ref["value"]
        color = ref.get("color", "#9CA3AF")
        if ref.get("axis", "x") == "y":
            ax.axhline(value, color=color, linestyle=ref.get("linestyle", "--"), linewidth=.8, zorder=1)
        else:
            ax.axvline(value, color=color, linestyle=ref.get("linestyle", "--"), linewidth=.8, zorder=1)
        if ref.get("label"):
            ax.text(value, 1.0, ref["label"], transform=ax.get_xaxis_transform(),
                    ha="right", va="bottom", fontsize=7, color=color,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def _finish(fig, ax, config, out_stem):
    ax.set_xlabel(config.get("x_label", ""), fontsize=8)
    ax.set_ylabel(config.get("y_label", ""), fontsize=8)
    if config.get("legend", True) and ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, fontsize=7, loc="lower center", bbox_to_anchor=(.5, 1.01),
                  ncol=min(4, len(ax.get_legend_handles_labels()[1])), handletextpad=.4,
                  columnspacing=1.2, borderaxespad=0)
    fig.subplots_adjust(left=.16, right=.98, top=.84, bottom=.16)
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def render_dot(config, rows, out_stem):
    fig, ax = _setup(config)
    groups = config["groups"]
    series = config["series_order"]
    colors = config["colors"]
    labels = config.get("series_labels", {})
    y = {g: i for i, g in enumerate(groups)}
    for name in series:
        subset = [r for r in rows if r["series"] == name]
        xs = [r["value"] for r in subset]
        ys = [y[r["group"]] for r in subset]
        ax.scatter(xs, ys, s=config.get("dot_size", 28), color=colors[name],
                   edgecolors="white", linewidths=.6, label=labels.get(name, name), zorder=3)
        if any("low" in r and "high" in r for r in subset):
            lo = [r.get("low", r["value"]) for r in subset]
            hi = [r.get("high", r["value"]) for r in subset]
            ax.errorbar(xs, ys, xerr=[np.array(xs) - lo, np.array(hi) - xs],
                        fmt="none", ecolor=colors[name], elinewidth=.8, capsize=2, zorder=2)
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels(groups)
    ax.invert_yaxis()
    _reference(ax, config)
    if config.get("x_min") is not None or config.get("x_max") is not None:
        ax.set_xlim(config.get("x_min"), config.get("x_max"))
    return _finish(fig, ax, config, out_stem)


def render_dumbbell(config, rows, out_stem):
    fig, ax = _setup(config)
    groups = config["groups"]
    series = config["series_order"]
    if len(series) != 2:
        raise ValueError("dumbbell requires exactly two series")
    colors = config["colors"]
    labels = config.get("series_labels", {})
    y = {g: i for i, g in enumerate(groups)}
    by = {(r["group"], r["series"]): r["value"] for r in rows}
    for group in groups:
        a, b = by[(group, series[0])], by[(group, series[1])]
        yy = y[group]
        ax.plot([a, b], [yy, yy], color="#CBD5E1", linewidth=2.2, zorder=1, solid_capstyle="round")
        ax.scatter([a], [yy], s=34, color=colors[series[0]], edgecolors="white",
                   linewidths=.7, zorder=3, label=labels.get(series[0], series[0]) if group == groups[0] else None)
        ax.scatter([b], [yy], s=34, color=colors[series[1]], edgecolors="white",
                   linewidths=.7, zorder=3, label=labels.get(series[1], series[1]) if group == groups[0] else None)
        delta = b - a
        ax.text(max(a, b) + 2, yy, f"{delta:+.0f}", va="center", fontsize=6.5,
                color=colors[series[1]])
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels(groups)
    ax.invert_yaxis()
    _reference(ax, config)
    return _finish(fig, ax, config, out_stem)
