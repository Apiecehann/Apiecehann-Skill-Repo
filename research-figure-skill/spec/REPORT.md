# IR 与模式库实施记录

## 计划与边界

起点为 `91593f2`，工作分支为 `feat/pattern-library`。已完整阅读任务书及指定的渲染器、预设、测试和说明。按五个可验收阶段提交，每次提交前运行完整测试：

1. `feat(spec): add figure IR and compiler`：严格 JSON Schema、无额外依赖的验证器、CSV 映射、预设复用、配置与决策日志。
2. `feat(spec): add emphasis cards and recipes`：三张分层卡、八个合成数据模板、强调与差值翻译。
3. `feat(render): support capacity bars`：容量数据验证、空心总量柱、标签和自动轴。
4. `test(spec): add compiler and catalog coverage`：目录、打标、十二条请求检查、测试与生成资产。
5. `docs(spec): document IR, cards and recipes`：中文使用说明与主入口迁移、最终验收记录。

## 假设与选择

- 仅 grouped-bar 家族；横向与前后对比复用已有布局。不新增散点、折线或结构叙事图。
- 卡片为 JSON；编码、强调、标注、主题分层。后端仅绘制。
- 当前环境没有 jsonschema；按 schema 实际使用的关键词手动验证，不增加依赖。
- CSV 路径相对 IR 文件；输出包含规范化的 `data.csv`，配置相对引用它，可随目录迁移。保留显式 id；缺少 id 时按原始行序生成稳定 id。
- schema 明确声明 layout、theme.type_scale、theme.hatch、theme.series_styles、axis.baseline 和 id/low/high/label 映射，以支持横向、印刷、演示与区间校验；不接受任意低层配置。
- series_order 包含全部当前系列且不重复；允许预留暂时缺席的系列，沿用现有跨图配色规则。
- 未映射 panel 时使用单面板 main；多面板按单栏纵向排列并增加高度，保持最终物理宽度及字号。
- 图例自动列数由现有渲染器测量文字后决定；dry-run 不创建图形，日志明确保留这一延迟决策。
- 使用 DejaVu／系统字体，不下载字体或参考图；新示例数据全部为 MOCK / layout test。
- 六个冻结配置及 CSV 均不修改；原 render.py CLI 保持兼容。
- 分阶段交付中，卡片与容量渲染分别在后续阶段启用；不将尚未完成的能力报告为已验收。
- 仅在服务器本地提交，不自动发布或推送。服务器未配置 Git 作者；提交使用 Codex <codex@openai.com>，不修改全局 Git 设置。

## 命令与验证

在仓库根目录使用现有 `.venv/bin/python`；测试工作目录为 `research-figure-skill`。

基线：`../.venv/bin/python -m pytest quantitative-plots/grouped-bar/scripts -q` → `76 passed in 18.06s`。

每阶段完整测试：`../.venv/bin/python -m pytest quantitative-plots/grouped-bar/scripts spec -q`。

阶段 1：`87 passed in 19.38s`；含编译后配置 CLI 重放、PNG 一致性、三种导出、未知字段与百分比拒绝、dry-run 不绘图。

## 生成资产与未完成项

阶段 1–4 完成。Stage 4 生成 8 个 recipe 的目录资产、contact sheet 和 index.json；测试 137 passed。Stage 5 文档在验收阶段补齐。没有需要用户回答的问题；具体歧义按以上假设执行。

阶段 2：完整测试 `103 passed in 19.47s`。七份非容量模板成功导出 PNG/PDF/SVG；修正多面板标题顶部留白后无越界警告。

补充假设：卡片给定的 #A3ACB9 填充不满足白底 3:1，保留该填充并用 #57606C 描边满足轮廓对比；第五系列场景增加第四级灰 #343B45。若用户显式降低描边透明度则保留设置并在决策日志提示 QA，不伪称达标。

阶段 3：完整测试 `114 passed`（最终无警告）。容量模板成功导出 PNG/PDF/SVG，自动轴 [0, 100]，标签 88 / 96 (92%)。验证横纵向几何、容量柱层级、非零基线、自定义格式、CSV 解析、混合行拒绝、区间冲突、轴截断和零容量。

容量默认百分比为 value / capacity，与基线位置无关；0 / 0 显示 n/a，不编造比例。field=null 保持低层容量绘制关闭；已提供的容量数据仍需满足验证且纳入轴范围。

## 阶段 4–5 收尾（验收记录）

- Stage 4 的实现由 Codex 完成，验收时统一提交为 `f625cc2 test(spec): add compiler and catalog coverage`。包含 `catalog.py`、`evals/`、8 个 catalog 资产、`index.json` 和扩充后的 `test_compile.py`；完整测试 `137 passed`。
- 视觉检查：`examples/catalog/contact-sheet.png` 覆盖 8 个 recipe；`capacity-88-of-96` 的空心总量/实心完成值、`ours-vs-baselines` 的灰底 + focus、`before-after` 的 delta 均正常。
- 已知限制：`multi-panel` 在 `single` 下两面板较拥挤，建议改用 `double`；这是尺寸选择问题，不是渲染错误。
- Stage 5 文档：新增 `spec/README.md`、`library/README.md`；`SKILL.md` 改为 IR 主入口；`grouped-bar/README.md` 增加 IR quickstart；本报告补齐阶段 4–5。
- 最终验收命令：`../.venv/bin/python -m pytest quantitative-plots/grouped-bar/scripts spec -q`。
- 分支已推送到 `origin/feat/pattern-library`；服务器 `git fetch` 后已对齐到同一 commit，并复跑 137 passed。

## 风味迭代 1（验收后）

