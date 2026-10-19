"""Render the curated recipes and index all generated artifacts with tags."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from compile import ROOT, backend, compile_ir, load_recipes


def wrap_text(text, font, width, draw):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and draw.textlength(candidate, font=font) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    return [*lines, line]


def contact_sheet(entries, output):
    # These fonts ship with Matplotlib; no asset or font is fetched.
    font_path = backend.fm.findfont(backend.fm.FontProperties(family="DejaVu Sans"))
    chart_font = ImageFont.truetype(font_path, 15)
    title_font = ImageFont.truetype(font_path, 23)
    body_font = ImageFont.truetype(font_path, 17)
    width, height, columns = 720, 670, 2
    sheet = Image.new("RGB", (columns * width, math.ceil(len(entries) / columns) * height), "white")
    draw = ImageDraw.Draw(sheet)
    for i, entry in enumerate(entries):
        x, y = i % columns * width, i // columns * height
        draw.rectangle((x + 6, y + 6, x + width - 6, y + height - 6), outline="#ccd2dc", width=2)
        draw.text((x + 22, y + 14), f"{entry['chart']} / {entry['variant']}",
                  fill="#6B7280", font=chart_font)
        draw.text((x + 22, y + 38), entry["title"], fill="#20252c", font=title_font)
        tags = " / ".join(entry["tags"])
        for j, line in enumerate(wrap_text(tags, body_font, width - 44, draw)):
            draw.text((x + 22, y + 72 + j * 22), line, fill="#57606c", font=body_font)
        with Image.open(output / entry["files"]["png"]) as source:
            preview = source.convert("RGB")
            preview.thumbnail((width - 44, 470), Image.Resampling.LANCZOS)
            sheet.paste(preview, (x + (width - preview.width) // 2, y + 110 + (470 - preview.height) // 2))
        d = entry["decisions"]
        summary = f"{d['size']} | {d['palette']} | {', '.join(d['emphasis']) or 'equal emphasis'}"
        for j, line in enumerate(wrap_text(summary, body_font, width - 44, draw)):
            draw.text((x + 22, y + 592 + j * 21), line, fill="#20252c", font=body_font)
        draw.text((x + 22, y + height - 30), "MOCK / layout test", fill="#707780", font=body_font)
    sheet.save(output / "contact-sheet.png")


def build_catalog(output):
    output = Path(output)
    recipes = load_recipes()
    if not recipes:
        raise ValueError("Recipe registry is empty")
    chart_order = [c["id"] for c in json.loads((ROOT / "library/charts.json").read_text(encoding="utf8"))["charts"]]
    recipes = sorted(recipes, key=lambda r: (chart_order.index(r["chart"]), r["variant"]))
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for recipe in recipes:
        name = recipe["id"]
        config, decisions = compile_ir(ROOT / recipe["ir"], output / name, render=True)
        if set(config["figure"]["formats"]) != {"png", "pdf", "svg"}:
            raise ValueError(f"Catalog recipe {name} must export png, pdf and svg")
        files = {ext: f"{name}/figure.{ext}" for ext in ("png", "pdf", "svg")}
        files.update(config=f"{name}/config.json", data=f"{name}/data.csv", decisions=f"{name}/decisions.json")
        entries.append({"recipe": name, "title": recipe["title"], "chart": recipe["chart"],
                        "variant": recipe["variant"], "tags": recipe["tags"],
                        "files": files, "decisions": decisions})
    contact_sheet(entries, output)
    groups = {}
    for entry in entries:
        groups.setdefault(entry["chart"], []).append(entry["recipe"])
    index = {"version": 1, "contact_sheet": {"file": "contact-sheet.png", "recipe": "all",
             "tags": ["catalog", "mock"], "decisions": {"recipes": [e["recipe"] for e in entries]}},
             "groups": groups, "entries": entries}
    (output / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "examples/catalog")
    args = parser.parse_args()
    try:
        index = build_catalog(args.output)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Rendered {len(index['entries'])} recipes; {args.output / 'contact-sheet.png'}; {args.output / 'index.json'}")


if __name__ == "__main__":
    main()
