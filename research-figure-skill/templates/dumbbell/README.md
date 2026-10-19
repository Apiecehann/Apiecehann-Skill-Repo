# Dumbbell

两个 series 的成对对比：一条线连接 before/after，两端各一个点，右侧标差值。

## 什么时候用

- 同一任务/模型的两个版本；
- before/after、baseline/ours；
- 想同时看绝对值与差值；
- 类别数量不多（3–8 行）。

## 不要用

- 超过两个 series；
- 需要看完整分布（用 box/violin）。

## 数据

`data.csv` 为 **MOCK / layout test**：`group, series, value`，必须正好两个 series。

## IR

```json
"chart": "dumbbell",
"encoding": {"x": "group", "y": "value", "series": "series"}
```

## 生成

```bash
python spec/compile.py \
  --ir templates/dumbbell/figure.ir.json \
  --output /tmp/dumbbell --render
```
