# B1 批次报告（T-001 ~ T-005）

> 日期：2026-11-19 ｜ 基线：wiki@15090480 + docs-index@3cd4a76（未动）｜ 状态：**批次完成，待用户验收**
> 执行模式：会话内 zcode agent（GLM-5.3-Flash），编排方 = 主会话；并发上限 2（同页串行、跨页并行）实际执行 3 波。

## 1. 结果总览

| 任务 | 页面 | 段数 | agent token（实测） | 门禁 |
|---|---|---:|---:|---|
| T-001 | index.md（Home） | 4 | 321,625 | 全绿 |
| T-002 | QuickStart.md | 25 | 427,636 | 全绿 |
| T-003 | CMake.md | 37 | 380,869（初翻 83,022 + 规则补发修复 297,847） | 全绿 |
| T-004 | Custom-formatting.md | 24 | 544,571 | 全绿 |
| T-005 | Sinks.md | 67 | 1,757,757 | 全绿 |
| 校对抽检 | 5 页 | 94 段抽检 | 414,017 | 0×P0 / 1×P1 / 5×P2，已修复 |
| **合计** | **5 页** | **157** | **3,846,475** | |

- state 进度：157/461 段 translated（34.1%），progress.md 已重生成。
- 主会话（编排方：prompt 组装/复验/state 更新/报告）token 未计入上表（无逐任务观测手段）。

## 2. 门禁结果（全部退出码生效，无 `|| true`）

| 门禁 | 结果 | 说明 |
|---|---|---|
| check_alignment.py（新增工具） | 5/5 OK，exit 0 | 15 条告警全部复核接受：CF 10 条为分段器把纯代码行误判为段落（本就必须逐字保留）；Sinks 5 条为纯 API 名段落（`**rotating_file_sink**` 等） |
| validate_translation.py 全量 | exit 0 | 告警 6 条，见 §5 已知告警清单 |
| pytest | **95/95**（88 旧 + 7 新回归） | |
| `memgate mkdocs build` | exit 0，**零 error**，18 warning | 18 条全部为 index.md 导航指向 B2/B3 未落地页（B2/B3 落地后自动消除）；对照 M1 基线（占位站 0 warning）新增即为上述链接告警，无其他类别 |
| 断链 | 0（validate 6c 相对链接检查 + build 链接检查双确认；zh 内相对链接回退 source/ 解析） | |
| 术语黑名单 | 0 命中 | 抽检 agent 全量 grep 复核 |
| 占位符还原 | 100%（无 PROTECTED_* 残留） | |

构建产物在 /tmp/spdlog-zh-docs-site（仓库树外）；`> 原文：` 署名行 5 页各 1 条，均实测可达
（通道：curl 经代理 http://192.168.33.1:10808，2026-11-19；直连 github.com 超时按全局规则回退）。

## 3. 抽检（计划 §6.5：第二校对 agent ≥10%）

实际抽检 **94 段**（约 60%）：5 页全部散文段落 + 全部标题 + pattern 表 42 行含义列 + Aligning 两表 6 行。
机器硬核对（代码块逐字节 / 链接目标 / 表格 flag 与 example 列）全部一致。

- P0 语义错误：**0**
- P1 术语/风格违规：**1** —— CMake.md "你"→"您"（已修复）
- P2 可读性/微调：**5** —— QuickStart 句末补句号、Sinks "若是…的话"叠用、Sinks "**stdout_sink/stderr_sink with colors**" 残留英文（→"（带颜色）"）、Sinks "负责刷新的" 增译删除、qt_sink "from→到" 方向（上游疑笔误，按示例语义保持，不加译注）——前 4 项已修复，第 5 项记录不改
- 术语横评：5 页统一（日志记录器/接收器/格式化器/轮转/刷新/日志级别/线程安全等），首现括注规范

## 4. 执行事件与修复记录（透明留痕）

1. **T-003 派发 prompt 损坏**：CMake agent 收到的 prompt 中途截断并混入无关内容，缺失风格规则段；
   agent 在缺规则下翻译了代码块内注释（1 个代码块被改）。处置：SendMessage 补发完整规则 → agent
   恢复代码块逐字一致 → check_alignment/validate 全绿。教训沉淀：**长内联 prompt 有传输损坏风险，
   后续批次改用「agent 自读 config/glossary.yml + style-guide.md」的短 prompt 模式**（T-004 起已切换）。
