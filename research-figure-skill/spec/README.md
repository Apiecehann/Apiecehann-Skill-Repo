# Figure IR 与编译器

这一层把“模型直接写 164 个参数”改成：

```text
figure.ir.json（约 10 个语义字段）
  → spec/compile.py（cards + presets + 默认值）
  → render.py 的 config
  → render.py
  → PNG / PDF / SVG + decisions.json
```

`render.py` 仍然只负责画图；`compile.py` 负责翻译和校验，不是第二个渲染器。

## 快速开始

从 `research-figure-skill` 目录运行：

```bash
python spec/compile.py \
  --ir examples/templates/ours-vs-baselines/figure.ir.json \
  --output output/ours-vs-baselines --render
```

输出：

```text
output/ours-vs-baselines/
├── data.csv          # 规范化后的输入
├── config.json       # render.py 配置
├── decisions.json    # 实际决策与日志
├── figure.png
├── figure.pdf
└── figure.svg
```

`--dry-run` 只写 `data.csv`、`config.json`、`decisions.json`，不画图。

重建目录：

```bash
python spec/catalog.py --output examples/catalog
```

检查 eval 模板：

```bash
python spec/evals/check.py --cases spec/evals/cases.jsonl --check-templates
```

## IR 字段

必需：

| 字段 | 说明 |
|---|---|
| `claim` | 一句话说明这张图要证明什么 |
| `chart` | 当前只支持 `"grouped-bar"` |
| `data` | CSV 路径；相对 IR 文件所在目录 |
| `encoding` | `x` / `y` / `series` 对应的 CSV 列；可选 `panel`、`capacity`、`id`、`low`、`high`、`label` |
| `size` | `{"preset": "single"}` 或 `"double"` |
| `theme` | `style`、`palette`、`font`；可选 `type_scale`、`hatch`、`series_styles` |
| `labels` | `values` 是否标数值、`legend` 为 `"top"` 或 `"none"`；可选 `value_format` |
| `output` | `formats`、`dpi`、`svg_text` |

可选：

| 字段 | 说明 |
|---|---|
| `layout` | `grouped`、`horizontal`、`paired` |
| `series_order` | 颜色顺序；必须包含全部当前系列 |
| `series_labels` | 图例显示名 |
| `series_roles` | 语义色板需要的角色 |
| `emphasis` | 卡列表，当前为 `focus-gray` |
| `annotations` | 卡列表，当前为 `delta` |
| `axis` | `y_label`、`y_format`、`y_max`、`baseline` |

最小例子：

```json
{
  "claim": "ours beats three baselines on all benchmarks",
  "chart": "grouped-bar",
  "data": "data.csv",
  "encoding": {"x": "group", "y": "value", "series": "series"},
  "size": {"preset": "single"},
  "theme": {"style": "soft-outline", "palette": "neutral-accent", "font": "sans"},
  "labels": {"values": false, "legend": "top"},
  "output": {"formats": ["png", "pdf", "svg"], "dpi": 300, "svg_text": true}
}
```

约束：

- `axis.y_format` 以 `%` 结尾时，CSV 的 y 值必须在 `[0, 1]`；不会自动除以 100。
- `capacity` 必须满足 `capacity >= value >= baseline`；容量与 `low/high` 区间同时出现会报错。
- `series_order` 必须唯一并包含全部当前系列；允许预留暂时缺席的系列。
- `theme.type_scale`、`theme.series_styles`、`theme.hatch` 是高级出口；普通请求不要用它们替代 `size` / `style`。

## Cards

卡片定义在 [`library/cards.json`](../library/cards.json)。当前三张：

| 卡 | 层 | 作用 |
|---|---|---|
| `focus-gray` | emphasis | 一个 focus 用强调色，其余用灰阶 |
| `capacity` | encoding | 实心完成值 + 空心总量 |
| `delta` | annotation | 两根柱之间的差值箭头 |

选择规则：

- `focus-gray`：恰好一个 focus，2–5 个系列；超过 5 个或两个 focus 直接报错。
- `capacity`：总量必须有真实含义（题数、容量、预算），不是“另一个方法的分数”；有区间时不要用。
- `delta`：只支持纵向；同一 panel/group 内一对 from/to；有区间时不要用。

## 输出与决策日志

`compile.py` 会打印类似：

```text
size single -> 237.6 x 169.7 pt; type 7/8/6.5 pt
emphasis focus-gray -> 1 focus (ours), 3 muted
annotation delta -> main/Bench B: method-1 -> ours (+22.0 pp)
palette neutral-accent -> method-1 #A3ACB9, method-2 #7B848F, method-3 #57606C, ours #9979CB
axis main -> [0.0, 0.8]; ticks [0.0, 0.2, 0.4, 0.6, 0.8]
legend auto -> renderer measures columns at render time
```

`decisions.json` 保存同样的信息，便于回归和人工检查。

## 限制

- 只覆盖 grouped-bar 家族；散点、折线、示意图尚未实现。
- `delta` 与横向布局、区间、容量暂不兼容；会明确报错。
- 多面板在 `single` 下会拥挤；两个以上面板建议用 `double` 或自己检查成图。
- `spec/` 不下载图片或字体；所有示例数据都是 `MOCK / layout test`。
- 编译器只保证“结构和默认值正确”，最终审美仍由人确认。

## 测试

从 `research-figure-skill` 目录：

```bash
python -m pytest quantitative-plots/grouped-bar/scripts spec -q
```

当前覆盖：旧 renderer 回归、IR 校验、卡片翻译、capacity 柱、目录资产、12 条 eval 模板。
