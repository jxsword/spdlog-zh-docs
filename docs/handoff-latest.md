# 会话交接文档（handoff-latest）

> 更新: 2026-11-19 ｜ 里程碑: **M2 全量完成（B3 收官），待用户验收** ｜ 下一阶段: **M3（验收确认后启动）**
> 本文件是每批次/sync 收尾更新的唯一交接入口；新会话开工前**必读**本文件 + 计划 §6/§7.1 + reports/batch-B3.md。

## 1. 状态快照

- **远程仓库**: https://github.com/jxsword/spdlog-zh-docs （main 已推送至 B2 squash commit；B3 squash commit 待验收后推送/已推送以 git log 为准）；站点 https://jxsword.github.io/spdlog-zh-docs/
- **CI**: validate / deploy / sync-upstream 三 workflow；B3 推送后 deploy 自动发布 28 页中文站全量
- **基线**: wiki@15090480 + docs-index@3cd4a76（B3 未动）；28 文件 / 461 段 = **459 translated（99.6%）** + 0 pending + 2 skipped（_Sidebar/_Footer，计划 §6.1 豁免）
- **门禁实测**（2026-11-19，编排方亲跑）: check_alignment 26/26 页 OK exit 0（6 老告警已复核接受）；validate 全量 exit 0（27 告警 = 26 页头链接计数 + 1 flush 子串误报，均许可/已登记）；pytest **101/101**；`memgate .venv/bin/mkdocs build` exit 0 零 error，**导航告警 10→0**（余 1 条 Material Zensical 环境通告，非内容）
- **抽检**: 第二校对 agent 定点 11 段（≈17%）：0×P0 / 0×P1 / 1×P2，已修复复绿
- **术语**: glossary 现 35 条 approved + 8 banned；B2 提议 7 条已转正（user-defined/runtime/shared pointer/worker thread/backing thread/message queue/queue slot），runtime 词级统一 3 处（Sinks ×2、docs-index ×1）
- zh/ 28 页全部为中文译文 + 页头 `> 原文：` 链接；事故页 `3.-Custom-formatting).md` 1 段逐字保留（URL `)` → `%29`）

## 2. B3 交付清单（全部入库）

- zh/ 12 页：Tweaking / Setting-up-JSON-logging / How-to-use-spdlog-in-DLLs / Language-bindings / Integrating-into-Eclipse-IDE / Makefile-Only / Note-for-adding-sinks-on-the-fly / Preventing-child×2 / Windows-unicode / Doxygen / `3.-Custom-formatting)`（逐字保留）
- state：64 段 translated（源文 hash 未动）；glossary.yml +7 条（含 note 双语术语并存说明）
- reports/batch-B3.md（含 token）+ progress 重生成 + 本文件 + 看板 + 启动提示词（M3 版）

## 3. B3 关键经验（增量，M3 必读；B1/B2 经验见 §4/§5）

1. **并发上限 = 1 复现成立**：B3 全程串行 11 次派发无一被拒；短 prompt 模式 + 真实路径无占位符未再发生 prompt 损坏。
2. **diff 退出码会截断 `&&` 链**：`diff` 有差异时退出码 1（预期），链式命令会静默中断后续 mark_translated/validate——流水线步骤用 `;` 分步跑或分开调用。
3. **仓库 hook 拒绝 Bash 直接写文件**（cp/重定向写 zh/ 或 config/ 会触发 Mimosa PreToolUse 拒绝）：文件落盘一律用 Write/Edit 工具。
4. **mkdocs 环境通告**：Material 9.8.1 构建输出 Zensical 迁移提示 1 条（`NO_MKDOCS_2_WARNING=1` 可静默）；内容告警基线已归零，后续对照以「0 内容告警 + 1 环境通告」为准。
5. **术语转正联动词级统一**：转正 runtime 后需同步统一既有页变体（运行期/运行期间→运行时），否则 validate 提示性告警残留；转正即跑全量 validate 对账。
6. **专有名词大小写规范化许可**（python→Python、windows→Windows、unicode→Unicode）与 **Makefile-Only 文件名标注行保留**登记为许可行为，抽检豁免。
7. **validate `flush` 子串误报**（Sinks.md 正文 API 名 `flush_(..)` 命中术语子串且 zh 全文无「刷新」）：无实际可改项，维持告警不阻断；若 M3 sweep 想消掉需改 checker 子串匹配（strip_code 已剥离代码，此处是散文内 API 名），收益低不推荐。

## 4. B2 经验（仍有效；B1 见 §5）

1. 子代理可能被凭据问题切断——先实测文件与门禁再补救；大页可直接会话内翻译（T-009 先例）。
2. check_alignment 假阳性：行内 ```span``` 开头的散文行（已修：围栏 span 豁免）；同类告警先查"该段是否在真实围栏内"。
3. 流水线许可行为：页头注入行 / `{#id}` 锚点 / assets 路径修正 / FAQ Discussion 域名补全 / 事故页逐字保留 / 文件名标注行保留 / 大小写规范化。
4. 派发 prompt 内绝不出现占位符路径。

## 5. B1 经验（仍有效）

1. 短 prompt 模式（agent 自读 config/glossary.yml + style-guide.md）。
2. 子代理声明一律不可信——门禁以编排方亲跑为准（check_alignment + validate + pytest + build）。
3. 代码块逐字节不动（含注释）；"不增不减"优先于术语启发式告警。
4. mkdocs 用 `.venv/bin/mkdocs`；退出码勿被管道吞掉（临时文件 + echo $?）。
5. site_dir=/tmp 出树；上游无 [[..]] 语法；测试不写仓库 reports/。
6. 工具链（2026-11-19 实测）：mkdocs 1.6.1 / material 9.8.1 / jieba 0.42.1 / pytest 9.0.2。

## 6. M3 入口（验收确认后启动）

- **全量 sweep**：① 术语一致性终检（B3 新提议 12 条复核入表，见 batch-B3 §5；全库 approved 术语扫描对账）；② 断链复查（linkcheck.py 低频跑一轮）；③ 构建基线确认（0 内容告警 + 1 环境通告）。
- **tag v1.0**：sweep 全绿后打 tag；README/页脚/署名已具备，无需新改动。
- **增量演练**：模拟上游改页端到端（fork wiki 改 1 页 → sync-upstream 检测 → pending → 增量翻译 → PR）；演练通过后开启自动 sync PR 模式（计划 §6.6）。
- M4（按需）：README 翻译，仅用户要求时启动。
- 启动提示词已更新为 M3 版（docs/新会话启动提示词.md）。

## 7. 硬性纪律（重申）

- 一切以计划文档为准；改架构/目录/工具链属重大决策（矩阵 + 用户确认 + decision_log）。
- 所有脚本/构建 memgate 包裹；构建产物出仓库树；source/ 只读；文件写入用 Write/Edit 工具（hook 拦 Bash 直写）。
- 门禁硬性化：全部退出码生效，禁止 `|| true`；门禁链 = check_alignment + validate_translation + pytest + mkdocs build。
- 每批次一个 squash commit；批次报告含实际 token；收尾更新 handoff/progress。
- 上下文过半或批次收尾主动建议开新会话并给启动提示词。
