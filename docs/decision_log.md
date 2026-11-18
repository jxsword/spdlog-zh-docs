# 决策记录（Decision Records）

编号规则：取当前最大编号 + 1。条目为结论级摘要；被推翻时不改旧条，新增条目并把旧条状态改为 `[状态: 已替代 → DR-新编号]`。

## DR-001 2026-11-19 翻译范围：wiki 全部页面 + RTD 单页，README 按需后置  [状态: 生效]
- 背景: spdlog 官方文档主体在 GitHub wiki（~10 页 Markdown）；用户引用的 RTD 站仅为 docs2.x 分支 docs/index.md 单页（渲染版停更 10 个月）
- 选项与权衡: 方案A wiki全部页面+RTD单页(覆盖完整、比仅wiki多1页) ← 选中; 方案B 仅wiki(最小但缺install内容, 弃用); 方案C 仅RTD单页(覆盖极少价值低, 弃用); 方案D 全套含README(与A/B重叠冗余、三处同步成本大, 弃用)
- 结论: 翻译 wiki 全部页面 + docs2.x:docs/index.md；README 不翻译，在看板最末标注"全部任务结束后按需翻译"（仅用户要求时启动，M4）
- 理由: 官方文档主体在 wiki；一站式覆盖用户引用的 RTD 内容；README 与前两者重叠度高
- 影响: source/ 与 zh/ 页面清单；translation-board.md 任务范围；里程碑 M4 定义
- 记录时间 / 会话: 2026-11-19 / spdlog-zh-docs 计划会话

## DR-002 2026-11-19 托管发布：GitHub 公开仓库 + GitHub Pages  [状态: 生效]
- 背景: 译文需对外发布且可持续 CI；gh CLI 已认证 jxsword；libuv-zh-docs 的 Pages 部署链路已实测
- 选项与权衡: 方案A GitHub公开仓库+Pages(复用已验证部署与 Actions 链路) ← 选中; 方案B 仅本地git(零发布风险但无法在线阅读、无 CI, 弃用); 方案C readthedocs.org(与上游同平台但需另配账号/webhook、上游 RTD 已停更 10 个月、docsforge 平台之死教训, 弃用)
- 结论: 创建公开仓库 jxsword/spdlog-zh-docs，GitHub Pages 经 actions/deploy-pages 发布
- 理由: 链路已在 libuv-zh-docs 验证；避免第三方文档平台停服风险；一开始就接真实远程（吸取 fmt 占位符未落地教训）
- 影响: deploy.yml 行为；M1 仓库创建步骤；README 在线地址
- 记录时间 / 会话: 2026-11-19 / spdlog-zh-docs 计划会话

## DR-003 2026-11-19 增量机制：移植 fmt 段落级 hash 状态机  [状态: 生效]
- 背景: 需跟随上游 wiki/docs 持续更新且仅翻译变更内容；上游为 Markdown+MkDocs 形态
- 选项与权衡: 方案A 段落级hash状态机(增量精确到段、fmt-zh-docs 已跑通可直接移植) ← 选中; 方案B 文件级diff整页处理(最简单但小改动触发整页重翻, 弃用); 方案C gettext PO 路线(增量原生但不适配 MkDocs/Markdown、需 Sphinx 中转代价大, 弃用)
- 结论: 移植 fmt-zh-docs 段落 sha256[:16] hash + .translation-state.json 状态机 + A/M/D/R 迁移；初译期基线锁定（上游变更只开 issue，v1.0 后开启自动 sync PR）
- 理由: 同构上游形态、脚本已验证（先找轮子）；基线锁定沿用 libuv DR-004 实战策略
- 影响: scripts/ 全套移植清单；.translation-state.json 结构；sync-upstream.yml 行为分期
- 记录时间 / 会话: 2026-11-19 / spdlog-zh-docs 计划会话
