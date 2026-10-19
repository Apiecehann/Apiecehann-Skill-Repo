"""Translate a semantic grouped-bar IR into the existing renderer configuration."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "quantitative-plots/grouped-bar/scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as backend
import distribution as distribution_backend
import charts2d
import charts3d


def validate(value, schema, path="IR"):
    """Validate the subset of draft 2020-12 used by figure.schema.json.

    The schema is the source of truth for shape, including nested unknown keys.
    Cross-field and CSV semantics are checked below. No optional dependency is needed.
    """
    kinds = schema.get("type", [])
    kinds = [kinds] if isinstance(kinds, str) else kinds
    checks = {
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "number": lambda v: type(v) in (int, float) and math.isfinite(v),
        "integer": lambda v: type(v) in (int, float) and math.isfinite(v) and int(v) == v,
        "null": lambda v: v is None,
    }
    if kinds and not any(checks[k](value) for k in kinds):
        raise ValueError(f"{path}: expected {' or '.join(kinds)}")
    if "const" in schema and value != schema["const"]:
        raise ValueError(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: choose from {schema['enum']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{path}: missing required field {key!r}")
        for key, item in value.items():
            rule = props.get(key, schema.get("additionalProperties", True))
            if rule is False:
                raise ValueError(f"{path}: unknown field {key!r}")
            if isinstance(rule, dict):
                validate(item, rule, f"{path}.{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ValueError(f"{path}: needs at least {schema['minItems']} item(s)")
        if schema.get("uniqueItems") and len({json.dumps(v, sort_keys=True) for v in value}) != len(value):
            raise ValueError(f"{path}: entries must be unique")
        for i, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{path}[{i}]")
    elif isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            raise ValueError(f"{path}: must not be empty")
    elif type(value) in (int, float):
        if value < schema.get("minimum", -math.inf) or value > schema.get("maximum", math.inf):
            raise ValueError(f"{path}: outside allowed range")


def load_ir(path):
    path = Path(path)
    ir = json.loads(path.read_text(encoding="utf-8-sig"))
    schema = json.loads((Path(__file__).parent / "figure.schema.json").read_text(encoding="utf8"))
    validate(ir, schema)
    return ir


def load_recipes():
    """Load the curated registry; recipe paths are relative to the skill root."""
    registry = json.loads((ROOT / "library/recipes.json").read_text(encoding="utf8"))
    if registry.get("version") != 1 or not isinstance(registry.get("recipes"), list):
        raise ValueError("recipes.json requires version 1 and a recipes list")
    seen = set()
    chart_ids = {c["id"] for c in json.loads((ROOT / "library/charts.json").read_text(encoding="utf8"))["charts"]}
    for recipe in registry["recipes"]:
        if set(recipe) != {"id", "title", "chart", "variant", "tags", "ir"}:
            raise ValueError("Each recipe needs id, title, chart, variant, tags and ir")
        name = recipe["id"]
        if not isinstance(name, str) or not name or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in name) or name in seen:
            raise ValueError(f"Invalid or duplicate recipe id {name!r}")
        seen.add(name)
        if recipe["chart"] not in chart_ids:
            raise ValueError(f"Recipe {name}: unknown chart {recipe['chart']!r}")
        if not isinstance(recipe["variant"], str) or not recipe["variant"].strip():
            raise ValueError(f"Recipe {name}: variant is required")
        if not isinstance(recipe["title"], str) or not recipe["title"].strip():
            raise ValueError(f"Recipe {name}: title is required")
        tags = recipe["tags"]
        if not isinstance(tags, list) or not tags or any(not isinstance(t, str) or not t.strip() for t in tags) or len(set(tags)) != len(tags):
            raise ValueError(f"Recipe {name}: tags must be unique nonempty strings")
        path = (ROOT / recipe["ir"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError(f"Recipe {name}: ir must reference a file inside the skill")
    return registry["recipes"]


def numeric(raw, field, row_id):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError(f"CSV row {row_id}: {field} must be a number, got {raw!r}") from None
    if not math.isfinite(value):
        raise ValueError(f"CSV row {row_id}: {field} must be finite")
    return value


def read_rows(ir, ir_path):
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        if len(set(columns)) != len(columns):
            raise ValueError("CSV: duplicate column names")
        enc = ir["encoding"]
        missing = set(enc.values()) - set(columns)
        if missing:
            raise ValueError(f"CSV {path}: missing columns {sorted(missing)}; fix encoding or CSV")
        source = list(reader)
    if not source:
        raise ValueError(f"CSV {path}: no rows")
    rows, seen, cells = [], set(), set()
    for i, raw in enumerate(source, 1):
        if None in raw or any(v is None for v in raw.values()):
            raise ValueError(f"CSV row {i}: column count does not match header")
        row_id = raw.get(enc.get("id", "id"), f"row-{i:04d}").strip()
        row = {"id": row_id, "panel": raw[enc["panel"]].strip() if "panel" in enc else "main",
               "group": raw[enc["x"]].strip(), "series": raw[enc["series"]].strip(),
               "value": numeric(raw[enc["y"]], enc["y"], row_id)}
        for key in ("id", "panel", "group", "series"):
            if not row[key]:
                raise ValueError(f"CSV row {i}: empty {key}")
        if row_id in seen:
            raise ValueError(f"CSV: duplicate row id {row_id!r}")
        seen.add(row_id)
        cell = (row["panel"], row["group"], row["series"])
        if cell in cells:
            raise ValueError(f"CSV: duplicate panel/group/series {cell}; aggregate observations first")
        cells.add(cell)
        for key in ("low", "high", "label", "capacity", "base"):
            column = enc.get(key, key)
            if key in ("capacity", "base") and key not in enc:
                continue
            if raw.get(column, "").strip():
                row[key] = raw[column] if key == "label" else numeric(raw[column], column, row_id)
            elif key in enc:
                raise ValueError(f"CSV row {row_id}: missing {column}")
        if ("low" in row) != ("high" in row):
            raise ValueError(f"CSV row {row_id}: supply both low/high interval endpoints")
        if "low" in row and not row["low"] <= row["value"] <= row["high"]:
            raise ValueError(f"CSV row {row_id}: interval must contain value")
        if "base" in row and raw.get(enc.get("capacity", "capacity"), "").strip():
            raise ValueError(f"CSV row {row_id}: base cannot be combined with capacity")
        if "capacity" in row:
            baseline = ir.get("axis", {}).get("baseline", 0)
            if "low" in row:
                raise ValueError(f"CSV row {row_id}: interval + capacity is not supported")
            if not row["capacity"] >= row["value"] >= baseline:
                raise ValueError(f"CSV row {row_id}: require capacity >= value >= baseline ({baseline})")
        rows.append(row)
    backend.validate_increment(rows, ir.get("axis", {}).get("baseline", 0),
                               "horizontal" if ir.get("layout") == "horizontal" else "vertical")
    present = list(dict.fromkeys(r["series"] for r in rows))
    order = ir.get("series_order", present)
    if not set(present).issubset(order):
        raise ValueError("series_order must contain every plotted series")
    for key in ("series_labels", "series_roles"):
        if set(ir.get(key, {})) - set(order):
            raise ValueError(f"{key}: unknown series; add it to series_order or correct the name")
    if set(ir["theme"].get("series_styles", {})) - set(order):
        raise ValueError("theme.series_styles: unknown series")
    # Sorting affects only category placement; row ids remain tied to original rows.
    panels = list(dict.fromkeys(r["panel"] for r in rows))
    groups = {p: list(dict.fromkeys(r["group"] for r in rows if r["panel"] == p)) for p in panels}
    rows.sort(key=lambda r: (panels.index(r["panel"]), groups[r["panel"]].index(r["group"]), order.index(r["series"])))
    formats = [ir.get("axis", {}).get("y_format", ".2g"), ir["labels"].get("value_format", ".2g")]
    for fmt in formats:
        try:
            format(0.5, fmt)
        except ValueError:
            raise ValueError(f"Invalid numeric format {fmt!r}") from None
        if fmt.endswith("%") and any(not 0 <= r[k] <= 1 for r in rows for k in ("value", "low", "high", "capacity", "base") if k in r):
            raise ValueError("Percentage format requires CSV values and endpoints in [0, 1]; divide percentages by 100")
    return rows, order


def contrast_on_white(rgba):
    rgb = [v * rgba[3] + 1 - rgba[3] for v in rgba[:3]]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return 1.05 / (sum(v * w for v, w in zip(linear, (.2126, .7152, .0722))) + .05)


def apply_cards(ir, config, rows, log):
    library = json.loads((ROOT / "library/cards.json").read_text(encoding="utf8"))
    if "base" in ir["encoding"]:
        params = library["encoding"]["increment"]["params"]
        config["panel_defaults"]["increment"].update(params, field="base")
        log.append(f"encoding increment -> {ir['encoding']['base']} normalized to base; value is total")
    if "capacity" in ir["encoding"]:
        params = library["encoding"]["capacity"]["params"]
        config["panel_defaults"]["capacity"].update(params, field="capacity")
        log.append(f"encoding capacity -> {ir['encoding']['capacity']} normalized to capacity")
    emphasis = ir.get("emphasis", [])
    for request in emphasis:
        if request["card"] not in library["emphasis"]:
            raise ValueError(f"Unknown emphasis card {request['card']!r}; choose focus-gray")
    if emphasis:
        if len(emphasis) != 1:
            raise ValueError("focus-gray requires exactly one focus series")
        present = {r["series"] for r in rows}
        order = config["series_order"]
        if not 2 <= len(order) <= 5:
            raise ValueError("focus-gray requires 2-5 series")
        request = emphasis[0]
        focus = request["series"]
        if focus not in present:
            raise ValueError(f"focus-gray series {focus!r} is absent from CSV")
        params = library["emphasis"]["focus-gray"]["params"]
        accent = request.get("accent", params["accent"])
        try:
            backend.matplotlib.colors.to_rgba(accent)
        except ValueError:
            raise ValueError(f"focus-gray: invalid accent {accent!r}") from None
        muted = [s for s in order if s != focus]
        colors = dict(zip(muted, params["gray_ramp"]))
        colors[focus] = accent
        for series, color in colors.items():
            # Keep all user-specified alpha and hatch fields.
            config["palette"][series].update(fill=color, edge=color, label="#20252c")
            if series != focus and contrast_on_white(backend.matplotlib.colors.to_rgba(color)) < 3:
                config["palette"][series]["edge"] = params["outline"]
        config["panel_defaults"]["bar_edge_width"] = max(.7, config["panel_defaults"]["bar_edge_width"])
        for series in muted:
            _, edge = backend.bar_colors(config["palette"][series], config["panel_defaults"])
            if contrast_on_white(edge) < 3:
                log.append(f"QA focus-gray: {series} outline contrast below 3:1 after alpha override")
        log.append(f"emphasis focus-gray -> 1 focus ({focus}), {len(muted)} muted")
    for request in ir.get("annotations", []):
        if request["card"] not in library["annotations"]:
            raise ValueError(f"Unknown annotation card {request['card']!r}; choose delta")
        if config["panel_defaults"]["orientation"] != "vertical":
            raise ValueError("delta currently requires vertical layout; remove delta or change layout")
        if request["from"] == request["to"]:
            raise ValueError("delta needs distinct from/to series")
        groups = {}
        for row in rows:
            if ("panel" not in request or row["panel"] == request["panel"]) and ("group" not in request or row["group"] == request["group"]):
                groups.setdefault((row["panel"], row["group"]), {})[row["series"]] = row
        pairs = [(key, members) for key, members in groups.items() if request["from"] in members and request["to"] in members]
        if len(pairs) != 1:
            raise ValueError(f"delta {request['from']} -> {request['to']}: expected one pair, found {len(pairs)}; specify matching group and panel")
        (panel, group), members = pairs[0]
        before, after = members[request["from"]], members[request["to"]]
        if "low" in before or "low" in after:
            raise ValueError("delta with intervals is not supported; remove delta or use data without intervals")
        params = library["annotations"]["delta"]["params"]
        gain = {key: request.get(key, params[key]) for key in ("label_format", "label_scale")}
        gain.update({"from": before["id"], "to": after["id"], "label_suffix": request.get("label_suffix", "")})
        difference = (after["value"] - before["value"]) * gain["label_scale"]
        if not math.isfinite(difference):
            raise ValueError("delta: scaled difference must be finite")
        try:
            label = format(difference, gain["label_format"]) + gain["label_suffix"]
        except ValueError:
            raise ValueError(f"delta: invalid label_format {gain['label_format']!r}") from None
        gain["label_position"] = [.5, 1 if after["value"] >= before["value"] else 0]
        config["gains"].append(gain)
        log.append(f"annotation delta -> {panel}/{group}: {request['from']} -> {request['to']} ({label})")


def translate(ir, rows, order):
    theme = ir["theme"]
    layout = ir.get("layout", "grouped")
    axis = ir.get("axis", {})
    labels = ir["labels"]
    value_format = labels.get("value_format", axis.get("y_format", ".2g"))
    config = {
        "data": "data.csv",
        "preset": {"style": theme["style"], "layout": layout, "size": ir["size"]["preset"],
                   "palette": theme["palette"], "font": theme["font"]},
        "series_order": order, "series_roles": ir.get("series_roles", {}),
        "figure": ir["output"],
        "panel_defaults": {"limits": "auto", "ticks": "auto", "baseline": axis.get("baseline", 0),
                           "tick_format": axis.get("y_format", ".2g"), "ylabel": axis.get("y_label", ""),
                           "value_labels": labels["values"], "value_format": value_format,
                           "category_mode": "group"},
        "legend_defaults": {"show": labels["legend"] == "top", "columns": "auto",
                            "labels": ir.get("series_labels", {})},
        "palette": theme.get("series_styles", {}),
    }
    if "value_size" in labels:
        config["panel_defaults"]["value_size"] = labels["value_size"]
    config = backend.resolve_config(config, rows)
    log = []
    scale = theme.get("type_scale", 1)
    for key in ("tick_size", "category_size", "label_size", "value_size"):
        config["panel_defaults"][key] *= scale
    config["legend_defaults"]["size"] *= scale
    config["gain_defaults"]["label_size"] = config["panel_defaults"]["label_size"]
    # An annotation scales with the type hierarchy, not with the number of bars.
    config["gain_defaults"].update(linewidth=1, head_length_pt=3, head_width_pt=3,
                                   tail_dx_pt=0, tip_dx_pt=0, tip_anchor="center",
                                   label_offset_pt=[0, 6])
    if scale != 1:
        for key in ("left_pt", "right_pt", "top_pt", "bottom_pt", "row_gap_pt"):
            config["layout"][key] *= scale
        log.append(f"type scale -> {scale:g}")
    if theme.get("hatch"):
        hatches = ["/", "\\", "x", ".", "+"]
        if len(order) > len(hatches):
            raise ValueError("theme.hatch supports at most 5 series")
        for key, hatch in zip(order, hatches):
            config["palette"][key].setdefault("hatch", hatch)
            config["palette"][key]["edge"] = "#20252c"
        config["panel_defaults"]["bar_edge_width"] = max(.7, config["panel_defaults"]["bar_edge_width"])
    if layout == "horizontal":
        # Size presets override layout margins; reserve room for semantic group labels.
        longest = max(len(r["group"]) for r in rows)
        config["layout"]["left_pt"] = max(config["layout"]["left_pt"], min(90, longest * 4 + 12))
        config["layout"]["right_pt"] = max(config["layout"]["right_pt"], 30 if labels["values"] else 10)
        # Horizontal bars read better without a grid; see the pastel reference.
        config["panel_defaults"]["grid"]["kind"] = "none"
    panel_count = len(config["panels"])
    if panel_count > 1:
        config["figure"]["size_pt"][1] *= panel_count
        config["layout"]["top_pt"] = max(config["layout"]["top_pt"], 42 * scale)
        config["layout"]["row_gap_pt"] = max(config["layout"]["row_gap_pt"], 48 * scale)
    series_count = len({r["series"] for r in rows})
    if "capacity" in ir["encoding"] and len({r["group"] for r in rows}) == 1:
        # A single capacity bar should not fill the whole category slot.
        config["panel_defaults"]["bar_width"] = 0.35
        config["panel_defaults"]["category_margin"] = 0.55
        log.append("capacity single group -> bar width 0.35, margin 0.55")
    if layout == "horizontal" and series_count == 1:
        # Horizontal single-series bars should sit close together vertically.
        config["panel_defaults"]["group_gap"] = 0.06
        log.append("horizontal single series -> group gap 0.06")
    if "y_max" in axis and axis["y_max"] is not None:
        upper = axis["y_max"]
        lower = axis.get("baseline", 0)
        if upper <= lower:
            raise ValueError("axis.y_max must exceed baseline")
        for row in rows:
            if min(row.get("low", row["value"]), row["value"]) < lower or max(row.get("high", row["value"]), row.get("capacity", row["value"])) > upper:
                raise ValueError("axis.y_max/baseline would clip CSV values, intervals or capacity")
        config["panel_defaults"]["limits"] = [lower, upper]
    apply_cards(ir, config, rows, log)
    if layout == "horizontal" and "capacity" in ir["encoding"]:
        style = config["panel_defaults"]
        props = backend.font(config, style["value_font"], style["value_size"])
        widths = [backend.TextToPath().get_text_width_height_descent(
            backend.capacity_text(r, style["capacity"]), props, False)[0] for r in rows]
        config["layout"]["right_pt"] = max(config["layout"]["right_pt"], max(widths) + style["value_pad"] + 8)
    width, height = config["figure"]["size_pt"]
    style = config["panel_defaults"]
    log.insert(0, f"size {ir['size']['preset']} -> {width:g} x {height:g} pt; type {style['tick_size']:g}/{style['label_size']:g}/{config['legend_defaults']['size']:g} pt")
    log.append(f"palette {theme['palette']} -> " + ", ".join(f"{s} {config['palette'][s]['fill']}" for s in order))
    axes = {}
    for panel, rect in zip(config["panels"], backend.panel_rectangles(config)):
        members = [r for r in rows if r["panel"] == panel["id"]]
        limits, ticks = backend.panel_axis(members, style, rect[3], config)
        axes[panel["id"]] = {"limits": limits, "ticks": ticks}
        log.append(f"axis {panel['id']} -> {limits}; ticks {ticks}")
        if panel_count > 1:
            config["annotations"].append({"text": panel["id"], "position_pt": [rect[0], rect[1] + rect[3] + 24 * scale],
                                           "size": style["label_size"], "font": "bold"})
    log.append("legend auto -> renderer measures columns at render time" if labels["legend"] == "top" else "legend -> hidden")
    decisions = {"claim": ir["claim"], "chart": ir["chart"], "size": ir["size"]["preset"],
                 "size_pt": [width, height], "palette": theme["palette"], "layout": layout,
                 "encoding": ["increment"] if "base" in ir["encoding"] else (["capacity"] if "capacity" in ir["encoding"] else ["grouped-bar"]),
                 "emphasis": [c["card"] for c in ir.get("emphasis", [])],
                 "annotations": [c["card"] for c in ir.get("annotations", [])],
                 "labels": labels, "axes": axes, "log": log}
    return config, decisions


def distribution_rows(ir, ir_path):
    enc = ir["encoding"]
    value_col = enc.get("value", "value")
    series_col = enc.get("series", "series")
    panel_col = enc.get("panel", "panel")
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    if not source:
        raise ValueError("Distribution CSV is empty")
    rows, seen = [], set()
    for index, raw in enumerate(source, 2):
        panel = raw.get(panel_col, "main")
        series = raw.get(series_col, "")
        if not panel or not series:
            raise ValueError(f"CSV row {index}: panel and series are required")
        value = numeric(raw.get(value_col), value_col, f"{index} ({panel}/{series})")
        key = (panel, series, raw.get(enc.get("id", "id"), str(index)))
        if key in seen:
            raise ValueError(f"CSV row {index}: duplicate observation {key}")
        seen.add(key)
        rows.append({"id": key[2], "panel": panel, "series": series, "value": value})
    return rows


def compile_distribution(ir, ir_path, output, render=False):
    output = Path(output)
    rows = distribution_rows(ir, ir_path)
    panels = list(dict.fromkeys(r["panel"] for r in rows))
    present = list(dict.fromkeys(r["series"] for r in rows))
    order = ir.get("series_order", present)
    if set(order) != set(present) or len(order) != len(present):
        raise ValueError("series_order must list every distribution series exactly once")
    if not 1 <= len(order) <= 4:
        raise ValueError("Distribution-overlap supports 1 to 4 series")
    axis = ir.get("axis", {})
    x_min, x_max = axis.get("x_min", 0.0), axis.get("x_max", 1.0)
    if not x_max > x_min:
        raise ValueError("axis.x_max must exceed axis.x_min")
    theme = ir["theme"]
    presets = json.loads((ROOT / "quantitative-plots/grouped-bar/scripts/presets.json").read_text(encoding="utf8"))
    palette_name = theme.get("palette", "blue-orange")
    palette = presets["palettes"].get(palette_name)
    if palette is None:
        raise ValueError(f"Unknown palette {palette_name!r}")
    colors = palette["colors"]
    if len(colors) < len(order):
        raise ValueError(f"Palette {palette_name!r} has {len(colors)} colors for {len(order)} series")
    color_map = dict(zip(order, colors))
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 216], "medium": [420, 234], "double": [504, 252],
               "slide": [648, 300]}[size]
    config = {
        "chart": "distribution-overlap", "panels": panels, "series_order": order,
        "series_labels": ir.get("series_labels", {}), "colors": color_map,
        "x_label": axis.get("x_label", "Value"), "y_label": axis.get("y_label", "Density"),
        "x_min": x_min, "x_max": x_max, "bins": axis.get("bins", 20),
        "title_prefix": ir.get("title_prefix", "Figure 4 | "),
        "size_pt": size_pt, "formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
        "svg_text": ir["output"].get("svg_text", True),
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "panel", "series", "value"])
        writer.writeheader()
        writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": "distribution-overlap", "size": size,
        "size_pt": size_pt, "palette": palette_name,
        "encoding": ["distribution-overlap"], "labels": ir["labels"],
        "layout": "distribution-overlap", "emphasis": [], "annotations": [],
        "axes": {"x": [x_min, x_max], "bins": config["bins"]},
        "log": [f"distribution -> {len(panels)} panel(s), {len(order)} series, "
                f"x [{x_min}, {x_max}], {config['bins']} bins",
                f"palette {palette_name} -> {', '.join(order)}"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        distribution_backend.render(config, rows, output / "figure")
    return config, decisions


def compile_2d(ir, ir_path, output, render=False):
    chart = ir["chart"]
    if chart not in ("dot-plot", "dumbbell", "line-band", "scatter"):
        raise ValueError(f"unsupported 2D chart {chart!r}")
    missing = {"x", "y", "series"} - set(ir["encoding"])
    if missing:
        raise ValueError(f"{chart} encoding requires {sorted(missing)}")
    rows, order = read_rows(ir, ir_path)
    if chart == "dumbbell" and len(order) != 2:
        raise ValueError("dumbbell requires exactly two series")
    theme = ir["theme"]
    presets = json.loads((ROOT / "quantitative-plots/grouped-bar/scripts/presets.json").read_text(encoding="utf8"))
    palette_name = theme.get("palette", "d3-orange")
    palette = presets["palettes"].get(palette_name)
    if palette is None:
        raise ValueError(f"Unknown palette {palette_name!r}")
    if len(palette["colors"]) < len(order):
        raise ValueError(f"Palette {palette_name!r} has {len(palette['colors'])} colors for {len(order)} series")
    palette_colors = palette["colors"][-len(order):]
    groups = list(dict.fromkeys(r["group"] for r in rows))
    axis = ir.get("axis", {})
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 240], "medium": [420, 260], "double": [504, 320],
               "slide": [648, 360]}[size]
    config = {
        "chart": chart,
        "groups": groups,
        "series_order": order,
        "colors": dict(zip(order, palette_colors)),
        "series_labels": ir.get("series_labels", {}),
        "x_label": axis.get("x_label", ""),
        "y_label": axis.get("y_label", ""),
        "x_min": axis.get("x_min"),
        "x_max": axis.get("x_max"),
        "reference": ir.get("reference", []),
        "stats": ir.get("stats", []),
        "overlays": ir.get("overlays", []),
        "legend": ir["labels"].get("legend", "top") == "top",
        "size_pt": size_pt,
        "formats": ir["output"]["formats"],
        "dpi": ir["output"]["dpi"],
        "svg_text": ir["output"].get("svg_text", True),
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        fields = ["id", "panel", "group", "series", "value"]
        fields += [key for key in ("low", "high", "label") if any(key in r for r in rows)]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": chart, "size": size, "size_pt": size_pt,
        "palette": palette_name, "encoding": [chart],
        "labels": ir["labels"], "layout": chart, "emphasis": [], "annotations": [],
        "axes": {"x": [axis.get("x_min"), axis.get("x_max")]},
        "log": [f"{chart} -> {len(groups)} groups, {len(order)} series"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        renderer = {"dot-plot": charts2d.render_dot, "dumbbell": charts2d.render_dumbbell,
                    "line-band": charts2d.render_line_band, "scatter": charts2d.render_scatter}[chart]
        renderer(config, rows, output / "figure")
    return config, decisions


def read_distribution_rows(ir, ir_path):
    """Long distribution rows may repeat (panel, group, series); do not deduplicate."""
    path = Path(ir_path).parent / ir["data"]
    enc = ir["encoding"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        missing = set(enc.values()) - set(columns)
        if missing:
            raise ValueError(f"CSV {path}: missing columns {sorted(missing)}; fix encoding or CSV")
        source = list(reader)
    if not source:
        raise ValueError(f"CSV {path}: no rows")
    rows = []
    for i, raw in enumerate(source, 1):
        row_id = raw.get(enc.get("id", "id"), f"row-{i:04d}").strip()
        group = raw[enc["x"]].strip()
        series = raw[enc["series"]].strip()
        if not group or not series:
            raise ValueError(f"CSV row {i}: group and series are required")
        rows.append({
            "id": row_id, "panel": raw[enc["panel"]].strip() if "panel" in enc else "main",
            "group": group, "series": series,
            "value": numeric(raw[enc["y"]], enc["y"], row_id),
        })
    present = list(dict.fromkeys(r["series"] for r in rows))
    order = ir.get("series_order", present)
    if set(order) != set(present) or len(order) != len(present):
        raise ValueError("series_order must list every distribution series exactly once")
    return rows, order


def compile_distribution_2d(ir, ir_path, output, render=False):
    chart = ir["chart"]
    if chart not in ("box", "violin", "ecdf", "kde", "ridgeline"):
        raise ValueError(f"unsupported distribution chart {chart!r}")
    missing = {"x", "y", "series"} - set(ir["encoding"])
    if missing:
        raise ValueError(f"{chart} encoding requires {sorted(missing)}")
    rows, order = read_distribution_rows(ir, ir_path)
    theme = ir["theme"]
    presets = json.loads((ROOT / "quantitative-plots/grouped-bar/scripts/presets.json").read_text(encoding="utf8"))
    palette_name = theme.get("palette", "d3-orange")
    palette = presets["palettes"].get(palette_name)
    if palette is None:
        raise ValueError(f"Unknown palette {palette_name!r}")
    if len(palette["colors"]) < len(order):
        raise ValueError(f"Palette {palette_name!r} has {len(palette['colors'])} colors for {len(order)} series")
    groups = list(dict.fromkeys(r["group"] for r in rows))
    axis = ir.get("axis", {})
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 240], "medium": [420, 260], "double": [504, 320],
               "slide": [648, 360]}[size]
    config = {
        "chart": chart, "groups": groups, "series_order": order,
        "colors": dict(zip(order, palette["colors"][-len(order):])),
        "series_labels": ir.get("series_labels", {}),
        "x_label": axis.get("x_label", ""), "y_label": axis.get("y_label", ""),
        "x_min": axis.get("x_min"), "x_max": axis.get("x_max"),
        "reference": ir.get("reference", []),
        "overlays": ir.get("overlays", []),
        "legend": ir["labels"].get("legend", "top") == "top",
        "size_pt": size_pt, "formats": ir["output"]["formats"],
        "dpi": ir["output"]["dpi"], "svg_text": ir["output"].get("svg_text", True),
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "panel", "group", "series", "value"])
        writer.writeheader()
        writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": chart, "size": size, "size_pt": size_pt,
        "palette": palette_name, "encoding": [chart], "labels": ir["labels"],
        "layout": chart, "emphasis": [], "annotations": [],
        "axes": {"x": [axis.get("x_min"), axis.get("x_max")]},
        "log": [f"{chart} -> {len(groups)} groups, {len(order)} series, {len(rows)} observations"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        renderer = {"box": charts2d.render_box, "violin": charts2d.render_violin,
                    "ecdf": charts2d.render_ecdf, "kde": charts2d.render_kde,
                    "ridgeline": charts2d.render_ridgeline}[chart]
        renderer(config, rows, output / "figure")
    return config, decisions


def read_classification_rows(ir, ir_path):
    path = Path(ir_path).parent / ir["data"]
    enc = ir["encoding"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        missing = {enc["score"], enc["label"]} - set(columns)
        if missing:
            raise ValueError(f"CSV {path}: missing columns {sorted(missing)}")
        source = list(reader)
    rows = []
    for i, raw in enumerate(source, 1):
        try:
            score = float(raw[enc["score"]])
            label = int(float(raw[enc["label"]]))
        except (TypeError, ValueError):
            raise ValueError(f"CSV row {i}: score/label must be numeric") from None
        if label not in (0, 1):
            raise ValueError(f"CSV row {i}: label must be 0 or 1")
        series = raw.get(enc.get("series", "series"), "all").strip() or "all"
        rows.append({"id": raw.get(enc.get("id", "id"), f"row-{i:04d}"),
                     "panel": "main", "series": series, "score": score, "label": label})
    present = list(dict.fromkeys(r["series"] for r in rows))
    order = ir.get("series_order", present)
    if set(order) != set(present) or len(order) != len(present):
        raise ValueError("series_order must list every classification series exactly once")
    return rows, order


def compile_heatmap(ir, ir_path, output, render=False):
    enc = ir["encoding"]
    missing = {"row", "col", "value"} - set(enc)
    if missing:
        raise ValueError(f"heatmap encoding requires {sorted(missing)}")
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    rows_order, cols_order, cells = [], [], {}
    for i, raw in enumerate(source, 1):
        row, col = raw[enc["row"]].strip(), raw[enc["col"]].strip()
        if not row or not col:
            raise ValueError(f"CSV row {i}: row and col are required")
        if row not in rows_order:
            rows_order.append(row)
        if col not in cols_order:
            cols_order.append(col)
        if (row, col) in cells:
            raise ValueError(f"CSV: duplicate heatmap cell {(row, col)}")
        cells[(row, col)] = numeric(raw[enc["value"]], enc["value"], f"{i}")
    matrix = [[cells[(row, col)] for col in cols_order] for row in rows_order]
    axis = ir.get("axis", {})
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 280], "medium": [420, 300], "double": [504, 340],
               "slide": [648, 360]}[size]
    config = {
        "chart": "heatmap", "rows": rows_order, "cols": cols_order, "matrix": matrix,
        "cell_values": ir["labels"].get("values", False),
        "colormap": ir["theme"].get("colormap", "Blues"),
        "x_label": axis.get("x_label", ""), "y_label": axis.get("y_label", ""),
        "size_pt": size_pt, "formats": ir["output"]["formats"],
        "dpi": ir["output"]["dpi"], "svg_text": ir["output"].get("svg_text", True),
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["row", "col", "value"])
        writer.writeheader()
        for row in rows_order:
            for col in cols_order:
                writer.writerow({"row": row, "col": col, "value": cells[(row, col)]})
    decisions = {
        "claim": ir["claim"], "chart": "heatmap", "size": size, "size_pt": size_pt,
        "palette": ir["theme"].get("palette", "none"), "encoding": ["heatmap"],
        "labels": ir["labels"], "layout": "heatmap", "emphasis": [], "annotations": [],
        "axes": {"rows": rows_order, "cols": cols_order},
        "log": [f"heatmap -> {len(rows_order)} x {len(cols_order)} cells"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        charts2d.render_heatmap(config, [], output / "figure")
    return config, decisions


def compile_classification(ir, ir_path, output, render=False):
    chart = ir["chart"]
    missing = {"score", "label"} - set(ir["encoding"])
    if missing:
        raise ValueError(f"{chart} encoding requires {sorted(missing)}")
    rows, order = read_classification_rows(ir, ir_path)
    theme = ir["theme"]
    presets = json.loads((ROOT / "quantitative-plots/grouped-bar/scripts/presets.json").read_text(encoding="utf8"))
    palette_name = theme.get("palette", "d3-blue")
    palette = presets["palettes"].get(palette_name)
    if palette is None:
        raise ValueError(f"Unknown palette {palette_name!r}")
    if len(palette["colors"]) < len(order):
        raise ValueError(f"Palette {palette_name!r} has {len(palette['colors'])} colors")
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 260], "medium": [420, 280], "double": [504, 320],
               "slide": [648, 360]}[size]
    axis = ir.get("axis", {})
    config = {
        "chart": chart, "series_order": order,
        "colors": dict(zip(order, palette["colors"][-len(order):])),
        "series_labels": ir.get("series_labels", {}),
        "bins": axis.get("bins", 10), "size_pt": size_pt,
        "x_label": axis.get("x_label", ""), "y_label": axis.get("y_label", ""),
        "legend": ir["labels"].get("legend", "top") == "top",
        "formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
        "svg_text": ir["output"].get("svg_text", True),
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "panel", "series", "score", "label"])
        writer.writeheader()
        writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": chart, "size": size, "size_pt": size_pt,
        "palette": palette_name, "encoding": [chart], "labels": ir["labels"],
        "layout": chart, "emphasis": [], "annotations": [],
        "axes": {"bins": config["bins"]},
        "log": [f"{chart} -> {len(rows)} observations, {len(order)} series"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        renderer = {"roc": charts2d.render_roc, "pr": charts2d.render_pr,
                    "calibration": charts2d.render_calibration, "det": charts2d.render_det}[chart]
        renderer(config, rows, output / "figure")
    return config, decisions


def compile_surface(ir, ir_path, output, render=False):
    enc = ir["encoding"]
    missing = {"x", "y", "z"} - set(enc)
    if missing:
        raise ValueError(f"surface encoding requires {sorted(missing)}")
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    cells = {}
    for i, raw in enumerate(source, 1):
        x, y = numeric(raw[enc["x"]], enc["x"], str(i)), numeric(raw[enc["y"]], enc["y"], str(i))
        z = numeric(raw[enc["z"]], enc["z"], str(i))
        if (x, y) in cells:
            raise ValueError(f"CSV: duplicate surface cell {(x, y)}")
        cells[(x, y)] = z
    xs = sorted({k[0] for k in cells})
    ys = sorted({k[1] for k in cells})
    if len(cells) != len(xs) * len(ys):
        raise ValueError("surface requires a complete x/y grid")
    X = [[x for x in xs] for _ in ys]
    Y = [[y for _ in xs] for y in ys]
    Z = [[cells[(x, y)] for x in xs] for y in ys]
    axis = ir.get("axis", {})
    size = ir["size"]["preset"]
    size_pt = {"single": [420, 260], "medium": [480, 280], "double": [560, 300],
               "slide": [680, 340]}[size]
    config = {
        "chart": "surface", "X": X, "Y": Y, "Z": Z,
        "x_label": axis.get("x_label", "x"), "y_label": axis.get("y_label", "y"),
        "z_label": axis.get("z_label", "z"), "colormap": ir["theme"].get("colormap", "viridis"),
        "size_pt": size_pt, "formats": ir["output"]["formats"],
        "dpi": ir["output"]["dpi"], "svg_text": ir["output"].get("svg_text", True),
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["x", "y", "z"])
        writer.writeheader()
        for y in ys:
            for x in xs:
                writer.writerow({"x": x, "y": y, "z": cells[(x, y)]})
    decisions = {
        "claim": ir["claim"], "chart": "surface", "size": size, "size_pt": size_pt,
        "palette": ir["theme"].get("palette", "viridis"), "encoding": ["surface"],
        "labels": ir["labels"], "layout": "surface", "emphasis": [], "annotations": [],
        "axes": {"x": xs, "y": ys}, "log": [f"surface -> {len(xs)} x {len(ys)} grid"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        charts3d.render_surface(config, [], output / "figure")
    return config, decisions


def compile_scatter3d(ir, ir_path, output, render=False):
    enc = ir["encoding"]
    missing = {"x", "y", "z", "series"} - set(enc)
    if missing:
        raise ValueError(f"scatter3d encoding requires {sorted(missing)}")
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    if not source:
        raise ValueError(f"CSV {path}: no rows")
    rows, seen = [], set()
    for i, raw in enumerate(source, 1):
        row_id = raw.get(enc.get("id", "id"), f"row-{i:04d}").strip()
        if row_id in seen:
            raise ValueError(f"CSV: duplicate row id {row_id!r}")
        seen.add(row_id)
        series = raw[enc["series"]].strip()
        if not series:
            raise ValueError(f"CSV row {row_id}: empty series")
        rows.append({"id": row_id, "series": series,
                     "x": numeric(raw[enc["x"]], enc["x"], row_id),
                     "y": numeric(raw[enc["y"]], enc["y"], row_id),
                     "z": numeric(raw[enc["z"]], enc["z"], row_id)})
    present = list(dict.fromkeys(r["series"] for r in rows))
    order = ir.get("series_order", present)
    if not set(present).issubset(order):
        raise ValueError("series_order must contain every plotted series")
    colors, _ = backend.palette_colors(ir["theme"]["palette"], order, ir.get("series_roles", {}))
    axis = ir.get("axis", {})
    view = ir.get("view", {})
    size = ir["size"]["preset"]
    size_pt = {"single": [420, 300], "medium": [480, 320], "double": [560, 340],
               "slide": [680, 380]}[size]
    config = {
        "chart": "scatter3d", "rows": rows, "series_order": order, "colors": colors,
        "series_labels": ir.get("series_labels", {}),
        "x_label": axis.get("x_label", "x"), "y_label": axis.get("y_label", "y"),
        "z_label": axis.get("z_label", "z"), "elev": view.get("elev", 24),
        "azim": view.get("azim", -55), "size_pt": size_pt,
        "formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "series", "x", "y", "z"])
        writer.writeheader()
        writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": "scatter3d", "size": size, "size_pt": size_pt,
        "palette": ir["theme"]["palette"], "encoding": ["scatter3d"],
        "labels": ir["labels"], "layout": "scatter3d", "emphasis": [], "annotations": [],
        "axes": {"x": axis.get("x_label", "x"), "y": axis.get("y_label", "y"),
                 "z": axis.get("z_label", "z")},
        "log": [f"scatter3d -> {len(rows)} points, {len(order)} series"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        charts3d.render_scatter3d(config, rows, output / "figure")
    return config, decisions


def compile_voxel(ir, ir_path, output, render=False):
    enc = ir["encoding"]
    missing = {"x", "y", "z", "value"} - set(enc)
    if missing:
        raise ValueError(f"voxel encoding requires {sorted(missing)}")
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    cells = {}
    for i, raw in enumerate(source, 1):
        x, y, z = numeric(raw[enc["x"]], enc["x"], str(i)), numeric(raw[enc["y"]], enc["y"], str(i)), numeric(raw[enc["z"]], enc["z"], str(i))
        if (x, y, z) in cells:
            raise ValueError(f"CSV: duplicate voxel {(x, y, z)}")
        cells[(x, y, z)] = numeric(raw[enc["value"]], enc["value"], str(i))
    xs = sorted({k[0] for k in cells}); ys = sorted({k[1] for k in cells}); zs = sorted({k[2] for k in cells})
    if len(cells) != len(xs) * len(ys) * len(zs):
        raise ValueError("voxel requires a complete x/y/z grid")
    rows = [{"x": x, "y": y, "z": z, "value": cells[(x, y, z)]} for z in zs for y in ys for x in xs]
    axis = ir.get("axis", {}); view = ir.get("view", {})
    size = ir["size"]["preset"]
    size_pt = {"single": [420, 300], "medium": [480, 320], "double": [560, 340],
               "slide": [680, 380]}[size]
    config = {
        "chart": "voxel", "xs": xs, "ys": ys, "zs": zs, "rows": rows,
        "threshold": ir.get("threshold", 0), "colormap": ir["theme"].get("colormap", "viridis"),
        "x_label": axis.get("x_label", "x"), "y_label": axis.get("y_label", "y"),
        "z_label": axis.get("z_label", "z"), "elev": view.get("elev", 24),
        "azim": view.get("azim", -55), "size_pt": size_pt,
        "formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["x", "y", "z", "value"])
        writer.writeheader(); writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": "voxel", "size": size, "size_pt": size_pt,
        "palette": ir["theme"].get("palette", "viridis"), "encoding": ["voxel"],
        "labels": ir["labels"], "layout": "voxel", "emphasis": [], "annotations": [],
        "axes": {"x": xs, "y": ys, "z": zs},
        "log": [f"voxel -> {len(xs)} x {len(ys)} x {len(zs)} grid"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        charts3d.render_voxel(config, rows, output / "figure")
    return config, decisions


def compile_node_link(ir, ir_path, output, render=False):
    enc = ir["encoding"]
    missing = {"source", "target"} - set(enc)
    if missing:
        raise ValueError(f"node-link encoding requires {sorted(missing)}")
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    rows, seen = [], set()
    for i, raw in enumerate(source, 1):
        s, t = raw[enc["source"]].strip(), raw[enc["target"]].strip()
        if not s or not t:
            raise ValueError(f"CSV row {i}: empty source/target")
        weight = numeric(raw[enc["weight"]], enc["weight"], str(i)) if "weight" in enc else 1.0
        if weight <= 0:
            raise ValueError(f"CSV row {i}: weight must be positive")
        key = (s, t)
        if key in seen:
            raise ValueError(f"CSV: duplicate edge {key}")
        seen.add(key)
        rows.append({"source": s, "target": t, "weight": weight})
    presets = json.loads((ROOT / "quantitative-plots/grouped-bar/scripts/presets.json").read_text(encoding="utf8"))
    palette = presets["palettes"].get(ir["theme"].get("palette", "d3-blue"))
    if palette is None:
        raise ValueError("Unknown palette")
    color = palette["colors"][-1]
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 300], "medium": [420, 320], "double": [504, 360],
               "slide": [648, 400]}[size]
    config = {
        "chart": "node-link", "rows": rows, "colors": [color], "edge_color": color,
        "node_size": 70, "size_pt": size_pt,
        "x_label": ir.get("axis", {}).get("x_label", ""),
        "y_label": ir.get("axis", {}).get("y_label", ""),
        "formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["source", "target", "weight"])
        writer.writeheader(); writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": "node-link", "size": size, "size_pt": size_pt,
        "palette": ir["theme"].get("palette", "d3-blue"), "encoding": ["node-link"],
        "labels": ir["labels"], "layout": "circular", "emphasis": [], "annotations": [],
        "axes": {}, "log": [f"node-link -> {len(rows)} edges"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        charts2d.render_node_link(config, rows, output / "figure")
    return config, decisions


def compile_flow(ir, ir_path, output, render=False):
    chart = ir["chart"]
    enc = ir["encoding"]
    path = Path(ir_path).parent / ir["data"]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        source = list(csv.DictReader(stream))
    if chart == "sankey":
        missing = {"source", "target", "value"} - set(enc)
        if missing:
            raise ValueError(f"sankey encoding requires {sorted(missing)}")
        rows = [{"source": raw[enc["source"]].strip(), "target": raw[enc["target"]].strip(),
                 "value": numeric(raw[enc["value"]], enc["value"], str(i))}
                for i, raw in enumerate(source, 1)]
    else:
        missing = {"label", "value"} - set(enc)
        if missing:
            raise ValueError(f"treemap encoding requires {sorted(missing)}")
        rows = [{"label": raw[enc["label"]].strip(), "value": numeric(raw[enc["value"]], enc["value"], str(i))}
                for i, raw in enumerate(source, 1)]
    presets = json.loads((ROOT / "quantitative-plots/grouped-bar/scripts/presets.json").read_text(encoding="utf8"))
    palette = presets["palettes"].get(ir["theme"].get("palette", "d3-blue"))
    if palette is None:
        raise ValueError("Unknown palette")
    size = ir["size"]["preset"]
    size_pt = {"single": [360, 280], "medium": [420, 300], "double": [504, 340],
               "slide": [648, 380]}[size]
    config = {
        "chart": chart, "rows": rows, "colors": palette["colors"],
        "size_pt": size_pt, "formats": ir["output"]["formats"],
        "dpi": ir["output"]["dpi"],
        "figure": {"formats": ir["output"]["formats"], "dpi": ir["output"]["dpi"],
                   "svg_text": ir["output"].get("svg_text", True)},
    }
    output.mkdir(parents=True, exist_ok=True)
    fields = ["source", "target", "value"] if chart == "sankey" else ["label", "value"]
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    decisions = {
        "claim": ir["claim"], "chart": chart, "size": size, "size_pt": size_pt,
        "palette": ir["theme"].get("palette", "d3-blue"), "encoding": [chart],
        "labels": ir["labels"], "layout": chart, "emphasis": [], "annotations": [],
        "axes": {}, "log": [f"{chart} -> {len(rows)} items"],
    }
    (output / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    (output / "decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        renderer = charts2d.render_sankey if chart == "sankey" else charts2d.render_treemap
        renderer(config, rows, output / "figure")
    return config, decisions


def compile_ir(ir_path, output, render=False):
    ir_path, output = Path(ir_path), Path(output)
    ir = load_ir(ir_path)
    if ir["chart"] == "distribution-overlap":
        return compile_distribution(ir, ir_path, output, render)
    if ir["chart"] in ("box", "violin", "ecdf", "kde", "ridgeline"):
        return compile_distribution_2d(ir, ir_path, output, render)
    if ir["chart"] == "heatmap":
        return compile_heatmap(ir, ir_path, output, render)
    if ir["chart"] in ("roc", "pr", "calibration", "det"):
        return compile_classification(ir, ir_path, output, render)
    if ir["chart"] == "surface":
        return compile_surface(ir, ir_path, output, render)
    if ir["chart"] == "scatter3d":
        return compile_scatter3d(ir, ir_path, output, render)
    if ir["chart"] == "voxel":
        return compile_voxel(ir, ir_path, output, render)
    if ir["chart"] == "node-link":
        return compile_node_link(ir, ir_path, output, render)
    if ir["chart"] in ("sankey", "treemap"):
        return compile_flow(ir, ir_path, output, render)
    if ir["chart"] in ("dot-plot", "dumbbell", "line-band", "scatter"):
        return compile_2d(ir, ir_path, output, render)
    missing = {"x", "y", "series"} - set(ir["encoding"])
    if missing:
        raise ValueError(f"grouped-bar encoding requires {sorted(missing)}")
    rows, order = read_rows(ir, ir_path)
    config, decisions = translate(ir, rows, order)
    output.mkdir(parents=True, exist_ok=True)
    fields = ["id", "panel", "group", "series", "value"]
    fields += [key for key in ("low", "high", "capacity", "base", "label") if any(key in r for r in rows)]
    with (output / "data.csv").open("w", encoding="utf8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    for name, content in (("config.json", config), ("decisions.json", decisions)):
        (output / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if render:
        backend.render(config, rows, output / "figure")
    return config, decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--render", action="store_true")
    mode.add_argument("--dry-run", action="store_true", help="Write config, normalized data and decisions only")
    args = parser.parse_args()
    try:
        _, decisions = compile_ir(args.ir, args.output, render=args.render)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print("\n".join(decisions["log"]))


if __name__ == "__main__":
    main()
