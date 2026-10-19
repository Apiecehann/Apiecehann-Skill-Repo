"""Node-link axis-review: style / type / layout / labels / size."""
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
ROOT = HERE.parents[2]
LABEL_FONT = r"C:\Windows\Fonts\msyh.ttc"
DATA = ROOT / "examples/templates/node-link/data.csv"
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
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .8}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "width": 2.6, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {"font": "comic"}), ("boxed-journal", {"all_spines": True}),
    ("grid-paper", {"grid": True}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10, "width": 2.8}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"width": 2.5, "bold": True}), ("pastel-poster", {"tick": 10}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
LAYOUTS = ["circular", "two-column"]
SIZES = [("tiny", (2.4, 2.0)), ("single", (3.3, 2.8)), ("square", (3.3, 3.3)),
         ("wide", (3.6, 2.0)), ("medium", (4.5, 3.4)), ("double", (7, 5)),
         ("double-wide", (7, 3.6)), ("slide", (9, 5.06)), ("tall", (2.6, 4.2))]


def load():
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["weight"] = float(row["weight"])
    return rows


def draw(rows, *, font="arial", tick=7, width=1.8, alpha=.55, bold=False,
         all_spines=False, grid=False, layout="circular", labels=True, figsize=(3.3, 2.8)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    nodes = list(dict.fromkeys([r["source"] for r in rows] + [r["target"] for r in rows]))
    if layout == "circular":
        angle = np.linspace(0, 2 * np.pi, len(nodes), endpoint=False)
        pos = {name: (float(np.cos(a)), float(np.sin(a))) for name, a in zip(nodes, angle)}
    else:
        half = (len(nodes) + 1) // 2
        pos = {name: (0, 1 - 2 * i / max(1, half - 1)) for i, name in enumerate(nodes[:half])}
        pos.update({name: (1, 1 - 2 * i / max(1, len(nodes) - half - 1)) for i, name in enumerate(nodes[half:])})
    max_w = max(r["weight"] for r in rows)
    for row in rows:
        x1, y1 = pos[row["source"]]; x2, y2 = pos[row["target"]]
        ax.plot([x1, x2], [y1, y2], color="#2F80C9",
                linewidth=.6 + width * row["weight"] / max_w, alpha=alpha, zorder=1)
    for name, (x, y) in pos.items():
        ax.scatter([x], [y], s=65, color="#2F80C9", edgecolors="white", linewidths=1.1, zorder=3)
        if labels:
            ax.text(x, y - .12, name, ha="center", va="top", fontsize=tick - 1)
    if layout == "circular":
        ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.25, 1.25)
    else:
        ax.set_xlim(-.2, 1.2); ax.set_ylim(-1.1, 1.1)
    ax.set_aspect("equal")
    if all_spines:
        ax.set_xticks([]); ax.set_yticks([])
    else:
        ax.axis("off")
    if grid:
        ax.grid(True, color="#E5E7EB", linewidth=.6)
    if bold:
        for text in ax.texts:
            text.set_fontweight("bold")
    fig.tight_layout(pad=.2)
    return fig


def sheet(title, subtitle, panels, columns, out, cell=(380, 300)):
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


def main():
    rows = load(); (HERE / "panels").mkdir(exist_ok=True)
    index = {"version": 1, "chart": "node-link", "sheets": []}

    def add(sheet_id, title, subtitle, items, columns):
        panels = []
        for i, (label, kwargs) in enumerate(items):
            fig = draw(rows, **kwargs)
            path = HERE / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, HERE / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})

    add("00-style", "style", "15 个白底风格", [(n, k) for n, k in STYLES], 3)
    add("01-type", "type", "15 个字体", [(n, {"font": f}) for n, f in TYPES], 3)
    add("02-layout", "layout", "布局", [(n, {"layout": n}) for n in LAYOUTS], 2)
    add("03-labels", "labels", "节点标签", [("labels", {"labels": True}), ("no labels", {"labels": False})], 2)
    add("04-size", "size", "物理尺寸", [(n, {"figsize": s}) for n, s in SIZES], 3)
    (HERE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
