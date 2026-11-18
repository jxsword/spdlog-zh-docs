# spdlog 官方文档中文翻译计划（spdlog-zh-docs）

> 版本：v1.1（连续 3 轮复审修订版，2026-11-19）｜ 状态：待执行（M0 起步）
> 唯一权威规范：本文件。执行时偏离须先修订本文件并记录决策，再执行。
> 决策依据：DR-001（翻译范围）、DR-002（托管发布）、DR-003（增量机制），见 [decision_log.md](decision_log.md)。
> 技术路线：移植 fmt-zh-docs 技术骨架 + libuv-zh-docs 流程纪律（理由见 §3）。

## 1. 背景与目标

在 `/home/ssy/soft-tech-docs-translate/spdlog-zh-docs` 新建 spdlog 官方文档中文翻译工程：

- 产出 1：git 仓库 `spdlog-zh-docs`，源文/译文/状态资产入库，托管 GitHub 公开仓库 `jxsword/spdlog-zh-docs`（DR-002）；
- 产出 2：mkdocs-material 中文文档站，发布 GitHub Pages；
- 产出 3：**增量同步机制**——段落级 hash 状态机（DR-003），跟随上游 wiki/docs 持续更新，仅翻译新增/变更段落；
- 产出 4：术语表与风格指南，保证跨批次译文一致。

翻译引擎：会话内 zcode agent（GLM，零 API key，同 fmt-zh-docs M2 模式）。

## 2. 事实基线（2026-11-19 实测核实，勿重复调研）

| 事实 | 结论 | 证据/通道 |
|---|---|---|
| 官方中文文档 | **无**。RTD `/zh_CN/latest/` 实测 404；RTD 项目语言列表仅 EN；wiki 无中文页；README 无任何翻译链接 | WebFetch 直连 2026-11-19 |
| 官方文档主体 | **GitHub wiki**（~10 页 Markdown：Home、Usage basics、Sinks、Custom formatting（带编号）、Asynchronous logging、FAQ、Tweaking、Language bindings、Doxygen reference 等；精确清单以 M1 clone 为准） | gh 搜索索引 + WebFetch，2026-11-19 |
| wiki git 仓库 | `https://github.com/gabime/spdlog.wiki.git` **存在且可服务 git 协议**（info/refs 返回 `application/x-git-upload-pack-advertisement`；M1 以 `git ls-remote` 复确认） | WebFetch 2026-11-19 |
| RTD 站实质 | = 主仓库 `docs2.x` 分支 `docs/index.md`（14,968 B，README 改编单页）+ `docs/mkdocs.yml`（单页 nav）；**latest 自 2025-01 后未再构建** → 翻译以 docs2.x 分支当前文件为准，注明基线，不以 RTD 渲染版为基准 | api.github.com contents 直连 |
| 最新 release | v1.17.0（2026-01-04）；44 个 tag 全部 v1.x，**无 v2 tag**（仅 v2.x 开发分支）；release 节奏 3–9 个月 | api.github.com releases/tags |
| 许可证 | MIT（"Gabi Melman and spdlog contributors"，文末附 bundled fmt 说明，故 GitHub 归类 NOASSERTION）；wiki 内容随仓库许可（GitHub ToS） | api /license + LICENSE 文件 |
| 活跃度 | 默认分支 v1.x，pushed 2026-10-24；29,770 stars；非 archived | api.github.com repos |

链接三件套（核实 2026-11-19）：官网/文档 https://spdlog.readthedocs.io/en/latest/ ；主仓库 https://github.com/gabime/spdlog ；文档源 https://github.com/gabime/spdlog/tree/docs2.x/docs ；wiki https://github.com/gabime/spdlog/wiki ；wiki git https://github.com/gabime/spdlog.wiki.git 。

网络通道记录：gh CLI 已认证 `jxsword`，GitHub API 直连可用；github.com 页面与 raw.githubusercontent.com 直连常超时/ECONNRESET；按全局规则，直连失败/缓慢时代理 `http://192.168.33.1:10808` 重试一次后方可下"不可达"结论；web_reader 对 github.com 仅返回导航框架（工具视角限制，已注明）。

