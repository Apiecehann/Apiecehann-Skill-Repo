# 来源与素材许可

最初三套示例来自小红书笔记「MIT学生教你画论文图」（作者：瑾瑾，笔记 ID `6ace9bd9000000001a02bf03`）所展示的 Sophie L. Wang 论文图。

- [原作者设计说明](https://www.sophielwang.com/blog/paper-writing)
- [论文及固定版本](https://arxiv.org/abs/2610.06851v1)：*Base Models Can Reason by Taking a Cue From Training Data*
- `cue-comparison` 对应 Figure 2；`data-edit` 对应 Figure 5 中间的数值图列；`teaser-strip` 对应首页图的数值汇总条。

脚本为本仓库重新实现。示例的数值及区间从作者发布的矢量图恢复，精度受导出坐标影响，不能替代作者原始试验数据。示例外观、标签及小型 chicken 图标沿用原图，用于对照复刻；不把它们描述为本仓库的原创设计或新的实验结果。仓库 Apache-2.0 许可不重新授予第三方素材权利。

新增三套示例根据用户提供的图片实现：

- `zero-shot-execution`：SAGA 的九任务、五系列对比图，采用用户截图中的幻灯片布局。45 个成功率从 [SAGA v1 的 Figure 5](https://arxiv.org/html/2512.12842v1) 矢量图恢复，按十次试验的 0.1 步长记录。
- `affordance-distribution`：[SAGA v1](https://arxiv.org/html/2512.12842v1) 数据分布图的左侧柱图。CSV 记录图中已舍入的八个百分比，不声称是原始计数。
- `planning-gains`：[VLA-OS 项目页](https://nus-lins-lab.github.io/vlaos/) Finding 6 的柱图版式，采用用户提供的两行标题。数值核对自[论文表格](https://openreview.net/pdf/05a810d8dce16f520e115b9ee80b8096e6512276.pdf)：73.3→79.1、74.2→79.8。使用线性坐标和数据计算差值，未沿用位图中略有偏差的柱高／刻度对齐。

`scripts/fonts/B612Mono-Regular.ttf` 来自 [Google Fonts / B612 Mono](https://github.com/google/fonts/tree/main/ofl/b612mono)，使用 SIL Open Font License 1.1，完整许可保存在同目录 `OFL.txt`。字体文件未修改。Graphik 字体文件及原始参考图不进入仓库。
