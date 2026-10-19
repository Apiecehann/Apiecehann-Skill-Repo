# Before and after

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：比较三个模拟任务的改动前后差异。

编码：分组柱。强调：平级比较，不设置重点系列。

组合理由：两系列成对并列，组内箭头直接解释变化；轴从零开始，不截断比较。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir templates/before-after/figure.ir.json --output output/before-after --render
```
