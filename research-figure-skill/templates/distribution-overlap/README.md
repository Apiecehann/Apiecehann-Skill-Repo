# Distribution overlap

Two-panel overlapping histogram: compare two continuous distributions (Correct / Incorrect) under the same x metric, with density on y.

## When

- compare confidence / error / score distributions;
- overlap matters, not only mean;
- two panels are the same metric under different settings (CE / LS).

## Avoid

- only mean and variance are needed (use bars/points with error bars);
- unequal sample sizes without density normalization;
- exact bin counts are required (use a table).

## Data

`data.csv` is **MOCK / layout test**:

```text
id,panel,series,value
ce-correct-0,CE Confidence,correct,0.81
...
```

`panel` is the facet, `series` is correct / incorrect, `value` is in [0, 1].

## IR

```json
"chart": "distribution-overlap",
"encoding": {"value": "value", "series": "series", "panel": "panel"},
"axis": {"x_label": "...", "y_label": "Density", "x_min": 0, "x_max": 1, "bins": 20}
```

## Generate

```bash
python spec/compile.py \
  --ir templates/distribution-overlap/figure.ir.json \
  --output /tmp/distribution-overlap --render
```

Output `figure.png` / `figure.pdf` / `figure.svg`.

## Rules

- two semantic colors: Correct vs Incorrect, not same-hue light/dark;
- semi-transparent overlap but still visible;
- hairline grid on both axes;
- legend without frame, inside upper right;
- title `Figure 4 | CE Confidence`, no duplicated "Confidence".
