> 原文：[Language bindings](https://github.com/gabime/spdlog/wiki/Language-bindings)

# 语言绑定
## Python
对于大小合理的日志消息（1000 字节以内），spdlog 完成单次日志事务（log transaction）所需的时间，约为 Python 标准日志记录器（FileLogger）所需时间的 **4%（启用异步模式）** 和 **7%（同步模式）**。
### 从 pypi.org 安装

`pip install spdlog`

### 源码
GitHub 仓库：[spdlog-python](https://github.com/bodgergely/spdlog-python)
### 特性

* 支持异步模式
* ConsoleLogger
* FileLogger
* DailyLogger
* RotatingLogger
* SyslogLogger
* LogLevels
* Sinks

缺失：
* 字符串格式化
