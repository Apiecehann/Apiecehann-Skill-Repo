# dot-plot axis review

结构对照 `reference/axis-review`：**一张图 = 一个轴**，图里是多个 panel。

| 文件 | 轴 | panel 数 |
|---|---|---|
| `00-color-structure.png` | 颜色结构 | 6 |
| `01-baseline-color.png` | baseline color | 4 |
| `02-accent.png` | accent hue | 5 |
| `03-paired.png` | paired | 5 |
| `04-categorical.png` | categorical | 6 |
| `05-grid.png` | grid | 5 |
| `06-style.png` | style | 15 |
| `07-type.png` | type | 15 |
| `08-annotation.png` | annotation | 2 |
| `09-size.png` | size | 9 |
| `10-series-count.png` | dot-plot 自己的轴 | 3 |

合计 **11 张轴图，75 个 panel**。

- 没有做 `color pairing` / `120 palette library`：这两个不进 per-chart。
- `style` / `type` 都是 15 个，不是 20。
- `series-count` 是 dot-plot 新增的轴：1 / 2 / 4 series。

生成：

```bash
python reference/chart-review/dot-plot/render.py
```

`index.json` 里有每张图的 axis、panel 数和 panel 标签。
