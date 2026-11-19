# B3 批次报告（12 小页收尾，M2 全量完成）

> 日期：2026-11-19 ｜ 基线：wiki@15090480 + docs-index@3cd4a76（未动）｜ 状态：**批次完成，待用户验收**
> 执行模式：会话内 zcode agent（GLM），全程串行派发（并发上限 1，B2 实测沉淀）；`3.-Custom-formatting).md` 事故页由编排方会话内处置（计划 §7.1 补注）。

## 1. 结果总览

| 任务 | 页面 | 段数 | agent token（实测） | 门禁 |
|---|---|---:|---:|---|
| B3-1 | Tweaking.md | 3 | 440,503 | 全绿（代码块 114 行逐字节未动） |
| B3-2 | Setting-up-JSON-logging-with-spdlog.md | 12 | 328,321 | 全绿（5 围栏含弯引号逐字节） |
| B3-3 | How-to-use-spdlog-in-DLLs.md | 6 | 227,029 | 全绿（含段内 ```span```） |
| B3-4 | Language-bindings.md | 10 | 237,358 | 全绿 |
| B3-5 | Integrating-into-Eclipse-IDE.md | 8 | 326,955 | 全绿（`<br>`/编号/源文错位反引号保留） |
| B3-6 | Makefile-Only.md | 6 | 224,180 | 全绿 |
| B3-7 | Note-for-adding-sinks-on-the-fly.md | 8 | 394,557 | 全绿 |
| B3-8 | Preventing-child-processes-from-inheriting-open-log-files.md | 2 | 288,778 | 全绿 |
| B3-9 | Preventing-undefined-thread-ids-in-child-processes.md | 3 | 270,392 | 全绿（段内 ```span```） |
| B3-10 | Windows-unicode-filenames.md | 4 | 376,860 | 全绿（尾随空格保留） |
| B3-11 | Reference-documentation-using-Doxygen.md | 1 | 262,133 | 全绿 |
| B3-12 | 3.-Custom-formatting).md | 1 | 会话内处置（编排方，无 subagent 计量） | 全绿（1 段逐字保留） |
| 校对抽检 | 8 页定点抽 11 段（≈17%） | 11 | 296,121 | 0×P0 / 0×P1 / 1×P2，已修复 |
| **合计** | **12 页** | **64** | **subagent 3,673,187（翻译 3,377,066 + 抽检 296,121）** | |

- state 进度：**459/461 段 translated（99.6%）**——M1 2 + B1 157 + B2 238 + B3 64；仅剩 _Sidebar/_Footer 2 段 skipped（计划 §6.1 豁免）。progress.md 已重生成。
- 主会话编排 token 未计入（无逐任务观测）。

## 2. 门禁结果（全部退出码生效，编排方亲跑）

| 门禁 | 结果 |
|---|---|
| check_alignment 全量 | 26/26 页 OK，exit 0；6 条告警全部为 B1/B2 已复核接受项（Sinks 5 条纯 API 名段落 + docs-index 徽章段），**B3 页零新增告警** |
| validate_translation 全量 | exit 0；黑名单 0 命中、占位符还原 100%、断链 0；告警 27 条 = 26 条页头链接 URL 计数（许可行为）+ 1 条 `flush` 子串误报（见 §4.8，B1 期已存在） |
| pytest | **101/101** |
| `memgate .venv/bin/mkdocs build` | exit 0 零 error；**导航告警 10 → 0**（B3 页全部落地）；另 1 条为 Material 工具链 Zensical 迁移通告（环境级、非内容告警，`NO_MKDOCS_2_WARNING=1` 可静默，见 §4.7） |
| 原文链接 | 12 页各 1 条注入（事故页 URL 中 `)` 按 `%29` 编码，实测 200）；12 个上游 wiki URL 经代理全部实测 200（2026-11-19） |
| 站点收录 | /tmp 出树构建 31 项 = 28 内容页全部收录（含 `3.-Custom-formatting)`） |

## 3. 抽检（第二校对 agent，定点 11 段 ≈17%）

抽 11 处（Tweaking 2 / JSON 2 / DLLs 1 / Language-bindings 1 / Eclipse 1 / Note-sinks 1 / Preventing-undefined 1 + runtime 词级修复 2 处复检）：

