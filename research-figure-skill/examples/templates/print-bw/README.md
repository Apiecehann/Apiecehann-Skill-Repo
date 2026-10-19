# Print in grayscale

**MOCK / layout test**：全部数据为人工构造，仅检查版式，不是实验结果。

主张：在黑白印刷下区分三个模拟方法。

编码：分组柱。强调：平级比较，不设置重点系列。

组合理由：灰度加纹理提供冗余编码；图例复用柱体纹理，取消密集的柱上数字。

从 research-figure-skill 目录运行：

```bash
python spec/compile.py --ir examples/templates/print-bw/figure.ir.json --output output/print-bw --render
```
