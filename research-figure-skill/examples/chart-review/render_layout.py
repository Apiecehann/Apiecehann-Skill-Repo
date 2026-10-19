"""Layout review: waffle / broken-axis / inset-zoom."""
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
    "arial": r"C:\Windows\Fonts\arial.ttf", "segoe": r"C:\Windows\Fonts\segoeui.ttf",
    "times": r"C:\Windows\Fonts\times.ttf", "consolas": r"C:\Windows\Fonts\consola.ttf",
}
COLORS = ["#2F80C9", "#E07A2F", "#1F9E89", "#C44E6E"]
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .8}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {}), ("boxed-journal", {"all_spines": True}),
    ("grid-paper", {"grid": True}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"bold": True}), ("pastel-poster", {"tick": 10, "alpha": .65}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "arial"), ("Segoe UI", "segoe"), ("Calibri", "arial"),
    ("Verdana", "arial"), ("Tahoma", "arial"), ("Trebuchet MS", "arial"),
    ("Times New Roman", "times"), ("Georgia", "times"), ("Garamond", "times"),
    ("Cambria", "times"), ("Consolas", "consolas"), ("Courier New", "consolas"),
    ("Comic Sans MS", "arial"), ("Segoe Script", "arial"),
]
SIZES = [("tiny", (2.4, 1.8)), ("single", (3.2, 2.3)), ("square", (3.0, 3.0)),
         ("wide", (3.6, 1.8)), ("medium", (4.2, 2.8)), ("double", (6.6, 4.6)),
         ("double-wide", (6.6, 3.2)), ("slide", (8.6, 4.8)), ("tall", (2.4, 4.0))]


def load(name):
    with (ROOT / "examples/templates" / name / "data.csv").open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def setup(ax, config):
    ax.set_facecolor("white")
    ax.tick_params(labelsize=config.get("tick", 7))
    if config.get("grid"):
        ax.grid(True, color="#E5E7EB", linewidth=.6)
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        if config.get("bold"):
            text.set_fontweight("bold")


def waffle(rows, color, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.0, 3.0)), dpi=180)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    total = sum(float(r["value"]) for r in rows); index = 0
    for i, row in enumerate(rows):
        count = round(float(row["value"]) / total * 100) if i < len(rows) - 1 else 100 - index
        for _ in range(count):
            ax.add_patch(matplotlib.patches.Rectangle((index % 10, 9 - index // 10), .9, .9,
                                                      color=COLORS[(i + color) % len(COLORS)],
                                                      alpha=config.get("alpha", 1)))
            index += 1
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    fig.tight_layout(pad=.3)
    return fig


def broken(rows, color, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=config.get("figsize", (3.2, 2.2)),
                                   gridspec_kw={"width_ratios": [1.4, 1]})
    fig.patch.set_facecolor("white")
    for ax in (ax1, ax2):
        ax.set_facecolor("white")
    for name in dict.fromkeys(r["series"] for r in rows):
        subset = sorted([r for r in rows if r["series"] == name], key=lambda r: float(r["group"]))
        xs = [float(r["group"]) for r in subset]; ys = [float(r["value"]) for r in subset]
        ax1.plot(xs, ys, color=COLORS[color % len(COLORS)], linewidth=1.5)
        ax2.plot(xs, ys, color=COLORS[color % len(COLORS)], linewidth=1.5)
    ax1.set_xlim(0, 50); ax2.set_xlim(50, 100)
    ax1.spines["right"].set_visible(False); ax2.spines["left"].set_visible(False)
    ax2.tick_params(left=False)
    setup(ax1, config); setup(ax2, config)
    fig.tight_layout(pad=.3)
    return fig


def inset(rows, color, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.2, 2.2)), dpi=180)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    for name in dict.fromkeys(r["series"] for r in rows):
        subset = [r for r in rows if r["series"] == name]
        ax.scatter([float(r["group"]) for r in subset], [float(r["value"]) for r in subset],
                   s=12, color=COLORS[color % len(COLORS)], edgecolors="white", linewidths=.2,
                   alpha=config.get("alpha", .9))
    inset_ax = ax.inset_axes([.56, .55, .38, .35])
    inset_ax.scatter([float(r["group"]) for r in rows], [float(r["value"]) for r in rows],
                     s=7, color=COLORS[color % len(COLORS)], edgecolors="white", linewidths=.2)
    inset_ax.set_xlim(55, 75); inset_ax.set_ylim(55, 75); inset_ax.tick_params(labelsize=5)
    ax.set_xlabel("Latency (ms)"); ax.set_ylabel("Throughput")
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def sheet(title, panels, columns, out, cell=(380, 300)):
    rows_n = (len(panels) + columns - 1) // columns
    image = Image.new("RGB", (cell[0] * columns + 40, 70 + cell[1] * rows_n + 16), "white")
    ctx = ImageDraw.Draw(image)
    ctx.text((24, 14), title, fill="#20252c", font=ImageFont.truetype(LABEL_FONT, 28))
    for i, (path, label) in enumerate(panels):
        x = 20 + (i % columns) * cell[0]; y = 60 + (i // columns) * cell[1]
        with Image.open(path) as source:
            preview = source.convert("RGB"); preview.thumbnail((cell[0] - 20, cell[1] - 42), Image.Resampling.LANCZOS)
            image.paste(preview, (x + (cell[0] - preview.width) // 2, y))
        ctx.text((x + 10, y + cell[1] - 32), label, fill="#20252c", font=ImageFont.truetype(LABEL_FONT, 15))
    image.save(out); print("wrote", out.name, len(panels))


def build(name, draw_fn):
    rows = load(name) if name != "broken-axis" else load("scatter")
    if name == "inset-zoom":
        rows = load("scatter")
    out = HERE / name; (out / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": name, "sheets": []}
    axes = [
        ("00-color", "color", [(f"color-{i}", {"color": i}) for i in range(3)], 3),
        ("01-style", "style", [(n, {"color": 0, **k}) for n, k in STYLES], 3),
        ("02-type", "type", [(n, {"color": 0, "font": f}) for n, f in TYPES], 3),
        ("03-size", "size", [(n, {"color": 0, "figsize": s}) for n, s in SIZES], 3),
    ]
    for sheet_id, title, items, columns in [(a, b, c, d) for a, b, c, d in axes]:
        panels = []
        for i, (label, kwargs) in enumerate(items):
            fig = draw_fn(rows, **kwargs)
            path = out / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, panels, columns, out / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "panels": len(panels)})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def main():
    build("waffle", waffle)
    build("broken-axis", broken)
    build("inset-zoom", inset)


if __name__ == "__main__":
    main()
