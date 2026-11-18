# 会话交接文档（handoff-latest）

> 更新: 2026-11-19 ｜ 里程碑: **M2-B1 完成，待用户验收** ｜ 下一阶段: **M2 批次 B2（验收确认后启动）**
> 本文件是每批次/sync 收尾更新的唯一交接入口；新会话开工前**必读**本文件 + 计划 §5/§6/§7.1 + reports/batch-B1.md。

## 1. 状态快照

- **远程仓库**: https://github.com/jxsword/spdlog-zh-docs （main 已推送至 B1 squash commit）；站点 https://jxsword.github.io/spdlog-zh-docs/
- **CI**: validate（PR 门禁）/ deploy（push main 自动发布）/ sync-upstream（周一 cron）——M1 冒烟全绿；B1 推送后 deploy 自动发布 5 页中文站
- **基线**: wiki@15090480 + docs-index@3cd4a76（2026-11-19 锁定，B1 未动基线）；28 文件 / 461 段
- **翻译进度**: **157/461 段 translated（34.1%）**——B1 五页全部完成：index 4 / QuickStart 25 / CMake 37 / Custom-formatting 24 / Sinks 67
- **门禁实测**（2026-11-19）: check_alignment 5/5 OK；validate 全量 exit 0；pytest **95/95**；`memgate .venv/bin/mkdocs build` exit 0 零 error（18 warning = index 导航指向 B2/B3 未落地页，落地后消除）
- **抽检**: 第二校对 agent 抽 94 段（≈60%）：0×P0 / 1×P1 / 5×P2，已修复 5 处（详见 reports/batch-B1.md §3）
- **安全审计**: Mimosa 深度扫描 findingCount 0（静态边界；依赖离线通告 2 包/11 条仅记录）；封印 sha256:407963f7…
- zh/index.md 占位页已被 Home 译文替换（站点首页即为中文）

## 2. B1 交付清单（全部入库）

- zh/：index.md、QuickStart.md、CMake.md、Custom-formatting.md、Sinks.md（每页页头 1 条 `> 原文：` wiki 链接，编排方统一注入）
- state：157 段 translated（metadata.translator/translated_at 齐全；源文 hash 未动，增量迁移机制完好）
- **新增脚本**: scripts/check_alignment.py（计划 §6.5 结构对等机检：围栏块逐字节 + 同源分段结构对齐 + 漏译停用词检测；全量模式自动跳过未开工页）、scripts/mark_translated.py（pending→translated，写前 .bak）
- **validate 门禁修复**（含 7 条回归测试）: normalize_inline_spans（行内多反引号 span 规范化，源/译对称）+ 配对检查豁免源文失衡伪标签（L1 计数不豁免）。守卫语义不变，仅消除假阳性
- reports/batch-B1.md（含实际 token 消耗 3,846,475 subagent tokens）+ progress.md 重生成

## 3. B1 关键经验（坑位沉淀，B2/B3 必读）

1. **长内联 agent prompt 有传输损坏风险**：B1 两次事故（T-003 截断混入无关内容、T-005 只剩占位残句）。
   **B2 起固定短 prompt 模式**：让 agent 自读 config/glossary.yml + config/style-guide.md + source/ 原文，
   prompt 只给路径、页级注意事项、输出契约、自检命令（T-004 即此模式，零事故）。
2. **子代理声明一律不可信**：T-005 在 prompt 损坏下自行推断任务完成，其报告虽全部属实，但编排方
   仍独立复验了全部门禁后才收尾。复验动作 = 编排方亲跑 check_alignment + validate + pytest + build。
3. **validate 门禁修复留痕**：行内 ```` ```x``` ```` 与伪标签 `<my_formatter_flag>` 两处假阳性已修
   （见 §2），若用户不认可可直接 revert 该 commit 内对应改动。
4. **翻译守则再确认**：代码块逐字节不动（含代码内注释，T-003 曾误译已纠正）；"不增不减"优先级
   高于术语告警（Sinks 删"负责刷新的"后出现 flush 启发式告警，接受留痕，见 batch-B1 §4.7）。
5. **check_alignment 的告警语义**：paragraph 与源文 identical 且停用词≥3 = 漏译（error）；
   identical 但为纯 API 名/伪段落代码行 = warning（人工复核接受）。CF/Sinks 共 15 条 warning 均属后者。
6. **mkdocs build 用 `.venv/bin/mkdocs`**（裸 mkdocs 不在 PATH）；退出码勿被管道吃掉（`tail` 会
   吞 $?，用临时文件 + `echo $?` 或 PIPESTATUS）。
7. **工具链版本**（2026-11-19 实测）：mkdocs 1.6.1 / material 9.8.1 / jieba 0.42.1 / pytest 9.0.2。
8. M1 经验（§4 of 上一版）继续有效：site_dir=/tmp 出树；上游无 [[..]] 语法；fmt 逐字转录用子代理；
   测试不写仓库 reports/；sync_docs 修复史有回归测试锚定。

## 4. B2 入口（验收确认后启动）

- **批次 B2（238 段）**：Creating-loggers 29 / Logger-registry 15 / Asynchronous-logging 34 /
  Thread-Safety 12 / Flush-policy 13 / Error-handling 11 / Default-logger 4 / FAQ 35 / docs-index 85
- 执行流程（B1 沉淀版）: 短 prompt 派发 → agent 写 zh + 自跑 check_alignment → 编排方复验 +
  mark_translated + validate --file → 注入原文链接 → 复验 → 批次 squash commit → 抽检 → 收尾产物
- docs-index.md（85 段）是 RTD 单页，代码占比高、术语密集（user-defined literal/binary mode/event handler），
  建议排 B2 末位单独一个 agent
- 收尾产物：reports/batch-B2.md（含 token）+ progress + handoff + 看板勾选 + squash commit
- B1 启动提示词模板见 docs/新会话启动提示词.md（已更新为 B2 版）

## 5. 硬性纪律（重申，同计划 §6 + 用户任务书）

- 一切以计划文档为准（§7.1 清单与批次段数）；改架构/目录/工具链属重大决策（矩阵 + 用户确认 + decision_log）。
- 所有脚本执行/构建一律 memgate 包裹；构建产物出仓库树（site_dir=/tmp/spdlog-zh-docs-site）。
- agent 翻译并发上限 2（同页串行、跨页并行）；source/ 只读（仅 sync 写入）。
- 门禁硬性化：全部退出码生效，禁止 `|| true`；门禁链 = check_alignment + validate_translation + pytest + mkdocs build 冒烟。
- 每批次一个 squash commit；批次报告含实际 token 消耗；收尾更新本文件与 progress.md。
- 上下文过半或批次收尾主动建议开新会话并给启动提示词（docs/新会话启动提示词.md）。
- 本地构建产物永不入仓库树。
