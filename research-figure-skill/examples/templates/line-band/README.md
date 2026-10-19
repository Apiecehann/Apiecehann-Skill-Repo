# Line + band

多个 step 的均值曲线 + 95% 区间；用于 training curve、scaling law、latency over time。

## 什么时候用

- 有重复观测或已有 `low/high`；
- 需要同时看趋势和不确定性；
- 两个 series 对比。

## 不要用

- 只有单次运行（用普通 line）；
- 区间不是同一置信水平（不要混用 std/CI）。

## 数据

`data.csv` 为 **MOCK / layout test**：`step, series, value, low, high`。

## IR

```json
"chart": "line-band",
"stats": [{"kind": "ci-band"}],
"reference": [{"axis": "y", "value": 75, "label": "SOTA"}]
```

## 生成

```bash
python spec/compile.py \
  --ir examples/templates/line-band/figure.ir.json \
  --output /tmp/line-band --render
```
