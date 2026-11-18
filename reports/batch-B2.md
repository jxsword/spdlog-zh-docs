# B2 批次报告（T-006 ~ T-009，8 wiki 页 + docs-index）

> 日期：2026-11-19 ｜ 基线：wiki@15090480 + docs-index@3cd4a76（未动）｜ 状态：**批次完成，待用户验收**
> 执行模式：会话内 zcode agent（GLM）；原计划并发 2，**实测账户并发上限为 1**（两次并行派发被"user concurrency limit exceeded"拒绝），改为全串行；T-009 docs-index 由编排方在会话内直接翻译（子代理基础设施不稳 + 本页风险最高，见 §4.3）。

## 1. 结果总览

| 任务 | 页面 | 段数 | agent token（实测） | 门禁 |
|---|---|---:|---:|---|
| T-006 | Creating-loggers.md | 29 | 459,207 | 全绿（含锚点 attr_list） |
| T-007 | Logger-registry.md | 15 | 388,848 | 全绿 |
| T-008 | Asynchronous-logging.md | 34 | 462,518 | 全绿 |
| B2-4 | Thread-Safety.md | 12 | 447,190 | 全绿 |
| B2-5 | Flush-policy.md | 13 | 294,073 | 全绿 |
| B2-6 | Error-handling.md | 11 | 324,436 | 全绿 |
| B2-7 | Default-logger.md | 4 | 309,940 | 全绿 |
| B2-8 | FAQ.md | 35 | 739,219（agent 中断前；残留 4 段假阳性由 checker 修复消除，译文实际完整） | 全绿 |
| T-009 | docs-index.md | 85 | 会话内翻译（编排方完成，无 subagent 计量） | 全绿（一次通过） |
| 校对抽检 | FAQ/docs-index/Async 3 页 | 66 段抽检 | 433,250 | 0×P0 / 1×P1 / 3×P2，已修复 |
| **合计** | **9 页** | **238** | **subagent 3,858,681** | |

- state 进度：**395/461 段 translated（85.7%）**，progress.md 已重生成。
- 主会话编排 token 未计入（无逐任务观测）；两个被并发限制拒绝的派发消耗 0 token。

## 2. 门禁结果（全部退出码生效）

| 门禁 | 结果 |
|---|---|
| check_alignment（已开工 13 页全量） | 13/13 OK，exit 0；6 条告警全部复核接受（Sinks 5 条纯 API 名段落 + docs-index 徽章段，均无文案可译） |
| validate_translation 全量 | exit 0（黑名单 0、占位符 100%、断链 0） |
| pytest | **101/101**（95 + 6 新增 checker 回归） |
| `memgate .venv/bin/mkdocs build` | exit 0 零 error；warning **18 → 10**（10 条全部 = index 导航指向 B3 页，对账 22 链接 − 12 已落地 = 10；B3 后归零） |
| 原文链接 | 9 页各 1 条注入（有 H1 在 H1 后，无 H1 在文件头）；上游 URL 经代理实测 200（2026-11-19） |

## 3. 抽检（第二校对 agent）

抽 **66 段**（FAQ 全部标题+指定段 / docs-index tagline+Features 17 条+20 个小节标题+锚点 / Async 3 段）：

- P0 = 0
- P1 = 1：docs-index "用户定义回调" vs 同页"用户自定义类型/标志"不一致 → 已改"用户自定义回调"
- P2 = 3：① FAQ 首标题陈述句被译成问句（根因：编排方派发指令误写"问句式标题"，源文为陈述句）→ 已改"日志文件保持为空"；② runtime 译名横页不统一（运行时/运行期/运行期间）→ 记术语提议；③ "或编译使用"生硬 → 已改"或以编译方式使用"
- 术语横评：跨页一致；流水线许可行为确认 2 类（`{#id}` 锚点注入、JetBrains img src 路径修正）建议登记，避免后续抽检误报

## 4. 执行事件与修复记录

1. **并发上限实测为 1**：T-006 与 B2-4 首次并行派发均被 "user concurrency limit exceeded" 拒绝（0 token），补派/串行后成功。B2 全程改串行，仍满足"上限 2"纪律。
2. **FAQ agent 中断**：抽检前 agent 在自检循环中被 "Account request credential is unavailable" 切断（账户切换所致）。实测其译文已完整落盘（161 行全文翻译），残留 4 个 check_alignment"漏译"错误实为假阳性（见 §4.4），译文无缺漏。编排方独立复验全文后收编。
3. **T-009 会话内翻译**：docs-index（85 段 / 24 代码块 / 21 hr / 2 锚点 / 徽章 / JetBrains logo）由编排方直接翻译，一次通过对齐。理由：子代理两度中断 + 本页是 RTD 等价页风险最高 + 串行模式下会话内翻译无并行损失。
4. **check_alignment 围栏 span 豁免修复（含 6 条回归测试）**：FAQ 源文第 34 行以行内三反引号 span 开头（上游换行），误导行级分段器（segment_md）把围栏配对整体错位，真实代码行被判成"段落"触发漏译假阳性（4 error / 6 warning）。修复 = 漏译检测豁免落在 FENCE_RE 正则视图围栏 span 内的段落（正则视图配对正确：行内 span 同行自闭合；字节守卫不变）。**segment_md 本体未动**（hash 与 state/sync 绑定）。修复同时正确豁免了 CF 的 10 条同类伪段落告警（全量告警 15→6）。
5. **JetBrains logo 资产修正**：源文 `<img src="logos/…">` 相对路径在上游即断链（logo 在仓库根 `logos/` 而非 `docs/`，gh api tree 实证；RTD 同样坏图）。处置：经代理取 SVG 入 `zh/assets/logos/jetbrains-variant-4.svg`（4,689 B，raw 200 实测），zh 侧 src 改 `assets/logos/…`。与 sync 的 assets 镜像机制一致，站点自包含。已登记为流水线许可行为。
6. **FAQ 断链修复（本批唯一许可的链接目标变更）**：`[Discussion](/gabime/spdlog/discussions/2640)` 上游缺域名 → zh 补全 https URL。
7. **docs-index 本地化细节**：包管理器 12 条命令原文未动、冒号全角化；平台列表专名保留、顿号/全角括号本地化；2 个页内锚点用 attr_list `{#benchmarks}`/`{#log-to-qt-with-nice-colors}` 保链（mkdocs attr_list 已启用）。

## 5. 术语提议（待 glossary PR 流程，B3 前复核）

- user-defined → 用户自定义（P1 横评发现的缺口；现与 QuickStart"用户自定义对象"一致；与已有"用户定义字面量"条目复核取一）
- runtime → 运行时（横页不统一：运行时/运行期/运行期间）
- shared pointer → 共享指针（T-007）；worker thread → 工作线程、backing thread → 后台线程（T-008，二者原文有别）；message queue → 消息队列、queue slot → 槽位（T-008；注意与 banned"日志槽"区分语境）

## 6. B3 入口

- 范围 64 段 / 12 小页：Tweaking 3（代码占比高）/ Setting-up-JSON 12 / DLLs 6 / Language-bindings 10 / Eclipse 8 / Makefile-Only 6 / Note-for-adding-sinks 8 / Preventing-child×2 2 / Preventing-undefined×2 3 / Windows-unicode 4 / Doxygen 1 / `3.-Custom-formatting).md` 1（Envoy 事故页，代码类逐字保留 + 报告登记）
- 复用 B2 沉淀：串行派发（并发上限 1）、短 prompt、编排方独立复验、checker/validate 门禁、原文链接注入、批次收尾
- mkdocs build 告警基线：10 条 index 导航（B3 落地后归零）
