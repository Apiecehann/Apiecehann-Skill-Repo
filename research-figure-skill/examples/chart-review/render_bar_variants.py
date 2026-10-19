"""Bar variants review: lollipop / bullet / waterfall / funnel / bump."""
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


def data():
    groups = ["Bench A", "Bench B", "Bench C", "Bench D"]
    return groups, [72, 61, 55, 66], [84, 74, 69, 78]


def draw(kind, variant, color=0, labels=True, figsize=(3.2, 2.2)):
    plt.rcParams["font.family"] = matplotlib.font_manager.FontProperties(fname=FONTS["arial"]).get_name()
    groups, base, ours = data()
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    c0, c1 = COLORS[color % len(COLORS)], COLORS[(color + 1) % len(COLORS)]
    if kind == "lollipop":
        x = np.arange(len(groups))
        ax.vlines(x, 0, ours, color=c1, linewidth=2)
        ax.scatter(x, ours, s=40, color=c1, zorder=3)
        ax.set_xticks(x); ax.set_xticklabels(groups)
        ax.set_ylabel("Success rate (%)")
    elif kind == "bullet":
        y = np.arange(len(groups))
        ax.barh(y, ours, color=c0, height=.5)
        ax.scatter(base, y, marker="|", s=90, color=c1, zorder=4)
        ax.set_yticks(y); ax.set_yticklabels(groups)
        ax.set_xlabel("Success rate (%)")
    elif kind == "waterfall":
        deltas = [ours[i] - base[i] for i in range(len(groups))]
        start = 40
        for i, d in enumerate(deltas):
            ax.bar(i, d, bottom=start, color=c1 if d >= 0 else c0)
            start += d
        ax.set_xticks(range(len(groups))); ax.set_xticklabels(groups)
        ax.set_ylabel("Cumulative gain")
    elif kind == "funnel":
        y = np.arange(len(groups))
        ax.barh(y, ours, color=c0, height=.6)
        ax.invert_yaxis()
        ax.set_yticks(y); ax.set_yticklabels(groups)
        ax.set_xlabel("Success rate (%)")
    else:
        ranks = [sorted(ours, reverse=True).index(v) + 1 for v in ours]
        ax.plot(range(len(groups)), ranks, marker="o", color=c1, linewidth=1.8)
        ax.set_xticks(range(len(groups))); ax.set_xticklabels(groups)
        ax.set_yticks([1, 2, 3, 4]); ax.invert_yaxis()
        ax.set_ylabel("Rank")
    ax.set_title(variant, fontsize=8)
    if labels and kind in ("lollipop", "funnel"):
        for i, v in enumerate(ours):
            ax.text(i, v + 1, f"{v}", ha="center", fontsize=6)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=.3)
    return fig


def sheet(title, panels, columns, out, cell=(380, 280)):
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


def main():
    out = HERE / "bar-variants"; (out / "panels").mkdir(parents=True, exist_ok=True)
    index = {"version": 1, "chart": "grouped-bar", "sheet_kind": "variants", "sheets": []}
    for kind in ("lollipop", "bullet", "waterfall", "funnel", "bump"):
        panels = []
        for i, (label, kwargs) in enumerate([
            ("canonical", {}), ("alt color", {"color": 1}),
            ("no labels", {"labels": False}), ("wide", {"figsize": (4.2, 2.4)}),
        ]):
            fig = draw(kind, kind, **kwargs)
            path = out / "panels" / f"{kind}-{i}.png"
            fig.savefig(path, dpi=180, facecolor="white"); plt.close(fig)
            panels.append((path, label))
        sheet(f"{kind} variant", panels, 2, out / f"{kind}.png")
        index["sheets"].append({"id": kind, "title": kind, "panels": len(panels)})
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()
