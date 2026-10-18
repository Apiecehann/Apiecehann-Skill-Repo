# Research Figure Skill

用一个绘图入口和可调整配置保存已经实现的科研图样式。当前先实现数值分析图中的分组柱状图；每个示例包含输入数据、版式参数及脚本生成的 PNG/PDF/SVG。

| 类型 | 入口 | 状态 |
|---|---|---|
| 数值分析图 | [Grouped bar](quantitative-plots/grouped-bar/README.md) | 三套参考布局，共 9 个面板、45 根柱 |
| 结构与叙事图 | [Schematic diagrams](schematic-diagrams/README.md) | 预留，尚未实现 |

![分组柱状图示例](quantitative-plots/grouped-bar/examples/cue-comparison/figure.png)

在本目录运行，Python 3.10 或以上：

```bash
python -m pip install -r requirements.txt
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/cue-comparison/config.json \
  --output output/cue-comparison
```

输出 `output/cue-comparison.png`、`.pdf`、`.svg`。原图采用的 Graphik 商业字体不随仓库提供；默认字体回退会改变文字外观。需要匹配参考排版时，使用 `--font-dir /path/to/licensed-fonts`，详见图型 README。

图件生成依赖脚本、配置、CSV 和随附的开放字体，不需要访问小红书或原始参考图片。来源与数值恢复方式记录在各示例配置的 `provenance` 中。示例数据用于图件复刻，不代表使用者的实验结果。

```text
quantitative-plots/grouped-bar/
├── scripts/       # 统一渲染器、测试、开放字体及许可
└── examples/      # 每个例子的配置、CSV 和生成图
```

运行行为检查：

```bash
python -m pip install pytest
python -m pytest quantitative-plots/grouped-bar/scripts/test_render.py -q
```

代码沿用仓库 Apache-2.0 许可；参考设计、示例来源和字体许可见 [NOTICE.md](NOTICE.md)。
