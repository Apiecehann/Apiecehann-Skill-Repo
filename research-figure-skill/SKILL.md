---
name: research-figure-skill
description: 用小型 figure IR 和 pattern cards 生成科研柱形图，支持分组、横向百分比、单栏/双栏、聚焦、容量柱和差值标注。适用于从数据/claim 生成新图或复刻已有示例。散点、折线、示意图尚未实现。
---

# Research Figure Skill

默认入口是 [figure IR](spec/README.md)：写 `figure.ir.json`（约 10 个字段）→ `spec/compile.py` → `render.py`。不要把 164 个 renderer 参数直接交给模型；`render.py` 的 config 只作为低层精调或复刻入口。

- 先写清 claim：一句话说明图要证明什么；再定 `encoding`（x / y / series / panel）。
- 先定最终物理宽度：`size.preset` 为 `single`（3.3 in）或 `double`（7 in）。尺寸决定字号、留白、柱宽和自动图例。
- 主题从 `theme.style / palette / font` 选；用 [`library/cards.json`](library/cards.json) 的 `focus-gray`、`capacity`、`delta`，不要用形容词直接描述风格。
- `focus-gray` 只允许一个 focus、2–5 个系列；`capacity` 只用于总量有真实含义的数据；`delta` 只用于纵向、无区间的一对柱。
- 未写 `axis.y_max` 时轴按数据自动取 nice 范围；比例图显式设 `y_format=".0%"`，不要继承参考图的截断轴。
- SVG 默认保留可编辑文字；投稿需要轮廓时加 `--svg-paths`。需要低层覆盖时用 `--set` 标量或 `--set-file`；`--list-presets` / `--defaults` / `--resolved-config` 用于检查预设和最终配置。
- 六个复刻配置带 `frozen_config`，只能用 `--palette` / `--font`，不能用 `--style` / `--layout` / `--size` 重排；需要新图请从 `examples/templates/` 起。
- 新增卡或 recipe 的流程见 [library/README.md](library/README.md)：必须有 `when`、`avoid`、`operations`、`qa`，并加回归测试和 catalog 条目。
- 数据变化后柱高、区间、标签和 delta 应共同变化；没有区间时不生成区间；不要把来源图的实验数值当成用户的结果。
- 旧示例的默认 `tokens.mode=readable` 使用可读标签；仅需忠实呈现原论文 token 时改为 `raw`。不要把可见的 `\n` 当作编码错误。
- 比较实际成图与选定示例；检查标签、颜色、间距、字号和导出。字体回退或仍有视觉差异时如实说明，不把测试通过当成像素一致。
- 精确字体用 `--font-dir` 提供本机可合法使用的字体。Graphik 不随仓库分发；公开运行使用系统字体及随附的 B612 Mono。

结构与叙事图暂见 [schematic-diagrams](schematic-diagrams/README.md)，当前没有对应渲染器。
