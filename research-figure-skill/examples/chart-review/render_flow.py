"""Sankey / treemap axis-review: color / style / type / layout / size."""
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
PALETTES = {
    "d3-blue": ["#D6E4F0", "#A8C8E8", "#6FA3D8", "#2F80C9"],
    "d3-orange": ["#F6D3B5", "#E9A875", "#D98A48", "#E07A2F"],
    "tol-bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44"],
    "pastel": ["#A8D5E5", "#F2C6CE", "#C9E4CB", "#E8D8B5"],
}
STYLES = [
    ("paper-clean", {}), ("soft-outline", {"alpha": .72}),
    ("serif-emphasis", {"font": "times"}), ("bold-slide", {"tick": 9, "bold": True}),
    ("minimal-mono", {"tick": 6, "alpha": .55}), ("hand-drawn", {"font": "comic"}),
    ("boxed-journal", {"all_spines": True}), ("grid-paper", {"grid": True}),
    ("editorial-serif", {"font": "times", "alpha": .5}),
    ("white-slide", {"font": "times", "tick": 9}), ("technical-grid", {"font": "consolas", "grid": True}),
    ("poster-bold", {"tick": 10, "border": 2}), ("compact-journal", {"tick": 6}),
    ("high-contrast", {"border": 2, "bold": True}), ("pastel-poster", {"tick": 10, "alpha": .6}),
]
TYPES = [
    ("Arial", "arial"), ("Helvetica", "helvetica"), ("Segoe UI", "segoe"), ("Calibri", "calibri"),
    ("Verdana", "verdana"), ("Tahoma", "tahoma"), ("Trebuchet MS", "trebuchet"),
    ("Times New Roman", "times"), ("Georgia", "georgia"), ("Garamond", "garamond"),
    ("Cambria", "cambria"), ("Consolas", "consolas"), ("Courier New", "courier"),
    ("Comic Sans MS", "comic"), ("Segoe Script", "script"),
]
SIZES = [("tiny", (2.4, 1.8)), ("single", (3.2, 2.2)), ("square", (3.0, 3.0)),
         ("wide", (3.6, 1.8)), ("medium", (4.2, 2.8)), ("double", (6.6, 4.6)),
         ("double-wide", (6.6, 3.2)), ("slide", (8.6, 4.8)), ("tall", (2.4, 4.0))]


def read(name):
    with (ROOT / "examples/templates" / name / "data.csv").open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def set_style(ax, config):
    ax.set_facecolor("white")
    for side in ("left", "bottom", "top", "right"):
        ax.spines[side].set_visible(config.get("all_spines", False))
        ax.spines[side].set_linewidth(config.get("border", .8))
    ax.tick_params(labelsize=config.get("tick", 7))
    if config.get("grid"):
        ax.grid(True, color="#E5E7EB", linewidth=.6)


def sankey(rows, colors, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.2, 2.2)), dpi=180)
    fig.patch.set_facecolor("white")
    nodes = list(dict.fromkeys([r["source"] for r in rows] + [r["target"] for r in rows]))
    out_total = {n: sum(float(r["value"]) for r in rows if r["source"] == n) for n in nodes}
    in_total = {n: sum(float(r["value"]) for r in rows if r["target"] == n) for n in nodes}
    layer = {n: 0 for n in nodes}
    for _ in range(len(nodes)):
        for r in rows:
            layer[r["target"]] = max(layer[r["target"]], layer[r["source"]] + 1)
    layers = {}
    for n in nodes:
        layers.setdefault(layer[n], []).append(n)
    total = max(sum(out_total.values()), sum(in_total.values()))
    pos = {}
    for li, names in layers.items():
        sizes = [max(in_total[n], out_total[n]) / total for n in names]
        span = sum(sizes) + .04 * (len(names) - 1)
        y = .5 + span / 2
        for n, h in zip(names, sizes):
            pos[n] = (li / max(layer.values()), y - h, h)
            y -= h + .04
    out_cur = {n: pos[n][1] + pos[n][2] for n in nodes}
    in_cur = {n: pos[n][1] + pos[n][2] for n in nodes}
    for i, row in enumerate(rows):
        src, tgt = row["source"], row["target"]
        sh = float(row["value"]) / total
        x1 = pos[src][0] + .02; x2 = pos[tgt][0]
        y1a = out_cur[src]; y1b = y1a - sh
        y2a = in_cur[tgt]; y2b = y2a - sh
        out_cur[src] -= sh; in_cur[tgt] -= sh
        verts = [(x1, y1a), ((x1 + x2) / 2, y1a), ((x1 + x2) / 2, y2a), (x2, y2a),
                 (x2, y2b), ((x1 + x2) / 2, y2b), ((x1 + x2) / 2, y1b), (x1, y1b)]
        codes = [1, 4, 4, 4, 2, 4, 4, 4]
        ax.add_patch(matplotlib.patches.PathPatch(matplotlib.path.Path(verts, codes),
                                                  facecolor=colors[i % len(colors)],
                                                  alpha=config.get("alpha", .35), edgecolor="none"))
    for n in nodes:
        x, y, h = pos[n]
        ax.add_patch(matplotlib.patches.Rectangle((x, y), .02, h, color=colors[nodes.index(n) % len(colors)]))
        ax.text(x - .01 if x == 0 else x + .03, y + h / 2, n,
                ha="right" if x == 0 else "left", va="center",
                fontsize=config.get("tick", 7) - 1)
    ax.set_xlim(-.22, 1.25); ax.set_ylim(0, 1.05); ax.axis("off")
    set_style(ax, config)
    fig.tight_layout(pad=.2)
    return fig


