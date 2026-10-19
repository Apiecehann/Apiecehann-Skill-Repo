# Axis review

这是**属性轴**的对照表，不是成品 recipe。每张图只回答一个维度的问题；所有数据都是 `MOCK / layout test`。

## 先看哪张

| 表 | 轴 | 你要判断什么 |
|---|---|---|
| `01-baseline-color.png` | baseline color | 全同色 / 灰阶 / 多色 / accent 浅色，保留哪些 |
| `02-baseline-mark.png` | baseline mark | 实色 / 描边 / 半透明 / 纹理，哪些属于“baseline 处理” |
| `03-baseline-matrix.png` | color × mark | 颜色和 mark 是正交的；组合后是否还成立 |
| `04-accent.png` | accent hue | orange / blue / teal / green / rose，哪个作为默认 |
| `05-paired.png` | paired palette | before/after 用哪组同色相浅深 |
| `06-categorical.png` | categorical palette | 5 个等权类别用哪组 |
| `07-grid.png` | grid | none / hairline / dashed / dots |
| `08-style.png` | style | 3 个已实现风格；其余 planned |
| `09-type.png` | type | sans / serif / mono；其余 planned |
| `10-layout.png` | layout | grouped / horizontal / paired |
| `11-size.png` | size | single / double |

## 关于 outline / alpha / hatch

它们**不属于 baseline color**，属于另一个子轴 `baseline_mark`：

- color：baseline 之间靠什么颜色关系区分（同色、灰阶、多色、accent 浅色）
- mark：每根 baseline 怎么画（实色、只描边、半透明、纹理）

两者可以组合，所以 `03-baseline-matrix.png` 是 4×4 的矩阵。你只需要分别选一个，不需要逐格选。

## 怎么给反馈

一次回一张表即可，格式随意。例如：

```text
baseline_color: A/B/C/D 都留；D 默认
baseline_mark: solid/outline/alpha/hatch 都留；hatch 只用于 increment，不做 baseline
accent: orange 默认；blue/teal 备选
paired: blue/green 保留；teal/orange/rose 先不做
categorical: pastel-eight / tol-muted 保留；其余先不做
grid: none/hairline/dashed 保留；dots 删
style: 三个已实现的保留；planned 先不评审
type: sans/serif 保留；mono 只给 token
layout: grouped/horizontal/paired 保留；multi-panel 用 double
size: single/double 都保留
```

不需要选“最终图”，只标“保留 / 删除 / 换颜色”。

## 状态

`library/axes.json` 里每个选项有 `status`：

- `implemented`：当前 renderer/compiler 能直接出图；
- `planned`：类别先定，代码后续补。

`08-style` / `09-type` 里只画了 implemented 的选项；planned 的（bold-slide、minimal-mono、hand-drawn、humanist、handwritten）等类别确认后再实现。

## 生成

```bash
cd research-figure-skill
python examples/axis-review/render_review.py
```

输出本目录的 11 张表和 `panels/`。不下载图片或字体；颜色来自公开色卡或参考图采样。
