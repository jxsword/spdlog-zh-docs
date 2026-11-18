# spdlog 中文文档（非官方翻译）

> **非官方声明**：本项目是 spdlog 官方文档的社区中文翻译，非 spdlog 官方项目；与官方英文文档可能存在滞后或出入，如有冲突以官方英文文档为准。
> 原文：[gabime/spdlog wiki](https://github.com/gabime/spdlog/wiki) ｜ [docs2.x docs/index.md](https://github.com/gabime/spdlog/blob/docs2.x/docs/index.md)（翻译基线：wiki@15090480，锁定于 2026-11-19；对应 v1.17.0 时代）。

## 项目状态

翻译工作按批次进行中，进度看板见仓库 [translation-board.md](https://github.com/jxsword/spdlog-zh-docs/blob/main/docs/translation-board.md) 与自动生成的 [progress.md](https://github.com/jxsword/spdlog-zh-docs/blob/main/reports/progress.md)。

## 关于 spdlog

spdlog 是一个快速的 C++ 日志库，仅头文件（header-only）即可使用。核心对象是日志记录器（logger），每条日志消息经由日志记录器写入所挂接的接收器（sink）：

- 语法直观，开箱即用
- 支持多种日志级别（trace / info / warn / error / critical）
- 模式格式化器（pattern formatter）可自定义日志格式
- 内置轮转文件、按日文件、控制台等多种接收器（sink）
- 异步模式：线程池 + 环形缓冲区 + 溢出策略
- 线程安全，支持回溯（backtrace）与错误处理器（error handler）

本页为占位页；M2 批次将翻译 wiki 的 Home 页并替换本页内容。