## 3. 既有翻译项目调研结论（先找轮子，2026-11-19 全网实测）

**结论：空白领域，无现成中文翻译项目。** GitHub（gh search repos/code，关键词 20+ 组合：spdlog 中文/翻译/文档/zh_CN/chinese/translation 等）、Gitee（API 无鉴权返回空；搜索确认只有源码镜像）、readthedocs.io（仅第三方项目提及）、docsforge（`spdlog.docsforge.com` DNS 已不解析，平台已死）四渠道零命中。中文内容仅散见个人博客/笔记（CSDN《spdlog库笔记》系列、知乎源码解析、掘金源码赏析、XMuli wiki 系列等，2022–2025），普遍**无版本锚定、无增量机制、无构建托管、无署名规范**，多基于 v1.x 而 RTD 已指向 v2.x 开发线。

**可借鉴资产（本地两工程）**：

| 来源 | 借鉴内容 | 弃用部分（理由） |
|---|---|---|
| fmt-zh-docs（同 Markdown+mkdocs 形态，已跑通 M2：4 页 447 段） | 段落级 hash + `.translation-state.json` 状态机；sync A/M/D/R 迁移；segment_markdown AST 切分；protect_untranslatable 占位符；validate_translation；fix_links；prompts/translate.md.j2；glossary 上下文消歇；tests 三件 | 翻译记忆库（sentence-transformers，未落地）、mike 多版本（wiki 无版本概念）、PDF 导出、CI 内 LLM 调用（translate_batch 是 stub）、monitoring、双语对照（YAGNI，以页头"原文"链接替代） |
| libuv-zh-docs（v1.0 已发布，1728/1728 条，最成熟） | 硬门禁链范式；批次报告+验收标准；handoff/启动提示词交接制度；基线锁定（DR-004 策略）；TASL 四要素署名；squash 提交纪律；上游周检 cron 自动开 issue；禁用译名黑名单机器扫描 | gettext PO 路线（不适配 MkDocs/Markdown 上游，引入 Sphinx 中转改造代价大） |

fmt 教训（必须吸取）：DR-011 sync_docs.py 死循环 OOM（12.4GB）→ **所有脚本/构建一律 memgate 包裹**；validate.yml `|| true` 软门禁 → 门禁硬性化；大量占位符（your-org/example.com）未落地 → 本工程一开始就接真实远程。

## 4. 已确认决策（用户 2026-11-19 选定，详见 decision_log.md）

- **DR-001 翻译范围**：wiki 全部页面 + docs2.x:docs/index.md（即 RTD 站内容）。**README 不翻译**，在看板最末标注"全部任务结束后按需翻译"（仅用户要求时启动）。
- **DR-002 托管发布**：GitHub 公开仓库 `jxsword/spdlog-zh-docs` + GitHub Pages。未选 readthedocs.org：上游 RTD 停更 10 个月、docsforge 第三方平台之死教训、libuv Pages 链路已实测。
- **DR-003 增量机制**：移植 fmt 段落级 hash 状态机（段落 sha256[:16]，A/M/D/R 按 hash 迁移）；初译期基线锁定（libuv DR-004 策略：M2 期间上游变更只开 issue 不切基线，v1.0 后开启自动 sync）。
- 技术形态随上游：Markdown + MkDocs → 走 fmt 形态（source/ + zh/ + 段落 hash），不走 libuv 的 PO 形态。

## 5. 仓库结构

