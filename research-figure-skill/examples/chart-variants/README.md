# Chart variants

每个图一张“轴覆盖”对照图，不是 recipe registry。

## dot-plot

`dot-plot.png` 有 17 个 panel：

| 轴 | panel |
|---|---|
| canonical | focus-tints |
| color | focus-neutral / focus-multi / multi-hue |
| style | bold-slide / minimal-mono / serif-emphasis |
| type | sans / serif / humanist / mono |
| annotation | errorbar / reference |
| grid | hairline / dashed |
| size | single / double |

没有新增 chart-specific 轴（dot-plot 本身没有额外语义轴）；grid 已加回；style/type 各取 4 个代表，不重复 20 个。

生成：

```bash
python examples/chart-variants/render_dot_sheet.py
```
