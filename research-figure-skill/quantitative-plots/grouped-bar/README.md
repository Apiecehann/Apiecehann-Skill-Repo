# 柱形图家族

同一个 [`scripts/render.py`](scripts/render.py) 读取配置和 CSV。渲染器没有按论文名称判断的绘图分支，也不把参考截图嵌入输出。

目录沿用 `grouped-bar`；横向单系列柱图和前后对比图复用同一个入口。六个示例只有配置与数据的区别，没有每图独立的 Python 文件。

| 示例 | 布局 | 输入与成图 |
|---|---|---|
| `cue-comparison` | 左侧主图 + 右侧四个小面板；两组模型、三种条件；双层标签 | [配置](examples/cue-comparison/config.json) · [数据](examples/cue-comparison/data.csv) · [PDF](examples/cue-comparison/figure.pdf) |
| `data-edit` | 三行比较；彩色 token 标签、数值、区间和小型图标 | [配置](examples/data-edit/config.json) · [数据](examples/data-edit/data.csv) · [PDF](examples/data-edit/figure.pdf) |
| `teaser-strip` | 不等数量分组；下方分组线及条件说明 | [配置](examples/teaser-strip/config.json) · [数据](examples/teaser-strip/data.csv) · [PDF](examples/teaser-strip/figure.pdf) |
| `zero-shot-execution` | 九个任务、五个系列、组中心标签、顶部图例及幻灯片标题 | [配置](examples/zero-shot-execution/config.json) · [数据](examples/zero-shot-execution/data.csv) · [PDF](examples/zero-shot-execution/figure.pdf) |
| `affordance-distribution` | 横向排列、每类单独配色、粗体百分比标签 | [配置](examples/affordance-distribution/config.json) · [数据](examples/affordance-distribution/data.csv) · [PDF](examples/affordance-distribution/figure.pdf) |
| `planning-gains` | 非零基线、虚线网格、前后对比及自动计算的增益箭头 | [配置](examples/planning-gains/config.json) · [数据](examples/planning-gains/data.csv) · [PDF](examples/planning-gains/figure.pdf) |

![九任务多系列对比](examples/zero-shot-execution/figure.png)

<img src="examples/affordance-distribution/figure.png" width="340" alt="横向百分比分布">

![前后对比与增益箭头](examples/planning-gains/figure.png)

![主图与四个小面板](examples/cue-comparison/figure.png)

![不等数量分组](examples/teaser-strip/figure.png)

<img src="examples/data-edit/figure.png" width="380" alt="三行数值图复刻">

## 运行和替换数据

以下命令从 `research-figure-skill` 目录运行。输入路径由配置文件所在目录解析，`--data`、`--output` 则由当前工作目录解析。

```bash
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/cue-comparison/config.json \
  --data my-data.csv --output output/my-figure
```

CSV 必需列：`id,panel,group,series,value`。

- `id` 唯一；`panel` 对应配置中的面板；`group` 用于自动排列；`series` 对应颜色角色。
- 可选 `low,high` 是已经计算好的区间两端，二者同时提供或同时省略。不自动推断区间的统计含义。
- 可选 `label` 是类别文字；可选 `x` 是明确的类别位置，同一面板内全部提供或全部省略。示例为了复刻采用显式位置；使用自动组间距时移除整列 `x`。
- 柱高或区间超出轴范围时默认报错。参考 `data-edit` 的一个接近零的区间下界为负，原图裁切在零处；仅该面板显式设置 `allow_interval_clipping=true`，完整端点仍保留在 CSV 中。

## 样式参数

```bash
python quantitative-plots/grouped-bar/scripts/render.py --defaults
```

| 参数组 | 内容 |
|---|---|
| `figure` | 画布尺寸（pt）、背景、分辨率、导出格式、SVG 文字或字形路径 |
| `fonts` | 正文、强调、等宽字体的文件名、系统回退字体及字重 |
| `palette` | 每个条件的填充色、描边色、数值标签色、可选纹理 |
| `panel_defaults` | 方向、坐标范围与刻度、字号、轴线、柱宽、组间距、区间、数值格式 |
| `grid` | 点状／线状／无网格、间距、颜色、透明度及最大点数 |
| `tokens` | 标签字号、间距、底色、描边、圆角、阴影与位置 |
| `layout` | 自动面板网格的列数、四边留白及行列间距 |
| `panels` | 每个面板的位置、局部样式及 token 标签映射 |
| `annotations` / `bands` | 标题、混合字重轴标签和下方分组线 |
| `legend_defaults` / `panels[].legend` | 图例顺序、文字、字体、列数、位置、边框及色块尺寸 |
| `gain_defaults` / `gains` | 关联行 ID、箭头曲率与端点偏移、箭头尺寸、差值格式与文字位置 |

