"""Render axis-review directories for batch 1: dumbbell, line-band, scatter."""
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
    ("tiny", (2.4, 1.7)), ("single", (3.3, 2.36)), ("square", (3.3, 3.3)),
    ("wide", (3.3, 1.8)), ("medium", (4.5, 3.2)), ("double", (7, 5)),
    ("double-wide", (7, 3.6)), ("slide", (9, 5.06)), ("tall", (2.5, 4.2)),
]


def read(name):
    path = ROOT / "examples" / "templates" / name / "data.csv"
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def mix(color, t):
    h = color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(c + (255 - c) * t):02x}" for c in rgb)


def setup(ax, config):
    ax.set_facecolor("white")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(config.get("all_spines", False) or side in ("left", "bottom"))
        ax.spines[side].set_color("#4B5563" if config.get("all_spines") else "#9CA3AF")
        ax.spines[side].set_linewidth(config.get("axis_width", .7))
    grid = config.get("grid", "hairline")
    if grid != "none":
        style = ":" if grid == "dots" else ("--" if grid == "dashed" else "-")
        axis = "both" if grid == "both" else "x"
        ax.grid(True, axis=axis, color="#D9DEE3", linewidth=.6, linestyle=style, zorder=0)
        ax.set_axisbelow(True)
    tick = config.get("tick", 8)
    ax.tick_params(labelsize=tick, length=3, color="#6B7280")
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        if config.get("bold"):
            text.set_fontweight("bold")


