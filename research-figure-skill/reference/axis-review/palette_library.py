"""Generate a 120-swatch palette library for the colour-pairing review."""
from __future__ import annotations

import colorsys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "library" / "palettes-120.json"

BASES = {
    "orange": "#E07A2F",
    "blue": "#2F80C9",
    "teal": "#1F9E89",
    "green": "#3A9D5D",
    "rose": "#C44E6E",
    "violet": "#7C5CBF",
    "amber": "#D9A441",
    "brown": "#A9714B",
    "slate": "#64748B",
    "plum": "#8B5E83",
}

CURATED = {
    "tol-bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44"],
    "tol-muted": ["#88CCEE", "#44AA99", "#999933", "#CC6677"],
    "tableau10": ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2"],
    "npg": ["#4DBBD5", "#00A087", "#3C5488", "#E64B35"],
    "set1": ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3"],
    "set2": ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3"],
    "set3": ["#8DD3C7", "#FFFFB3", "#BEBADA", "#FB8072"],
    "paired": ["#A6CEE3", "#1F78B4", "#B2DF8A", "#33A02C"],
    "pastel1": ["#FBB4AE", "#B3CDE3", "#CCEBC5", "#DECBE4"],
    "dark2": ["#1B9E77", "#D95F02", "#7570B3", "#E7298A"],
    "grayscale": ["#D9D9D9", "#A6A6A6", "#737373", "#404040"],
    "blues": ["#DEEBF7", "#9ECAE1", "#4292C6", "#08519C"],
    "greens": ["#E5F5E0", "#A1D99B", "#41AB5D", "#006D2C"],
    "oranges": ["#FEE6CE", "#FDAE6B", "#E6550D", "#A63603"],
    "reds": ["#FEE0D2", "#FC9272", "#DE2D26", "#A50F15"],
    "purples": ["#EFEDF5", "#BCBDDC", "#807DBA", "#54278F"],
    "viridis": ["#440154", "#31688E", "#35B779", "#FDE725"],
    "cividis": ["#00224E", "#123570", "#5C7C8A", "#FEE838"],
    "earth": ["#8C6D46", "#C2A878", "#5B7B5A", "#D9C3A5"],
    "ocean": ["#0B3954", "#087E8B", "#4EA5A5", "#C7E8E3"],
}


def hex_to_hls(color: str):
    value = color.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def hls_to_hex(h, l, s):
    h = h % 1.0
    l = min(.94, max(.08, l))
    s = min(1.0, max(.05, s))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#" + "".join(f"{round(c * 255):02x}" for c in (r, g, b))


def family(base, name):
    h, l, s = hex_to_hls(base)
    if name == "tints":
        return [hls_to_hex(h, l + d, max(.08, s - .12)) for d in (.20, .12, .04)]
    if name == "shades":
        return [hls_to_hex(h, l - d, min(1, s + .04)) for d in (.04, .14, .24)]
    if name == "analogous":
        return [hls_to_hex(h + d, l, s) for d in (-.09, -.045, .045)]
    if name == "complement":
        return [hls_to_hex(h + .5, l + d, s - .05) for d in (.18, .04, -.12)]
    if name == "split":
        return [hls_to_hex(h + d, l, s) for d in (.42, .5, .58)]
    if name == "triadic":
        return [hls_to_hex(h + d, l, s) for d in (.333, .5, .666)]
    if name == "tetradic":
        return [hls_to_hex(h + d, l, s) for d in (.25, .5, .75)]
    if name == "muted":
        return [hls_to_hex(h, l + d, s * .45) for d in (.12, 0, -.12)]
    if name == "pastel":
        return [hls_to_hex(h, .80 + d, s * .42) for d in (0, .06, -.04)]
    if name == "dark":
        return [hls_to_hex(h, .28 + d, min(1, s * 1.08)) for d in (.06, 0, -.06)]
    raise ValueError(name)


def main():
    items = []
    families = ["tints", "shades", "analogous", "complement", "split",
                "triadic", "tetradic", "muted", "pastel", "dark"]
    for base_name, base in BASES.items():
        for fam in families:
            colors = family(base, fam) + [base]
            items.append({"id": f"{base_name}-{fam}", "base": base_name,
                          "family": fam, "colors": colors})
    for name, colors in CURATED.items():
        items.append({"id": name, "base": "curated", "family": "curated", "colors": colors})
    OUT.write_text(json.dumps({"version": 1, "count": len(items), "palettes": items},
                              ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("wrote", OUT, len(items))


if __name__ == "__main__":
    main()