def treemap(rows, colors, **config):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(
        fname=FONTS[config.get("font", "arial")]).get_name()
    fig, ax = plt.subplots(figsize=config.get("figsize", (3.0, 2.2)), dpi=180)
    fig.patch.set_facecolor("white")
    items = sorted(rows, key=lambda r: float(r["value"]), reverse=True)
    total = sum(float(r["value"]) for r in items)
    x = y = 0.0; w = h = 1.0
    for i, row in enumerate(items):
        frac = float(row["value"]) / total
        if config.get("layout", "slice") == "rows":
            rect = (0, y, 1, frac); y += frac
        elif w >= h:
            rect = (x, y, w * frac, h); x += w * frac
        else:
            rect = (x, y, w, h * frac); y += h * frac
        ax.add_patch(matplotlib.patches.Rectangle((rect[0], rect[1]), rect[2], rect[3],
                                                  facecolor=colors[i % len(colors)],
                                                  edgecolor="white", linewidth=config.get("border", 1.4)))
        if rect[2] > .14 and rect[3] > .09:
            ax.text(rect[0] + rect[2] / 2, rect[1] + rect[3] / 2,
                    f"{row['label']}\n{float(row['value']):g}", ha="center", va="center",
                    fontsize=config.get("tick", 7) - 1)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    set_style(ax, config)
    fig.tight_layout(pad=.2)
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


def build(chart, rows, draw_fn, layout_items):
    out = HERE / chart; (out / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": chart, "sheets": []}
    axes = [
        ("00-color", "color", "4 个色板", [(rows, PALETTES[n], n, {}) for n in PALETTES], 2),
        ("01-style", "style", "15 个白底风格", [(rows, PALETTES["d3-blue"], n, k) for n, k in STYLES], 3),
        ("02-type", "type", "15 个字体", [(rows, PALETTES["d3-blue"], l, {"font": f}) for l, f in TYPES], 3),
        ("03-layout", "layout", "布局", layout_items, 2),
        ("04-size", "size", "物理尺寸", [(rows, PALETTES["d3-blue"], n, {"figsize": s}) for n, s in SIZES], 3),
    ]
    for sheet_id, title, subtitle, items, columns in axes:
        panels = []
        for i, (rows_arg, colors, label, kwargs) in enumerate(items):
            fig = draw_fn(rows_arg, colors, **kwargs)
            path = out / "panels" / f"{sheet_id}-{i:02d}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(title, subtitle, panels, columns, out / f"{sheet_id}.png")
        index["sheets"].append({"id": sheet_id, "title": title, "panels": len(panels),
                                "labels": [p[1] for p in panels]})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def main():
    build("sankey", read("sankey"), sankey,
          [(read("sankey"), PALETTES["d3-blue"], "curve", {}),
           (read("sankey"), PALETTES["d3-blue"], "compact", {"alpha": .6})])
    build("alluvial", read("alluvial"), sankey,
          [(read("alluvial"), PALETTES["d3-blue"], "flow", {}),
           (read("alluvial"), PALETTES["d3-blue"], "compact", {"alpha": .6})])
    build("treemap", read("treemap"), treemap,
          [(read("treemap"), PALETTES["d3-blue"], "slice", {}),
           (read("treemap"), PALETTES["d3-blue"], "rows", {"layout": "rows"})])


if __name__ == "__main__":
    main()