- P0 = 0、P1 = 0
- P2 = 1：Sinks.md:53 词级修复后「在运行时创建时」双「时」连用、反事实语气弱化 → 已按建议改为「即使这些文件若是在运行时创建，本应早已被清理。」，CA/validate 复绿
- 术语横评：跨页一致；许可行为（文件名标注行保留、专有名词大小写规范化、跨围栏连读重组、省略号全角化）全部确认豁免

## 4. 执行事件与修复记录

1. **并发上限 = 1 复现成立**：全程串行派发 11 次，无一被拒；Tweaking agent 自纠 1 处漏空行（agent 自查发现，编排方 diff 独立确认）。
2. **术语转正 7 条入 glossary.yml**（batch-B2 §5 → handoff §3.5）：user-defined→用户自定义（与已有「用户定义字面量」条目并存不冲突，前者为通用语、后者为 C++ 固定术语）/ runtime→运行时 / shared pointer→共享指针 / worker thread→工作线程 / backing thread→后台线程 / message queue→消息队列 / queue slot→槽位（与 banned「日志槽」区分语境）。随转正做 **runtime 词级统一 3 处**：Sinks.md「运行期间」×2 →「运行时」、docs-index.md「运行期」→「运行时」（转正后 validate 对表内术语的提示性告警归零路径）。
3. **`3.-Custom-formatting).md` 事故页处置**（计划 §7.1 补注）：1 段 Envoy 日志格式串按代码类逐字保留（编排方 Write 落盘，`cmp` 确认逐字节一致）；zh 侧按全库惯例多 1 个 EOF 换行（源文无尾换行），不影响分段与门禁。URL 中 `)` 编码为 `%29`。
4. **Makefile-Only "Makefile"/"main.cpp" 散文行保留原样**：两行为代码围栏前的文件名标注（独立 paragraph 段），译成「Makefile 文件：」之类属增译；保留后行数位置不变，不触发漏译检测。
5. **专有名词大小写规范化**：python→Python、windows→Windows、unicode→Unicode（源文小写）；登记为许可行为，后续抽检豁免。
6. **编排方流程事件 ×2**（不影响产物）：a) diff 退出码 1（存在差异属预期）截断 `&&` 链导致 Preventing-child 页流水线中断，分步重跑完成；b) 仓库 hook 拒绝 Bash `cp` 直接写 zh 文件，改用 Write 工具落盘（安全闸正常工作）。
7. **mkdocs 新增 1 条 Zensical 迁移通告**：Material 9.8.1 构建时输出「Zensical 是后继者」的迁移提示（环境级通告，非内容告警）；内容告警（导航 10 条）已归零。
8. **validate `flush` 子串误报（B1 期已存在，登记）**：Sinks.md 正文 API 名 `flush_(..)` 命中术语 "flush" 子串，而 zh/Sinks.md 全文无其他「刷新」出现点 → 提示性告警；API 名必须保持英文，无实际可改项，维持告警不阻断（exit 0）。
9. **Doxygen 页源文语法瑕疵**（"You find check a reference documentation"）按语义等价译出，不逐字硬译；上游笔误（Eclipse 页 `C/C+ Build` 缺 +）按「不译原则」逐字保留。

## 5. 术语处置记录

- **转正（approved，7 条）**：见 §4.2；validate 全量复跑无新告警。
- **B3 新提议（待后续 PR 复核，未入表）**：log entry→日志条目、log transaction→日志事务（首现括注）、thread local storage→线程局部存储、severity→严重级别、shared library→共享库、workaround→变通方法、copy constructor→拷贝构造函数、RHS→右侧（RHS）对象、child process→子进程、file descriptor→文件描述符、function signature→函数签名、sync mode→同步模式。
- **人名/专名**：本批无新增 banned 命中；`async mode`/`log level` 等表内术语首现括注执行到位。

## 6. M3 入口（验收确认后启动）

- **全量 sweep**：术语一致性（含 §5 新提议复核入表）、断链复查（linkcheck 低频）、构建基线归零确认；
- **tag v1.0**：sweep 全绿后打 tag（README TASL 四要素已具备，页脚非官方声明在位）；
- **增量演练**：模拟上游改页端到端（变更检测→pending→增量翻译→PR），开启自动 sync PR 模式；
- 启动提示词已更新为 M3 版（docs/新会话启动提示词.md）。
