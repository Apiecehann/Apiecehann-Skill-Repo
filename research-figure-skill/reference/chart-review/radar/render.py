"""Radar axis-review: color / style / type / axis-count / fill / size."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
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
PALETTES = {
    "tol-bright": ["#4477AA", "#EE6677", "#228833"],
    "d3-orange": ["#D98A48", "#E9A875", "#E07A2F"],
    "pastel": ["#7FB3D5", "#E6A0B0", "#8CC9A8"],
    "tableau": ["#4E79A7", "#F28E2B", "#59A14F"],
}
AXES = ["Accuracy", "Robustness", "Speed", "Memory", "Calibration", "Generalization", "Fairness", "Efficiency"]
SERIES = ["baseline-a", "baseline-b", "ours"]
VALUES = {
    "baseline-a": [62, 55, 70, 48, 60, 52, 58, 45],
    "baseline-b": [70, 64, 58, 66, 68, 60, 63, 55],
    "ours": [84, 78, 72, 69, 82, 80, 76, 70],
}
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .7}), ("serif-emphasis", {"font": "times"}),
    ("bold-slide", {"tick": 9, "bold": True}), ("minimal-mono", {"tick": 6}),
    ("hand-drawn", {"font": "comic"}), ("boxed-journal", {"all_spines": True}),
    ("grid-paper", {"grid": True}), ("editorial-serif", {"font": "times"}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10, "width": 2}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"width": 2, "bold": True}), ("pastel-poster", {"tick": 10, "alpha": .65}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
SIZES = [("tiny", (2.4, 2.2)), ("single", (3.3, 3.0)), ("square", (3.3, 3.3)),
         ("wide", (3.8, 2.4)), ("medium", (4.5, 3.6)), ("double", (7, 5.4)),
         ("double-wide", (7, 3.8)), ("slide", (9, 5.8)), ("tall", (2.8, 4.4))]


def draw(count, colors, *, font="arial", tick=7, width=1.8, alpha=.12, grid=True,
         fill=True, bold=False, all_spines=False, figsize=(3.3, 3.0)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS[font]).get_name()
    axes = AXES[:count]
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False).tolist(); angles += angles[:1]
    fig, ax = plt.subplots(figsize=figsize, subplot_kw={"projection": "polar"}, dpi=180)
    fig.patch.set_facecolor("white"); ax.set_facecolor("white")
    ax.set_theta_offset(np.pi / 2); ax.set_theta_direction(-1)
    ax.set_ylim(0, 100)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(axes, fontsize=tick)
    ax.tick_params(axis="y", labelsize=max(4, tick - 2), colors="#9CA3AF")
    ax.grid(grid)
    for name, color in zip(SERIES, colors):
        values = VALUES[name][:count] + [VALUES[name][0]]
        ax.plot(angles, values, color=color, linewidth=width, label=name.replace("baseline-", "Baseline ").title())
        if fill:
            ax.fill(angles, values, color=color, alpha=alpha)
    ax.legend(frameon=False, fontsize=max(5, tick - 2), loc="upper right", bbox_to_anchor=(1.18, 1.12))
    if all_spines:
        ax.spines["polar"].set_linewidth(1.2)
    if bold:
        for text in ax.get_xticklabels() + ax.get_yticklabels():
            text.set_fontweight("bold")
    fig.tight_layout(pad=.2)
    return fig


def sheet(title, subtitle, panels, columns, out, cell=(380, 320)):
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
    (HERE / "panels").mkdir(exist_ok=True)
    index = {"version": 1, "chart": "radar", "sheets": []}

    def add(sheet_id, title, subtitle, items, columns):
        panels = []
        for i, (label, kwargs) in enumerate(items):
            fig = draw(**kwargs)
            path = HERE / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, HERE / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})

    add("00-color", "color", "3-series 色板", [(n, {"count": 8, "colors": c}) for n, c in PALETTES.items()], 2)
    add("01-style", "style", "15 个白底风格", [(n, {"count": 8, "colors": PALETTES["tol-bright"], **k}) for n, k in STYLES], 3)
    add("02-type", "type", "15 个字体", [(n, {"count": 8, "colors": PALETTES["tol-bright"], "font": f}) for n, f in TYPES], 3)
    add("03-axis-count", "axis count", "5 / 6 / 8 个维度", [(f"{n} axes", {"count": n, "colors": PALETTES["tol-bright"]}) for n in (5, 6, 8)], 3)
    add("04-fill", "fill", "填充 / 只描边", [("fill", {"count": 8, "colors": PALETTES["tol-bright"], "fill": True}),
                                               ("outline", {"count": 8, "colors": PALETTES["tol-bright"], "fill": False})], 2)
    add("05-size", "size", "物理尺寸", [(n, {"count": 8, "colors": PALETTES["tol-bright"], "figsize": s}) for n, s in SIZES], 3)
    (HERE / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
