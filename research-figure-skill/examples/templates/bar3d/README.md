# bar3d

MOCK / layout test

三维柱状：`x,y,series`，每个 group 每个 series 一根柱。

```bash
python spec/compile.py --ir examples/templates/bar3d/figure.ir.json \
  --output /tmp/bar3d --render
```
