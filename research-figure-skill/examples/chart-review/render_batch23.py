"""Render Batch 2 (distribution) and Batch 3 (matrix/classification) chart reviews."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LABEL_FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTS = {
    "arial": r"C:\Windows\Fonts\arial.ttf", "helvetica": r"C:\Windows\Fonts\arial.ttf",
    "segoe": r"C:\Windows\Fonts\segoeui.ttf", "calibri": r"C:\Windows\Fonts\calibri.ttf",
    "verdana": r"C:\Windows\Fonts\verdana.ttf", "tahoma": r"C:\Windows\Fonts\tahoma.ttf",
    "trebuchet": r"C:\Windows\Fonts\trebuc.ttf", "times": r"C:\Windows\Fonts\times.ttf",
    "georgia": r"C:\Windows\Fonts\georgia.ttf", "garamond": r"C:\Windows\Fonts\gara.ttf",
    "cambria": r"C:\Windows\Fonts\cambria.ttc", "consolas": r"C:\Windows\Fonts\consola.ttf",
    "courier": r"C:\Windows\Fonts\cour.ttf", "comic": r"C:\Windows\Fonts\comic.ttf",
    "script": r"C:\Windows\Fonts\segoesc.ttf",
}
ACCENTS = {"orange": "#E07A2F", "blue": "#2F80C9", "teal": "#1F9E89", "green": "#3A9D5D", "rose": "#C44E6E"}
PAIRS = {
    "blue": ["#BDD8ED", "#2F80C9"], "green": ["#C9E4CB", "#3A9D5D"],
    "teal": ["#B7E0DA", "#1F9E89"], "orange": ["#F6D3B5", "#E07A2F"],
    "rose": ["#F2C6CE", "#C44E6E"],
}
D_ORANGE = ["#F6D3B5", "#E9A875", "#D98A48", "#E07A2F"]
TYPE_SPECS = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"),
    ("Calibri", "calibri"), ("Verdana", "verdana"), ("Tahoma", "tahoma"),
    ("Trebuchet MS", "trebuchet"), ("Times New Roman", "times"), ("Georgia", "georgia"),
    ("Garamond", "garamond"), ("Cambria", "cambria"), ("Consolas", "consolas"),
    ("Courier New", "courier"), ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
STYLE_SPECS = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .8}),
    ("serif-emphasis", {"font": "times", "grid": "dashed"}),
    ("bold-slide", {"tick": 10, "axis_width": 1.2, "grid": "none", "bold": True}),
    ("minimal-mono", {"tick": 7, "axis_width": .4, "grid": "none"}),
    ("hand-drawn", {"font": "comic", "grid": "none"}),
    ("boxed-journal", {"all_spines": True, "grid": "none"}),
    ("grid-paper", {"grid": "hairline"}),
    ("editorial-serif", {"font": "times", "grid": "none", "axis_width": .5}),
    ("white-slide", {"font": "times", "tick": 11, "axis_width": 1.2, "grid": "none"}),
    ("technical-grid", {"font": "consolas", "grid": "both", "all_spines": True}),
    ("poster-bold", {"tick": 10, "axis_width": 2, "grid": "none"}),
    ("compact-journal", {"tick": 7, "axis_width": .5, "grid": "none"}),
    ("high-contrast", {"axis_width": 1.5, "grid": "none", "bold": True}),
    ("pastel-poster", {"tick": 12, "axis_width": 1, "grid": "none"}),
]
SIZES = [
    ("tiny", (2.6, 1.8)), ("single", (3.3, 2.36)), ("square", (3.3, 3.3)),
    ("wide", (3.3, 1.8)), ("medium", (4.5, 3.2)), ("double", (7, 5)),
    ("double-wide", (7, 3.6)), ("slide", (9, 5.06)), ("tall", (2.5, 4.2)),
]
CMAPS = ["Blues", "viridis", "magma", "RdBu_r", "coolwarm", "Greys"]


def read(name):
    with (ROOT / "examples" / "templates" / name / "data.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def set_font(config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()


def setup(ax, config):
    ax.set_facecolor("white")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(config.get("all_spines", False) or side in ("left", "bottom"))
        ax.spines[side].set_color("#4B5563" if config.get("all_spines") else "#9CA3AF")
        ax.spines[side].set_linewidth(config.get("axis_width", .7))
    grid = config.get("grid", "hairline")
    if grid != "none":
        style = ":" if grid == "dots" else ("--" if grid == "dashed" else "-")
        grid_axis = config.get("grid_axis", "y")
        ax.grid(True, axis=grid_axis, color="#D9DEE3", linewidth=.6, linestyle=style, zorder=0)
        ax.set_axisbelow(True)
    tick = config.get("tick", 8)
    ax.tick_params(labelsize=tick, length=3, color="#6B7280")
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        if config.get("bold"):
            text.set_fontweight("bold")


def fig_ax(config):
    set_font(config)
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.4, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    return fig, ax


def distribution(rows, colors, mode="hist", **config):
    fig, ax = fig_ax(config)
    series = list(dict.fromkeys(r["series"] for r in rows))[:2]
    vals = {name: np.array([float(r["value"]) for r in rows if r["series"] == name]) for name in series}
    if mode == "hist":
        bins = np.linspace(min(v.min() for v in vals.values()), max(v.max() for v in vals.values()), 22)
        for name, color in zip(series, colors):
            ax.hist(vals[name], bins=bins, density=True, alpha=.65, color=color,
                    edgecolor="white", linewidth=.4, label=name.title())
    elif mode == "kde":
        grid = np.linspace(min(v.min() for v in vals.values()), max(v.max() for v in vals.values()), 200)
        for name, color in zip(series, colors):
            v = vals[name]
            std = v.std(ddof=1)
            bw = max(1.06 * std * len(v) ** (-1 / 5), 1e-9)
            z = (grid[:, None] - v[None, :]) / bw
            density = np.exp(-.5 * z ** 2).mean(axis=1) / (bw * np.sqrt(2 * np.pi))
            ax.plot(grid, density, color=color, linewidth=1.8, label=name.title())
            ax.fill_between(grid, 0, density, color=color, alpha=.12)
    ax.set_xlabel("Value", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Density", fontsize=config.get("tick", 8) + 1)
    ax.legend(frameon=False, fontsize=6.5, loc="upper right")
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def ecdf(rows, colors, **config):
    fig, ax = fig_ax(config)
    series = list(dict.fromkeys(r["series"] for r in rows))[:2]
    for name, color in zip(series, colors):
        values = np.sort(np.array([float(r["value"]) for r in rows if r["series"] == name]))
        y = np.arange(1, len(values) + 1) / len(values)
        ax.step(values, y, where="post", color=color, linewidth=1.8, label=name.title())
    ax.set_ylim(0, 1.02)
    if config.get("reference") is not None:
        ax.axvline(config["reference"], color="#9CA3AF", linestyle="--", linewidth=.8)
        ax.text(config["reference"], .02, "SOTA", ha="right", va="bottom", fontsize=6.5,
                color="#6B7280", bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    ax.set_xlabel("Value", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("ECDF", fontsize=config.get("tick", 8) + 1)
    ax.legend(frameon=False, fontsize=6.5, loc="lower right")
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def box_violin(rows, colors, kind="box", **config):
    fig, ax = fig_ax(config)
    groups = list(dict.fromkeys(r["group"] for r in rows))
    series = list(dict.fromkeys(r["series"] for r in rows))[:2]
    width = .38
    handles = []
    for i, (name, color) in enumerate(zip(series, colors)):
        data = [[float(r["value"]) for r in rows if r["group"] == g and r["series"] == name] for g in groups]
        positions = np.arange(len(groups)) + (i - .5) * width
        if kind == "box":
            bp = ax.boxplot(data, positions=positions, widths=width * .8, patch_artist=True,
                            showfliers=config.get("outliers", False),
                            showmeans=config.get("means", False),
                            meanprops={"marker": "D", "markersize": 3,
                                       "markerfacecolor": "white", "markeredgecolor": color},
                            medianprops={"color": color, "linewidth": 1})
            for patch in bp["boxes"]:
                patch.set_facecolor(color); patch.set_alpha(.45); patch.set_edgecolor(color)
        else:
            vp = ax.violinplot(data, positions=positions, widths=width * .85,
                               showmeans=config.get("means", False), showmedians=True,
                               showextrema=config.get("outliers", False))
            for body in vp["bodies"]:
                body.set_facecolor(color); body.set_edgecolor(color); body.set_alpha(.38)
            vp["cmedians"].set_color(color)
            if config.get("means", False):
                vp["cmeans"].set_color(color)
                vp["cmeans"].set_linewidth(1)
        handles.append(matplotlib.patches.Patch(facecolor=color, alpha=.45, edgecolor=color, label=name.title()))
        if config.get("raw"):
            rng = np.random.default_rng(0)
            for pos, values in zip(positions, data):
                ax.scatter(pos + rng.uniform(-.04, .04, len(values)), values, s=6, color=color, alpha=.5,
                           linewidths=0, zorder=2)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.set_xlabel("Group", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Value", fontsize=config.get("tick", 8) + 1)
    ax.legend(handles=handles, frameon=False, fontsize=6.5, loc="lower center",
              bbox_to_anchor=(.5, 1.01), ncol=2, borderaxespad=0)
    setup(ax, config)
    if config.get("reference") is not None:
        ax.axhline(config["reference"], color="#9CA3AF", linestyle="--", linewidth=.8)
        ax.text(1.0, config["reference"], "target", transform=ax.get_yaxis_transform(),
                ha="right", va="bottom", fontsize=6.5, color="#6B7280",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    if config.get("bracket"):
        ax.plot([0, 0, len(groups) - 1, len(groups) - 1],
                [ax.get_ylim()[1] * .92, ax.get_ylim()[1] * .96, ax.get_ylim()[1] * .96, ax.get_ylim()[1] * .92],
                color="#4B5563", linewidth=.8)
        ax.text((len(groups) - 1) / 2, ax.get_ylim()[1] * .97, "*", ha="center", va="bottom", fontsize=8)
    fig.tight_layout(pad=.3)
    return fig


def heatmap(rows, colors, **config):
    fig, ax = fig_ax(config)
    rows_order = list(dict.fromkeys(r["row"] for r in rows))
    cols_order = list(dict.fromkeys(r["col"] for r in rows))
    matrix = np.array([[float(next(r["value"] for r in rows if r["row"] == row and r["col"] == col))
                        for col in cols_order] for row in rows_order])
    image = ax.imshow(matrix, aspect="auto", cmap=plt.get_cmap(config.get("colormap", "Blues")))
    ax.set_xticks(range(len(cols_order))); ax.set_xticklabels(cols_order, fontsize=6.5)
    ax.set_yticks(range(len(rows_order))); ax.set_yticklabels(rows_order, fontsize=6.5)
    ax.tick_params(length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    if config.get("cells", True):
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                rgba = image.cmap(image.norm(matrix[i, j]))
                luminance = .2126 * rgba[0] + .7152 * rgba[1] + .0722 * rgba[2]
                color = "white" if luminance < .55 else "#111827"
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center",
                        fontsize=6.2, fontweight="bold", color=color)
    if config.get("colorbar", True):
        cbar = fig.colorbar(image, ax=ax, fraction=.046, pad=.04)
        cbar.ax.tick_params(labelsize=6, length=2)
    ax.set_xlabel("Column", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Row", fontsize=config.get("tick", 8) + 1)
    fig.tight_layout(pad=.3)
    return fig


def roc(rows, colors, **config):
    fig, ax = fig_ax(config)
    name = "all"
    scores = np.array([float(r["score"]) for r in rows])
    labels = np.array([int(float(r["label"])) for r in rows])
    order = np.argsort(-scores)
    labels = labels[order]
    tpr = np.r_[0, np.cumsum(labels == 1) / max(1, (labels == 1).sum())]
    fpr = np.r_[0, np.cumsum(labels == 0) / max(1, (labels == 0).sum())]
    color = colors[0]
    ax.plot(fpr, tpr, color=color, linewidth=1.8, drawstyle="steps-post")
    ax.plot([0, 1], [0, 1], color="#9CA3AF", linestyle="--", linewidth=.8)
    if config.get("operating"):
        idx = int(np.argmin(np.abs(fpr - .1)))
        ax.scatter([fpr[idx]], [tpr[idx]], s=28, color=color, zorder=4)
        ax.annotate("operating", (fpr[idx], tpr[idx]), xytext=(14, -16),
                    textcoords="offset points", fontsize=6.5, color="#374151",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.2},
                    arrowprops={"arrowstyle": "-", "color": "#6B7280", "linewidth": .6},
                    zorder=5)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel("False positive rate", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("True positive rate", fontsize=config.get("tick", 8) + 1)
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def pr(rows, colors, **config):
    fig, ax = fig_ax(config)
    scores = np.array([float(r["score"]) for r in rows])
    labels = np.array([int(float(r["label"])) for r in rows])
    order = np.argsort(-scores)
    labels = labels[order]
    tp = np.cumsum(labels == 1); fp = np.cumsum(labels == 0)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / max(1, (labels == 1).sum())
    color = colors[0]
    ax.step(np.r_[0, recall], np.r_[1, precision], where="post", color=color, linewidth=1.8)
    ax.axhline(labels.mean(), color=color, linestyle=":", linewidth=.8)
    if config.get("operating"):
        idx = int(np.argmin(np.abs(recall - .5)))
        ax.scatter([recall[idx]], [precision[idx]], s=28, color=color, zorder=4)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel("Recall", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Precision", fontsize=config.get("tick", 8) + 1)
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def calibration(rows, colors, **config):
    fig, ax = fig_ax(config)
    scores = np.array([float(r["score"]) for r in rows])
    labels = np.array([int(float(r["label"])) for r in rows])
    bins = int(config.get("bins", 10))
    edges = np.linspace(0, 1, bins + 1)
    xs, ys = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (scores >= lo) & (scores < hi if hi < 1 else scores <= hi)
        if mask.any():
            xs.append(scores[mask].mean()); ys.append(labels[mask].mean())
    ax.plot(xs, ys, marker="o", markersize=3, color=colors[0], linewidth=1.6)
    ax.plot([0, 1], [0, 1], color="#9CA3AF", linestyle="--", linewidth=.8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel("Confidence", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Accuracy", fontsize=config.get("tick", 8) + 1)
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def sheet(title, subtitle, panels, columns, out, cell=(380, 280)):
    rows_n = (len(panels) + columns - 1) // columns
    image = Image.new("RGB", (cell[0] * columns + 40, 70 + cell[1] * rows_n + 16), "white")
    ctx = ImageDraw.Draw(image)
    ctx.text((24, 14), title, fill="#20252c", font=ImageFont.truetype(LABEL_FONT, 28))
    ctx.text((24, 46), subtitle, fill="#57606c", font=ImageFont.truetype(LABEL_FONT, 13))
    for i, (path, label) in enumerate(panels):
        x = 20 + (i % columns) * cell[0]
        y = 70 + (i // columns) * cell[1]
        with Image.open(path) as source:
            preview = source.convert("RGB")
            preview.thumbnail((cell[0] - 20, cell[1] - 42), Image.Resampling.LANCZOS)
            image.paste(preview, (x + (cell[0] - preview.width) // 2, y))
        ctx.text((x + 10, y + cell[1] - 32), label, fill="#20252c",
                 font=ImageFont.truetype(LABEL_FONT, 15))
    image.save(out)
    print("wrote", out.name, len(panels))


def build(chart, rows, draw_fn, axes):
    out = HERE / chart
    (out / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": chart, "sheets": []}
    for sheet_id, title, subtitle, items, columns in axes:
        panels = []
        for i, (rows_arg, colors, label, kwargs) in enumerate(items):
            fig = draw_fn(rows_arg, colors, **kwargs)
            path = out / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white")
            plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, out / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def common(rows, specific):
    return [
        ("00-color", "color", "该图的颜色结构", [
            (rows, PAIRS[name], name, {}) if len({r["series"] for r in rows}) > 1 else
            (rows, [ACCENTS[name]], name, {}) for name in ("blue", "green", "teal", "orange", "rose")
        ], 3),
        ("01-style", "style", "15 个白底风格", [(rows, PAIRS["blue"], name, kwargs) for name, kwargs in STYLE_SPECS], 3),
        ("02-type", "type", "15 个字体", [(rows, PAIRS["blue"], label, {"font": font}) for label, font in TYPE_SPECS], 3),
        ("03-annotation", "annotation", "该图支持的标注", specific, 2),
        ("04-grid", "grid", "背景参考线", [(rows, PAIRS["blue"], name, {"grid": name}) for name in ("none", "hairline", "dashed", "dots")], 3),
        ("05-size", "size", "物理尺寸", [(rows, PAIRS["blue"], name, {"figsize": size}) for name, size in SIZES], 3),
    ]


def main():
    hist = read("distribution-overlap")
    hist_single = [r for r in hist if r["panel"] == "CE Confidence"]
    kde_rows = read("kde")
    box_rows = read("box")
    violin_rows = read("violin")
    ecdf_rows = read("ecdf")
    heat_rows = read("heatmap")
    roc_rows = read("roc")
    pr_rows = read("pr")
    cal_rows = read("calibration")

    build("distribution-overlap", hist, distribution, [
        ("00-color", "color", "两组分布的颜色", [(hist, PAIRS[n], n, {}) for n in ("blue", "green", "teal", "orange", "rose")], 3),
        ("01-style", "style", "15 个白底风格", [(hist, PAIRS["blue"], n, k) for n, k in STYLE_SPECS], 3),
        ("02-type", "type", "15 个字体", [(hist, PAIRS["blue"], l, {"font": f}) for l, f in TYPE_SPECS], 3),
        ("03-grid", "grid", "背景参考线", [(hist, PAIRS["blue"], n, {"grid": n}) for n in ("none", "hairline", "dashed", "dots")], 3),
        ("04-size", "size", "物理尺寸", [(hist, PAIRS["blue"], n, {"figsize": s}) for n, s in SIZES], 3),
        ("05-panel-count", "panel count", "1 panel / 2 panels", [
            (hist_single, PAIRS["blue"], "1 panel", {}), (hist, PAIRS["blue"], "2 panels", {})], 2),
    ])

    build("kde", kde_rows, distribution, [
        ("00-color", "color", "两组 density 的颜色", [(kde_rows, PAIRS[n], n, {"mode": "kde"}) for n in ("blue", "green", "teal", "orange", "rose")], 3),
        ("01-style", "style", "15 个白底风格", [(kde_rows, PAIRS["blue"], n, {**k, "mode": "kde"}) for n, k in STYLE_SPECS], 3),
        ("02-type", "type", "15 个字体", [(kde_rows, PAIRS["blue"], l, {"font": f, "mode": "kde"}) for l, f in TYPE_SPECS], 3),
        ("03-annotation", "annotation", "density 支持", [
            (kde_rows, PAIRS["blue"], "single series", {"mode": "kde"})], 1),
        ("04-grid", "grid", "背景参考线", [(kde_rows, PAIRS["blue"], n, {"grid": n, "mode": "kde"}) for n in ("none", "hairline", "dashed", "dots")], 3),
        ("05-size", "size", "物理尺寸", [(kde_rows, PAIRS["blue"], n, {"figsize": s, "mode": "kde"}) for n, s in SIZES], 3),
    ])

    for chart, rows, kind in [("box", box_rows, "box"), ("violin", violin_rows, "violin")]:
        build(chart, rows, box_violin, [
            ("00-color", "color", "两组分布的颜色", [(rows, PAIRS[n], n, {"kind": kind}) for n in ("blue", "green", "teal", "orange", "rose")], 3),
            ("01-style", "style", "15 个白底风格", [(rows, PAIRS["blue"], n, {**k, "kind": kind}) for n, k in STYLE_SPECS], 3),
            ("02-type", "type", "15 个字体", [(rows, PAIRS["blue"], l, {"font": f, "kind": kind}) for l, f in TYPE_SPECS], 3),
            ("03-annotation", "annotation", "该图支持", [
                (rows, PAIRS["blue"], "raw points", {"kind": kind, "raw": True}),
                (rows, PAIRS["blue"], "significance", {"kind": kind, "bracket": True}),
                (rows, PAIRS["blue"], "reference", {"kind": kind, "reference": 90}),
                (rows, PAIRS["blue"], "means", {"kind": kind, "means": True}),
                (rows, PAIRS["blue"], "outliers", {"kind": kind, "outliers": True}),
            ], 3),
            ("04-grid", "grid", "背景参考线", [(rows, PAIRS["blue"], n, {"grid": n, "kind": kind}) for n in ("none", "hairline", "dashed", "dots")], 3),
            ("05-size", "size", "物理尺寸", [(rows, PAIRS["blue"], n, {"figsize": s, "kind": kind}) for n, s in SIZES], 3),
        ])

    build("ecdf", ecdf_rows, ecdf, common(ecdf_rows, [
        (ecdf_rows, PAIRS["blue"], "single series", {}),
        (ecdf_rows, PAIRS["blue"], "reference", {"reference": 80}),
    ]))

    build("heatmap", heat_rows, heatmap, [
        ("00-style", "style", "15 个白底风格", [(heat_rows, ["#2F80C9"], n, k) for n, k in STYLE_SPECS], 3),
        ("01-type", "type", "15 个字体", [(heat_rows, ["#2F80C9"], l, {"font": f}) for l, f in TYPE_SPECS], 3),
        ("02-colormap", "colormap", "色图", [(heat_rows, ["#2F80C9"], c, {"colormap": c}) for c in CMAPS], 2),
        ("03-annotation", "annotation", "cell labels / colorbar", [
            (heat_rows, ["#2F80C9"], "cells on", {"cells": True}),
            (heat_rows, ["#2F80C9"], "cells off", {"cells": False}),
            (heat_rows, ["#2F80C9"], "no colorbar", {"colorbar": False}),
        ], 3),
        ("04-size", "size", "物理尺寸", [(heat_rows, ["#2F80C9"], n, {"figsize": s}) for n, s in SIZES], 3),
    ])

    for chart, rows, fn, extra in [("roc", roc_rows, roc, "operating"), ("pr", pr_rows, pr, "operating")]:
        build(chart, rows, fn, [
            ("00-color", "color", "单系列颜色", [(rows, [ACCENTS[n]], n, {}) for n in ("blue", "green", "teal", "orange", "rose")], 3),
            ("01-style", "style", "15 个白底风格", [(rows, [ACCENTS["blue"]], n, k) for n, k in STYLE_SPECS], 3),
            ("02-type", "type", "15 个字体", [(rows, [ACCENTS["blue"]], l, {"font": f}) for l, f in TYPE_SPECS], 3),
            ("03-annotation", "annotation", "operating point", [
                (rows, [ACCENTS["blue"]], "none", {}), (rows, [ACCENTS["blue"]], extra, {extra: True})], 2),
            ("04-grid", "grid", "背景参考线", [(rows, [ACCENTS["blue"]], n, {"grid": n}) for n in ("none", "hairline", "dashed", "dots")], 3),
            ("05-size", "size", "物理尺寸", [(rows, [ACCENTS["blue"]], n, {"figsize": s}) for n, s in SIZES], 3),
        ])

    build("calibration", cal_rows, calibration, [
        ("00-color", "color", "单系列颜色", [(cal_rows, [ACCENTS[n]], n, {}) for n in ("blue", "green", "teal", "orange", "rose")], 3),
        ("01-style", "style", "15 个白底风格", [(cal_rows, [ACCENTS["blue"]], n, k) for n, k in STYLE_SPECS], 3),
        ("02-type", "type", "15 个字体", [(cal_rows, [ACCENTS["blue"]], l, {"font": f}) for l, f in TYPE_SPECS], 3),
        ("03-annotation", "annotation", "bin count", [
            (cal_rows, [ACCENTS["blue"]], "5 bins", {"bins": 5}),
            (cal_rows, [ACCENTS["blue"]], "10 bins", {"bins": 10}),
            (cal_rows, [ACCENTS["blue"]], "20 bins", {"bins": 20}),
        ], 3),
        ("04-grid", "grid", "背景参考线", [(cal_rows, [ACCENTS["blue"]], n, {"grid": n}) for n in ("none", "hairline", "dashed", "dots")], 3),
        ("05-size", "size", "物理尺寸", [(cal_rows, [ACCENTS["blue"]], n, {"figsize": s}) for n, s in SIZES], 3),
    ])


if __name__ == "__main__":
    main()
