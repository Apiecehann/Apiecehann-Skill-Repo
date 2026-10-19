"""Render one axis-coverage sheet for dot-plot.

This is a review sheet, not a recipe registry: every panel changes one axis.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "axis-review" / "data" / "focus.csv"
OUT = ROOT / "chart-variants"
LABEL_FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTS = {
    "sans": r"C:\Windows\Fonts\arial.ttf",
    "serif": r"C:\Windows\Fonts\times.ttf",
    "mono": r"C:\Windows\Fonts\consola.ttf",
    "humanist": r"C:\Windows\Fonts\segoeui.ttf",
}

D_ORANGE = ["#F6D3B5", "#E9A875", "#D98A48", "#E07A2F"]
A_GRAY = ["#C9D0D6", "#A3ACB9", "#7B848F", "#E07A2F"]
C_HUES = ["#B7D3E8", "#A8D5C8", "#D9C7E8", "#E07A2F"]
MULTI = ["#4477AA", "#EE6677", "#228833", "#CCBB44"]
SERIES = ["method-1", "method-2", "method-3", "ours"]
LABELS = {"method-1": "Method 1", "method-2": "Method 2", "method-3": "Method 3", "ours": "Ours"}


def load():
    with DATA.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    groups = list(dict.fromkeys(r["group"] for r in rows))
    return rows, groups


def draw(rows, groups, *, colors, title, font="sans", tick=8, axis_width=.7,
         marker=32, grid=True, errorbar=False, reference=None, bold=False,
         figsize=(3.6, 2.4)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    y = {g: i for i, g in enumerate(groups)}
    for name, color in zip(SERIES, colors):
        subset = [r for r in rows if r["series"] == name]
        xs = [float(r["value"]) for r in subset]
        ys = [y[r["group"]] for r in subset]
        ax.scatter(xs, ys, s=marker, color=color, edgecolors="white", linewidths=.6,
                   label=LABELS[name], zorder=3)
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
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#9CA3AF")
        ax.spines[side].set_linewidth(axis_width)
    if grid:
        ax.grid(True, axis="x", color="#D9DEE3", linewidth=.6,
                linestyle="--" if grid == "dashed" else "-", zorder=0)
        ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=6.5, loc="lower center", bbox_to_anchor=(.5, 1.01),
              ncol=4, handletextpad=.4, columnspacing=1.0, borderaxespad=0)
    ax.set_title(title, fontsize=8, pad=18, fontweight="bold" if bold else "normal")
    fig.tight_layout(pad=.4)
    return fig


def main():
    rows, groups = load()
    specs = [
        ("canonical", dict(colors=D_ORANGE, title="canonical")),
        ("color / focus-neutral", dict(colors=A_GRAY, title="color / focus-neutral")),
        ("color / focus-multi", dict(colors=C_HUES, title="color / focus-multi")),
        ("color / multi-hue", dict(colors=MULTI, title="color / multi-hue")),
        ("style / bold-slide", dict(colors=D_ORANGE, title="style / bold-slide",
                                    tick=10, axis_width=1.2, marker=46, grid=False, bold=True)),
        ("style / minimal-mono", dict(colors=D_ORANGE, title="style / minimal-mono",
                                      tick=7, axis_width=.4, marker=26, grid=False)),
        ("style / serif-emphasis", dict(colors=D_ORANGE, title="style / serif-emphasis",
                                        font="serif", grid="dashed")),
        ("type / sans", dict(colors=D_ORANGE, title="type / sans", font="sans")),
        ("type / serif", dict(colors=D_ORANGE, title="type / serif", font="serif")),
        ("type / humanist", dict(colors=D_ORANGE, title="type / humanist", font="humanist")),
        ("type / mono", dict(colors=D_ORANGE, title="type / mono", font="mono")),
        ("annotation / errorbar", dict(colors=D_ORANGE, title="annotation / errorbar", errorbar=True)),
        ("annotation / reference", dict(colors=D_ORANGE, title="annotation / reference", reference=.85)),
        ("grid / hairline", dict(colors=D_ORANGE, title="grid / hairline", grid=True)),
        ("grid / dashed", dict(colors=D_ORANGE, title="grid / dashed", grid="dashed")),
        ("size / single", dict(colors=D_ORANGE, title="size / single", figsize=(3.6, 2.4))),
        ("size / double", dict(colors=D_ORANGE, title="size / double", figsize=(5.0, 3.3))),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    panels = []
    for i, (name, kwargs) in enumerate(specs):
        fig = draw(rows, groups, **kwargs)
        path = OUT / "panels" / f"dot-{i:02d}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=180, facecolor="white")
        plt.close(fig)
        panels.append((path, name))

    cell_w, cell_h, cols = 420, 320, 3
    rows_n = (len(panels) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols + 40, 72 + cell_h * rows_n + 24), "white")
    draw_ctx = ImageDraw.Draw(sheet)
    draw_ctx.text((24, 18), "dot plot / axis coverage", fill="#20252c",
                  font=ImageFont.truetype(LABEL_FONT, 30))
    draw_ctx.text((24, 50), f"each panel changes one axis; grouped-bar has 9 recipes, this has {len(specs)} panels",
                  fill="#57606c", font=ImageFont.truetype(LABEL_FONT, 14))
    for i, (path, label) in enumerate(panels):
        x = 20 + (i % cols) * cell_w
        y = 72 + (i // cols) * cell_h
        with Image.open(path) as source:
            preview = source.convert("RGB")
            preview.thumbnail((cell_w - 24, cell_h - 54), Image.Resampling.LANCZOS)
            sheet.paste(preview, (x + (cell_w - preview.width) // 2, y))
        draw_ctx.text((x + 12, y + cell_h - 42), label, fill="#20252c",
                      font=ImageFont.truetype(LABEL_FONT, 17))
    sheet.save(OUT / "dot-plot.png")
    print("wrote", OUT / "dot-plot.png")


if __name__ == "__main__":
    main()
