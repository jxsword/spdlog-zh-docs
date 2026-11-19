# 会话交接文档（handoff-latest）

> 更新: 2026-11-20 ｜ 里程碑: **M3 完成（v1.0 已发布，进入维护态）** ｜ 下一阶段: **维护态（上游增量跟进）；M4 README 仅按需启动**
> 本文件是每批次/sync 收尾更新的唯一交接入口；新会话开工前**必读**本文件 + 计划 §6/§7 + reports/m3-report.md。

## 1. 状态快照

- **远程仓库**: https://github.com/jxsword/spdlog-zh-docs （main 已推送至 M3 sweep commit `1f72b16`）｜ 站点 https://jxsword.github.io/spdlog-zh-docs/
- **tag v1.0 已发布**（annotated，tag 对象 `07fe6b1` → commit `1f72b16`）；sync-upstream 自动 Sync PR 模式自此解锁
- **CI**: validate / deploy / sync-upstream 三 workflow；deploy 随 main push 自动发布
- **基线**: wiki@15090480 + docs-index@3cd4a76（M3 未动）；28 文件 / 461 段 = **459 translated（99.6%）** + 0 pending + 2 skipped（_Sidebar/_Footer，计划 §6.1 豁免）
- **门禁实测**（2026-11-20，编排方亲跑）: check_alignment 全量 exit 0；validate 全量 exit 0（27 告警 = 26 页头链接 + 1 flush 子串误报，均许可/登记）；pytest **101/101**；`memgate .venv/bin/mkdocs build` exit 0（**0 内容告警 + 1 Material Zensical 环境通告**）
- **术语**: glossary **47 条 approved** + 8 banned（M3 sweep 转正 B3 提议 12 条，validate 对账零新增告警）
- **外链**: 直连+代理双通道 71/72 ok；唯一异常 `internal.dunescience.org`（上游固有 Fermilab SSO 内网站点）已复核接受
- zh/ 28 页全部为中文译文 + 页头 `> 原文：` 链接；事故页 `3.-Custom-formatting).md` 1 段逐字保留（URL `)` → `%29`）

## 2. M3 交付清单（全部入库）

- sweep：glossary.yml +12 条（B3 提议复核转正）；sweep commit `1f72b16`
- tag v1.0：annotated tag 推送，README TASL/页脚/LICENSE_TRANSLATION 确认在位
- 增量演练端到端走通（模拟上游改 Default-logger 1 页 → sync 检测 M +2/−1 段 kept 3 → 增量翻译 2 段 → 四门禁 → PR #1 CI 绿 → 关闭不合并）；演练证据 reports/m3-report.md §3 + reports/sync-2026-11-20-0d3a26ed.md（随演练分支，未合并）
- workflow 双 bug 修复：sync_upstream.sh 破坏性镜像 → 增量镜像；sync-upstream.yml auto PR 补提交 .translation-state.json
- 自动 PR 模式实测：workflow_dispatch run 44568219100 全步骤 success
- reports/m3-report.md + 本文件 + 看板 + 启动提示词（维护态版）

## 3. M3 关键经验（增量；B1/B2/B3 经验仍有效，见 m3-report 与历史批次报告）

1. **演练即测试**：模拟上游改页暴露了 2 个真实 workflow bug（rm -rf 破坏性镜像会误删 zh 侧自备资产；auto PR `git add` 漏 state 文件会致每周重复开 PR）——已修复，后续真实 Sync PR 不再受影响。
2. **check 5 子串匹配预检**：术语转正前先排查英文术语是否为其他词的子串（"asy**nc mode**" ⊃ "sync mode"），逐文件确认译文含对应中文词，可零告警转正。
3. **HEAD 不可达 ≠ 断链**：linkcheck 用 HEAD 请求，部分站点拒 HEAD 返 5xx（dunescience GET 303→SSO）；逐条人工复核后再定性。
4. **PR 演练纪律**：模拟上游的 PR 必须**关闭不合并**（state.upstream_commit 会指向模拟 commit，合并将污染真基线并破坏下次 sync 的 `cat-file -e` 校验）。
5. mkdocs-material 构建时会重写 docs_dir 相对 `src="..."` 为 `assets/...`（B2 手工补入的 jetbrains logo 渲染正常，此机制已实测确认）。

## 4. B3 经验（仍有效；B2 见 §5，B1 见 §6）

1. **并发上限 = 1 复现成立**；短 prompt 模式 + 真实路径无占位符。
2. **diff 退出码会截断 `&&` 链**：流水线步骤用 `;` 分步或分开调用。
3. **仓库 hook 拒绝 Bash 直接写文件**：文件落盘一律用 Write/Edit 工具。
4. **mkdocs 环境通告**：0 内容告警 + 1 Zensical 通告为基线。
5. **术语转正联动词级统一**：先 grep 变体再改，改完全量 validate 对账。
6. **许可行为清单**（抽检豁免）：页头注入行 / `{#id}` 锚点 / assets 修正 / FAQ 域名补全 / 事故页逐字保留 / Makefile-Only 文件名行 / 大小写规范化。
7. **validate `flush` 子串误报**：维持告警不阻断，勿改 checker。

## 5. 维护态操作手册（上游增量跟进 SOP）

真实上游变更出现时（每周一自动或手动 `gh workflow run sync-upstream.yml`）：

1. workflow 开出 `sync/<date>` 分支 + Sync PR（含 source/ 更新、state pending 标记、sync 报告）；
2. 在 PR 分支上**增量翻译 pending 段**（小量会话内直译，大量按批次派发 agent），`mark_translated` 后跑四门禁；
3. 门禁全绿 → squash merge → deploy 自动发布；同步更新 handoff/progress/看板（如页面结构变化）；
4. 注意事项：镜像为增量式（zh 侧自备资产保留）；state 随 PR 提交（已修复）；历史遗留 archive/ 归档机制不变。
   - 手动增量（不经 CI）参考：`memgate bash scripts/sync_upstream.sh --since <state 中的 sha> --repo <wiki URL> --skip-docs-index`（退出码 0=无变更/1=有变更/2=错误）。

## 6. M4 入口（按需）

- **README 翻译：仅用户明确要求时启动**（DR-001，看板排最末）。
- 启动提示词已更新为维护态版（docs/新会话启动提示词.md）。
