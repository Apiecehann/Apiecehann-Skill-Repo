"""Hist2d / hexbin axis-review: colormap / style / type / bins / size."""
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
CMAPS = ["Blues", "viridis", "magma", "RdBu_r"]
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .8}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {"font": "comic"}), ("boxed-journal", {"all_spines": True}),
    ("grid-paper", {"grid": True}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"bold": True}), ("pastel-poster", {"tick": 10}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
BINS = [10, 16, 24, 32]
SIZES = [("tiny", (2.4, 1.8)), ("single", (3.2, 2.3)), ("square", (3.0, 3.0)),
         ("wide", (3.6, 1.8)), ("medium", (4.2, 2.8)), ("double", (6.6, 4.6)),
         ("double-wide", (6.6, 3.2)), ("slide", (8.6, 4.8)), ("tall", (2.4, 4.0))]


def load(name):
    with (ROOT / "examples/templates" / name / "data.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["x"], row["y"] = float(row["x"]), float(row["y"])
    return rows


def setup(ax, config):
    ax.set_facecolor("white")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(config.get("all_spines", False) or side in ("left", "bottom"))
        ax.spines[side].set_color("#9CA3AF"); ax.spines[side].set_linewidth(.7)
    ax.tick_params(labelsize=config.get("tick", 7), length=3, color="#6B7280")
    if config.get("grid"):
        ax.grid(True, color="#E5E7EB", linewidth=.6)
    for text in ax.get_xticklabels() + ax.get_yticklabels():
        if config.get("bold"):
            text.set_fontweight("bold")


def show(rows, cmap, *, font="arial", tick=7, bins=20, alpha=1, bold=False,
         all_spines=False, grid=False, figsize=(3.2, 2.3)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    return fig, ax


def hist(rows, cmap, **config):
    fig, ax = show(rows, cmap, **config)
    ax.hist2d([r["x"] for r in rows], [r["y"] for r in rows],
              bins=config.get("bins", 20), cmap=plt.get_cmap(cmap), alpha=config.get("alpha", 1))
    ax.set_xlabel("Latency (ms)", fontsize=config.get("tick", 7) + 1)
    ax.set_ylabel("Throughput", fontsize=config.get("tick", 7) + 1)
    setup(ax, config); fig.tight_layout(pad=.3)
    return fig


def hexb(rows, cmap, **config):
    fig, ax = show(rows, cmap, **config)
    ax.hexbin([r["x"] for r in rows], [r["y"] for r in rows],
              gridsize=config.get("bins", 18), cmap=plt.get_cmap(cmap), mincnt=1, linewidths=.2)
    ax.set_xlabel("Latency (ms)", fontsize=config.get("tick", 7) + 1)
    ax.set_ylabel("Throughput", fontsize=config.get("tick", 7) + 1)
    setup(ax, config); fig.tight_layout(pad=.3)
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
        ("00-colormap", "colormap", "4 个色图", [(c, {"cmap": c}) for c in CMAPS], 2),
        ("01-style", "style", "15 个白底风格", [(n, {"cmap": "Blues", **k}) for n, k in STYLES], 3),
        ("02-type", "type", "15 个字体", [(n, {"cmap": "Blues", "font": f}) for n, f in TYPES], 3),
        ("03-bins", "bins", "分箱数", [(str(n), {"cmap": "Blues", "bins": n}) for n in BINS], 2),
        ("04-size", "size", "物理尺寸", [(n, {"cmap": "Blues", "figsize": s}) for n, s in SIZES], 3),
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
    build("hist2d", hist)
    build("hexbin", hexb)


if __name__ == "__main__":
    main()
