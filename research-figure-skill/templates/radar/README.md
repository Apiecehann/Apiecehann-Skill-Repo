# radar

MOCK / layout test

雷达图：`axis,series,value`，每个 series 覆盖全部 axis。

```bash
python spec/compile.py --ir templates/radar/figure.ir.json \
  --output /tmp/radar --render
```