- `auto_axis` 收紧 headroom：85% 的数据现在到 90%，不再是 100%。
- capacity 单组柱宽降到 0.35、`category_margin` 0.55，不再占满槽宽。
- horizontal 单系列 `group_gap` 降到 0.06，并关闭网格；横向条更紧凑。
- 新增 `examples/palette-shootout/`：4 种 baseline 策略 × 3 个 accent 的真实成图对照，附 `stage1.png` 和 `index.json`，用于用户选色。
- 回归测试增加到 140 passed。

## increment/delta 能力任务

起点为 feat/pattern-library 的 8e09c1b（包含并行新增的 axes catalog），基线完整测试 141 passed in 29.57s。按任务书三阶段提交，作者统一为 Apiecehann & Codex <1507392430@qq.com>。不修改色板、风格、字体、library/axes.json、palette-shootout 或原模板颜色。

阶段 1 实现 base CSV／IR／编码卡及纵向基数加增量：value 始终是总值；两段高度之和为 value - baseline。base 同面板必须齐全，要求 0 <= base <= value 且 baseline <= base，禁止区间、容量及横向。基数填充是现有系列色混入 70% 白色，不新增色板。

兼容约定：artists[row_id]["bar"] 是不绘制的完整总值矩形，仅保留几何元数据；base_bar 与 increment_bar 是实际两段。total_label／increment_label／increment_leader 暴露标签与引线。增量卡总值标签独立于普通 value_labels 开关；放不下的增量标签置于总值标签上方并加引线。新模板、注册与扩展几何覆盖将在阶段 3 完成。

阶段 1 验收：完整测试 152 passed in 26.83s；/tmp/increment-base 中立预览已导出 PNG/PDF/SVG 并人工查看，三组的基数、增量、分隔与标签均正常。

阶段 2：新 gain 默认 auto_layout=true，在物理 pt 坐标中测量柱体、数值标签与已有 delta 标签，采样三段三次曲线路径并布置标签；同组标签优先限制在本组槽内，移位较大时加引线。clearance_pt=5、label_collision_pad_pt=2、label_leader_pt=8 可调，后者是触发引线的水平位移阈值。自动轴仅在存在自动 gain 时预留标注空间，编译决策和渲染使用同一计算函数；无 gain 的轴行为不变。

兼容与边界：auto_layout=false 完整保留旧几何；frozen_config=true 且未显式选择 auto_layout 时自动走旧路径，不改六份配置。显式轴范围不被悄悄扩大；空间不足以安全容纳箭头或标签时，明确要求增加 y_max／画布尺寸或缩短文字。artists[from_id]["auto_gains"] 提供 arrow、label、leader、path_pt、points_pt 供几何检查。

阶段 2 验证覆盖升降、微小差值、左右反向、邻组槽、不同柱宽与锚点、容量／增量标签、空间不足、六个冻结示例。每个渲染曲线段独立采样 101 点，连同箭头头部检查 1 pt 膨胀柱体、数值标签及面板边界；冻结 gain 快照在修改前采集。before-after 与三组升降预览已导出 PNG/PDF/SVG 并查看。

并行协作记录：共享检出被其他进程 reset 到 c9e7579，保留其 axis-review 提交，在 /tmp/increment-delta-work 独立检出恢复阶段 1 并完成阶段 2，再将两个能力提交整合回 feat/pattern-library。没有改动并行的色板／风格／字体／axes.json／palette-shootout。上下文轮换后按用户要求在阶段 2 绿灯提交处停下；阶段 3 尚需 increment-base 模板、recipes/evals 注册、相关验收与文档。

阶段 2 最终验收：完整测试 173 passed in 30.04s，无警告；git diff --check 通过。冻结 gain 的坐标与标签快照逐一一致。

阶段 3 完成 increment-base 模板与注册：`examples/templates/increment-base/` 含 3 年 MOCK 数据、`encoding.base` 的 IR、中文 README；`library/recipes.json` 与 `spec/evals/cases.jsonl` 各加一条，check.py 的 `encoding_cards` 识别 increment。模板导出 PNG/PDF/SVG。测试从 173 增至 179 passed（含 curved delta 与白底 style 的回归）。

附加：gain 增加 `arrow_style: "curved"`，用单段三次弧线并在碰撞时抬高 ceiling；默认仍为 `route`，冻结 gain 不变。`12-annotation` 使用 curved 版本；新增 `14-bar-spacing` 与 `15-color-pairing`（固定 orange accent，24 组 baseline）。

补充（用户收敛）：annotation 轴只保留 curved delta 与 distribution overlap；后者新增 examples/distribution-overlap/（两 panel 重叠直方图，白底 + 双向 grid）。颜色筛选新增 library/palettes-120.json 与 16-palette-library.png（120 组 4-color 卡）。

Promote：15 个 style、15 个 font、5 个 palette（d3-orange / d3-blue / d3-teal / d3-rose / neutral-slate）已写入 presets；review 图仍保留作对照。curved delta 仍是变体，默认 route。Distribution Overlap 已接入 IR：chart 枚举、encoding.value、compile_distribution、library/recipes.json、evals case-14；模板 examples/templates/distribution-overlap/ 可导出 PNG/PDF/SVG。

P0 开发文档：docs/DEVELOPMENT.md；新增 library/charts.json 与 library/overlays.json。M1 实现 dot-plot 与 dumbbell：IR、renderer、template、recipes/evals、catalog；tests 187 passed。

M2：line-band 与 scatter 已实现；line-band 用 low/high 画 CI band，scatter 支持 trend + confidence-ellipse + reference；recipes/evals 增至 14/18，tests 191 passed。

M3：kde/box/violin/ecdf 已实现；distribution 数据允许重复观测；recipes/evals 增至 18/22，tests 199 passed。
