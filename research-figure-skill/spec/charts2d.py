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
            if ref.get("label"):
                ax.text(1.0, value, ref["label"], transform=ax.get_yaxis_transform(),
                        ha="right", va="bottom", fontsize=7, color=color,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1}, clip_on=False)
        else:
            ax.axvline(value, color=color, linestyle=ref.get("linestyle", "--"), linewidth=.8, zorder=1)
            if ref.get("label"):
                ax.text(value, .98, ref["label"], transform=ax.get_xaxis_transform(),
                        ha="right", va="top", fontsize=7, color=color,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1}, clip_on=False)


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


def _sorted_xy(rows, name):
    subset = sorted((r for r in rows if r["series"] == name), key=lambda r: float(r["group"]))
    x = np.array([float(r["group"]) for r in subset])
    y = np.array([r["value"] for r in subset])
    low = np.array([r.get("low", r["value"]) for r in subset])
    high = np.array([r.get("high", r["value"]) for r in subset])
    return subset, x, y, low, high


def render_line_band(config, rows, out_stem):
    fig, ax = _setup(config)
    colors = config["colors"]
    labels = config.get("series_labels", {})
    for name in config["series_order"]:
        subset, x, y, low, high = _sorted_xy(rows, name)
        if len(x) == 0:
            continue
        ax.plot(x, y, color=colors[name], linewidth=1.8, marker="o", markersize=3,
                markerfacecolor="white", markeredgewidth=1, label=labels.get(name, name), zorder=3)
        if any("low" in r and "high" in r for r in subset):
            ax.fill_between(x, low, high, color=colors[name], alpha=.16, linewidth=0, zorder=2)
    _reference(ax, config)
    if config.get("x_min") is not None or config.get("x_max") is not None:
        ax.set_xlim(config.get("x_min"), config.get("x_max"))
    return _finish(fig, ax, config, out_stem)


def _trend(ax, x, y, color):
    if len(x) < 2 or np.ptp(x) == 0:
        return
    slope, intercept = np.polyfit(x, y, 1)
    grid = np.linspace(x.min(), x.max(), 100)
    fit = slope * grid + intercept
    ax.plot(grid, fit, color=color, linewidth=1.4, linestyle="--", zorder=4)
    residual = y - (slope * x + intercept)
    dof = max(1, len(x) - 2)
    s_err = np.sqrt(np.sum(residual ** 2) / dof)
    sxx = np.sum((x - x.mean()) ** 2)
    if sxx > 0:
        ci = 1.96 * s_err * np.sqrt(1 / len(x) + (grid - x.mean()) ** 2 / sxx)
        ax.fill_between(grid, fit - ci, fit + ci, color=color, alpha=.12, linewidth=0, zorder=1)


def _ellipse(ax, x, y, color):
    if len(x) < 3:
        return
    cov = np.cov(x, y)
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]
    angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
    width, height = 2 * 2.4477 * np.sqrt(np.maximum(vals, 1e-12))
    ellipse = matplotlib.patches.Ellipse((x.mean(), y.mean()), width, height, angle=angle,
                                          facecolor=color, edgecolor=color, alpha=.10,
                                          linewidth=1, zorder=1)
    ax.add_patch(ellipse)


def render_scatter(config, rows, out_stem):
    fig, ax = _setup(config)
    colors = config["colors"]
    labels = config.get("series_labels", {})
    stats = {s["kind"] for s in config.get("stats", [])}
    for name in config["series_order"]:
        subset = [r for r in rows if r["series"] == name]
        x = np.array([float(r["group"]) for r in subset])
        y = np.array([r["value"] for r in subset])
        ax.scatter(x, y, s=18, color=colors[name], edgecolors="white", linewidths=.4,
                   alpha=.82, label=labels.get(name, name), zorder=3)
        if "confidence-ellipse" in stats:
            _ellipse(ax, x, y, colors[name])
        if "trend" in stats:
            _trend(ax, x, y, colors[name])
    _reference(ax, config)
    if config.get("x_min") is not None or config.get("x_max") is not None:
        ax.set_xlim(config.get("x_min"), config.get("x_max"))
    return _finish(fig, ax, config, out_stem)


def _category_grid(ax):
    ax.grid(False)
    ax.grid(True, axis="y", color="#D9DEE3", linewidth=.6, zorder=0)
    ax.set_axisbelow(True)


def _series_values(rows, groups, series):
    return [[r["value"] for r in rows if r["group"] == group and r["series"] == series]
            for group in groups]


