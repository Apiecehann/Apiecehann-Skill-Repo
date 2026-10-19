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

阶段 1–2 完成。测试资产在 pytest 临时目录；七份渲染预览位于 /tmp/pattern-library-stage2，容量模板暂只编译。阶段 3–5 待完成。没有需要用户回答的问题；具体歧义按以上假设执行。

阶段 2：完整测试 `103 passed in 19.47s`。七份非容量模板成功导出 PNG/PDF/SVG；修正多面板标题顶部留白后无越界警告。

补充假设：卡片给定的 #A3ACB9 填充不满足白底 3:1，保留该填充并用 #57606C 描边满足轮廓对比；第五系列场景增加第四级灰 #343B45。若用户显式降低描边透明度则保留设置并在决策日志提示 QA，不伪称达标。
