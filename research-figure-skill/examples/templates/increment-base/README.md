# Base plus increment

展示“今年基数 + 明年增量”的堆叠柱：下半段是 hatched 的基数，上半段是实色增量，柱顶是总量。

## 什么时候用

- 同一实体有 baseline 和 next-year 两个数；
- 读者需要同时看“现在多大”和“增长了多少”；
- 不想把 base 和 increment 画成两个并列的方法。

## 不要用

- base 和 value 不是同一量纲；
- base 为 0（那就是普通柱）；
- 需要 before/after 两个独立方法对比（用 paired）。

## 数据

`data.csv` 为 **MOCK / layout test**：

| group | value | base |
|---|---|---|
| 2023 | 0.72 | 0.64 |
| 2024 | 0.81 | 0.72 |
| 2025 | 0.88 | 0.81 |

`base` 必须满足 `0 <= base <= value`；不能和 `low/high/capacity` 同时出现。

默认用 `medium`（4.5 in），让 7–8% 的小增量标签能放进实色段；如果用 `single`，标签可能被推到柱顶并加引线。

## IR

```json
"encoding": {"x": "group", "y": "value", "series": "series", "base": "base"}
```

编译器会把它转成 `panel_defaults.increment.field = "base"`，并自动加 hatched 基数和增量标签。

## 生成

```bash
python spec/compile.py \
  --ir examples/templates/increment-base/figure.ir.json \
  --output /tmp/increment-base --render
```

输出 PNG / PDF / SVG；SVG 默认文字可编辑。
