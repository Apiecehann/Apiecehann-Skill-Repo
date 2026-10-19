# voxel

MOCK / layout test

三维体素：`x,y,z,value`，要求完整网格。`value > threshold` 的格子显示。

```bash
python spec/compile.py --ir examples/templates/voxel/figure.ir.json \
  --output /tmp/voxel --render
```
