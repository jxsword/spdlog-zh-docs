# M3 里程碑报告（全量 sweep + tag v1.0 + 增量演练）

> 日期：2026-11-20 ｜ 基线：wiki@15090480 + docs-index@3cd4a76（未动）｜ 状态：**M3 完成**
> 执行模式：编排方会话内执行（GLM，零 subagent 派发；token 无 subagent 计量项）

## 1. 全量 sweep（三项全绿）

### 1.1 术语一致性终检（Sweep-1）

**B3 提议 12 条复核**：逐条 grep 源文/译文对账，全部一致，无需词级修正：

| # | en | zh | 源文散文命中 | 复核结论 |
|---|---|---|---|---|
| 1 | log entry | 日志条目 | FAQ ×1、JSON ×1 | Sinks/JSON 其余命中在代码注释内（逐字保留，正确） |
| 2 | log transaction | 日志事务 | Language-bindings ×1 | 首现括注「日志事务（log transaction）」到位 |
| 3 | thread local storage | 线程局部存储 | Preventing-undefined ×1 | 首现括注到位；Tweaking 命中在代码注释内 |
| 4 | severity | 严重级别 | Flush-policy ×1、JSON ×1 | 标题与正文一致；无 严重性/严重度 变体 |
| 5 | shared library | 共享库 | CMake ×2、FAQ ×3、DLLs ×1 | 全部一致 |
| 6 | workaround | 变通方法 | DLLs ×1 | QuickStart 命中在代码注释内 |
| 7 | copy constructor | 拷贝构造函数 | Note-sinks ×1 | 一致 |
| 8 | RHS | 右侧（RHS）对象 | Note-sinks ×1 | 缩写括注形式一致 |
| 9 | child process | 子进程 | index ×2、Preventing-child ×1 | Tweaking 命中在代码注释内 |
| 10 | file descriptor | 文件描述符 |散文命中 | Preventing-child ×1；Tweaking 命中在代码注释内 |
| 11 | function signature | 函数签名 | Doxygen ×1 | 一致 |
| 12 | sync mode | 同步模式 | Language-bindings ×1 | docs-index「Synchronous mode」→ 同步模式，同条适用 |

- 关键预检：check 5 为子串匹配，"asy**nc mode**" 含 "sync mode" 子串——全库散文仅 Language-bindings.md 命中且译文已含「同步模式」，加表后零新增告警（实测验证）。
- 12 条已入 `config/glossary.yml`（35→**47 条 approved**，banned 8 条不变），aliases 备注代码注释豁免语境。
- **validate 全量对账：exit 0，告警维持 27 条零新增**（26 页头 URL 计数 + 1 flush 子串误报，与 B3 基线逐条一致）。

### 1.2 断链复查（Sweep-2）

`memgate python3 scripts/linkcheck.py --check` 双通道实测（2026-11-20）：

| 通道 | 结果 |
|---|---|
| 直连 | 71/72 ok；1 条 http-500 |
| 代理（192.168.33.1:10808） | 71/72 ok；1 条 http-500 |

唯一异常：`https://internal.dunescience.org/doxygen/namespacespdlog.html`（2 处引用，zh+source 的 Doxygen 页）。
人工复核：HEAD 500 但 GET 303 → Fermilab SSO 登录页——**上游原文自带链接，目标为 DUNE 协作组内网 Doxygen（SSO 登录墙后）**，属上游固有状态而非本工程断链；按「链接目标不译/不增不减」如实保留。登记：已复核接受。

### 1.3 构建基线确认（Sweep-3）

`memgate .venv/bin/mkdocs build --site-dir /tmp/m3-site-build`：exit 0，**0 内容告警 + 1 环境通告**（Material Zensical 迁移提示，与 B3 基线一致）；26 个导航页全部产出（28 文件 − _Sidebar/_Footer 豁免）。

### 1.4 门禁基线亲跑复现

- validate 全量 exit 0（27 告警逐条与 handoff 一致）
- pytest **101/101**（0.68s）
- check_alignment 全量 exit 0

## 2. tag v1.0

