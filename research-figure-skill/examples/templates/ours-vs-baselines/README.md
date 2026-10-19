# Ours vs baselines

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：在三个模拟基准中突出本文方法，并标注 Bench B 相对 Method 1 的提升。

编码：分组柱。强调：focus-gray 单一重点。

组合理由：中性基线与紫色重点表达主次；差值以百分点表示；单栏取消柱上数字，避免与箭头争抢空间。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir examples/templates/ours-vs-baselines/figure.ir.json --output output/ours-vs-baselines --render
```
