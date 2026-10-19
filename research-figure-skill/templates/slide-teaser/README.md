# Slide teaser

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：在演示中突出一个方法在三个模拟基准上的结果。

编码：分组柱。强调：focus-gray 单一重点。

组合理由：双栏物理宽度配合放大字号与留白，重点用紫色；不堆叠数值和差值标注。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir templates/slide-teaser/figure.ir.json --output output/slide-teaser --render
```