```
spdlog-zh-docs/
├── .github/workflows/
│   ├── sync-upstream.yml        # 每周一 cron：检测 wiki HEAD + docs-index SHA 变化 → 自动 Sync PR；失败开 issue；每月查 release 仅记录
│   ├── validate.yml             # PR 门禁：validate_translation 全量 + pytest + mkdocs build 冒烟
│   └── deploy.yml               # push main → mkdocs build → actions/deploy-pages 发布
├── scripts/
│   ├── sync_upstream.sh         # 总控（libuv 范式）：幂等、先备份、退出码 0=无变更/1=有变更/2=错误
│   ├── sync_docs.py             # 移植 fmt：源改 spdlog.wiki.git（flat .md + 非 .md 附件）
│   ├── fetch_docs_index.py      # gh api 拉 docs2.x docs/index.md（失败走代理）
│   ├── segment_markdown.py      # 移植 fmt：markdown-it-py AST 语义切分
│   ├── protect_untranslatable.py# 移植 fmt：占位符保护
│   ├── fix_links.py             # 移植 fmt + 新增 [[wiki-link]]→标准 md 链接转换
│   ├── validate_translation.py  # 结构对等/代码块hash/占位符还原/术语黑名单/断链检查
│   ├── linkcheck.py             # 低频外链检查，仅告警不阻断
│   ├── progress.py              # 自动生成 reports/progress.md（页 × 段落状态统计，禁手改）
│   └── prompts/translate.md.j2  # agent 翻译提示词模板
├── source/                      # 英文原文（只读，仅 sync 写入）：wiki 页 slug 化 + assets/ 附件 + docs-index.md
├── zh/                          # 中文译文（同构）+ assets/
├── config/
│   ├── glossary.yml             # 术语表（en/zh/status/context/aliases + 禁用译名黑名单）
│   └── style-guide.md           # 翻译风格指南
├── docs/
│   ├── spdlog-zh-docs-翻译计划.md   # 本文件
│   ├── decision_log.md          # DR-001~003 起步（已预写）
│   ├── translation-board.md     # 任务看板（T-001…，含"README 按需翻译"排最末）
│   ├── handoff-latest.md        # 交接文档（每批次收尾更新）
│   └── 新会话启动提示词.md       # 本工程交接用（已预写）
├── reports/                     # 批次报告、sync 报告、progress.md
├── tests/                       # fmt 三件移植 + test_fix_links_wiki.py + wiki 形态 fixture
├── .translation-state.json      # 入库；per-file 增 upstream_page_title/wiki_commit 元数据
├── mkdocs.yml                   # material，docs_dir: zh，单版本 latest，zh/en 搜索，页脚非官方声明
├── README.md                    # TASL 四要素 + 非官方声明 + 基线锚定（wiki commit/日期/v1.17.0 时代）
├── LICENSE(MIT) + LICENSE_TRANSLATION.md
└── .gitignore                   # site/ .venv/ .mimosa/ workdir/ __pycache__/ *.bak
```

## 6. 关键设计

1. **同步（双源总控）**：`sync_upstream.sh` = ① git fetch `spdlog.wiki.git`（sync_docs.py：flat .md、slug 规范化=空格→连字符+保留编号如 `3.-Custom-formatting.md`、非 .md 附件入 `source/assets/` 保留相对路径、绝对 URL 图片原样、`_Sidebar.md`/`_Footer.md` 进 excluded-skipped）+ ② `fetch_docs_index.py`（gh api contents，失败走代理）。基线 = wiki commit SHA，记入 state 与 sync 报告。
2. **增量**：段落 sha256[:16] hash；A/M/D/R 四类变更按 hash 迁移状态；页重命名按页名映射迁移；未变段落译文自动保留；obsolete 页归档（fmt archive 机制）。
3. **wiki-link**：`[[Page]]`/`[[Page|text]]` 转标准链接（目标名按 slug 映射不译、显示文本可译）；validate 断链检查；fix_links 处理 zh 页间相对链接与锚点。
4. **agent 翻译工作流**：翻译单元 = 1 个 zh 页（大页可按段落区间拆子任务，同页串行）；**并发上限 2**（同页串行、跨页并行）；每任务输入 = 目标文件 + glossary + style-guide + 上游原文路径；prompt 注入术语表 + 风格规则 + 占位符保护 + 硬性规则（代码块/内联代码/API 名/链接目标不译，中英文间空格，全角标点，语义等价不增不减）；完成后自跑 validate 单文件模式必须全绿。
5. **批次验收标准**（每批全部满足）：抽检 ≥10% 段落语义准确（由第二校对 agent 对照原文执行）+ 术语违规 0 + 占位符还原 100% + 结构对等 100%（标题层级/列表/表格 AST 对比）+ `memgate mkdocs build` 零 error（warning 对照基线）+ 断链 0 + 批次报告落盘（含实际 token 消耗，供 M3 回填估算）。
6. **基线锁定**：初译期（M2）上游变更由 sync-upstream.yml 自动开 issue 记录、不切基线；M2 全量完成 tag v1.0 后开启自动 sync PR 模式。
7. **门禁硬性化**：validate 全部退出码生效，禁止 `|| true`；门禁链 = validate_translation（术语/占位符/结构/断链）+ pytest + mkdocs build 冒烟。
8. **术语表**：config/glossary.yml 单一来源；种子 ~25 条（M1 定稿）：logger=日志记录器、sink=接收器（首现括注 sink）、formatter=格式化器、pattern formatter=模式格式化器、flush=刷新、level=级别、async=异步、rotation=轮转、overflow policy=溢出策略、ring buffer=环形缓冲区、thread pool=线程池、backtrace=回溯、header-only=仅头文件 等 + 禁用译名黑名单；变更走 PR + 术语扫描全量生效。原则：API 名/函数/类/宏/头文件/代码不译；术语首现括注原文。
9. **署名合规**：LICENSE（MIT，spdlog-zh-docs Contributors）+ LICENSE_TRANSLATION.md（原作 MIT：Gabi Melman and spdlog contributors；译文衍生作品同 MIT）；README TASL 四要素（Title: spdlog documentation 中文翻译；Author: Gabi Melman and spdlog contributors；Source: wiki + docs2.x 两 URL；License: MIT）+ 非官方免责声明；站点页脚注入非官方声明（mkdocs 配置）；每篇 zh 页头加"原文"链接指向上游 wiki 页。
10. **中文搜索**：requirements pin `mkdocs-material[recommended]` + jieba；search 插件 `lang: ['zh','en']`；M1 构建验证中文可检索。

