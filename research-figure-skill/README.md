# Research Figure Skill

科研图 Skill：用小型 figure IR 生成论文图，覆盖 comparison、distribution、relationship、matrix、classification、3D、hierarchy、flow、layout 与 bar variants。

入口见 [SKILL.md](SKILL.md)。

## 快速开始

```bash
python -m pip install -r requirements.txt

python spec/compile.py \
  --ir templates/ours-vs-baselines/figure.ir.json \
  --output output/ours-vs-baselines --render
```

输出 `figure.png` / `figure.pdf` / `figure.svg`。新图先复制 `templates/<recipe>/` 的 `data.csv` + `figure.ir.json`，再改 claim 和数据。

## 目录

```text
SKILL.md          # Skill 入口与工作流
spec/             # IR schema、compiler、renderer
library/          # charts / recipes / overlays / palettes
templates/        # 可复制 IR + data
reference/        # 轴参考、chart review、catalog；不参与运行
docs/             # 架构、轴覆盖、变体
quantitative-plots/grouped-bar/  # 旧版 grouped-bar 低层 renderer（保留兼容）
```

## 当前覆盖

- **40 charts**：16 个 P0 + 7 个 P1 + 17 个 P2
- **48 recipes**
- **52 eval cases**
- **259 tests**

图表能力矩阵见 [library/charts.json](library/charts.json)，配方见 [library/recipes.json](library/recipes.json)。

## 参考图

`reference/` 是给人看的，不是运行时依赖：

- [axis-review](reference/axis-review)：全局轴参考
- [chart-review](reference/chart-review)：每个 chart 的轴覆盖
- [catalog](reference/catalog)：成品 contact sheet

## 测试

```bash
python -m pytest quantitative-plots/grouped-bar/scripts spec -q
```

## 旧版 grouped-bar 入口

旧版 renderer 仍保留，用于复刻和低层精调：

```bash
python quantitative-plots/grouped-bar/scripts/render.py \
  --config quantitative-plots/grouped-bar/examples/style-guide/config.json \
  --size single --style soft-outline --palette tol-muted \
  --output output/my-figure
```

代码沿用仓库 Apache-2.0 许可；来源与字体许可见 [NOTICE.md](NOTICE.md)。
