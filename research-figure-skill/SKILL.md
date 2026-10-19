---
name: research-figure-skill
description: 用统一脚本和示例配置生成科研柱形图，支持多系列分组、多面板、横向百分比、区间和增益箭头。适用于替换数据、调整字体配色或复刻已有示例。机制与叙事图尚未实现。
---

# Research Figure Skill

从 [柱形图目录](quantitative-plots/grouped-bar/README.md) 进入。日常绘图优先读 [风格、配色与字体索引](quantitative-plots/grouped-bar/examples/style-guide/README.md)，选 `preset.style / layout / size / palette`，复用精简配置与同一个 `scripts/render.py`；需要精确复刻时选择六个原始示例。

- 先定最终物理宽度：单栏用 `--size single`（3.3 in），双栏用 `--size double`（7 in）；尺寸预设同时给字号、留白、柱宽和自动图例，显式配置仍优先。
- 先保留已选示例的版式，替换数据字段；样式调整通过配置、`--set` 标量或 `--set-file`（嵌套值）实现。六个复刻配置带 `frozen_config`，只能用 `--palette`/`--font`，不能用 `--style`/`--layout`/`--size` 重排。
- 新增版式时扩展共用组件及参数，示例目录只放数据、配置和成图，不新增按图片命名的绘图脚本。
- `--list-presets` 列出预设，`--defaults` 列出底层参数，`--resolved-config` 展开实际配置。SVG 默认保留可编辑文字，投稿需要轮廓时加 `--svg-paths`。明确配置覆盖预设，面板局部值覆盖全局值。原始配置默认保留显式 `x`；预设布局使用 `position_mode=auto` 重新分组，可明确改回 `data`。
- 未写 `limits`/`ticks` 时轴按数据自动取 nice 范围和刻度，区间端点也纳入；比例图显式设 `tick_format`，不要从风格预设继承截断坐标轴。
- 从数据的比较关系选择色板；保存 `series_order`，语义色板必须提供 `series_roles`。透明度分别调整填充与描边；误差棒、数值和刻度不要随填充一起变淡。
- 需要重新选科研配色时，先看 [100 候选研究与短名单](quantitative-plots/grouped-bar/examples/palette-study/README.md)。按推荐系列数、是否叠加纹理和实际背景选择；自动色差排名不是美观排名，短名单也不代表用户已认可。改变背景、透明度或系列数后重做相关诊断。
- 数据变化后，柱高、区间和数值标签应共同变化；`gains` 绑定两根柱的行 ID，差值文字与箭头位置随数据更新。没有区间时不生成区间；不要把来源图的实验数值当成用户的结果。
- 旧示例的默认 `tokens.mode=readable` 使用可读标签。仅需忠实呈现原论文 token 时改为 `raw`；不要将可见的 `\n` 当作文件编码错误处理。
- 示例的原始图片保存在仓库外；仓库只保留脚本、输入数据、配置、生成图和必要的素材许可。使用来源说明定位参考，不下载参考图来充当脚本输出。
- 比较实际成图与选定示例；检查全部数据、标签、颜色、间距和导出。字体回退或仍有视觉差异时如实说明，不把功能测试通过当成像素一致。
- 需要精确匹配原字体时使用 `--font-dir` 提供本机可合法使用的字体。Graphik 不随仓库分发。公开运行默认使用系统字体及随附的 B612 Mono。

结构与叙事图暂见 [schematic-diagrams](schematic-diagrams/README.md)，当前没有对应渲染器。
