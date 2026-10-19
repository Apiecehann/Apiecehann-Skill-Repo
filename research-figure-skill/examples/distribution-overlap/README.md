# Distribution overlap

两个 panel 的 **重叠直方图**：同一坐标下比较 Correct / Incorrect 两个分布，y 用 density，x 用 probability。

## 什么时候用

- 比较两组连续值分布（confidence、误差、score）；
- 需要看 overlap，而不是只看均值；
- 两个 panel 是同一指标的不同 setting（CE / LS）。

## 不要用

- 只有均值/方差（用带 error bar 的柱或点）；
- 两组样本量差很多且不做 density 归一化；
- 需要精确读每个 bin 的计数（用表格）。

## 数据

`data.csv` 是 **MOCK / layout test**：

```text
id,panel,series,value
ce-correct-0,CE Confidence,correct,0.81
...
```

`panel` 是 two-panel facet；`series` 是 correct / incorrect；`value` 在 [0, 1]。

## 生成

```bash
python examples/distribution-overlap/render.py
```

输出 `figure.png` / `figure.pdf` / `figure.svg`。白底、双向 grid、图例在右上、两个 panel 共用 x 语义。

## 设计规则

- 两组颜色要有明确语义：Correct vs Incorrect，不用同色相浅深；
- 半透明重叠，但不要低到看不见；
- grid 用 hairline，不能压过 hist；
- 图例不要框，放在 panel 内右上；
- 标题写成 `Figure 4 | CE Confidence`，不要重复 "Confidence Confidence"。
