# 翻译任务看板（translation-board）

> 状态快照：2026-11-20（M3 后，**v1.0 已发布，维护态**） ｜ 基线：wiki@15090480 + docs-index@3cd4a76 ｜ 461 段（**459 translated + 0 pending** + 2 skipped）
> 任务粒度 = 1 个 zh 页（大页按段落区间拆子任务时**同页串行**）；agent 并发上限实测 1（B2/B3 复现），全程串行。
> 批次结构对齐计划 §7.1 实测清单；每批完成后更新本表并落批次报告 reports/batch-*.md。

## 批次总览

| 批次 | 范围 | 段数 | 状态 |
|---|---|---:|---|
| M1 基建 | 同步管线 + 脚本/测试/门禁/站点/CI | 0 | **已完成**（2026-11-19，验收证据见 [handoff-latest.md](handoff-latest.md)） |
| B1 核心 | 5 页：index(Home)/QuickStart/CMake/Custom-formatting/Sinks | 157 | **已完成**（2026-11-19，证据见 [batch-B1.md](../reports/batch-B1.md)） |
| B2 主体 | 8 页 + docs-index | 238 | **已完成**（2026-11-19，证据见 [batch-B2.md](../reports/batch-B2.md)） |
| B3 收尾 | 12 小页 | 64 | **已完成，待验收**（2026-11-19，证据见 [batch-B3.md](../reports/batch-B3.md)） |
| M3 | 全量 sweep + tag v1.0 + 增量演练 | — | **已完成**（2026-11-20，证据见 [m3-report.md](../reports/m3-report.md)） |
| 维护态 | 上游增量跟进（sync-upstream 每周一自动检测 → Sync PR → 增量翻译，SOP 见 [handoff-latest.md §5](handoff-latest.md)） | — | 常态运转 |
| M4 README 翻译 | **全部任务结束后按需翻译**（仅用户要求时启动，DR-001） | — | 按需 |

## B1 核心（段数 157）——已完成

| 任务 ID | 页面 | 段数 | 状态 | 备注 |
|---|---|---:|---|---|
| T-001 | index.md（Home） | 4 | ✅ 已完成 | 站点 index；占位页已被译文替换 |
| T-002 | QuickStart.md | 25 | ✅ 已完成 | |
| T-003 | CMake.md | 37 | ✅ 已完成 | 初翻 prompt 损坏事故已修复（batch-B1 §4.1） |
| T-004 | Custom-formatting.md | 24 | ✅ 已完成 | 触发 validate 门禁 2 处假阳性修复（batch-B1 §4.3） |
| T-005 | Sinks.md | 67 | ✅ 已完成 | 单 agent 完成（未拆分）；派发 prompt 损坏事故下 agent 自推断完成，编排方独立复验（batch-B1 §4.2） |

## B2 主体（段数 238）——已完成

| 任务 ID | 页面 | 段数 | 状态 | 备注 |
|---|---|---:|---|---|
| T-006 | Creating-loggers.md | 29 | ✅ 已完成 | 锚点 {#creating-loggers-manually} attr_list 保页内链接 |
| T-007 | Logger-registry.md | 15 | ✅ 已完成 | |
| T-008 | Asynchronous-logging.md | 34 | ✅ 已完成 | |
| B2-4 | Thread-Safety.md | 12 | ✅ 已完成 | |
| B2-5 | Flush-policy.md | 13 | ✅ 已完成 | |
| B2-6 | Error-handling.md | 11 | ✅ 已完成 | |
| B2-7 | Default-logger.md | 4 | ✅ 已完成 | |
| B2-8 | FAQ.md | 35 | ✅ 已完成 | agent 中断但译文完整；checker 围栏豁免修复；Discussion 断链补全 |
| T-009 | docs-index.md | 85 | ✅ 已完成 | 编排方会话内翻译；锚点 ×2 + JetBrains logo 资产修正 |

## B3 收尾（段数 64）——已完成

| 任务 ID | 页面 | 段数 | 状态 | 备注 |
|---|---|---:|---|---|
| B3-1 | Tweaking.md | 3 | ✅ 已完成 | tweakme.h 代码块 114 行逐字节未动 |
| B3-2 | Setting-up-JSON-logging-with-spdlog.md | 12 | ✅ 已完成 | 5 围栏含弯引号逐字节保留 |
| B3-3 | How-to-use-spdlog-in-DLLs.md | 6 | ✅ 已完成 | 段内 ```span``` 结构保留 |
| B3-4 | Language-bindings.md | 10 | ✅ 已完成 | 特性类名列表保持英文 |
| B3-5 | Integrating-into-Eclipse-IDE.md | 8 | ✅ 已完成 | `<br>`/编号 1)-5)/源文错位反引号保留 |
| B3-6 | Makefile-Only.md | 6 | ✅ 已完成 | 文件名标注散文行保留原样 |
| B3-7 | Note-for-adding-sinks-on-the-fly.md | 8 | ✅ 已完成 | callback sink 首现括注 |
| B3-8 | Preventing-child-processes-from-inheriting-open-log-files.md | 2 | ✅ 已完成 | |
| B3-9 | Preventing-undefined-thread-ids-in-child-processes.md | 3 | ✅ 已完成 | 段内 ```span``` 结构保留 |
| B3-10 | Windows-unicode-filenames.md | 4 | ✅ 已完成 | 尾随空格保留；Windows/Unicode 大小写规范化 |
| B3-11 | Reference-documentation-using-Doxygen.md | 1 | ✅ 已完成 | 裸 URL 原样；源文语法瑕疵按语义等价译 |
| B3-12 | 3.-Custom-formatting).md | 1 | ✅ 已完成 | 上游 Envoy 粘贴事故页：1 段逐字保留（URL `)` 编码 `%29`）；编排方会话内处置 |

