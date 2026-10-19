# Chart variants

每个图一张“轴覆盖”对照图，不是 recipe registry。

## dot-plot

`dot-plot.png` 有 10 个 panel：

| 轴 | panel |
|---|---|
| canonical | focus-tints |
| color | focus-neutral |
| color | focus-multi |
| color | multi-hue |
| style | bold-slide |
| style | minimal-mono |
| type | serif |
| type | mono |
| annotation | errorbar |
| annotation | reference |

没有做 grid，因为 grid 优先级低；style/type 只做 2 个对比，不做 15×15。

生成：

```bash
python examples/chart-variants/render_dot_sheet.py
```