def render_box(config, rows, out_stem):
    fig, ax = _setup(config)
    _category_grid(ax)
    groups, series, colors = config["groups"], config["series_order"], config["colors"]
    labels = config.get("series_labels", {})
    n = len(series)
    width = .78 / n
    handles = []
    for i, name in enumerate(series):
        data = _series_values(rows, groups, name)
        positions = np.arange(len(groups)) + (i - (n - 1) / 2) * width
        bp = ax.boxplot(data, positions=positions, widths=width * .82, patch_artist=True,
                        showfliers=False, medianprops={"color": colors[name], "linewidth": 1.2},
                        whiskerprops={"color": colors[name], "linewidth": .8},
                        capprops={"color": colors[name], "linewidth": .8})
        for patch in bp["boxes"]:
            patch.set_facecolor(colors[name])
            patch.set_alpha(.45)
            patch.set_edgecolor(colors[name])
            patch.set_linewidth(.8)
        handles.append(matplotlib.patches.Patch(facecolor=colors[name], alpha=.45,
                                                edgecolor=colors[name], label=labels.get(name, name)))
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    _reference(ax, config)
    if config.get("y_min") is not None or config.get("y_max") is not None:
        ax.set_ylim(config.get("y_min"), config.get("y_max"))
    return _finish_handles(fig, ax, config, out_stem, handles)


def render_violin(config, rows, out_stem):
    fig, ax = _setup(config)
    _category_grid(ax)
    groups, series, colors = config["groups"], config["series_order"], config["colors"]
    labels = config.get("series_labels", {})
    n = len(series)
    width = .78 / n
    handles = []
    for i, name in enumerate(series):
        data = _series_values(rows, groups, name)
        positions = np.arange(len(groups)) + (i - (n - 1) / 2) * width
        vp = ax.violinplot(data, positions=positions, widths=width * .85,
                           showmeans=False, showmedians=True, showextrema=False)
        for body in vp["bodies"]:
            body.set_facecolor(colors[name])
            body.set_edgecolor(colors[name])
            body.set_alpha(.38)
        vp["cmedians"].set_color(colors[name])
        vp["cmedians"].set_linewidth(1.1)
        handles.append(matplotlib.patches.Patch(facecolor=colors[name], alpha=.38,
                                                edgecolor=colors[name], label=labels.get(name, name)))
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    _reference(ax, config)
    return _finish_handles(fig, ax, config, out_stem, handles)


def _gaussian_kde(values, grid):
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return np.zeros_like(grid)
    std = values.std(ddof=1)
    bw = 1.06 * std * len(values) ** (-1 / 5)
    bw = max(bw, 1e-9)
    z = (grid[:, None] - values[None, :]) / bw
    return np.exp(-.5 * z ** 2).mean(axis=1) / (bw * np.sqrt(2 * np.pi))


def render_ecdf(config, rows, out_stem):
    fig, ax = _setup(config)
    colors, labels = config["colors"], config.get("series_labels", {})
    for name in config["series_order"]:
        values = np.sort(np.array([r["value"] for r in rows if r["series"] == name]))
        if len(values) == 0:
            continue
        y = np.arange(1, len(values) + 1) / len(values)
        ax.step(values, y, where="post", color=colors[name], linewidth=1.8,
                label=labels.get(name, name))
    ax.set_ylim(0, 1.02)
    _reference(ax, config)
    if config.get("x_min") is not None or config.get("x_max") is not None:
        ax.set_xlim(config.get("x_min"), config.get("x_max"))
    return _finish(fig, ax, config, out_stem)


def render_kde(config, rows, out_stem):
    fig, ax = _setup(config)
    colors, labels = config["colors"], config.get("series_labels", {})
    all_values = np.array([r["value"] for r in rows])
    grid = np.linspace(all_values.min(), all_values.max(), 240)
    for name in config["series_order"]:
        values = [r["value"] for r in rows if r["series"] == name]
        if len(values) < 2:
            continue
        density = _gaussian_kde(values, grid)
        ax.plot(grid, density, color=colors[name], linewidth=1.8, label=labels.get(name, name))
        ax.fill_between(grid, 0, density, color=colors[name], alpha=.12)
    _reference(ax, config)
    if config.get("x_min") is not None or config.get("x_max") is not None:
        ax.set_xlim(config.get("x_min"), config.get("x_max"))
    return _finish(fig, ax, config, out_stem)


def _finish_handles(fig, ax, config, out_stem, handles):
    ax.set_xlabel(config.get("x_label", ""), fontsize=8)
    ax.set_ylabel(config.get("y_label", ""), fontsize=8)
    if config.get("legend", True) and handles:
        ax.legend(handles=handles, frameon=False, fontsize=7, loc="lower center",
                  bbox_to_anchor=(.5, 1.01), ncol=min(4, len(handles)), handletextpad=.4,
                  columnspacing=1.2, borderaxespad=0)
    fig.subplots_adjust(left=.16, right=.98, top=.84, bottom=.16)
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def render_heatmap(config, rows, out_stem):
    fig, ax = plt.subplots(figsize=(config["size_pt"][0] / 72, config["size_pt"][1] / 72), dpi=200)
    fig.patch.set_facecolor("white")
    matrix = np.array(config["matrix"], dtype=float)
    image = ax.imshow(matrix, aspect="auto", cmap=plt.get_cmap(config.get("colormap", "Blues")))
    ax.set_xticks(range(len(config["cols"])))
    ax.set_xticklabels(config["cols"], fontsize=7)
    ax.set_yticks(range(len(config["rows"])))
    ax.set_yticklabels(config["rows"], fontsize=7)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    if config.get("cell_values"):
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax.text(j, i, f"{matrix[i, j]:g}", ha="center", va="center",
                        fontsize=6.5, color="#111827")
    cbar = fig.colorbar(image, ax=ax, fraction=.046, pad=.04)
    cbar.ax.tick_params(labelsize=6.5, length=2)
    ax.set_xlabel(config.get("x_label", ""), fontsize=8)
    ax.set_ylabel(config.get("y_label", ""), fontsize=8)
    fig.subplots_adjust(left=.18, right=.95, top=.96, bottom=.16)
    return _save_fig(fig, out_stem)