抽检：定点 11 段（≈17%）→ 0×P0 / 0×P1 / 1×P2（Sinks 措辞，已修复）；术语转正 7 条入 glossary.yml + runtime 词级统一 3 处。

## M3 收官（2026-11-20）

- [x] 全量 sweep 三项全绿：术语 12 条复核转正（glossary 35→47 条 approved，validate 对账零新增告警）；
      断链双通道复查 71/72（dunescience SSO 内网站点上游固有，复核接受）；构建基线 0 内容告警 + 1 环境通告
- [x] tag v1.0 发布（annotated，commit 1f72b16；README TASL/页脚/LICENSE_TRANSLATION 确认在位）
- [x] 增量演练端到端走通（模拟上游改 Default-logger 1 页 → sync 检测 +2/−1 段 kept 3 → 增量翻译 2 段
      → 四门禁全绿 → PR #1 CI 绿 → 关闭不合并，main 基线完好）；演练发现并修复 2 个 workflow bug
      （破坏性镜像 → 增量镜像；auto PR 补提交 state）
- [x] sync-upstream 自动 PR 模式确认可用（workflow_dispatch 实测 success，v1.0 门控接通）

## 已完成（M1 基建 + B1 核心）

- [x] M0 init commit（计划/DR/启动提示词入库，Decision: DR-001..003）
- [x] M1a wiki ls-remote 复确认（HEAD 15090480，直连可达）
- [x] M1b 同步管线 + sync --init（28 文件 / 461 段入库）+ 计划 §7.1 回填 + 本看板创建
- [x] M1c 脚本 + tests 88/88 全绿（含 test_fix_links_wiki.py）
- [x] M1d glossary 28 条 + banned 8 条 + style-guide 初版
- [x] M1e mkdocs + 3 workflow + jieba 中文检索实测 PASS（10/10 token）
- [x] M1f gh repo create + push + Pages 占位站（HTTP 200）+ 3 workflow CI 冒烟全绿
- [x] M1g handoff + progress + 验收汇报（等用户确认进 M2）
- [x] B1 五页 157 段翻译 + 抽检 94 段修复 5 处 + 门禁修复（validate 2 处假阳性 + 7 回归测试）
      + check_alignment/mark_translated 新增工具 + batch-B1 报告（token 实测 3,846,475）
- [x] B2 九页 238 段翻译（串行派发）+ checker 围栏豁免修复（6 回归测试）+ 抽检 66 段修复 4 处
      + docs-index 会话内翻译（锚点 ×2 + logo 资产修正）+ batch-B2 报告（subagent token 实测 3,858,681）
- [x] B3 十二小页 64 段翻译（串行派发）+ 事故页 3.-Custom-formatting).md 会话内逐字保留处置 + 抽检 11 段修复 1 处
      + 术语转正 7 条（glossary.yml）+ runtime 词级统一 3 处 + batch-B3 报告（subagent token 实测 3,673,187）
      + **M2 全量完成：459/461 段 translated（99.6%）**，导航告警归零

## 硬性纪律（每批适用）

- agent 输入 = 目标文件 + glossary + style-guide + 上游原文路径；prompt 注入术语表/风格规则/占位符保护/硬性规则（代码块/内联代码/API 名/链接目标不译，中英文间空格，全角标点，语义等价不增不减）；完成后自跑 validate 单文件模式必须全绿。
- 门禁链 = validate_translation（术语/占位符/结构/断链）+ pytest + mkdocs build 冒烟，全部退出码生效，禁止 `|| true`。
- 每批次一个 squash commit；批次报告落盘 reports/（含实际 token 消耗）；收尾更新 handoff-latest.md 与 reports/progress.md（自动生成禁手改）。
- 上下文过半或里程碑收尾（M1/M2 各批）主动建议开新会话并给启动提示词（docs/新会话启动提示词.md）。
