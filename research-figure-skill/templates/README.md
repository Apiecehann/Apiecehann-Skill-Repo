# Templates

每个 recipe 一个目录：

```text
<recipe>/
├─ data.csv
├─ figure.ir.json
└─ README.md
```

用法：

```bash
cp -r templates/grouped-bar-raw /tmp/my-figure
python spec/compile.py --ir /tmp/my-figure/figure.ir.json \
  --output /tmp/my-figure/output --render
```

模板是起点，不是固定成品；改 `claim`、`data.csv` 和 `encoding`。

配方索引：`library/recipes.json`。
