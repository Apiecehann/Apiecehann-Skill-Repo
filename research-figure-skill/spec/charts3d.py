"""P0 3D surface renderer: surface + 2D contour projection."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
import numpy as np


def render_mesh3d(config, rows, out_stem):
    width, height = config.get("size_pt", [420, 300])
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=200)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="3d")
    xs, ys = config["xs"], config["ys"]
    Z = np.array([[next(r["z"] for r in rows if r["x"] == x and r["y"] == y) for x in xs] for y in ys])
    X, Y = np.meshgrid(xs, ys)
    ax.plot_wireframe(X, Y, Z, color=config.get("color", "#2F80C9"), linewidth=.7)
    ax.set_xlabel(config.get("x_label", "x"), fontsize=7, labelpad=1)
    ax.set_ylabel(config.get("y_label", "y"), fontsize=7, labelpad=1)
    ax.set_zlabel(config.get("z_label", "z"), fontsize=7, labelpad=1)
    ax.tick_params(labelsize=6, pad=0)
    ax.view_init(elev=config.get("elev", 24), azim=config.get("azim", -55))
    fig.subplots_adjust(left=.02, right=.98, bottom=.02, top=.98)
    out_stem = Path(out_stem); out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def render_bar3d(config, rows, out_stem):
    width, height = config.get("size_pt", [420, 300])
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=200)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="3d")
    groups = config["groups"]; series = config["series_order"]
    for j, name in enumerate(series):
        for i, group in enumerate(groups):
            value = next(r["value"] for r in rows if r["group"] == group and r["series"] == name)
            ax.bar3d(i - .22, j - .22, 0, .36, .36, value,
                     color=config["colors"][name], edgecolor="white", linewidth=.3, alpha=.9)
    ax.set_xticks(range(len(groups))); ax.set_xticklabels(groups, fontsize=6)
    ax.set_yticks(range(len(series))); ax.set_yticklabels(series, fontsize=6)
    ax.set_zlabel(config.get("z_label", "Value"), fontsize=7, labelpad=2)
    ax.tick_params(labelsize=6, pad=0)
    ax.view_init(elev=config.get("elev", 24), azim=config.get("azim", -55))
    fig.subplots_adjust(left=.02, right=.98, bottom=.02, top=.98)
    out_stem = Path(out_stem); out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def render_scatter3d(config, rows, out_stem):
    width, height = config.get("size_pt", [420, 300])
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=200)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="3d")
    for name in config["series_order"]:
        subset = [r for r in rows if r["series"] == name]
        ax.scatter([r["x"] for r in subset], [r["y"] for r in subset], [r["z"] for r in subset],
                   s=config.get("marker", 18), color=config["colors"][name],
                   edgecolors="white", linewidths=.3, alpha=.85,
                   label=config.get("series_labels", {}).get(name, name))
    ax.set_xlabel(config.get("x_label", "x"), fontsize=7, labelpad=2)
    ax.set_ylabel(config.get("y_label", "y"), fontsize=7, labelpad=2)
    ax.set_zlabel(config.get("z_label", "z"), fontsize=7, labelpad=2)
    ax.tick_params(labelsize=6, pad=1)
    ax.view_init(elev=config.get("elev", 24), azim=config.get("azim", -55))
    ax.legend(frameon=False, fontsize=6.5, loc="upper left")
    fig.tight_layout(pad=.3)
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def render_voxel(config, rows, out_stem):
    width, height = config.get("size_pt", [420, 300])
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=200)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="3d")
    xs, ys, zs = config["xs"], config["ys"], config["zs"]
    filled = np.zeros((len(xs), len(ys), len(zs)), dtype=bool)
    values = np.zeros_like(filled, dtype=float)
    for row in rows:
        i, j, k = xs.index(row["x"]), ys.index(row["y"]), zs.index(row["z"])
        values[i, j, k] = row["value"]
        filled[i, j, k] = row["value"] > config.get("threshold", 0)
    cmap = plt.get_cmap(config.get("colormap", "viridis"))
    norm = plt.Normalize(values[filled].min() if filled.any() else 0,
                         values[filled].max() if filled.any() else 1)
    colors = np.empty(filled.shape, dtype=object)
    for idx in np.ndindex(filled.shape):
        if filled[idx]:
            colors[idx] = cmap(norm(values[idx]))
    ax.voxels(filled, facecolors=colors, edgecolors="white", linewidth=.15)
    ax.set_xlabel(config.get("x_label", "x"), fontsize=7, labelpad=1)
    ax.set_ylabel(config.get("y_label", "y"), fontsize=7, labelpad=1)
    ax.set_zlabel(config.get("z_label", "z"), fontsize=7, labelpad=1)
    ax.tick_params(labelsize=6, pad=1)
    ax.view_init(elev=config.get("elev", 24), azim=config.get("azim", -55))
    fig.tight_layout(pad=.2)
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]


def render_surface(config, rows, out_stem):
    width, height = config.get("size_pt", [504, 252])
    fig = plt.figure(figsize=(width / 72, height / 72), dpi=200)
    fig.patch.set_facecolor("white")
    ax3 = fig.add_subplot(1, 2, 1, projection="3d")
    ax2 = fig.add_subplot(1, 2, 2)
    X, Y, Z = np.array(config["X"]), np.array(config["Y"]), np.array(config["Z"])
    cmap = plt.get_cmap(config.get("colormap", "viridis"))
    surf = ax3.plot_surface(X, Y, Z, cmap=cmap, linewidth=0, antialiased=True, alpha=.96)
    ax3.set_xlabel(config.get("x_label", "x"), fontsize=7, labelpad=2)
    ax3.set_ylabel(config.get("y_label", "y"), fontsize=7, labelpad=2)
    ax3.set_zlabel(config.get("z_label", "z"), fontsize=7, labelpad=2)
    ax3.tick_params(labelsize=6, pad=1)
    ax3.set_box_aspect((1, 1, .7))
    ax3.view_init(elev=28, azim=-135)
    contour = ax2.contourf(X, Y, Z, levels=14, cmap=cmap)
    ax2.set_xlabel(config.get("x_label", "x"), fontsize=7)
    ax2.set_ylabel(config.get("y_label", "y"), fontsize=7)
    ax2.tick_params(labelsize=6, length=2)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)
    cbar = fig.colorbar(contour, ax=[ax3, ax2], fraction=.035, pad=.03)
    cbar.ax.tick_params(labelsize=6, length=2)
    cbar.ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    fig.subplots_adjust(left=.03, right=.91, top=.94, bottom=.14, wspace=.16)
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf", "svg"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=300, facecolor="white")
    plt.close(fig)
    return [out_stem.with_suffix("." + ext) for ext in ("png", "pdf", "svg")]
