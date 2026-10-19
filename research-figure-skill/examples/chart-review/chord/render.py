"""Chord axis-review: color / style / type / labels / size."""
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
DATA = ROOT / "examples/templates/chord/data.csv"
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
PALETTES = {
    "tol-bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44"],
    "d3-orange": ["#F6D3B5", "#E9A875", "#D98A48", "#E07A2F"],
    "pastel": ["#A8D5E5", "#F2C6CE", "#C9E4CB", "#E8D8B5"],
    "tableau": ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2"],
}
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .5}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {"font": "comic"}), ("boxed-journal", {"border": 1.4}),
    ("grid-paper", {"grid": True}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10, "width": 2}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"width": 2, "bold": True}), ("pastel-poster", {"tick": 10, "alpha": .45}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
SIZES = [("tiny", (2.4, 2.2)), ("single", (3.2, 2.8)), ("square", (3.2, 3.2)),
         ("wide", (3.6, 2.2)), ("medium", (4.2, 3.4)), ("double", (6.6, 4.8)),
         ("double-wide", (6.6, 3.4)), ("slide", (8.6, 5.0)), ("tall", (2.6, 4.2))]


def load():
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["value"] = float(row["value"])
    return rows


def draw(rows, colors, *, font="arial", tick=7, labels=True, alpha=.55,
         width=2.5, bold=False, grid=False, border=1, figsize=(3.2, 2.8)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white"); ax.axis("off")
    nodes = list(dict.fromkeys([r["source"] for r in rows] + [r["target"] for r in rows]))
    totals = {n: sum(r["value"] for r in rows if n in (r["source"], r["target"])) for n in nodes}
    total = sum(totals.values())
    angles = {}; cursor = 0.0
    for node in nodes:
        span = 2 * np.pi * totals[node] / total - .02
        angles[node] = (cursor, cursor + span); cursor += span + .02
    for node, (a0, a1) in angles.items():
        theta = np.linspace(a0, a1, 40)
        ax.plot(np.cos(theta), np.sin(theta), color="#4B5563", linewidth=width)
        mid = (a0 + a1) / 2
        if labels:
            ax.text(1.15 * np.cos(mid), 1.15 * np.sin(mid), node, ha="center", va="center",
                    fontsize=max(5, tick - 1))
    max_v = max(r["value"] for r in rows)
    for i, row in enumerate(rows):
        a0 = sum(angles[row["source"]]) / 2; a1 = sum(angles[row["target"]]) / 2
        p0 = (np.cos(a0), np.sin(a0)); p1 = (np.cos(a1), np.sin(a1))
        verts = [p0, (0, 0), p1]
        codes = [1, 3, 3]
        ax.add_patch(matplotlib.patches.PathPatch(matplotlib.path.Path(verts, codes), fill=False,
                                                  edgecolor=colors[i % len(colors)],
                                                  linewidth=.8 + 3 * row["value"] / max_v, alpha=alpha))
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.35, 1.35); ax.set_aspect("equal")
    if bold:
        for text in ax.texts:
            text.set_fontweight("bold")
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
    index = {"version": 1, "chart": "chord", "sheets": []}
    axes = [
        ("00-color", "color", "4 个色板", [(n, {"colors": c}) for n, c in PALETTES.items()], 2),
        ("01-style", "style", "15 个白底风格", [(n, {"colors": PALETTES["tol-bright"], **k}) for n, k in STYLES], 3),
        ("02-type", "type", "15 个字体", [(n, {"colors": PALETTES["tol-bright"], "font": f}) for n, f in TYPES], 3),
        ("03-labels", "labels", "标签开关", [("labels", {"colors": PALETTES["tol-bright"], "labels": True}),
                                              ("no labels", {"colors": PALETTES["tol-bright"], "labels": False})], 2),
        ("04-size", "size", "物理尺寸", [(n, {"colors": PALETTES["tol-bright"], "figsize": s}) for n, s in SIZES], 3),
    ]
    for sheet_id, title, subtitle, items, columns in axes:
        panels = []
        for i, (label, kwargs) in enumerate(items):
            fig = draw(rows, **kwargs)
            path = HERE / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, HERE / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})
    (HERE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
