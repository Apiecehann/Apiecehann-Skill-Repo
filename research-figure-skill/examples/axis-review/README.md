# Axis review

这是**属性轴**的对照表，不是成品 recipe。每张图只回答一个维度的问题；所有数据都是 `MOCK / layout test`。

## 先看哪张

| 表 | 轴 | 你要判断什么 |
|---|---|---|
| `00-color-structure.png` | color structure | 2 series 还是 N series；accent / paired / categorical 的选择 |
| `01-baseline-color.png` | baseline color | 全同色 / 灰阶 / 多色 / accent 浅色，保留哪些 |
| `02-baseline-mark.png` | baseline mark | 实色 / 描边 / 半透明 / 纹理，哪些属于“baseline 处理” |
| `03-baseline-matrix.png` | color × mark | 颜色和 mark 是正交的；组合后是否还成立 |
| `04-accent.png` | accent hue | orange / blue / teal / green / rose，哪个作为默认 |
| `05-paired.png` | paired palette | before/after 用哪组同色相浅深 |
| `06-categorical.png` | categorical palette | 5 个等权类别用哪组 |
| `07-grid.png` | grid | none / h-hairline / h-dashed / full-hairline / full-dashed / dots |
| `08-style.png` | style | 6 个风格：paper / soft / serif / bold-slide / minimal-mono / hand-drawn |
| `09-type.png` | type | Arial / Times / Consolas / Segoe UI / Comic Sans |
| `10-layout.png` | layout | 竖/横 × 1/2/4 series × 单/多面板 |
| `11-size.png` | size | 9 种宽度/高度/长宽比 |
| `12-annotation.png` | annotation | delta / capacity / reference-line；increment 等 Codex |
| `13-panel-gap.png` | panel gap | normal / zero gap / composite |

## 关于 outline / alpha / hatch

它们**不属于 baseline color**，属于另一个子轴 `baseline_mark`：

- color：baseline 之间靠什么颜色关系区分（同色、灰阶、多色、accent 浅色）
- mark：每根 baseline 怎么画（实色、只描边、半透明、纹理）

两者可以组合，所以 `03-baseline-matrix.png` 是 4×4 的矩阵。你只需要分别选一个，不需要逐格选。

## Accent / Paired / Categorical 的关系

它们不是三个平行问题，而是**同一个问题的三种 series 数**：

- **2 series**：`paired`（同色相浅/深）或 `two-hue`（两个色相）
- **1 个焦点 + N 个 baseline**：`focus-neutral`、`focus-tints`、`focus-multi`
- **N 个无序类别**：`multi-hue`（categorical）

`00-color-structure.png` 把这 6 种放在一张表里；`04-accent` / `05-paired` / `06-categorical` 是展开细节。

## 怎么给反馈

一次回一张表即可，格式随意。例如：

```text
baseline_color: A/B/C/D 都留；D 默认
baseline_mark: solid/outline/alpha/hatch 都留；hatch 只用于 increment，不做 baseline
accent: orange 默认；blue/teal 备选
paired: blue/green/teal/orange/rose 都留
categorical: pastel-eight/tol-bright/tol-muted/set2/npg/tableau10 都留
grid: none/hairline/dashed 保留；dots 删
style: 6 个都留
type: 5 个都留
layout: 4 个都留
size: 4 个都留
annotation: delta/capacity/reference-line 保留；increment 等 Codex；bracket/direct planned
```

不需要选“最终图”，只标“保留 / 删除 / 换颜色”。

## 状态

`library/axes.json` 里每个选项有 `status`：

- `implemented`：当前 renderer/compiler 能直接出图；
- `planned`：类别先定，代码后续补。

`08-style` / `09-type` 现在都画了 6 / 5 个选项；`12-annotation` 里的 increment、bracket、direct-label 仍是 planned，等 Codex 或后续实现。

## 生成

```bash
cd research-figure-skill
python examples/axis-review/render_review.py
```

输出本目录的 14 张表和 `panels/`。不下载图片或字体；颜色来自公开色卡或参考图采样。
