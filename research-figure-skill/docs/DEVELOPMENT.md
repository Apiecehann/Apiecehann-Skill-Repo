# Quantitative plots: P0 development plan

这份文档定义 `research-figure-skill/quantitative-plots/` 从 2 个 chart family 扩到 P0 集合的架构、范围、顺序和验收标准。目标不是“多画几种图”，而是让 **chart / stat / reference / annotation** 四层可以组合，而不是每种图重写一套额外覆盖。

## 1. 当前状态

已有正式 chart family：

| id | 来源 | 状态 |
|---|---|---|
| `grouped-bar` | `quantitative-plots/grouped-bar/scripts/render.py` | 稳定，182 tests |
| `distribution-overlap` | `spec/distribution.py` | 稳定，已进 IR / recipes / evals |

已有模板：10 个 recipes。
已有轴表：17 张，属于 reference，不是 chart family。

## 2. 四层模型

| 层 | 负责 | 例子 | 是否 chart-specific |
|---|---|---|---|
| **chart** | 几何形状 | bar / line / scatter / box / heatmap / surface | 是 |
| **stat** | 从原始数据算统计量 | mean±std、CI、quantile、KDE、regression、ellipse | 否，声明兼容 chart |
| **reference** | 跟某个值比 | SOTA、threshold、baseline、target、mean line | 否，任何 chart 都可 |
| **annotation** | 在图上说明 | delta arrow、bracket、callout、region、operating point | 部分 |

现有 `delta` 属于 annotation；`increment`/`capacity` 属于 encoding；`distribution-overlap` 属于 chart。

## 3. P0 范围

P0 的目标是覆盖 CS 论文里最常见的 80% 图，不是覆盖所有 Matplotlib/Pandas 图型。

### 3.1 P0 charts

| # | chart id | family | 主要用途 | 状态 |
|---|---|---|---|---|
| 1 | `grouped-bar` | comparison | benchmark 多方法 | 已有 |
| 2 | `horizontal-bar` | comparison | 类别名长/排序 | 用 grouped-bar + layout |
| 3 | `dot-plot` | comparison | 多方法多任务，比 grouped 更干净 | 已实现 |
| 4 | `dumbbell` | comparison | 两个方法/两个版本差值 | 已实现 |
| 5 | `line-band` | time | 多种子均值 ± std/CI | 已实现 |
| 6 | `scatter` | relationship | latency/throughput、score/size、embedding | 已实现 |
| 7 | `histogram` | distribution | confidence/误差分布 | 已有 `distribution-overlap` |
| 8 | `kde` | distribution | 平滑分布/overlap | 已实现 |
| 9 | `box` | distribution | 多种子/多任务分布 | 已实现 |
| 10 | `violin` | distribution | 分布形状 + 中位数 | 已实现 |
| 11 | `ecdf` | distribution | latency CDF、误差累积 | 已实现 |
| 12 | `heatmap` | matrix | 超参网格、层间指标 | 已实现 |
| 13 | `roc` | classification | 二分类阈值表现 | 已实现 |
| 14 | `pr` | classification | 不平衡分类 | 已实现 |
| 15 | `calibration` | classification | 置信度校准 | 已实现 |
| 16 | `surface` | 3D | loss landscape、超参响应面 | 待做 |

说明：

- `horizontal-bar` 不新建 renderer；它是 `grouped-bar` 的 `layout=horizontal`，但要有独立 template 和 eval。
- `histogram` / `kde` / `box` / `violin` / `ecdf` 共用一个 `distribution` renderer，用 `mode` 区分；IR 仍用独立 chart id，避免作者记 mode。
- 3D 只做 `surface` 一个 P0；`scatter3d`/`voxel` 放 P1，避免 3D 过度扩张。

### 3.2 P0 overlays

