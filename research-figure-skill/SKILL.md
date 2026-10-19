---
name: research-figure-skill
description: 用小型 figure IR 生成科研图。覆盖 comparison、distribution、relationship、matrix、classification、3D、hierarchy、flow、layout 与 bar variants；适用于从数据/claim 生成新图，或从模板复刻已有示例。
---

# Research Figure Skill

入口只有一条：

```text
claim + data → figure.ir.json → spec/compile.py → figure.png / pdf / svg
```

不要把 renderer 参数直接交给模型。IR 是稳定接口，renderer config 只做低层精调。

## 1. 选 chart family

先读 [`library/charts.json`](library/charts.json)，按数据形状选 `chart`：

- comparison：`grouped-bar` / `horizontal-bar` / `dot-plot` / `dumbbell` / `radar` / `waffle`
- distribution：`distribution-overlap` / `kde` / `box` / `violin` / `ecdf` / `ridgeline`
- relationship：`line-band` / `scatter`
- matrix：`heatmap` / `clustermap` / `calendar-heatmap`
- classification：`roc` / `pr` / `calibration` / `det`
- 3D：`surface` / `scatter3d` / `voxel` / `bar3d` / `mesh3d` / `quiver3d`
- hierarchy / flow：`sunburst` / `icicle` / `treemap` / `node-link` / `sankey` / `chord` / `alluvial`
- layout：`broken-axis` / `inset-zoom`

bar variants（`lollipop` / `bullet` / `waterfall` / `funnel` / `bump`）不是独立 chart family，归在 `grouped-bar` 下。

## 2. 从模板复制

```text
templates/<recipe>/
├─ data.csv
├─ figure.ir.json
└─ README.md
```

先复制这三个文件，再改数据和 claim。不要从空白 IR 开始。

配方索引见 [`library/recipes.json`](library/recipes.json)。

## 3. 写 IR

最少字段：

```json
{
  "claim": "一句话说明图要证明什么",
  "chart": "grouped-bar",
  "data": "data.csv",
  "encoding": {"x": "group", "y": "value", "series": "series"},
  "size": {"preset": "single"},
  "theme": {"style": "paper-clean", "palette": "d3-blue", "font": "sans"},
  "labels": {"values": true, "legend": "top"},
  "output": {"formats": ["png", "pdf", "svg"], "dpi": 300, "svg_text": true}
}
```

约束：

- `claim` 必须先写。
- `size` 先定最终物理宽度：`single` 3.3 in / `double` 7 in。
- `theme` 只从预设选，不要写颜色 hex。
- 比例图显式设 `axis.y_format = ".0%"`，不要继承截断轴。
- 同一 cell 的重复观测用 `encoding.replicate`，bar 才会叠 raw points。

## 4. 渲染

```bash
python spec/compile.py --ir templates/grouped-bar-raw/figure.ir.json \
  --output /tmp/figure --render
```

先 `--dry-run` 检查 config，再 `--render`。

## 5. 检查

- 白底，无意外灰底。
- 网格方向跟数值轴一致；不默认全 2D。
- 颜色结构是 focus / paired / categorical 之一，不是随手多色。
- 标注有语义：reference / errorbar / bracket / delta / trend / ellipse。
- 标签不压数据；SVG 中文字仍可编辑。
- 数据变化后柱高、区间、标签、delta 一起变化。
- 不把参考图的实验数值当成用户结果。

## 6. 参考库

`reference/` 是给人看的，不是运行时依赖：

- [`reference/axis-review`](reference/axis-review)：全局轴参考
- [`reference/chart-review`](reference/chart-review)：每个 chart 的轴覆盖
- [`reference/catalog`](reference/catalog)：成品 contact sheet

已知实现边界见 [`docs/COVERAGE.md`](docs/COVERAGE.md)。

## 7. 目录

```text
SKILL.md          ← 本文件
spec/             ← IR / compiler / renderer
library/          ← charts / recipes / overlays / palettes
templates/        ← 可复制 IR + data
reference/        ← 参考图，不参与运行
evals/            ← 语义到 IR 的回归用例
tests/            ← 渲染与 schema 测试
docs/             ← 架构与覆盖
```

