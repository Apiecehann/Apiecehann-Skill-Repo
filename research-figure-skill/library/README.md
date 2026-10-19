# Pattern library

`cards.json` 描述可复用的图件操作；`recipes.json` 描述经过挑选的组合。模型选卡/选 recipe，`spec/compile.py` 展开成 `render.py` 配置。

## 卡片契约

每张卡至少包含：

| 字段 | 作用 |
|---|---|
| `layer` | `encoding` / `emphasis` / `annotation` |
| `intent` | 这张卡解决什么问题 |
| `when` | 适用条件；不满足就应拒绝 |
| `avoid` | 典型误用 |
| `params` | 编译器读取的参数 |
| `operations` | 具体改什么，必须能映射到 renderer |
| `qa` | 交付前检查项 |
| `example` | 指向一个可运行的 IR |

卡片不是“风格介绍”。如果 `operations` 写不出具体改动，这张卡就还不该存在。

当前卡片：

| 卡 | 层 | 核心约束 |
|---|---|---|
| `focus-gray` | emphasis | 1 个 focus；2–5 个系列；非 focus 用灰阶 |
| `capacity` | encoding | `capacity >= value >= baseline`；有区间时禁用 |
| `delta` | annotation | 纵向；同一 panel/group 一对 from/to；有区间时禁用 |

## Recipe 契约

`recipes.json` 里的每一项：

```json
{
  "id": "ours-vs-baselines",
  "title": "Ours vs baselines",
  "tags": ["paper", "single-column", "focus", "delta"],
  "ir": "examples/templates/ours-vs-baselines/figure.ir.json"
}
```

recipe 是**策展组合**，不是笛卡尔积。当前 8 个：

- `ours-vs-baselines`：中性灰 + 紫色 focus + delta
- `before-after`：两系列 + 三组 delta
- `capacity-88-of-96`：空心总量 + 实心完成值
- `ablation-legend`：五系列、双栏、顶部图例
- `horizontal-percent`：横向百分比
- `print-bw`：灰度 + 纹理
- `multi-panel`：两个 panel
- `slide-teaser`：双栏、大字号、focus

## 新增一张卡

1. 在 `cards.json` 的 `encoding` / `emphasis` / `annotations` 下增加条目。
2. 在 `spec/compile.py` 的 `apply_cards()` 里实现参数到 renderer 配置的映射。
3. 加至少一个 `examples/templates/<recipe>/`：IR、mock CSV、中文 README。
4. 加测试：合法路径、拒绝路径、生成配置的关键字段。
5. 跑 `python spec/catalog.py --output examples/catalog`，检查 contact sheet。
6. 更新 `spec/REPORT.md` 和本文件的卡片表。

## 新增一个 recipe

1. 复制一个最接近的模板，改 IR 与 mock 数据。
2. 确认 `spec/compile.py --ir ... --render` 能出 PNG/PDF/SVG。
3. 在 `recipes.json` 里登记 `id`、`title`、`tags`、`ir`。
4. 在 `spec/evals/cases.jsonl` 里加一条中文请求和期望决策。
5. 重建 catalog，确认 `index.json` 有 tags 和 decisions。

## 约束

- 不下载参考图或字体；示例数据必须是 `MOCK / layout test`。
- 不修改六个 `frozen_config` 复刻配置。
- 卡片参数应尽量少；复杂几何留在 renderer，不要塞进 IR。
- 卡片的 `when` / `avoid` 必须能转成编译器的 `ValueError`，否则只是文档。
