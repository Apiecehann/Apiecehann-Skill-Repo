# grouped-bar-raw

MOCK / layout test

带重复观测的 grouped bar：`x,y,series,replicate`。bar 用 `y`，原始点用 `replicate`。

```bash
python spec/compile.py --ir examples/templates/grouped-bar-raw/figure.ir.json \
  --output /tmp/grouped-bar-raw --render
```
