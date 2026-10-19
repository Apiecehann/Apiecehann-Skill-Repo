"""Render the dot-plot axis-review directory.

One sheet per axis, several panels per sheet. This mirrors reference/axis-review:
the sheet is the axis, the panel is one option.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "examples" / "axis-review" / "data" / "focus.csv"
LABEL_FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTS = {
    "arial": r"C:\Windows\Fonts\arial.ttf",
    "helvetica": r"C:\Windows\Fonts\arial.ttf",
    "segoe": r"C:\Windows\Fonts\segoeui.ttf",
    "calibri": r"C:\Windows\Fonts\calibri.ttf",
    "verdana": r"C:\Windows\Fonts\verdana.ttf",
    "tahoma": r"C:\Windows\Fonts\tahoma.ttf",
    "trebuchet": r"C:\Windows\Fonts\trebuc.ttf",
    "times": r"C:\Windows\Fonts\times.ttf",
    "georgia": r"C:\Windows\Fonts\georgia.ttf",
    "garamond": r"C:\Windows\Fonts\gara.ttf",
    "cambria": r"C:\Windows\Fonts\cambria.ttc",
    "consolas": r"C:\Windows\Fonts\consola.ttf",
    "courier": r"C:\Windows\Fonts\cour.ttf",
    "comic": r"C:\Windows\Fonts\comic.ttf",
    "script": r"C:\Windows\Fonts\segoesc.ttf",
}
SERIES = ["method-1", "method-2", "method-3", "ours"]
LABELS = {"method-1": "Method 1", "method-2": "Method 2", "method-3": "Method 3", "ours": "Ours"}
ACCENTS = {"orange": "#E07A2F", "blue": "#2F80C9", "teal": "#1F9E89", "green": "#3A9D5D", "rose": "#C44E6E"}
A_GRAY = ["#A3ACB9"] * 4
B_GRAY = ["#C9D0D6", "#A3ACB9", "#7B848F", "#4B5563"]
C_HUES = ["#B7D3E8", "#A8D5C8", "#D9C7E8", "#E07A2F"]
D_ORANGE = ["#F6D3B5", "#E9A875", "#D98A48", "#E07A2F"]
MULTI = ["#4477AA", "#EE6677", "#228833", "#CCBB44"]
PAIRS = {
    "blue": ["#BDD8ED", "#2F80C9"],
    "green": ["#C9E4CB", "#3A9D5D"],
    "teal": ["#B7E0DA", "#1F9E89"],
    "orange": ["#F6D3B5", "#E07A2F"],
    "rose": ["#F2C6CE", "#C44E6E"],
}
CATEGORICAL = {
    "pastel-eight": ["#D88D91", "#99B4D7", "#F9D78D", "#9CC2A4"],
    "tol-bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44"],
    "tol-muted": ["#88CCEE", "#44AA99", "#999933", "#CC6677"],
    "set2": ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3"],
    "npg": ["#4DBBD5", "#00A087", "#3C5488", "#E64B35"],
    "tableau10": ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2"],
}


def mix(color, t):
    h = color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(c + (255 - c) * t):02x}" for c in rgb)


def load():
    with DATA.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    groups = list(dict.fromkeys(r["group"] for r in rows))
    return rows, groups


def draw(rows, groups, colors, *, font="arial", tick=8, axis_width=.7, marker=32,
         grid="hairline", all_spines=False, alpha=.95, bold=False, errorbar=False,
         reference=None, figsize=(3.6, 2.4)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    order = list(dict.fromkeys(r["series"] for r in rows))
    y = {g: i for i, g in enumerate(groups)}
    for name, color in zip(order, colors):
        subset = [r for r in rows if r["series"] == name]
        xs = [float(r["value"]) for r in subset]
        ys = [y[r["group"]] for r in subset]
        ax.scatter(xs, ys, s=marker, color=color, edgecolors="white", linewidths=.6,
                   alpha=alpha, label=LABELS[name], zorder=3)
        if errorbar:
            ax.errorbar(xs, ys, xerr=.04, fmt="none", ecolor=color, elinewidth=.8,
                        capsize=2, zorder=2)
    if reference is not None:
        ax.axvline(reference, color="#9CA3AF", linestyle="--", linewidth=.8)
        ax.text(reference - .01, len(groups) - .55, "SOTA", ha="right", va="top",
                fontsize=6.5, color="#6B7280",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels(groups)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Success rate", fontsize=tick + 1)
    ax.set_ylabel("Benchmark", fontsize=tick + 1)
    ax.tick_params(labelsize=tick, length=3, color="#6B7280")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(all_spines or side in ("left", "bottom"))
        ax.spines[side].set_color("#9CA3AF" if not all_spines else "#4B5563")
        ax.spines[side].set_linewidth(axis_width)
    if grid != "none":
        style = ":" if grid == "dots" else ("--" if grid == "dashed" else "-")
        axis = "both" if grid == "both" else "x"
        ax.grid(True, axis=axis, color="#D9DEE3", linewidth=.6, linestyle=style, zorder=0)
        ax.set_axisbelow(True)
    if len(order) > 1:
        ax.legend(frameon=False, fontsize=6.5, loc="lower center", bbox_to_anchor=(.5, 1.01),
                  ncol=min(4, len(order)), handletextpad=.4, columnspacing=1.0, borderaxespad=0)
    if bold:
        for text in ax.get_xticklabels() + ax.get_yticklabels():
            text.set_fontweight("bold")
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


def render(name, rows, groups, colors, label, **kwargs):
    fig = draw(rows, groups, colors, **kwargs)
    path = HERE / "panels" / f"{name}.png"
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)
    return path, label


def main():
    rows, groups = load()
    (HERE / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": "dot-plot", "sheets": []}

    def add(sheet_id, title, subtitle, items, columns):
        panels = [render(f"{sheet_id}-{i:02d}", *item[0], item[1], **item[2])
                  for i, item in enumerate(items)]
        sheet(title, subtitle, panels, columns, f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})

    add("00-color-structure", "color structure", "先看 series 数，再看颜色结构", [
        ((rows, groups, D_ORANGE), "focus-tints", {}),
        ((rows, groups, A_GRAY), "focus-neutral", {}),
        ((rows, groups, C_HUES), "focus-multi", {}),
        ((rows, groups, MULTI), "multi-hue", {}),
        (([r for r in rows if r["series"] in ("method-1", "ours")], groups, PAIRS["blue"]), "paired", {}),
        (([r for r in rows if r["series"] in ("method-1", "ours")], groups, ["#5A9BD3", "#E07A2F"]), "two-hue", {}),
    ], 3)

    add("01-baseline-color", "baseline color", "baseline 之间的关系", [
        ((rows, groups, A_GRAY), "A / all same", {}),
        ((rows, groups, B_GRAY), "B / gray ramp", {}),
        ((rows, groups, C_HUES), "C / multi-hue", {}),
        ((rows, groups, D_ORANGE), "D / focus tints", {}),
    ], 2)

    add("02-accent", "accent hue", "focus 色相；baseline 跟着变浅", [
        ((rows, groups, [mix(ACCENTS[h], .78), mix(ACCENTS[h], .55), mix(ACCENTS[h], .32), ACCENTS[h]]),
         h, {}) for h in ("orange", "blue", "teal", "green", "rose")
    ], 3)

    add("03-paired", "paired palette", "2 series 的同色相浅深", [
        (([r for r in rows if r["series"] in ("method-1", "ours")], groups, PAIRS[name]), name, {})
        for name in ("blue", "green", "teal", "orange", "rose")
    ], 3)

    add("04-categorical", "categorical palette", "4 个无序类别", [
        ((rows, groups, colors), name, {}) for name, colors in CATEGORICAL.items()
    ], 3)

    add("05-grid", "grid", "背景参考线", [
        ((rows, groups, D_ORANGE), "none", {"grid": "none"}),
        ((rows, groups, D_ORANGE), "hairline", {"grid": "hairline"}),
        ((rows, groups, D_ORANGE), "dashed", {"grid": "dashed"}),
        ((rows, groups, D_ORANGE), "dots", {"grid": "dots"}),
    ], 2)

    style_specs = [
        ("paper-clean", {}), ("soft-outline", {"alpha": .8, "marker": 28}),
        ("serif-emphasis", {"font": "times", "grid": "dashed"}),
        ("bold-slide", {"tick": 10, "axis_width": 1.2, "marker": 42, "grid": "none", "bold": True}),
        ("minimal-mono", {"tick": 7, "axis_width": .4, "marker": 26, "grid": "none"}),
        ("hand-drawn", {"font": "comic", "grid": "none"}),
        ("boxed-journal", {"all_spines": True, "grid": "none"}),
        ("grid-paper", {"grid": "hairline"}),
        ("editorial-serif", {"font": "times", "grid": "none", "axis_width": .5}),
        ("white-slide", {"font": "times", "tick": 11, "axis_width": 1.2, "grid": "none"}),
        ("technical-grid", {"font": "consolas", "grid": "hairline", "all_spines": True}),
        ("poster-bold", {"tick": 10, "axis_width": 2, "grid": "none"}),
        ("compact-journal", {"tick": 7, "axis_width": .5, "grid": "none"}),
        ("high-contrast", {"axis_width": 1.5, "grid": "none", "bold": True}),
        ("pastel-poster", {"tick": 12, "axis_width": 1, "grid": "none"}),
    ]
    add("06-style", "style", "15 个白底风格；同一颜色结构", [
        ((rows, groups, D_ORANGE), name, kwargs) for name, kwargs in style_specs
    ], 3)

    type_specs = [
        ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"),
        ("Calibri", "calibri"), ("Verdana", "verdana"), ("Tahoma", "tahoma"),
        ("Trebuchet MS", "trebuchet"), ("Times New Roman", "times"), ("Georgia", "georgia"),
        ("Garamond", "garamond"), ("Cambria", "cambria"), ("Consolas", "consolas"),
        ("Courier New", "courier"), ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
    ]
    add("07-type", "type", "15 个字体；同一颜色/风格", [
        ((rows, groups, D_ORANGE), label, {"font": font}) for label, font in type_specs
    ], 3)

    add("08-annotation", "annotation", "dot plot 支持的标注", [
        ((rows, groups, D_ORANGE), "errorbar", {"errorbar": True}),
        ((rows, groups, D_ORANGE), "reference line", {"reference": .85}),
    ], 2)

    sizes = [
        ("tiny", (2.4, 1.7)), ("single", (3.3, 2.36)), ("square", (3.3, 3.3)),
        ("wide", (3.3, 1.8)), ("medium", (4.5, 3.2)), ("double", (7, 5)),
        ("double-wide", (7, 3.6)), ("slide", (9, 5.06)), ("tall", (2.5, 4.2)),
    ]
    add("09-size", "size", "物理尺寸与长宽比", [
        ((rows, groups, D_ORANGE), name, {"figsize": size}) for name, size in sizes
    ], 3)

    add("10-series-count", "series count", "dot-plot 自己的轴：1 / 2 / 4 series", [
        (([r for r in rows if r["series"] == "ours"], groups, [ACCENTS["orange"]]), "1 series", {}),
        (([r for r in rows if r["series"] in ("method-1", "ours")], groups, PAIRS["blue"]), "2 series", {}),
        ((rows, groups, D_ORANGE), "4 series", {}),
    ], 3)

    (HERE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
