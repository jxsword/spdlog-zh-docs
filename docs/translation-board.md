# 翻译任务看板（translation-board）

> 状态快照：2026-11-19 ｜ 基线：wiki@15090480 + docs-index@3cd4a76 ｜ 461 段（459 pending + 2 skipped）
> 任务粒度 = 1 个 zh 页（大页按段落区间拆子任务时**同页串行**）；agent 并发上限 2（同页串行、跨页并行）。
> 批次结构对齐计划 §7.1 实测清单；每批完成后更新本表并落批次报告 reports/batch-*.md。

## 批次总览

| 批次 | 范围 | 段数 | 状态 |
|---|---|---:|---|
| M1 基建 | 同步管线 + 脚本/测试/门禁/站点/CI | 0 | **已完成**（2026-11-19，验收证据见 [handoff-latest.md](handoff-latest.md)） |
| B1 核心 | 5 页：index(Home)/QuickStart/CMake/Custom-formatting/Sinks | 157 | pending |
| B2 主体 | 8 页 + docs-index | 238 | pending |
| B3 收尾 | 12 小页 | 64 | pending |
| M3 | 全量 sweep + tag v1.0 + 增量演练 | — | pending |
| M4 README 翻译 | **全部任务结束后按需翻译**（仅用户要求时启动，DR-001） | — | 按需 |

## B1 核心（段数 157）

| 任务 ID | 页面 | 段数 | 状态 | 备注 |
|---|---|---:|---|---|
| T-001 | index.md（Home） | 4 | pending | 站点 index；占位站阶段为中文项目占位页，B1 时被译文替换 |
| T-002 | QuickStart.md | 25 | pending | |
| T-003 | CMake.md | 37 | pending | |
| T-004 | Custom-formatting.md | 24 | pending | |
| T-005 | Sinks.md | 67 | pending | 最大页（67 段），可按段落区间拆 2–3 个串行子任务 |

## B2 主体（段数 238）

| 任务 ID | 页面 | 段数 | 状态 | 备注 |
|---|---|---:|---|---|
| T-006 | Creating-loggers.md | 29 | pending | |
| T-007 | Logger-registry.md | 15 | pending | |
| T-008 | Asynchronous-logging.md | 34 | pending | |
| B2-4 | Thread-Safety.md | 12 | pending | |
| B2-5 | Flush-policy.md | 13 | pending | |
| B2-6 | Error-handling.md | 11 | pending | |
| B2-7 | Default-logger.md | 4 | pending | |
| B2-8 | FAQ.md | 35 | pending | |
| T-009 | docs-index.md | 85 | pending | RTD 单页（DR-001）；代码块占比高 |

## B3 收尾（段数 64）

| 任务 ID | 页面 | 段数 | 状态 | 备注 |
|---|---|---:|---|---|
| B3-1 | Tweaking.md | 3 | pending | 段数少但代码占比高 |
| B3-2 | Setting-up-JSON-logging-with-spdlog.md | 12 | pending | |
| B3-3 | How-to-use-spdlog-in-DLLs.md | 6 | pending | |
| B3-4 | Language-bindings.md | 10 | pending | |
| B3-5 | Integrating-into-Eclipse-IDE.md | 8 | pending | |
| B3-6 | Makefile-Only.md | 6 | pending | |
| B3-7 | Note-for-adding-sinks-on-the-fly.md | 8 | pending | |
| B3-8 | Preventing-child-processes-from-inheriting-open-log-files.md | 2 | pending | |
| B3-9 | Preventing-undefined-thread-ids-in-child-processes.md | 3 | pending | |
| B3-10 | Windows-unicode-filenames.md | 4 | pending | |
| B3-11 | Reference-documentation-using-Doxygen.md | 1 | pending | |
| B3-12 | 3.-Custom-formatting).md | 1 | pending | 上游遗留垃圾页（Envoy 日志格式串粘贴事故页）：1 段按"代码类内容逐字保留"处理并登记批次报告 |

## 已完成（M1 基建）

- [x] M0 init commit（计划/DR/启动提示词入库，Decision: DR-001..003）
- [x] M1a wiki ls-remote 复确认（HEAD 15090480，直连可达）
- [x] M1b 同步管线 + sync --init（28 文件 / 461 段入库）+ 计划 §7.1 回填 + 本看板创建
- [x] M1c 脚本 + tests 88/88 全绿（含 test_fix_links_wiki.py）
- [x] M1d glossary 28 条 + banned 8 条 + style-guide 初版
- [x] M1e mkdocs + 3 workflow + jieba 中文检索实测 PASS（10/10 token）
- [x] M1f gh repo create + push + Pages 占位站（HTTP 200）+ 3 workflow CI 冒烟全绿
- [x] M1g handoff + progress + 验收汇报（等用户确认进 M2）

## 硬性纪律（每批适用）

- agent 输入 = 目标文件 + glossary + style-guide + 上游原文路径；prompt 注入术语表/风格规则/占位符保护/硬性规则（代码块/内联代码/API 名/链接目标不译，中英文间空格，全角标点，语义等价不增不减）；完成后自跑 validate 单文件模式必须全绿。
- 门禁链 = validate_translation（术语/占位符/结构/断链）+ pytest + mkdocs build 冒烟，全部退出码生效，禁止 `|| true`。
- 每批次一个 squash commit；批次报告落盘 reports/（含实际 token 消耗）；收尾更新 handoff-latest.md 与 reports/progress.md（自动生成禁手改）。
- 上下文过半或里程碑收尾（M1/M2 各批）主动建议开新会话并给启动提示词（docs/新会话启动提示词.md）。
