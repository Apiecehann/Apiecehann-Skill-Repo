# Research Figure Skill

用一个绘图入口和可调整配置保存已经实现的科研图样式。当前先实现数值分析图中的分组柱状图；每个示例包含输入数据、版式参数及脚本生成的 PNG/PDF/SVG。

| 类型 | 入口 | 状态 |
|---|---|---|
| 数值分析图 | [柱形图家族](quantitative-plots/grouped-bar/README.md) | 一个渲染器；六套原始示例（12 面板、102 柱），另有风格预设与对照页 |
| 结构与叙事图 | [Schematic diagrams](schematic-diagrams/README.md) | 预留，尚未实现 |

![分组柱状图示例](quantitative-plots/grouped-bar/examples/cue-comparison/figure.png)

在本目录运行，Python 3.10 或以上：

```bash
python -m pip install -r requirements.txt
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/style-guide/config.json \
  --size single --style soft-outline --palette tol-muted --output output/my-figure
```

输出 `output/my-figure.png`、`.pdf`、`.svg`。日常使用只需选择风格、布局、尺寸和配色；需要精调时展开底层参数。`--size single` / `double` 分别对应 3.3 in 单栏和 7 in 双栏；未写轴范围时按数据自动取 nice limits，SVG 默认保留可编辑文字（投稿用 `--svg-paths`）。查看 [配置共性、配色与字体索引](quantitative-plots/grouped-bar/examples/style-guide/README.md) 和 [五页成图对照 PDF](quantitative-plots/grouped-bar/examples/style-guide/catalog.pdf)。原始复刻所用的 Graphik 商业字体不随仓库提供；精确字体入口仍为 `--font-dir`，详见图型 README。

重新选配色时看 [100 个候选研究与 10 组短名单](quantitative-plots/grouped-bar/examples/palette-study/README.md)：包含普通柱图、下层纹理、色觉模拟和灰度对照，以及可供 Illustrator 检查的 SVG / PDF 色卡。短名单标注适用系列数与限制，尚未替换现有预设。

图件生成依赖脚本、配置、CSV 和随附的开放字体，不需要访问小红书或原始参考图片。来源与数值恢复方式记录在各示例配置的 `provenance` 中。示例数据用于图件复刻，不代表使用者的实验结果。

新增示例覆盖五系列任务比较、横向百分比和带增益箭头的前后对照。旧示例默认显示 `Okay`、`Alright`、`Chicken` 等可读标签；原始换行 token 写法可以通过配置恢复。

```text
quantitative-plots/grouped-bar/
├── scripts/       # render.py、预设、catalog.py、palette_audit.py、测试及开放字体
└── examples/      # 六个原始示例、style-guide、palette-study
```

运行行为检查：

```bash
python -m pip install pytest
python -m pytest quantitative-plots/grouped-bar/scripts -q
```

代码沿用仓库 Apache-2.0 许可；参考设计、示例来源和字体许可见 [NOTICE.md](NOTICE.md)。
