"""Stage 1 palette shootout: focus strategies x accent colours.

This is a study, not a skill recipe. It renders the same 4x3 data with four
baseline strategies and three accents, then composes a labelled contact sheet.
No external image or font is used.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCRIPTS = ROOT / "quantitative-plots/grouped-bar/scripts"
sys.path.insert(0, str(SCRIPTS))
import render as backend  # noqa: E402

SERIES = ["method-1", "method-2", "method-3", "ours"]
LABELS = {"method-1": "Method 1", "method-2": "Method 2",
          "method-3": "Method 3", "ours": "Ours"}
ACCENTS = {"blue": "#2F80C9", "teal": "#1F9E89", "orange": "#E07A2F"}


def mix(color: str, t: float) -> str:
    """Mix a hex colour with white; t=0 keeps the colour, t=1 is white."""
    h = color.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    out = [round(c + (255 - c) * t) for c in rgb]
    return "#" + "".join(f"{v:02x}" for v in out)


def strategy_colors(strategy: str, accent: str) -> list[str]:
    if strategy == "A same-gray":
        return ["#C9C6BF", "#C9C6BF", "#C9C6BF"]
    if strategy == "B gray-tints":
        return ["#DEDAD2", "#C9C6BF", "#A8A49C"]
    if strategy == "C muted-hues":
        return ["#D8A7A7", "#A8C3B0", "#A9B8C9"]
    if strategy == "D accent-tints":
        return [mix(accent, .78), mix(accent, .55), mix(accent, .32)]
    raise ValueError(strategy)


def config_for(colors: list[str], accent: str) -> dict:
    palette = {series: {"fill": color, "edge": color, "label": "#20252c"}
               for series, color in zip(SERIES[:3], colors)}
    palette["ours"] = {"fill": accent, "edge": accent, "label": "#20252c"}
    return {
        "data": str(HERE / "data.csv"),
        "figure": {"formats": ["png"], "dpi": 200},
        "preset": {"style": "paper-clean", "layout": "grouped",
                   "size": "single", "palette": "tol-bright", "font": "sans"},
        "series_order": SERIES,
        "panel_defaults": {
            "limits": "auto", "ticks": "auto", "tick_format": ".0%",
            "ylabel": "Success rate", "value_labels": False,
            "bar_fill_alpha": 1, "bar_edge_alpha": 1, "bar_edge_width": 0,
            "category_pad": 6, "grid": {"kind": "none"},
        },
        "legend_defaults": {
            "show": True, "columns": "auto", "loc": "lower center",
            "anchor": [.5, 1.06], "frame": False, "size": 6.5,
            "labels": LABELS, "handlelength": 1.2, "columnspacing": 1.2,
            "handletextpad": .4, "borderaxespad": 0,
        },
        "palette": palette,
    }


def main() -> int:
    rows = backend.load_data(HERE / "data.csv")
    out = HERE / "panels"
    out.mkdir(exist_ok=True)
    strategies = ["A same-gray", "B gray-tints", "C muted-hues", "D accent-tints"]
    entries = []
    for strategy in strategies:
        for accent_name, accent in ACCENTS.items():
            sid = f"{strategy.split()[0]}-{accent_name}"
            colors = strategy_colors(strategy, accent)
            config = config_for(colors, accent)
            backend.render(config, rows, out / sid)
            entries.append({"id": sid, "strategy": strategy, "accent": accent_name,
                            "accent_hex": accent, "baseline_colors": colors,
                            "file": f"panels/{sid}.png"})
            print("rendered", sid)

    font_path = backend.fm.findfont(backend.fm.FontProperties(family="DejaVu Sans"))
    title = ImageFont.truetype(font_path, 28)
    label = ImageFont.truetype(font_path, 20)
    small = ImageFont.truetype(font_path, 16)
    hex_font = ImageFont.truetype(font_path, 12)

    cell_w, cell_h, left, top = 450, 360, 150, 92
    sheet = Image.new("RGB", (left + cell_w * 3 + 30, top + cell_h * 4 + 50), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), "Focus strategies x accent — Stage 1", fill="#20252c", font=title)
    draw.text((24, 54), "Same data, same layout; labels are the only series cue in A. MOCK / layout test.",
              fill="#57606c", font=small)
    for j, accent_name in enumerate(ACCENTS):
        draw.text((left + j * cell_w + 12, 70), accent_name, fill="#20252c", font=label)
    for i, strategy in enumerate(strategies):
        y = top + i * cell_h
        draw.text((24, y + 12), strategy, fill="#20252c", font=label)
        for j, accent_name in enumerate(ACCENTS):
            sid = f"{strategy.split()[0]}-{accent_name}"
            entry = next(e for e in entries if e["id"] == sid)
            with Image.open(out / f"{sid}.png") as source:
                preview = source.convert("RGB")
                preview.thumbnail((cell_w - 24, cell_h - 44), Image.Resampling.LANCZOS)
                x = left + j * cell_w + (cell_w - preview.width) // 2
                sheet.paste(preview, (x, y + 8))
            # swatches: three baselines + accent; hex values are listed below
            for k, color in enumerate(entry["baseline_colors"] + [entry["accent_hex"]]):
                sx = left + j * cell_w + 14 + k * 24
                sy = y + cell_h - 36
                draw.rectangle((sx, sy, sx + 16, sy + 16), fill=color, outline="#cfd5dc")
            draw.text((left + j * cell_w + 14, y + cell_h - 16),
                      " ".join(entry["baseline_colors"] + [entry["accent_hex"]]),
                      fill="#57606c", font=hex_font)
    sheet.save(HERE / "stage1.png")
    (HERE / "index.json").write_text(json.dumps(
        {"version": 1, "data": "data.csv", "sheet": "stage1.png", "entries": entries},
        ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("wrote", HERE / "stage1.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
