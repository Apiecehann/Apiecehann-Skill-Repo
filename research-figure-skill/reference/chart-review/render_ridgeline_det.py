"""Axis review for ridgeline and det (P1.2)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import NormalDist

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
ACCENTS = {"blue": "#2F80C9", "green": "#3A9D5D", "teal": "#1F9E89", "orange": "#E07A2F", "rose": "#C44E6E"}
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .7}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "axis_width": 1.2, "bold": True}),
    ("minimal-mono", {"tick": 6, "axis_width": .4}), ("hand-drawn", {"font": "comic"}),
    ("boxed-journal", {"all_spines": True}), ("grid-paper", {"grid": "both"}),
    ("editorial-serif", {"font": "times", "axis_width": .5}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": "both"}),
    ("poster-bold", {"tick": 10, "axis_width": 2}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"axis_width": 1.5, "bold": True}), ("pastel-poster", {"tick": 10}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
SIZES = [("tiny", (2.4, 1.7)), ("single", (3.3, 2.36)), ("square", (3.3, 3.3)),
         ("wide", (3.3, 1.8)), ("medium", (4.5, 3.2)), ("double", (7, 5)),
         ("double-wide", (7, 3.6)), ("slide", (9, 5.06)), ("tall", (2.5, 4.2))]


def read(name):
    with (ROOT / "templates" / name / "data.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def setup(ax, config):
    ax.set_facecolor("white")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(config.get("all_spines", False) or side in ("left", "bottom"))
        ax.spines[side].set_color("#9CA3AF"); ax.spines[side].set_linewidth(config.get("axis_width", .7))
    grid = config.get("grid", "x")
    if grid != "none":
        ax.grid(True, axis="y" if grid == "both" else "x", color="#D9DEE3", linewidth=.6,
                linestyle="--" if grid == "dashed" else "-", zorder=0)
        ax.set_axisbelow(True)
    ax.tick_params(labelsize=config.get("tick", 8), length=3, color="#6B7280")
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        if config.get("bold"):
            text.set_fontweight("bold")


def set_font(config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()


def gaussian(values, grid):
    v = np.asarray(values, dtype=float)
    std = v.std(ddof=1)
    bw = max(1.06 * std * len(v) ** (-1 / 5), 1e-9)
    z = (grid[:, None] - v[None, :]) / bw
    return np.exp(-.5 * z ** 2).mean(axis=1) / (bw * np.sqrt(2 * np.pi))


def ridgeline(rows, colors, **config):
    set_font(config)
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.4, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    groups = list(dict.fromkeys(r["group"] for r in rows))
    values = np.array([float(r["value"]) for r in rows])
    grid = np.linspace(values.min(), values.max(), 220)
    for i, group in enumerate(groups):
        subset = [float(r["value"]) for r in rows if r["group"] == group]
        density = gaussian(subset, grid); density = density / density.max() * .55
        base = len(groups) - 1 - i
        ax.fill_between(grid, base, base + density, color=colors[0], alpha=.55, linewidth=0)
        ax.plot(grid, base + density, color="white", linewidth=1.4)
        ax.text(grid.min(), base + .02, group, fontsize=7, va="bottom")
    ax.set_yticks([]); ax.set_ylim(-.12, len(groups) - .1)
    ax.set_xlabel("Success rate (%)", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Difficulty", fontsize=config.get("tick", 8) + 1)
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def det(rows, colors, **config):
    set_font(config)
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.4, 2.5)), dpi=180)
    fig.patch.set_facecolor("white")
    scores = np.array([float(r["score"]) for r in rows]); labels = np.array([int(float(r["label"])) for r in rows])
    order = np.argsort(-scores); labels = labels[order]
    tp = np.cumsum(labels == 1); fp = np.cumsum(labels == 0)
    tpr = np.r_[0, tp / max(1, (labels == 1).sum())]
    fpr = np.r_[0, fp / max(1, (labels == 0).sum())]
    fnr = 1 - tpr
    norm = NormalDist()
    def z(p): return [norm.inv_cdf(float(np.clip(v, 1e-4, 1 - 1e-4))) for v in p]
    ax.plot(z(fpr), z(fnr), color=colors[0], linewidth=1.8)
    if config.get("operating"):
        idx = int(np.argmin(np.abs(fpr - .1)))
        ax.scatter([z(fpr)[idx]], [z(fnr)[idx]], s=28, color=colors[0], zorder=4)
        ax.annotate("operating", (z(fpr)[idx], z(fnr)[idx]), xytext=(12, -12),
                    textcoords="offset points", fontsize=6.5, color="#374151",
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 1},
                    arrowprops={"arrowstyle": "-", "color": "#6B7280", "linewidth": .6})
    ticks = [0.01, 0.2, 0.5, 0.8]
    ax.plot(z(ticks), z(ticks), color="#9CA3AF", linestyle="--", linewidth=.8)
    ax.set_xticks(z(ticks)); ax.set_xticklabels([f"{t:g}" for t in ticks], fontsize=7)
    ax.set_yticks(z(ticks)); ax.set_yticklabels([f"{t:g}" for t in ticks], fontsize=7)
    ax.set_xlabel("False positive rate", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("False negative rate", fontsize=config.get("tick", 8) + 1)
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
        x = 20 + (i % columns) * cell[0]; y = 70 + (i // columns) * cell[1]
        with Image.open(path) as source:
            preview = source.convert("RGB"); preview.thumbnail((cell[0] - 20, cell[1] - 42), Image.Resampling.LANCZOS)
            image.paste(preview, (x + (cell[0] - preview.width) // 2, y))
        ctx.text((x + 10, y + cell[1] - 32), label, fill="#20252c", font=ImageFont.truetype(LABEL_FONT, 15))
    image.save(out); print("wrote", out.name, len(panels))


def build(chart, rows, draw_fn, specific):
    out = HERE / chart; (out / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": chart, "sheets": []}
    axes = [
        ("00-color", "color", "单系列颜色", [(rows, [ACCENTS[n]], n, {}) for n in ACCENTS], 3),
        ("01-style", "style", "15 个白底风格", [(rows, [ACCENTS["blue"]], n, k) for n, k in STYLES], 3),
        ("02-type", "type", "15 个字体", [(rows, [ACCENTS["blue"]], l, {"font": f}) for l, f in TYPES], 3),
        ("03-annotation", "annotation", "该图支持", specific, 2),
        ("04-grid", "grid", "背景参考线", [(rows, [ACCENTS["blue"]], n, {"grid": n}) for n in ("none", "x", "dashed", "both")], 2),
        ("05-size", "size", "物理尺寸", [(rows, [ACCENTS["blue"]], n, {"figsize": s}) for n, s in SIZES], 3),
    ]
    for sheet_id, title, subtitle, items, columns in axes:
        panels = []
        for i, (rows_arg, colors, label, kwargs) in enumerate(items):
            fig = draw_fn(rows_arg, colors, **kwargs)
            path = out / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, out / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def main():
    build("ridgeline", read("ridgeline"), ridgeline, [(read("ridgeline"), [ACCENTS["blue"]], "single", {})])
    build("det", read("det"), det, [
        (read("det"), [ACCENTS["blue"]], "operating", {"operating": True}),
        (read("det"), [ACCENTS["blue"]], "no operating", {"operating": False}),
    ])


if __name__ == "__main__":
    main()