2. **T-005 派发 prompt 损坏（更严重）**：Sinks agent 仅收到残句（仓库路径为占位符）。该 agent 从
   看板/git 历史自行推断任务并完成翻译、自跑 mark_translated + validate + pytest + build。
   编排方**独立复验全部声明**：check_alignment OK、validate exit 0、state 157 段无误、git 状态吻合，
   复验全部通过后才进入收尾。教训：子代理声明一律不可信，门禁以编排方实测为准。
3. **validate 门禁解析缺陷修复（2 处，含 7 条回归测试）**：Custom-formatting.md 实测暴露——
   a) CommonMark 允许 N≥2 反引号作行内代码界定符，单反引号朴素正则会把两个 ```span``` 之间的残余
   反引号虚构成假 span，span 间连词正常翻译后误报 multiset 不一致 → 新增
   `normalize_inline_spans`（行内多反引号 span 规范化，源/译对称应用，行首围栏不受影响）；
   b) 源文自带的未配对伪标签 `<my_formatter_flag>` 使 L2 配对检查结构性必挂 → 配对检查豁免
   源文本就失衡的标签名（L1 类型计数不豁免，译文弄断已配对标签仍报错）。
   修复后 CF exit 0，其余 4 页复验无副作用；**分级判断：轻量决策**（守卫语义不变、修的是假阳性、
   有测试锚定、可 revert），未走 DR 流程，如不认可可直接回滚该 commit 内两处。
4. **新增工具脚本**：`scripts/check_alignment.py`（实现计划 §6.5「结构对等 100%」机检：双视图
   —— 围栏块逐字节 + segment_md 同源分段结构对齐 + 漏译停用词检测 + 分隔线/图片 URL/表格行守卫；
   全量模式自动跳过未开工页）；`scripts/mark_translated.py`（state 段落 pending→translated，
   保留源文 hash 供增量迁移，写前 .bak）。均为计划内步骤的实现补齐，轻量决策。
5. **T-005 未拆分子任务**：单 agent 完成（67 段 / 278 行在单 agent 能力范围内，且跨段术语一致性
   更优）；用户任务书中"可拆 2–3 个串行子任务"按可选项处理。
6. **原文链接注入机制（计划 §6.9）**：由编排方统一注入 `> 原文：[页名](wiki URL)` 引用行（有 H1
   的页在 H1 后，无 H1 的页在文件头），agent 不生成；check_alignment 分段前剥离该行。
7. **抽检后 glossary flush 告警**：删除 Sinks "负责刷新的" 增译后，validate 术语启发式产生 1 条
   告警（源文 flush 仅以 flush_(..) 函数名形式出现，刷新概念未在该页正文讨论）——接受并留痕。

## 5. 已知告警清单（全部为 warning，exit 0）

| 告警 | 数量 | 定性 |
|---|---:|---|
| `URL count mismatch`（5 页各 +1） | 5 | by-design：页头"原文"链接（计划 §6.9） |
| mkdocs build：index.md 导航目标缺失 | 18 | by-design：B2/B3 页面未落地，落地后消除 |
| Sinks flush 术语启发式 | 1 | 见 §4.7 |
| check_alignment 15 条 identical 段 | 15 | 已复核：伪段落代码行 + 纯 API 名段落 |

## 6. 术语提议（待 glossary PR 流程，B2 前复核）

- pattern string → 模式字符串；pattern flags → 模式标志；source location flags → 源位置标志（CF agent 提议）
- 通用译法参考：basename → 基名、epoch → 纪元、race condition → 竞态条件、deep copy → 深拷贝、pretty-print → 美化打印（CF agent）
- QuickStart 页对 glossary "async logger" 的适配：源文用词为 asynchronous logger，首现括注按源文原文处理

## 7. B2 入口

- 范围 238 段：Creating-loggers 29 / Logger-registry 15 / Asynchronous-logging 34 / Thread-Safety 12 /
  Flush-policy 13 / Error-handling 11 / Default-logger 4 / FAQ 35 / docs-index 85（RTD 单页）
- 复用本批沉淀：短 prompt 模式（自读 config）→ check_alignment 自检 → 编排方复验 + mark_translated
  → validate --file → 注入原文链接 → 批次 squash commit
- mkdocs build 告警基线：18 条 index 导航（随 B2/B3 递减至 0）
