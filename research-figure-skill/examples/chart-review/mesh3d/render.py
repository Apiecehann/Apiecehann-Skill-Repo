"""Bar3d axis-review: color / style / type / view / size."""
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
LABEL_FONT = r"C:\Windows\Fonts\msyh.ttc"
DATA = ROOT / "examples" / "templates" / "bar3d" / "data.csv"
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
    "tol-bright": ["#4477AA", "#EE6677"],
    "d3-orange": ["#D98A48", "#E07A2F"],
    "pastel": ["#A8D5E5", "#F2C6CE"],
    "tableau": ["#4E79A7", "#F28E2B"],
}
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .75}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {"font": "comic"}), ("boxed-journal", {"pane": True}),
    ("grid-paper", {"grid": True}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"bold": True, "alpha": 1}), ("pastel-poster", {"tick": 10, "alpha": .7}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
VIEWS = [("default", (24, -55)), ("front", (10, -90)), ("low", (8, -35)), ("top", (60, 45))]
SIZES = [("tiny", (2.6, 2.0)), ("single", (3.3, 2.5)), ("square", (3.3, 3.3)),
         ("wide", (3.6, 2.0)), ("medium", (4.5, 3.2)), ("double", (7, 5)),
         ("double-wide", (7, 3.6)), ("slide", (9, 5.06)), ("tall", (2.6, 4.2))]


def load():
    with DATA.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["value"] = float(row["value"])
    return rows


def draw(rows, colors, *, font="arial", tick=7, alpha=.9, bold=False,
         grid=True, pane=False, view=(24, -55), figsize=(3.3, 2.5)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    fig = plt.figure(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    ax = fig.add_subplot(111, projection="3d")
    groups = list(dict.fromkeys(r["group"] for r in rows))
    series = list(dict.fromkeys(r["series"] for r in rows))
    for j, name in enumerate(series):
        for i, group in enumerate(groups):
            value = next(r["value"] for r in rows if r["group"] == group and r["series"] == name)
            ax.bar3d(i - .22, j - .22, 0, .36, .36, value, color=colors[j],
                     edgecolor="white", linewidth=.3, alpha=alpha)
    ax.set_xticks(range(len(groups))); ax.set_xticklabels(groups, fontsize=max(5, tick - 1))
    ax.set_yticks(range(len(series))); ax.set_yticklabels(series, fontsize=max(5, tick - 1))
    ax.set_zlabel("Success rate (%)", fontsize=tick, labelpad=1)
    ax.tick_params(labelsize=max(5, tick - 1), pad=0)
    ax.view_init(elev=view[0], azim=view[1])
    ax.grid(grid)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1, 1, 1, 1))
        axis.pane.set_edgecolor("#9CA3AF" if pane else (1, 1, 1, 1))
        axis._axinfo["grid"]["color"] = (0.85, 0.87, 0.89, 1)
    if bold:
        for text in ax.get_xticklabels() + ax.get_yticklabels() + ax.get_zticklabels():
            text.set_fontweight("bold")
    fig.subplots_adjust(left=.02, right=.98, bottom=.02, top=.98)
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
    index = {"version": 1, "chart": "bar3d", "sheets": []}

    def add(sheet_id, title, subtitle, items, columns):
        panels = []
        for i, (colors, label, kwargs) in enumerate(items):
            fig = draw(rows, colors, **kwargs)
            path = HERE / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, HERE / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})

    add("00-color", "color", "两系列色板", [(c, n, {}) for n, c in PALETTES.items()], 2)
    add("01-style", "style", "15 个白底风格", [(PALETTES["tol-bright"], n, k) for n, k in STYLES], 3)
    add("02-type", "type", "15 个字体", [(PALETTES["tol-bright"], n, {"font": f}) for n, f in TYPES], 3)
    add("03-view", "view angle", "三维视角", [(PALETTES["tol-bright"], n, {"view": v}) for n, v in VIEWS], 2)
    add("04-size", "size", "物理尺寸", [(PALETTES["tol-bright"], n, {"figsize": s}) for n, s in SIZES], 3)
    (HERE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
