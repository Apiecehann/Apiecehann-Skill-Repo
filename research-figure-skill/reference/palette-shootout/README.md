# Palette shootout — Stage 1

同一份 `MOCK / layout test` 数据（4 方法 × 3 benchmark）、同一个版式，只换 baseline 策略和 accent，用来选“图 1”的颜色骨架。

## 怎么读

- 行：4 种 baseline 策略
  - **A same-gray**：3 个 baseline 全部同一个中性灰；只能靠标签区分
  - **B gray-tints**：3 级灰；容易看起来像“越大越黑”
  - **C muted-hues**：3 个等明度低饱和色；baseline 彼此可分
  - **D accent-tints**：accent 的 3 个浅色；同色相、整体最协调
- 列：3 个 accent（blue `#2F80C9`、teal `#1F9E89`、orange `#E07A2F`）
- 每格底部：3 个 baseline 色 + accent 的 HEX；完整列表在 `index.json`。

## 怎么选

回复一个编号即可，例如：

```text
C-teal
```

或者：

```text
D-blue；orange 做备选
```

选完 Stage 1 后，Stage 2 再从 ColorBrewer / CARTO / Tol / ggsci / Tableau / Colorcet 拉 20–30 组，做 before/after 的 paired 和 ablation 的 categorical 对照。

## 生成

```bash
cd research-figure-skill
python reference/palette-shootout/render_stage1.py
```

输出 `stage1.png`、`panels/*.png`、`index.json`。不下载图片或字体；数据是模拟值，只用于配色比较。