| overlay | 层 | requires | 支持 chart | 优先级 |
|---|---|---|---|---|
| `errorbar` | stat | `x,y,yerr` 或 raw replicates | bar、line、dot、scatter(binned) | P0 |
| `ci-band` | stat | `x,y,replicate` 或 `low,high` | line、scatter、roc、pr | P0 |
| `raw-points` | stat | `x,y` + group | bar、box、violin、dot | P0 |
| `reference-line` | reference | `axis,value` | 所有 2D chart | P0 |
| `trend` | stat | `x,y` + optional group | scatter、line | P0 |
| `confidence-ellipse` | stat | `x,y` + series | scatter | P0 |
| `significance-bracket` | annotation | two groups + optional p | bar、dot、box、violin | P0 |
| `delta` | annotation | two rows/values | bar、dot、dumbbell | 已有 |
| `operating-point` | annotation | `x,y,label` | roc、pr、calibration | P1 |

### 3.3 P0 明确不做

- network / hierarchy（node-link、Sankey、treemap）
- 3D bar、3D pie
- volume / voxel / isosurface
- ridge、QQ、DET、bootstrap、Andrews、RadViz
- 交互式图（P0 只出 PNG/PDF/SVG）

## 4. IR 设计

### 4.1 通用结构

```json
{
  "chart": "scatter",
  "data": "data.csv",
  "encoding": {
    "x": "latency",
    "y": "throughput",
    "series": "method",
    "replicate": "seed"
  },
  "stats": [
    {"kind": "trend", "method": "linear", "ci": 0.95},
    {"kind": "confidence-ellipse", "level": 0.95}
  ],
  "reference": [
    {"kind": "line", "axis": "y", "value": 100, "label": "SLO"}
  ],
  "annotations": [
    {"kind": "callout", "x": 20, "y": 80, "text": "ours"}
  ],
  "theme": {"style": "paper-clean", "palette": "d3-orange", "font": "sans"},
  "size": {"preset": "single"},
  "output": {"formats": ["png", "pdf", "svg"], "dpi": 300, "svg_text": true}
}
```

### 4.2 数据约定

| 场景 | 列 |
|---|---|
| 原始重复观测 | `x,y,series,replicate`，stat 负责聚合 |
| 预计算区间 | `x,y,low,high`，不再跑 stat |
| 分类 | `score,label[,series]` |
| 分布 | `panel,series,value` |
| 矩阵 | `row,col,value` |
| 3D surface | `x,y,z` 或 grid + z |

原则：

- 不把 `mean/std` 写进 CSV 再让 chart 猜；要么给 raw `replicate`，要么显式 `low/high`。
- 百分比统一 `[0,1]`，格式由 `axis.y_format` 控制。
- 缺列时编译器报“哪个 overlay 缺哪个列”，不静默 fallback。

### 4.3 兼容性校验

`library/charts.json` 每个 chart 声明：

```json
{
  "id": "scatter",
  "supports": ["ci-band", "raw-points", "reference-line", "trend", "confidence-ellipse"],
  "requires": ["x", "y"]
}
```

`library/overlays.json` 每个 overlay 声明：

```json
{
  "id": "confidence-ellipse",
  "layer": "stat",
  "requires": ["x", "y", "series"],
  "params": {"level": 0.95},
  "supports": ["scatter"],
  "avoid": ["少于 3 个点", "类别轴"]
}
```

编译器流程：

1. chart 是否注册；
2. `supports` 是否包含 overlay；
3. `requires` 是否被 encoding/CSV 满足；
4. 参数范围；
5. 交给 renderer。

## 5. 目录结构

新图统一进 family 目录；`grouped-bar` 暂不搬，避免破坏 182 tests。

```text
quantitative-plots/
├─ grouped-bar/                 # 已有，保留
├─ comparison/
│  ├─ dot-plot/
│  └─ dumbbell/
├─ time/
│  └─ line-band/
├─ relationship/
│  └─ scatter/
├─ distribution/
│  ├─ histogram/
│  ├─ kde/
│  ├─ box/
│  ├─ violin/
│  └─ ecdf/
├─ matrix/
│  └─ heatmap/
├─ classification/
│  ├─ roc/
│  ├─ pr/
│  └─ calibration/
├─ three-d/
│  └─ surface/
└─ primitives/
   ├─ io.py
   ├─ style.py
   ├─ axes.py
   ├─ stats.py
   ├─ marks.py
   └─ overlays.py
```