def _save_fig(fig, out_stem):
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def _roc_points(scores, labels):
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)
    order = np.argsort(-scores)
    scores, labels = scores[order], labels[order]
    tp = np.cumsum(labels == 1)
    fp = np.cumsum(labels == 0)
    pos, neg = max(1, int((labels == 1).sum())), max(1, int((labels == 0).sum()))
    tpr = np.r_[0, tp / pos]
    fpr = np.r_[0, fp / neg]
    auc = float(np.sum((fpr[1:] - fpr[:-1]) * (tpr[1:] + tpr[:-1]) / 2)) if len(fpr) > 1 else 0.0
    return fpr, tpr, auc


def render_roc(config, rows, out_stem):
    fig, ax = _setup(config)
    colors = config["colors"]
    labels = config.get("series_labels", {})
    for name in config["series_order"]:
        subset = [r for r in rows if r["series"] == name]
        fpr, tpr, auc = _roc_points([r["score"] for r in subset], [r["label"] for r in subset])
        ax.plot(fpr, tpr, color=colors[name], linewidth=1.8, drawstyle="steps-post",
                label=f"{labels.get(name, name)} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], color="#9CA3AF", linestyle="--", linewidth=.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("False positive rate", fontsize=8)
    ax.set_ylabel("True positive rate", fontsize=8)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.subplots_adjust(left=.16, right=.98, top=.84, bottom=.18)
    return _save_fig(fig, out_stem)


def _pr_points(scores, labels):
    scores = np.asarray(scores, dtype=float)
    labels = np.asarray(labels, dtype=int)
    order = np.argsort(-scores)
    labels = labels[order]
    tp = np.cumsum(labels == 1)
    fp = np.cumsum(labels == 0)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / max(1, int((labels == 1).sum()))
    baseline = float(labels.mean()) if len(labels) else 0.0
    return np.r_[0, recall], np.r_[1, precision], baseline


def render_pr(config, rows, out_stem):
    fig, ax = _setup(config)
    colors = config["colors"]
    labels = config.get("series_labels", {})
    for name in config["series_order"]:
        subset = [r for r in rows if r["series"] == name]
        recall, precision, baseline = _pr_points([r["score"] for r in subset], [r["label"] for r in subset])
        ax.step(recall, precision, where="post", color=colors[name], linewidth=1.8,
                label=labels.get(name, name))
        ax.axhline(baseline, color=colors[name], linestyle=":", linewidth=.8, alpha=.7)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Recall", fontsize=8)
    ax.set_ylabel("Precision", fontsize=8)
    ax.legend(frameon=False, fontsize=7, loc="lower left")
    fig.subplots_adjust(left=.16, right=.98, top=.84, bottom=.18)
    return _save_fig(fig, out_stem)


def render_calibration(config, rows, out_stem):
    fig, ax = _setup(config)
    colors = config["colors"]
    labels = config.get("series_labels", {})
    edges = np.linspace(0, 1, int(config.get("bins", 10)) + 1)
    for name in config["series_order"]:
        subset = [r for r in rows if r["series"] == name]
        scores = np.array([r["score"] for r in subset])
        targets = np.array([r["label"] for r in subset])
        xs, ys = [], []
        for lo, hi in zip(edges[:-1], edges[1:]):
            mask = (scores >= lo) & (scores < hi if hi < 1 else scores <= hi)
            if mask.any():
                xs.append(scores[mask].mean())
                ys.append(targets[mask].mean())
        ax.plot(xs, ys, marker="o", markersize=3, color=colors[name], linewidth=1.6,
                label=labels.get(name, name))
    ax.plot([0, 1], [0, 1], color="#9CA3AF", linestyle="--", linewidth=.8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Confidence", fontsize=8)
    ax.set_ylabel("Accuracy", fontsize=8)
    ax.legend(frameon=False, fontsize=7, loc="upper left")
    fig.subplots_adjust(left=.16, right=.98, top=.84, bottom=.18)
    return _save_fig(fig, out_stem)