def set_font(config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()


def reference(ax, config, axis="x"):
    if config.get("reference") is None:
        return
    value = config["reference"]
    if axis == "y":
        ax.axhline(value, color="#9CA3AF", linestyle="--", linewidth=.8)
        ax.text(1.0, value, "SOTA", transform=ax.get_yaxis_transform(), ha="right", va="bottom",
                fontsize=6.5, color="#6B7280",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    else:
        ax.axvline(value, color="#9CA3AF", linestyle="--", linewidth=.8)
        ax.text(value, .98, "SOTA", transform=ax.get_xaxis_transform(), ha="right", va="top",
                fontsize=6.5, color="#6B7280",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def dumbbell(rows, colors, **config):
    set_font(config)
    rows = [r for r in rows if r["series"] in ("before", "after")]
    groups = list(dict.fromkeys(r["group"] for r in rows))
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.4, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    y = {g: i for i, g in enumerate(groups)}
    by = {(r["group"], r["series"]): float(r["value"]) for r in rows}
    for group in groups:
        a, b = by[(group, "before")], by[(group, "after")]
        yy = y[group]
        ax.plot([a, b], [yy, yy], color="#CBD5E1", linewidth=config.get("line_width", 2.2),
                zorder=1, solid_capstyle="round")
        ax.scatter([a], [yy], s=config.get("marker", 34), color=colors[0], edgecolors="white",
                   linewidths=.7, zorder=3, label="Before" if group == groups[0] else None)
        ax.scatter([b], [yy], s=config.get("marker", 34), color=colors[1], edgecolors="white",
                   linewidths=.7, zorder=3, label="After" if group == groups[0] else None)
        if config.get("delta", True):
            ax.text(max(a, b) + 2, yy, f"{b - a:+.0f}", va="center", fontsize=6.5, color=colors[1])
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels(groups)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Success rate (%)", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Task", fontsize=config.get("tick", 8) + 1)
    ax.legend(frameon=False, fontsize=6.5, loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=2,
              borderaxespad=0)
    setup(ax, config)
    reference(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def line_band(rows, colors, **config):
    set_font(config)
    rows = [r for r in rows if r["series"] in ("method-1", "ours")]
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.4, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    for name, color in zip(("method-1", "ours"), colors):
        subset = sorted((r for r in rows if r["series"] == name), key=lambda r: float(r["group"]))
        x = [float(r["group"]) for r in subset]
        y = [float(r["value"]) for r in subset]
        low = [float(r["low"]) for r in subset]
        high = [float(r["high"]) for r in subset]
        ax.plot(x, y, color=color, linewidth=config.get("line_width", 1.8), marker="o",
                markersize=3, markerfacecolor="white", markeredgewidth=1,
                label="Method 1" if name == "method-1" else "Ours")
        if config.get("band", True):
            ax.fill_between(x, low, high, color=color, alpha=.16, linewidth=0)
    ax.set_xlim(1, 5)
    ax.set_xlabel("Training step", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Success rate (%)", fontsize=config.get("tick", 8) + 1)
    ax.legend(frameon=False, fontsize=6.5, loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=2,
              borderaxespad=0)
    setup(ax, config)
    reference(ax, config, axis="y")
    fig.tight_layout(pad=.3)
    return fig


def scatter(rows, colors, **config):
    set_font(config)
    rows = [r for r in rows if r["series"] in ("method-1", "ours")]
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.4, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    for name, color in zip(("method-1", "ours"), colors):
        subset = [r for r in rows if r["series"] == name]
        x = np.array([float(r["group"]) for r in subset])
        y = np.array([float(r["value"]) for r in subset])
        ax.scatter(x, y, s=config.get("marker", 18), color=color, edgecolors="white",
                   linewidths=.4, alpha=config.get("alpha", .82),
                   label="Method 1" if name == "method-1" else "Ours", zorder=3)
        if config.get("trend"):
            slope, intercept = np.polyfit(x, y, 1)
            grid = np.linspace(x.min(), x.max(), 80)
            ax.plot(grid, slope * grid + intercept, color=color, linewidth=1.3, linestyle="--")
        if config.get("ellipse"):
            cov = np.cov(x, y)
            vals, vecs = np.linalg.eigh(cov)
            order = vals.argsort()[::-1]
            vals, vecs = vals[order], vecs[:, order]
            angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
            width, height = 2 * 2.4477 * np.sqrt(np.maximum(vals, 1e-12))
            ax.add_patch(matplotlib.patches.Ellipse((x.mean(), y.mean()), width, height, angle=angle,
                                                    facecolor=color, edgecolor=color, alpha=.10,
                                                    linewidth=1, zorder=1))
    ax.set_xlim(0, 100)
    ax.set_xlabel("Latency (ms)", fontsize=config.get("tick", 8) + 1)
    ax.set_ylabel("Throughput", fontsize=config.get("tick", 8) + 1)
    ax.legend(frameon=False, fontsize=6.5, loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=2,
              borderaxespad=0)
    setup(ax, config)
    reference(ax, config, axis="y")
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
    image.save(HERE / out)
    print("wrote", out, len(panels))


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


def main():
    dumbbell_rows = read("dumbbell")
    line_rows = read("line-band")
    scatter_rows = read("scatter")
    common = lambda rows, draw_fn, specific: [
        ("00-color-structure", "color structure", "2-series 的颜色结构", [
            (rows, PAIRS[name], name, {}) for name in ("blue", "green", "teal", "orange", "rose")
        ], 3),
        ("01-style", "style", "15 个白底风格；同一颜色", [
            (rows, PAIRS["blue"], name, kwargs) for name, kwargs in STYLE_SPECS
        ], 3),
        ("02-type", "type", "15 个字体；同一颜色", [
            (rows, PAIRS["blue"], label, {"font": font}) for label, font in TYPE_SPECS
        ], 3),
        ("03-annotation", "annotation", "该图支持的标注", specific, 2),
        ("04-grid", "grid", "背景参考线", [
            (rows, PAIRS["blue"], name, {"grid": name}) for name in ("none", "hairline", "dashed", "dots")
        ], 3),
        ("05-size", "size", "物理尺寸与长宽比", [
            (rows, PAIRS["blue"], name, {"figsize": size}) for name, size in SIZES
        ], 3),
    ]
    build("dumbbell", dumbbell_rows, dumbbell, common(dumbbell_rows, dumbbell, [
        (dumbbell_rows, PAIRS["blue"], "delta label", {"delta": True}),
        (dumbbell_rows, PAIRS["blue"], "reference line", {"reference": 75}),
    ]))
    build("line-band", line_rows, line_band, common(line_rows, line_band, [
        (line_rows, PAIRS["blue"], "CI band", {"band": True}),
        (line_rows, PAIRS["blue"], "no band", {"band": False}),
        (line_rows, PAIRS["blue"], "reference line", {"reference": 75}),
    ]))
    build("scatter", scatter_rows, scatter, common(scatter_rows, scatter, [
        (scatter_rows, PAIRS["blue"], "trend", {"trend": True}),
        (scatter_rows, PAIRS["blue"], "ellipse", {"ellipse": True}),
        (scatter_rows, PAIRS["blue"], "reference line", {"reference": 80}),
    ]))


if __name__ == "__main__":
    main()
