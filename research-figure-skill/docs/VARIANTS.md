# Chart families and variants

> 修正：per-chart variant 不是拍脑袋几个变量，而是按轴覆盖。完整规则见 [AXIS_COVERAGE.md](AXIS_COVERAGE.md)。这份文档保留早期的 variant 命名草案。

两层结构：

1. **chart family**：几何形状（grouped-bar、dot-plot、dumbbell、box、surface…）
2. **variant**：同一 family 下的具体使用情况（focus、paired、capacity、ablation…）

`library/recipes.json` 现在每条 recipe 都有 `chart` 和 `variant`；`examples/catalog/index.json` 的 `groups` 按 chart 分组。

## Grouped Bar（已有 9 个 variant）

| variant | recipe |
|---|---|
| focus | `ours-vs-baselines` |
| paired | `before-after` |
| capacity | `capacity-88-of-96` |
| ablation | `ablation-legend` |
| horizontal | `horizontal-percent` |
| print | `print-bw` |
| multi-panel | `multi-panel` |
| slide | `slide-teaser` |
| increment | `increment-base` |

这 9 个不是 9 种 chart，全部是 **grouped-bar** 的 variant。

## P0 其他 chart 的 variant 目标

当前每个新 chart 只有 1 个示例；目标至少 2 个，重要 chart 3 个。

| chart | 已有一个 | 需要补 |
|---|---|---|
| dot-plot | 4-series | 2-series、带 errorbar、ablation 版 |
| dumbbell | 3-group | 2-group、5-group、无 delta label |
| line-band | training | scaling、4-series、单 series |
| scatter | trend+ellipse | embedding（无 trend）、density、单 series |
| distribution-overlap | 2-panel | 1-panel、3-series |
| kde | overlap | 3-series、单 series |
| box | raw+significance | raw-only、3-series、no bracket |
| violin | raw | 3-series、split、no raw |
| ecdf | latency | error ECDF、单 series |
| heatmap | layer-task | confusion、attention、similarity |
| roc | single | 3-series、operating point |
| pr | single | 3-series、baseline |
| calibration | single | 3-series、不同 bins |
| surface | loss landscape | hyperparam、不同 colormap/view |

## 命名

```text
<chart>-<variant>
例如：
dot-plot-errorbar
dumbbell-five-group
line-band-scaling
scatter-embedding
```

## 目录

```text
examples/templates/<chart>-<variant>/
├─ data.csv
├─ figure.ir.json
└─ README.md
```

## 验收

每个 variant 必须有：

- 独立 `data.csv`
- 独立 IR
- README
- recipe（带 `chart` / `variant`）
- eval case
- catalog 条目

同一 chart 的 variant 不是“换尺寸/换色”，而是覆盖不同使用情况（series 数、annotation、layout、数据形状）。