## 7. 里程碑

| 阶段 | 内容 | 验收 |
|---|---|---|
| **M0 落盘** | git init(main) + .gitignore（含 `.mimosa/`）+ 目录骨架 + 校对 decision_log（已预写 DR-001~003，每条 ≤15 行）+ 提交（正文列 `Decision: DR-001..003`） | 一条 init commit；本计划随 commit 入库 |
| **M1 基建** | `git ls-remote` 复确认 wiki 仓库 → sync `--init`（memgate）拉 wiki 快照 + docs-index 入 source/；**页面清单/行数/段数回填本计划 §7 与看板** → 移植 5 脚本 + tests（含 wiki fixture：编号标题/[[wiki-link]]/嵌套代码块/表格）→ glossary/style-guide 初版 → mkdocs.yml + 3 条 workflow → `gh repo create jxsword/spdlog-zh-docs --public --source . --push` + Pages 占位站 | pytest 全绿；占位站公网可访问；中文搜索命中；清单回填 |
| **M2 全量翻译** | 按实际页清单分 2–3 批（B1 核心：Home/Usage basics/Custom formatting/Sinks；B2 其余页 + docs-index；B3 FAQ/Tweaking 等收尾）；每批：agent 翻译 → 门禁 → 批次报告 → squash 合并 → Pages 发布 | §6.5 批次验收标准全满足；100% 段落 translated |
| **M3 v1.0 与增量演练** | 全量 sweep（术语一致性/断链/构建基线）→ tag v1.0 → 模拟上游改页端到端演练（变更检测→pending→增量翻译→PR）→ 开启自动 sync PR 模式 | 增量只处理变更段；token 全量估算回填 |
| **M4 按需** | README 翻译（仅用户要求时启动，看板标注） | — |

规模预估：wiki + 单页约 150–400 段（M1 精确回填）；agent 翻译+校对约 3–8M tokens 量级。

## 8. 风险与对策

| 风险 | 对策 |
|---|---|
| wiki-link/附件破坏 mkdocs 渲染 | §6.3 转换 + validate 断链检查 + wiki fixture 测试 |
| v2 发布致上游文档结构迁移 | docs-index 重译、wiki 按页名映射重挂（低频事件接受） |
| agent 漏译/幻觉 | 结构对等校验 + 第二校对 agent 抽检 ≥10% |
| state 损坏/大面积翻译错误 | state 写前 .bak + 批次 squash commit → `git revert` 即回滚 |
| 上游 wiki 页改名/停更 | 页名映射迁移 + obsolete 归档 |
| 脚本失控（fmt OOM 事故） | 一律 memgate 包裹；sync 幂等可重跑 |
| 本机网络限制 | gh api 直连 → 代理一次回退（全局规则）；web_reader 仅作辅助（工具视角） |

