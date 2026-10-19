# Dot plot

多方法多任务对比的 dot plot：每个 group 一行，每个 series 一个点；比 grouped bar 更干净，适合 3–5 个 series。

## 什么时候用

- benchmark × method；
- 类别名较长；
- 想弱化柱子的面积，强调点的位置；
- 有 `low/high` 时可以带水平 error bar。

## 不要用

- 需要强调“总量/组成”（用 bar/stacked）；
- 只有一个 series（用 lollipop 或 bar）。

## 数据

`data.csv` 为 **MOCK / layout test**：`group, series, value`，可选 `low, high`。

## IR

```json
"chart": "dot-plot",
"encoding": {"x": "group", "y": "value", "series": "series"}
```

## 生成

```bash
python spec/compile.py \
  --ir templates/dot-plot/figure.ir.json \
  --output /tmp/dot-plot --render
```
