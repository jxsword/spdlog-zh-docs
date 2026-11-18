# 会话交接文档（handoff-latest）

> 更新: 2026-11-19 ｜ 里程碑: **M0 + M1 基建完成，待用户验收** ｜ 下一阶段: **M2 全量翻译（B1 起步）**
> 本文件是每批次/sync 收尾更新的唯一交接入口；新会话开工前**必读**本文件 + 计划 §5/§6/§7.1。

## 1. 状态快照

- **远程仓库**: https://github.com/jxsword/spdlog-zh-docs （公开，main 已推送至 78cb599）
- **站点**: https://jxsword.github.io/spdlog-zh-docs/ （Pages = actions/deploy-pages v5 链路，占位站 HTTP 200 验证）
- **CI**: validate（PR 门禁: pytest 88 + validate_translation + mkdocs build）/ deploy（push main）/ sync-upstream（周一 cron）——三条 workflow 手动触发冒烟**全绿**（18s/16s/49s）
- **基线**: wiki@15090480 + docs-index@3cd4a76（2026-11-19 锁定，对应 v1.17.0 时代）；28 文件 / 2219 行 / **461 段**（459 pending + 2 skipped: _Sidebar/_Footer excluded）
- **翻译进度**: 0%（M1 基建阶段，所有段落 pending）——progress.md 自动生成
- pytest **88/88 全绿**；validate 全量退出码 0；`memgate mkdocs build` 零 error
- 术语表 28 条（approved）+ 禁用译名黑名单 8 条；风格指南初版
- jieba 中文检索**实测 PASS**（搜索索引 10/10 token 命中；mkdocs 搜索插件实证调用 jieba）

## 2. M1 交付清单（全部入库）

- 同步管线：sync_upstream.sh（总控，退出码 0/1/2）+ sync_docs.py（wiki 形态改造：flat 仓库/slug 规范化
  Home→index/附件 assets/excluded/docs-index 统一入 state/幂等 reconcile/state 写前 .bak）+
  fetch_docs_index.py（gh api 直连→代理回退）+ segment_markdown.py（fmt segment_md 抽出，OOM 护栏保留）
- fix_links.py：normalize_links（裸页名→.md、[[..]]→标准链接、附件→assets/、.md#anchor 保留）
- validate_translation.py：fmt 移植 + 三扩展（banned 黑名单 / 断链 / 全 pending 页跳过）
- linkcheck.py（仅告警）/ progress.py（自动生成禁手改）/ prompts/translate.md.j2
- tests/：88 用例（fmt 三件移植 + test_fix_links_wiki.py + wiki fixture 5 页）
- config/：glossary.yml + style-guide.md；README TASL 署名 + LICENSE(MIT) + LICENSE_TRANSLATION.md
- mkdocs.yml + requirements.txt（版本 2026-11-19 PyPI 实测 pin）+ zh/index.md 中文占位页

## 3. M2 入口（下一阶段，计划 §7 B1 起步）

- **批次 B1（157 段）**：index(Home) 4 / QuickStart 25 / CMake 37 / Custom-formatting 24 / Sinks 67
- 执行模式：agent 翻译（并发上限 2，同页串行）→ 门禁链 → 批次报告 → squash commit → Pages 自动发布
- agent 输入 = 目标 zh 文件 + glossary.yml + style-guide.md + source/ 原文路径；
  prompt 模板 scripts/prompts/translate.md.j2；完成后自跑 validate 单文件模式必须全绿
- **zh/index.md 占位页将被 B1 的 Home 译文替换**（占位内容不入翻译状态机，validate 因全 pending 跳过）
- B1 收尾产物：reports/batch-B1.md（含 token 消耗）+ handoff 更新 + progress.md 重生成

## 4. M1 关键经验（坑位沉淀）

1. **Mimosa L3 提交门禁会全树扫描并自行构建项目**：material 打包的 vendor 库（lunr wordcut.js，
   泰语/CJK 切词正规库）被误报"代码注入"高危并拦截提交。解法 = `site_dir: /tmp/spdlog-zh-docs-site`
   （仓库外输出，mkdocs.yml 与 deploy.yml 同步该路径）；任何构建后不要把 site/ 留在仓库树内。
2. **上游 wiki 无 [[..]] 语法**：页间链接 = 标准 md 裸页名 URL（`[t](Page-Name)`），GitHub wiki 渲染时解析；
   sync 期 normalize_links 统一补 `.md`（含锚点）。现脚本对两种语法都兼容。
3. **fmt 逐字转录对本会话生成不稳定**（protect_untranslatable/glossary 曾连续产生污染文本）：
   转录型文件改由**子代理移植**（diff 仅 docstring），新写内容自写。后续遇到逐字移植需求优先派子代理。
4. **测试副作用**：sync_init/sync_since 曾无条件写报告到真实 reports/（88 用例产生 19 个散落报告）——
   已修复为显式 --report + SyncContext.report_dir 注入；测试永不写仓库 reports/。
5. **sync_docs 修复史**：migrate_segment_dicts 遗漏 out.append(d)（state 段落全空）→ 附件循环 repo_dir
   笔误 → normalize_links 正则括号不齐（[[ 畸形）→ .md#anchor 误判资产。全部有回归测试锚定。
6. 工具链版本 2026-11-19 实测：mkdocs 1.6.1 / material 9.8.1 / jieba 0.42.1 / pytest 9.0.2；
   Actions: checkout v7 / setup-python v7 / upload-pages-artifact v5 / deploy-pages v5。

## 5. 硬性纪律（重申）

- 一切以计划文档为准（含 §7.1 实测清单与批次段数）；改架构/目录/工具链属重大决策
  （决策矩阵 + 用户确认 + decision_log）。
- 所有脚本执行/构建/sync 一律 memgate 包裹；网络回退：gh api 直连优先 → 代理
  http://192.168.33.1:10808 重试一次后方可下"不可达"结论。
- agent 翻译并发上限 2（同页串行、跨页并行）；source/ 只读（仅 sync 写入）。
- 门禁硬性化：validate 全部退出码生效，禁止 `|| true`；门禁链 = validate_translation + pytest + mkdocs build 冒烟。
- 每批次/每次 sync 一个 squash commit；批次报告含实际 token 消耗；收尾更新本文件与 progress.md。
- 上下文过半或里程碑收尾主动建议开新会话并给启动提示词（docs/新会话启动提示词.md）。
- 本地构建产物永不入仓库树（site_dir 已指向 /tmp）。
