# Two-panel comparison

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：在两个模拟环境中保持相同系列顺序与配色。

编码：分组柱。强调：focus-gray 单一重点。

组合理由：两个面板纵向排列以保持单栏宽度；字号与语义配色保持一致，面板标题标明环境。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir templates/multi-panel/figure.ir.json --output output/multi-panel --render
```