- 前置确认：README TASL 四要素（Title/Author/Source×2/License）✓、README 非官方声明 ✓、mkdocs 页脚 copyright 非官方声明 ✓、LICENSE_TRANSLATION.md（TASL + 基线锚定）✓。
- sweep commit `1f72b16`（glossary 12 条转正）后打 **annotated tag `v1.0`**（tag 对象 `07fe6b1`）并推送；`git ls-remote --tags origin` 实测可见。
- main push 后 deploy workflow 自动发布成功（run 44567428630）。

## 3. 增量演练（端到端全链路走通）

**模拟上游**：本地仓库 `file:///tmp/drill-wiki`（真 wiki@15090480 克隆之上 1 个模拟 commit `0d3a26ed`「Updated Default logger (markdown)」），不动真 wiki。

| 环节 | 证据 |
|---|---|
| 变更设计 | Default-logger.md M 型：修改 1 段 + 追加 1 段（含页间链接 `[QuickStart](QuickStart)`） |
| sync 检测 | `memgate bash scripts/sync_upstream.sh --since 15090480… --repo file:///tmp/drill-wiki --skip-docs-index` → **exit 1**（有变更需翻译）；`Default-logger.md M (+2/-1 segs, kept 3)` |
| 增量语义 | state 未变 3 段保持 translated；仅 2 段转 pending；source/ 更新且 `[QuickStart](QuickStart)` 规范化为 `QuickStart.md`；sync 报告 `reports/sync-2026-11-20-0d3a26ed.md` 落盘 |
| 增量翻译 | 会话内翻译 2 段（1 修改 + 1 新增）→ `mark_translated` 2 段 → translated |
| 门禁 | 四件全绿：check_alignment 0 / validate 0（27 告警不变）/ pytest 101/101 / mkdocs build 0 内容告警 |
| PR 流程 | 分支 `drill/sync-2026-11-20` push → **PR #1** 创建 → CI validate ✓（run 44568031601）→ **关闭不合并**（模拟上游不入真基线）→ 分支已删除 |
| main 完好 | main `upstream_commit=15090480…`、Default-logger 4 段全 translated、与 origin/main 一致 |

## 4. 演练发现的 2 个 workflow bug（已修复，随收尾 commit 入库）

1. **破坏性附件镜像**：`sync_upstream.sh` 步骤 3 `rm -rf zh/assets` 会误删 zh 侧自备资产（`zh/assets/logos/jetbrains-variant-4.svg`，B2 为 docs-index 手工补入；上游 docs2.x 附件不经 fetch_docs_index 同步）。真实 auto Sync PR 会静默删掉 docs-index 的 JetBrains logo。→ 改为**增量镜像**（只增不删，上游同名覆盖；zh-only 资产保留）。站点渲染本身无恙（material 构建时重写 `src` 为 `assets/...`，实测图片可达）。
2. **auto PR 漏提交 state**：`sync-upstream.yml` `git add source zh reports` 未包含 `.translation-state.json`——state 是增量迁移依据，漏提交会导致每周重复开同一 Sync PR。→ 补入 git add 与 porcelain 检查。

## 5. sync-upstream 自动 PR 模式确认（计划 §6.6）

- 解锁机制：workflow 以 `git ls-remote --tags origin refs/tags/v1.0` 判定，tag 推送即解锁，无需改 workflow。
- 实测：`gh workflow run sync-upstream.yml`（run 44568219100）全步骤 success，Detect 步骤判定 changed=false（上游无变更），Issue-only 与 Auto sync PR 两步正确 skipped。
- 与 §3 演练联合成立：真实上游变更出现时，workflow 将走「sync → branch `sync/<date>` → PR」路径，其内部命令与演练验证的 sync_docs.py --since 完全同一路径。

## 6. 维护态入口（M3 后）

- **M4 README 翻译：仅用户明确要求时启动**（DR-001，看板排最末）。
- 常态运转：sync-upstream 每周一 02:30 UTC 自动检测；上游变更 → 自动 Sync PR → 增量翻译变更段 → 四门禁 → squash merge（PR 内补译）。
- 基线切换自此解禁：下次真实 sync 合并后，state.upstream_commit 随 PR 前进，基线记录见 sync 报告 `reports/sync-<date>-<sha8>.md`。
