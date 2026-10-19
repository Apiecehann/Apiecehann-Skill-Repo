# Axis coverage per chart

这份文档修正“每个 chart 只做几个 variant”的做法。

原则：**每个 chart 按轴覆盖，而不是拍脑袋挑几个变量**。

用户优先级修正（2026-10-19，第二版）：

- 颜色结构：重要，必做。
- 风格 / 字体：各 **15 个**，每个 chart 各一张 sheet；不展开 15×15。
- 标注：保留。
- 网格：**加回来，必做**。
- 每 chart 目标：约 **60–90 个 panel**（dot-plot 是 11 张轴图 / 75 panel），不是 5 个，也不是 150 个。
- **允许新增 chart-specific 轴**；删掉不适用的轴后，要补上这个图真正需要的轴。

## 1. 先分两类轴

### 全局轴（不按 chart 重复做）

这些轴对所有 chart 都适用，已经有独立 reference 表：

- `style`：全局 **15 个**
- `type`：全局 **15 个**
- `accent` / `categorical` / `paired` / `color_pairing`：全局色板
- `grid`：全局网格策略
- `size`：4 个物理尺寸
- `panel_gap` / `bar_spacing`：布局级

它们不进入每个 chart 的全量列表；每个 chart 用完整 15 个 style/type，不展开 15×15。

### 每 chart 轴（需要按 chart 覆盖）

每个 chart 选**适用的**轴，至少每个选项出现一次：

1. **color structure**：focus-neutral / focus-tints / paired / two-hue / focus-multi / multi-hue
2. **grid**：none / hairline / dashed / full 2D
3. **annotation**：reference / errorbar / bracket / delta / trend / ellipse / operating point
4. **layout**：vertical / horizontal / paired / multi-panel（只选适用的）
5. **size**：single / medium / double / slide（选 2–3 个代表）
6. **style/type contrast**：完整 15 个 style、15 个 type，各一张 sheet

### Chart-specific 轴（新增）

删掉不适用的轴后，要补上这个图真正需要的轴。它们不是“额外装饰”，而是该图的语义维度：

| chart | 新增轴 |
|---|---|
| scatter | `trend`（趋势）、`confidence-ellipse`（置信椭圆）、`density`（密度） |
| box | `raw-points`（原始点）、`significance-bracket`（显著性括号） |
| violin | `raw-points`、`split`（分组半小提琴） |
| line-band | `uncertainty`（CI/分位带）、`trend` |
| heatmap | `cell-labels`、`colorbar`、`clustering` |
| roc / pr | `operating-point`、`auc-label`、`baseline` |
| calibration | `bin-count`、`reliability-band` |
| surface | `view-angle`、`contour-projection`、`colorbar` |
| grouped-bar | `capacity`、`increment`、`delta`、`significance-bracket` |

这些轴进入 `reference/chart-review/<chart>/` 的 sheet，不写进全局 `axes.json` 的 13 轴。

## 2. 覆盖规则

- 每个 chart 先有一个 **canonical**。
- 每个适用轴的每个选项**至少出现一次**。
- 关键交互只做 1–2 个，不做全笛卡尔积。
- 每个 panel 只改一个轴；组合 panel 单独标注。
- 全局轴由 `axis-review` 负责，不在每个 chart sheet 里重复。

## 3. 每 chart 目标

> grid 已加回；每 chart 目标 **12–18 panels**，style/type 各取 6–8 个代表。下表是早期估算，按新目标会略增。

| chart | color | grid | annotation | layout | size | style/type | 目标 panels |
|---|---|---|---|---|---|---|---|
| grouped-bar | 3 | 3 | 4 | 2 | 2 | 2 | 14 |
| dot-plot | 3 | 3 | 3 | 1 | 2 | 2 | 12 |
| dumbbell | 2 | 2 | 2 | 1 | 2 | 1 | 9 |
| line-band | 2 | 2 | 3 | 1 | 2 | 2 | 11 |
| scatter | 3 | 2 | 4 | 1 | 2 | 2 | 13 |
| distribution-overlap | 2 | 2 | 2 | 1 | 2 | 2 | 10 |
| kde | 2 | 2 | 2 | 1 | 2 | 1 | 9 |
| box | 3 | 2 | 3 | 1 | 2 | 2 | 12 |
| violin | 3 | 2 | 3 | 1 | 2 | 1 | 11 |
| ecdf | 2 | 2 | 2 | 1 | 2 | 1 | 9 |
| heatmap | 2 | 1 | 2 | 1 | 2 | 2 | 9 |
| roc | 2 | 2 | 3 | 1 | 2 | 1 | 10 |
| pr | 2 | 2 | 2 | 1 | 2 | 1 | 9 |
| calibration | 2 | 2 | 2 | 1 | 2 | 1 | 9 |
| surface | 1 | 1 | 1 | 1 | 2 | 2 | 7 |
| **合计** | | | | | | | **~154 panels** |

## 4. 输出

每个 chart 一张 contact sheet：

```text
examples/chart-variants/
├─ grouped-bar.png
├─ dot-plot.png
├─ dumbbell.png
├─ line-band.png
├─ scatter.png
├─ distribution-overlap.png
├─ kde.png
├─ box.png
├─ violin.png
├─ ecdf.png
├─ heatmap.png
├─ roc.png
├─ pr.png
├─ calibration.png
└─ surface.png
```

每张 sheet 的 panel 标签写清轴和选项：

```text
canonical
color / focus-tints
color / focus-multi
grid / none
grid / dashed
annotation / reference
annotation / errorbar
layout / horizontal
size / double
style / bold-slide
```

## 5. 与 recipes 的关系

- `library/recipes.json` 保留 canonical + 关键 variant（目前 23 个）。
- `examples/chart-variants/` 是**覆盖表**，不是 recipe registry。
- 覆盖表里的 panel 可以直接用 chart renderer + config 生成，不进 catalog。
- 只有当某个 axis panel 值得作为独立 recipe 时，才 promote 到 `recipes.json`。

## 6. 第一批

先做：

1. `grouped-bar.png`
2. `dot-plot.png`
3. `dumbbell.png`
4. `line-band.png`
5. `scatter.png`

每个 10–14 panels，确认覆盖表的密度和可读性，再批量做 distribution / matrix / classification / surface。

## 7. 验收

- 每个 chart 的每个适用轴，至少有一个 panel。
- 每个 panel 的差异能在图上直接看出来。
- 不出现“只改尺寸/只改颜色”的假 variant。
- 全局轴不重复进每个 chart sheet。
- 总 panel 数 ~150，不是 16 × 全组合的几千。
