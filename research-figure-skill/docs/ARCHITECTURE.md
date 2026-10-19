# Architecture

## 1. Runtime vs reference

```text
SKILL.md + spec/ + library/ + templates/   ← runtime
reference/ + docs/                         ← human-facing, not imported
quantitative-plots/grouped-bar/            ← legacy low-level renderer
```

`reference/` 不参与编译；`templates/` 是可复制输入。

## 2. 数据流

```text
claim + data.csv
  → figure.ir.json
  → validate(schema)
  → compile(chart)
  → renderer
  → figure.png / pdf / svg
```

IR 是稳定接口；renderer 参数只做低层精调。

## 3. 四层

| 层 | 负责 | 例子 |
|---|---|---|
| chart | 几何形状 | bar / line / scatter / box / heatmap / surface |
| stat | 统计量 | mean±std、CI、quantile、KDE、regression、ellipse |
| reference | 参照值 | SOTA、threshold、baseline、target |
| annotation | 图内说明 | delta、bracket、callout、operating point |

## 4. 目录

```text
spec/
├─ figure.schema.json
├─ compile.py          # load / validate / dispatch
├─ distribution.py     # two-panel histogram
├─ charts2d.py         # compatibility shim
├─ charts3d.py         # compatibility shim
└─ renderers/
   ├─ charts2d.py      # 2D renderers
   └─ charts3d.py      # 3D renderers

library/
├─ charts.json         # chart family capability matrix
├─ recipes.json        # recipe index
├─ overlays.json       # overlay capabilities
├─ cards.json          # style cards
└─ palettes-120.json
```

`spec/compile.py` 目前保留各 chart 的 compiler；renderer 已独立到 `spec/renderers/`。下一步可继续拆 compiler，不影响 IR。

## 5. Compiler 分派

| group | charts |
|---|---|
| grouped-bar | `grouped-bar` |
| distribution | `box` `violin` `ecdf` `kde` `ridgeline` `distribution-overlap` |
| relationship | `dot-plot` `dumbbell` `line-band` `scatter` |
| matrix | `heatmap` `clustermap` `calendar-heatmap` |
| classification | `roc` `pr` `calibration` `det` |
| 3D | `surface` `scatter3d` `voxel` `bar3d` `mesh3d` `quiver3d` |
| hierarchy / flow | `sunburst` `icicle` `treemap` `node-link` `sankey` `chord` `alluvial` |
| comparison | `radar` `waffle` |
| layout | `broken-axis` `inset-zoom` |

## 6. 新增 chart

1. 在 `library/charts.json` 加 family 和 requires。
2. 在 `spec/figure.schema.json` 加 `chart` enum 和 encoding 字段。
3. 写 compiler + renderer。
4. 加 `templates/<chart>/`。
5. 加 recipe、eval case、catalog 条目。
6. 加 chart-review。
7. 跑全量 tests。

## 7. 测试

```bash
python -m pytest quantitative-plots/grouped-bar/scripts spec -q
```

测试覆盖：

- schema / invalid IR
- 每个 template 编译
- 每个 template 渲染
- recipes / catalog 数量
- eval cases

## 8. 参考资产

- `reference/axis-review/`：全局轴
- `reference/chart-review/`：每个 chart 的轴覆盖
- `reference/catalog/`：contact sheet 与成品

这些不是运行时依赖，可以单独发布或裁剪。
