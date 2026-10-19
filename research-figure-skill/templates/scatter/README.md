# Scatter + trend / ellipse

散点图 + 线性趋势带 + 每个 series 的 95% 置信椭圆。

## 什么时候用

- latency vs throughput、score vs size；
- embedding / 表征（二维投影）；
- 需要看相关方向、离群点和组间分离。

## 不要用

- 类别轴；
- 点太多（用 hexbin/2D density）；
- 少于 3 个点时不要画椭圆。

## 数据

`data.csv` 为 **MOCK / layout test**：`x, series, value`。

## IR

```json
"chart": "scatter",
"stats": [
  {"kind": "trend", "method": "linear"},
  {"kind": "confidence-ellipse", "level": 0.95}
]
```

## 生成

```bash
python spec/compile.py \
  --ir templates/scatter/figure.ir.json \
  --output /tmp/scatter --render
```
