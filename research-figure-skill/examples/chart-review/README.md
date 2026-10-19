# Chart axis review

`axis-review/` 是全局参考表；`chart-review/<chart>/` 是单个图的轴覆盖。

## 已完成

- `dot-plot/`：11 张轴图，74 个 panel
- `dumbbell/`：6 张轴图，50 个 panel
- `line-band/`：6 张轴图，51 个 panel
- `scatter/`：6 张轴图，51 个 panel
- `distribution-overlap/`：6 张，50
- `kde/`：6 张，49
- `box/`：6 张，53
- `violin/`：6 张，53
- `ecdf/`：6 张，50
- `heatmap/`：5 张，48
- `roc/`：6 张，50
- `pr/`：6 张，50
- `calibration/`：6 张，51
- `scatter3d/`：5 张，47
- `voxel/`：5 张，47
- `ridgeline/`：6 张，49
- `det/`：6 张，50
- `node-link/`：5 张，43
- `sankey/`：5 张，45
- `treemap/`：5 张，45
- `radar/`：6 张，48
- `bar3d/`：5 张，47
- `mesh3d/`：5 张，47
- `quiver3d/`：5 张，47
- `sunburst/`：5 张，45
- `icicle/`：5 张，45

P2 已开始：`radar`、`bar3d`、`mesh3d`、`quiver3d`、`sunburst`、`icicle` 已完成；其余 P2 图继续按批推进。

Batch 1 = dumbbell / line-band / scatter。Batch 2 = distribution-overlap / kde / box / violin / ecdf。Batch 3 = heatmap / roc / pr / calibration。两 series 的图不做 `categorical`，heatmap 不做 color structure，所以不是每张都 11 张。

## 结构

```text
examples/chart-review/<chart>/
├─ 00-color-structure.png
├─ 01-baseline-color.png
├─ 02-accent.png
├─ 03-paired.png
├─ 04-categorical.png
├─ 05-grid.png
├─ 06-style.png
├─ 07-type.png
├─ 08-annotation.png
├─ 09-size.png
├─ 10-<chart-specific>.png
└─ index.json
```

不是每张都固定 11 张：不适用的轴删掉，图自己的轴补上。

## 生成方式

不为每个图手写一份 500 行脚本。用：

```text
examples/chart-review/
├─ _shared/review.py       ← sheet 排版、字体、panel 标签
├─ _shared/adapters.py     ← chart 的 data / panel 函数
└─ <chart>/render.py       ← 只声明轴和 panel 参数
```

每个 chart adapter 只负责：

1. 读数据；
2. 给定 panel 参数，返回一张 matplotlib figure；
3. 声明自己有哪些轴。

## P0 批次

### Batch 1：comparison / time / relationship

- `dumbbell`
- `line-band`
- `scatter`

### Batch 2：distribution

- `distribution-overlap`
- `kde`
- `box`
- `violin`
- `ecdf`

### Batch 3：matrix / classification

- `heatmap`
- `roc`
- `pr`
- `calibration`

### Batch 4：3D

- `surface`

## 每 chart 的轴

| chart | 轴 |
|---|---|
| dumbbell | color / style / type / annotation / grid / size / series-pair |
| line-band | color / style / type / annotation / grid / size / series-count / uncertainty |
| scatter | color / style / type / annotation / grid / size / trend / ellipse / density |
| distribution-overlap | color / style / type / annotation / grid / size / panel-count |
| kde | color / style / type / annotation / grid / size / series-count |
| box | color / style / type / annotation / grid / size / raw-points / significance |
| violin | color / style / type / annotation / grid / size / raw-points / split |
| ecdf | color / style / type / annotation / grid / size / series-count |
| heatmap | style / type / annotation / size / colormap / cell-labels / colorbar |
| roc | color / style / type / annotation / grid / size / operating-point |
| pr | color / style / type / annotation / grid / size / operating-point |
| calibration | color / style / type / annotation / grid / size / bins |
| surface | style / type / size / view / contour / colorbar |

## 规则

- style / type 各 15 个；不展开 15×15。
- 颜色结构 4–6 个；不重复 120 色卡。
- 每个 panel 只改一个轴。
- 全局 style/type/色板表只做一次；per-chart sheet 只取该图需要的。
