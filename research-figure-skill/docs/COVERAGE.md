# Coverage

当前：**40 charts / 48 recipes / 52 eval cases / 259 tests**。

## 1. Chart families

| family | charts |
|---|---|
| comparison | `grouped-bar` `horizontal-bar` `dot-plot` `dumbbell` `radar` `waffle` |
| distribution | `distribution-overlap` `kde` `box` `violin` `ecdf` `ridgeline` |
| relationship | `line-band` `scatter` |
| matrix | `heatmap` `clustermap` `calendar-heatmap` |
| classification | `roc` `pr` `calibration` `det` |
| 3D | `surface` `scatter3d` `voxel` `bar3d` `mesh3d` `quiver3d` |
| hierarchy / flow | `sunburst` `icicle` `treemap` `node-link` `sankey` `chord` `alluvial` |
| layout | `broken-axis` `inset-zoom` |

## 2. Bar variants

这些不是 chart family，归在 `grouped-bar` / `horizontal-bar`：

- `lollipop`
- `bullet`
- `waterfall`
- `funnel`
- `bump`

参考图：`reference/chart-review/bar-variants/`。

## 3. 轴优先级

用户确认：

- 颜色结构：必做。
- style / type：各 15 个。
- annotation：保留。
- grid：保留；数值在 y 轴时横线，横向图（dot / dumbbell）用竖线。
- color pairing / 120 色卡：不进 per-chart。

每 chart 的 review 结构：

```text
reference/chart-review/<chart>/
├─ 00-color*
├─ 01-style      15
├─ 02-type       15
├─ 03-annotation
├─ 04-grid
├─ 05-size
└─ index.json
```

按图适用性裁剪；不是每张都 11 张。

## 4. 全局轴 reference

```text
reference/axis-review/
├─ 00-color-structure
├─ 01-baseline-color
├─ 02-baseline-mark
├─ 03-baseline-matrix
├─ 04-accent
├─ 05-paired
├─ 06-categorical
├─ 07-grid
├─ 08-style
├─ 09-type
├─ 10-layout
├─ 11-size
├─ 12-annotation
├─ 13-panel-gap
├─ 14-bar-spacing
├─ 15-color-pairing
└─ 16-palette-library
```

## 5. 已知实现边界

- `chord`：curved edge chord，不是 ribbon-filled chord。
- `alluvial`：复用 sankey 的 layered flow，不是独立 alluvial engine。
- `clustermap`：按行列总量排序，没有 dendrogram。
- `broken-axis` / `inset-zoom`：基础布局，没有复杂连接线。
- `bar-variants`：只有 reference review，没有独立 IR/recipe。
- `grouped-bar` 旧 renderer 仍在 `quantitative-plots/grouped-bar/`，作为兼容入口。

这些是边界，不是隐藏缺陷。

## 6. 验收

```bash
python spec/compile.py --ir templates/radar/figure.ir.json \
  --output /tmp/radar --render
python -m pytest quantitative-plots/grouped-bar/scripts spec -q
```
