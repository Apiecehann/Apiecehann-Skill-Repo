"""QQ / eventplot axis-review: color / style / type / grid / size."""
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
COLORS = ["#2F80C9", "#E07A2F", "#1F9E89", "#C44E6E", "#7B61A8"]
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .7}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {"font": "comic"}), ("boxed-journal", {"all_spines": True}),
    ("grid-paper", {"grid": "both"}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": "both"}),
    ("poster-bold", {"tick": 10}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"bold": True}), ("pastel-poster", {"tick": 10, "alpha": .65}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
SIZES = [("tiny", (2.4, 1.8)), ("single", (3.2, 2.3)), ("square", (3.0, 3.0)),
         ("wide", (3.6, 1.8)), ("medium", (4.2, 2.8)), ("double", (6.6, 4.6)),
         ("double-wide", (6.6, 3.2)), ("slide", (8.6, 4.8)), ("tall", (2.4, 4.0))]


def load(name):
    with (ROOT / "templates" / name / "data.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["value"] = float(row["value"])
    return rows


def setup(ax, config):
    ax.set_facecolor("white")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(config.get("all_spines", False) or side in ("left", "bottom"))
        ax.spines[side].set_color("#9CA3AF"); ax.spines[side].set_linewidth(.7)
    grid = config.get("grid", "x")
    if grid != "none":
        ax.grid(True, axis="both" if grid == "both" else "x", color="#D9DEE3",
                linewidth=.6, linestyle="--" if grid == "dashed" else "-", zorder=0)
        ax.set_axisbelow(True)
    ax.tick_params(labelsize=config.get("tick", 7), length=3, color="#6B7280")
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        if config.get("bold"):
            text.set_fontweight("bold")


def qq(rows, color, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.2, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    values = np.sort(np.array([r["value"] for r in rows]))
    probs = (np.arange(1, len(values) + 1) - .5) / len(values)
    norm = NormalDist()
    theoretical = [norm.inv_cdf(float(p)) for p in probs]
    ax.scatter(theoretical, values, s=9, color=color, edgecolors="white", linewidths=.2, alpha=.85)
    ax.set_xlabel("Theoretical quantiles", fontsize=config.get("tick", 7) + 1)
    ax.set_ylabel("Sample quantiles", fontsize=config.get("tick", 7) + 1)
    setup(ax, config)
    fig.tight_layout(pad=.3)
    return fig


def event(rows, color, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.2, 2.3)), dpi=180)
    fig.patch.set_facecolor("white")
    for i, name in enumerate(dict.fromkeys(r["series"] for r in rows)):
        vals = [r["value"] for r in rows if r["series"] == name]
        ax.eventplot(vals, lineoffsets=i, colors=color, linewidths=1.4)
    ax.set_yticks(range(len(dict.fromkeys(r["series"] for r in rows))))
    ax.set_yticklabels(list(dict.fromkeys(r["series"] for r in rows)), fontsize=7)
    ax.set_xlabel("Latency (ms)", fontsize=config.get("tick", 7) + 1)
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


def build(name, draw_fn):
    rows = load(name); out = HERE / name; (out / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": name, "sheets": []}
    axes = [
        ("00-color", "color", "单色", [(f"color-{i}", {"color": c}) for i, c in enumerate(COLORS)], 3),
        ("01-style", "style", "15 个白底风格", [(n, {"color": COLORS[0], **k}) for n, k in STYLES], 3),
        ("02-type", "type", "15 个字体", [(n, {"color": COLORS[0], "font": f}) for n, f in TYPES], 3),
        ("03-grid", "grid", "背景参考线", [(n, {"color": COLORS[0], "grid": n}) for n in ("none", "x", "dashed", "both")], 2),
        ("04-size", "size", "物理尺寸", [(n, {"color": COLORS[0], "figsize": s}) for n, s in SIZES], 3),
    ]
    for sheet_id, title, subtitle, items, columns in axes:
        panels = []
        for i, (label, kwargs) in enumerate(items):
            fig = draw_fn(rows, **kwargs)
            path = out / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, out / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def main():
    build("qq", qq)
    build("eventplot", event)


if __name__ == "__main__":
    main()