## 9. 三轮复审记录（v1.0 → v1.1，2026-11-19）

- **R1 技术正确性（8 项）**：R1-1 🔴 wiki-link 语法缺口（[[Page]] 不被 mkdocs 解析）→ §6.3；R1-2 🔴 wiki 非 .md 附件 → 同步快照 assets；R1-3 🟡 双源编排缺口 → sync_upstream.sh 总控+退出码；R1-4 🟡 mkdocs 中文搜索需 jieba → §6.10；R1-5 🟡 RTD 渲染版停更 → 以 docs2.x 文件为准注明基线；R1-6 🟢 wiki git 仓库存在性实测确认（info/refs 通告）；R1-7 🟡 slug/nav 规则明确化（Home 作站点 index、编号保留）；R1-8 🟡 state 增 upstream_page_title/wiki_commit 元数据。
- **R2 流程完备性（9 项）**：批次验收细化（抽检由第二校对 agent 执行）；progress.md 自动生成禁手改；回滚预案（.bak + revert）；新增 v2 迁移风险；CI 细节（actions/deploy-pages、pip 依赖无 gettext、release 月检）；wiki fixture 测试；sync 报告范式（`sync-<date>-<wikisha8>.md`）；.mimosa gitignore 确认；token 消耗逐批记录回填。
- **R3 合规与长期维护（7 项）**：wiki 内容许可随仓库 MIT（GitHub ToS）写入 LICENSE_TRANSLATION；版本锚定声明（基线 commit/日期/v1.17.0 时代）+ 页脚非官方声明；glossary 单一来源 + 变更走 PR；linkcheck 独立低频仅告警；M0 合并一条 init commit 列 `Decision: DR-001..003`；DR-002 留痕未选 RTD.org 理由；页头"原文"链接替代双语对照（YAGNI）。

## 10. 验证方式

1. M1：pytest 全绿；`memgate mkdocs serve` 本地预览；Pages 占位站公网可访问；中文搜索命中测试。
2. M2 每批：validate 全绿 + `memgate mkdocs build` 零 error（warning 对基线）+ 批次报告落盘 + 抽检达标。
3. M3：模拟上游变更端到端演练，sync 报告生成且增量只译变更段。
4. 会话连续性：每批收尾更新 handoff-latest.md；上下文过半或里程碑收尾时建议开新会话并给启动提示词；半成品不入库（gitignore 区或 /tmp）。

## 11. 执行第一批动作（M0 + M1 起点）

1. `git init`（main）+ `.gitignore`（含 `.mimosa/`、`site/`、`.venv/`、`workdir/`、`__pycache__/`、`*.bak`）+ 目录骨架（本计划、decision_log、启动提示词已在 docs/ 预写落盘，一并入库）；
2. 校对 `docs/decision_log.md`（DR-001~003 已于 2026-11-19 预写，核对无误即可）；
3. commit（`chore: init spdlog-zh-docs project with M0 plan`，正文列 `Decision: DR-001..003`）；
4. `git ls-remote https://github.com/gabime/spdlog.wiki.git` 复确认（失败走代理）→ `memgate bash scripts/sync_upstream.sh --init`：clone wiki + gh api 拉 docs-index 入 source/，页面清单/行数/段数回填本计划与看板；
5. 移植脚本与测试（源：`/home/ssy/soft-tech-docs-translate/fmt-zh-docs/scripts/` 与 `tests/`）、glossary/style-guide 初版、mkdocs.yml、3 条 workflow；
6. `gh repo create jxsword/spdlog-zh-docs --public --source . --push`，启用 Pages（actions/deploy-pages），确认英文占位站可访问；
7. 更新 handoff-latest.md，汇报 M1 验收结果，等确认再进 M2。
