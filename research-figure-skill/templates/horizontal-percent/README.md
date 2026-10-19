# Horizontal percentages

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：比较四个模拟类别的成功比例。

编码：横向分组柱。强调：平级比较，不设置重点系列。

组合理由：类别横向排列便于阅读；输入保持 0–1 比例，柱尾数值与坐标轴统一百分比。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir templates/horizontal-percent/figure.ir.json --output output/horizontal-percent --render
```