每个 chart 目录：

```text
<chart>/
├─ scripts/render.py
├─ figure.ir.json
├─ data.csv
└─ README.md
```

## 6. Compiler / renderer

`spec/compile.py` 保留 grouped-bar 与 distribution 分支；新增通用 2D 分支：

```python
CHART_RENDERERS = {
  "dot-plot": charts2d.render_dot,
  "dumbbell": charts2d.render_dumbbell,
  "line-band": charts2d.render_line_band,
  "scatter": charts2d.render_scatter,
  "histogram": charts2d.render_distribution,
  "kde": charts2d.render_distribution,
  "box": charts2d.render_distribution,
  "violin": charts2d.render_distribution,
  "ecdf": charts2d.render_distribution,
  "heatmap": charts2d.render_heatmap,
  "roc": charts2d.render_roc,
  "pr": charts2d.render_pr,
  "calibration": charts2d.render_calibration,
  "surface": charts3d.render_surface,
}
```

P0 先做一个 `spec/charts2d.py`，避免 12 个文件重复实现 style/grid/legend；chart-specific 代码只保留 mark 和 stat 组合。3D 单独 `spec/charts3d.py`。

## 7. 里程碑

### M0: 文档 + primitives（本文件）

- 写本文件；
- 建 `quantitative-plots/primitives/`；
- 建 `library/charts.json`、`library/overlays.json` 草案；
- 不新增图。

### M1: comparison

- `dot-plot` + `dumbbell`；
- overlays：`errorbar`、`raw-points`、`reference-line`、`significance-bracket`、`delta`；
- 每个 chart 一个 template + README + eval。

### M2: time / relationship

- `line-band` + `scatter`；
- overlays：`ci-band`、`trend`、`confidence-ellipse`、`reference-line`；
- scatter 的 mean/std 只允许 binned 版本，不默认加。

### M3: distribution

- `histogram`/`kde`/`box`/`violin`/`ecdf`；
- overlays：`raw-points`、`reference-line`、mean/median line；
- 复用 `distribution` renderer。

### M4: matrix / classification

- `heatmap`、`roc`、`pr`、`calibration`；
- overlays：`reference-line`、`ci-band`、`operating-point`；
- 分类数据 `score,label`。

### M5: 3D surface

- `surface` only；
- 2D contour projection + 3D surface；
- 不做 3D bar/pie/voxel。

### M6: catalog / evals / docs

- 所有 P0 进 `library/recipes.json` 或 `library/charts.json`；
- catalog 至少 20 个条目；
- evals 每个 chart 至少 1 个 case；
- 全量测试、REPORT、README。

## 8. 验收标准

每个 chart 必须满足：

- `spec/compile.py --ir ... --render` 产出 PNG/PDF/SVG；
- SVG 文字可编辑（`<text>`，不是全 outline）；
- 无 matplotlib warning；
- `catalog.py` 能生成缩略图；
- 至少 1 个 eval case；
- README 写清 when/avoid/data/IR；
- 至少 1 个 overlay 组合测试；
- 不修改冻结 replicas 和已有 182 tests。

P0 整体验收：

- 16 个 chart id（含已有）；
- 8 个 overlay；
- 20+ catalog 条目；
- 200+ tests；
- `distribution-overlap`、`increment`、`curved delta` 保持可用。

## 9. 3D 规则

- 只有 z 是真实测量变量才用 3D：loss、depth、occupancy、trajectory；
- 类别比较不用 3D；
- 静态论文图优先 2D contour/heatmap + 一个 3D inset；
- 3D surface 必须有 colorbar 和 2D 投影；
- 不做 3D bar、3D pie、3D 类别散点。

## 10. 工作方式

- 按里程碑垂直切片，不先写 16 个 renderer 再补 overlay；
- 每个 overlay 只写一次，用 2–3 个 chart 做兼容性测试；
- 每完成一个里程碑：测试绿、commit、push、服务器同步；
- 失败时先修兼容性，不加新图。
