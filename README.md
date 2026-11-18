# spdlog 中文文档（spdlog-zh-docs）

spdlog 官方文档的社区中文翻译：覆盖 [gabime/spdlog wiki](https://github.com/gabime/spdlog/wiki) 全部页面与 [docs2.x 分支 docs/index.md](https://github.com/gabime/spdlog/blob/docs2.x/docs/index.md)（即 readthedocs 渲染内容）。

> **非官方声明**：本项目非 spdlog 官方项目；与官方英文文档可能存在滞后或出入，如有冲突以官方英文文档为准。译文问题请提 issue。

## 在线阅读

- 站点：<https://jxsword.github.io/spdlog-zh-docs/>（GitHub Pages，push main 自动发布）
- 进度：[docs/translation-board.md](docs/translation-board.md) ｜ 自动生成的 [reports/progress.md](reports/progress.md)

## 署名（TASL 四要素）

| 要素 | 内容 |
|---|---|
| Title | spdlog documentation 中文翻译 |
| Author | Gabi Melman and spdlog contributors |
| Source | https://github.com/gabime/spdlog/wiki ｜ https://github.com/gabime/spdlog/blob/docs2.x/docs/index.md |
| License | [MIT](LICENSE_TRANSLATION.md)（原文许可；译文以同许可发布） |

## 翻译基线锚定

- 基线：wiki@15090480 + docs-index@3cd4a76，锁定于 2026-11-19（对应 spdlog v1.17.0 时代）
- 上游变更由 sync-upstream workflow 每周检测；初译期（v1.0 tag 前）仅开 issue 记录（DR-003 基线锁定）

## 工程结构

| 路径 | 说明 |
|---|---|
| `source/` | 英文原文快照（只读，仅 sync 写入；wiki-link 已规范化为标准 md 链接） |
| `zh/` | 中文译文（与 source/ 同构；`Home` → `index` 作站点首页） |
| `.translation-state.json` | 段落级 hash 状态机（增量翻译的迁移依据） |
| `scripts/` | 同步/切分/保护/校验/报告管线（见各脚本 docstring） |
| `config/` | 术语表（glossary.yml，含禁用译名黑名单）与风格指南 |
| `docs/` | 翻译计划（权威规范）、decision_log、任务看板、交接文档 |

## 许可证

- 本仓库自身（脚本、译文、配置）：[MIT](LICENSE)（spdlog-zh-docs Contributors）
- 上游原文许可与署名：见 [LICENSE_TRANSLATION.md](LICENSE_TRANSLATION.md)
