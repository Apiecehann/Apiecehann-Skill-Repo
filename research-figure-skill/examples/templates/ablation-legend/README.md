# Ablation with legend

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：比较五个模拟消融设置在三个任务上的得分。

编码：分组柱。强调：平级比较，不设置重点系列。

组合理由：五系列使用平级配色与顶部完整图例，双栏给图例与任务标签足够空间。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir examples/templates/ablation-legend/figure.ir.json --output output/ablation-legend --render
```