配置优先级：默认值 → 全局配置 → 面板局部配置。`--set` 按 JSON 类型覆盖指定字段：

```bash
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/cue-comparison/config.json \
  --set 'palette.cue={"fill":"#86c6ba","edge":"#347f71","label":"#1f574e"}' \
  --set 'panel_defaults.value_size=9' \
  --output output/teal
```

所有尺寸按物理点数定义（72 pt = 1 inch）。示例的 `rect_pt` 固定面板位置；省略它时采用自动网格。`figure.size_pt` 改变画布，固定的 `rect_pt` 不会自动拉伸。字体、标签和数据都可以改，但新增面板、长文字或大幅改动组数后仍应查看成图。

`grid`、`tokens` 位于 `panel_defaults` 或各面板的 `style` 内。Token 可以直接写字符串，也可以用 `runs` 指定混合字体；精细复刻时用 `padding_em`、`height_em`、`baseline_em` 控制标签框，以字号为单位缩放，文字变长时框宽会随之增长。`palette` 的可选 `token_fill`、`token_edge` 控制标签色；迁移配色时同时修改，或删除它们以恢复自动取色。

无分组线的普通配置同时支持横向和纵向柱。`bands`、行绑定的图标和增益箭头目前按纵向版式定义，直接改为横向会明确报错。

## 分组、横向与增益箭头

- `category_mode=group` 将刻度放在每组柱的中心；组名来自 CSV 的 `group`，也可用面板的 `group_labels` 改显示名称。`legend.show=true` 开启图例，顺序必须包含该面板全部系列，避免漏标。
- `orientation=horizontal` 切换横向；`invert_categories=true` 使 CSV 第一行出现在最上方。`value_format=".1%"` 将比例显示为一位小数的百分比。`tick_font`、`category_font`、`label_font`、`value_font` 分别选择字体角色。
- `baseline` 是柱的起点，`limits` 是数轴范围，两者独立且必须一致。`planning-gains` 从 70 起绘；`zero-shot-execution` 按原图延伸至 −0.03，使零值仍能在零刻度下方辨认，CSV 中的零值不变。
- `grid.linestyle` 接受 `"--"` 等字符串或 `[偏移, [实线长度, 间隔长度]]`；`spines` 控制显示哪些轴线。

每个 `gains` 项指定 `from`、`to` 两个 CSV 行 ID。箭头连接这两根柱的当前数值，文字自动计算 `to.value - from.value`；`label_scale=100` 可将比例差换成百分点。颜色默认取目标柱的调色板，可单独覆盖。曲线控制点 `control1`、`control2` 是起点到终点的相对位置，端点与标签的偏移以 pt 为单位。

## 原始 token 与可读标签

最初三张参考的 `.\n\n` 是论文中的字面 token 标记。默认 `panel_defaults.tokens.mode="readable"` 使用各面板 `readable_tokens` 中的 `Okay`、`Alright`、`Chicken` 等文字，避免把转义符号带入通用示例。

需要恢复原始论文标签时，保留同一配置并运行：

```bash
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/cue-comparison/config.json \
  --set 'panel_defaults.tokens.mode="raw"' --output output/raw-tokens
```

`raw` 使用原来的 `tokens` 和精细位置参数；两种模式均不改变数值。

## 精确字体与复刻范围

最初三套参考使用 Graphik Light / Regular 和 B612 Mono。公开运行无需商业字体；默认回退到系统无衬线字体和随附 B612 Mono，文字外观会与参考不同。新增示例使用 DejaVu Sans Mono、Liberation Sans / Arial、Liberation Serif / Times New Roman；字体列表按本机可用情况匹配。已有合法可用字体时：

```bash
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/cue-comparison/config.json \
  --font-dir /path/to/licensed-fonts --output output/matched
```

目录内使用 `Graphik-Light.ttf`、`Graphik-Regular.ttf`、`B612Mono-Regular.ttf`，或在 `fonts` 中改文件名。终端会列出发生回退的字体角色。

仓库成图使用原图字体轮廓做过本地对照；字体文件和原始参考 PDF 不随仓库分发。柱、区间及面板几何来自矢量源图；token 标签阴影、字体栅格化等细节仍需视觉核对，不宣称逐像素完全相同。来源详见 [NOTICE](../../NOTICE.md)。

最初三套覆盖小红书笔记 `6ace9bd9000000001a02bf03`：第 2 页的 Figure 2、第 1 页 Figure 5 的中间数值列、第 3 页的 teaser 柱图。Figure 5 两侧的文字与分支属于结构叙事图，不包含在这里；第 4 页教程没有新增独立柱图。新增三套对应用户提供的 SAGA 与 VLA-OS 图片，来源和数值读取方式见各配置的 `provenance` 与 [NOTICE](../../NOTICE.md)。
