
# spdlog

> 原文：[docs/index.md（docs2.x 分支）](https://github.com/gabime/spdlog/blob/docs2.x/docs/index.md)


[![ci](https://github.com/gabime/spdlog/actions/workflows/linux.yml/badge.svg)](https://github.com/gabime/spdlog/actions/workflows/linux.yml)&nbsp;
[![ci](https://github.com/gabime/spdlog/actions/workflows/windows.yml/badge.svg)](https://github.com/gabime/spdlog/actions/workflows/windows.yml)&nbsp;
[![ci](https://github.com/gabime/spdlog/actions/workflows/macos.yml/badge.svg)](https://github.com/gabime/spdlog/actions/workflows/macos.yml)&nbsp;
[![Release](https://img.shields.io/github/release/gabime/spdlog.svg)](https://github.com/gabime/spdlog/releases/latest)

快速的 C++ 日志库

## 安装
```console
$ git clone https://github.com/gabime/spdlog.git
$ cd spdlog && mkdir build && cd build
$ cmake .. && cmake --build .
```

使用方法请参见示例 [CMakeLists.txt](https://github.com/gabime/spdlog/blob/v2.x/example/CMakeLists.txt)。

## 平台
* Linux、FreeBSD、OpenBSD、Solaris、AIX
* Windows（msvc、cygwin）
* macOS 
* Android

## 包管理器：
* Debian：`sudo apt install libspdlog-dev`
* Homebrew：`brew install spdlog`
* MacPorts：`sudo port install spdlog`
* FreeBSD：`pkg install spdlog`
* Fedora：`dnf install spdlog`
* Gentoo：`emerge dev-libs/spdlog`
* Arch Linux：`pacman -S spdlog`
* openSUSE：`sudo zypper in spdlog-devel`
* vcpkg：`vcpkg install spdlog`
* conan：`conan install --requires=spdlog/[*]`
* conda：`conda install -c conda-forge spdlog`
* build2：```depends: spdlog ^1.8.2```


## 特性
* 性能极快（参见下文[基准测试](#benchmarks)）。
* 仅头文件（header-only）或以编译方式使用
* 功能丰富的格式化，使用出色的 [fmt](https://github.com/fmtlib/fmt) 库。
* 异步模式（可选）
* [自定义](https://github.com/gabime/spdlog/wiki/3.-Custom-formatting)格式化。
* 多线程/单线程日志记录器。
* 多种日志目标：
  * 轮转日志文件。
  * 按日日志文件。
  * 控制台日志（支持颜色）。
  * syslog。
  * Windows 事件日志。
  * Windows 调试器（```OutputDebugString(..)```）。
  * 记录到 Qt 部件（[示例](#log-to-qt-with-nice-colors)）。
  * 可通过自定义日志目标轻松[扩展](https://github.com/gabime/spdlog/wiki/4.-Sinks#implementing-your-own-sink)。
* 日志过滤——日志级别可在运行期与编译期修改。
* 支持从 argv 或环境变量加载日志级别。

## 用法示例

#### 基本用法
```c++
#include "spdlog/spdlog.h"

int main() 
{
    spdlog::info("Welcome to spdlog!");
    spdlog::error("Some error message with arg: {}", 1);
    
    spdlog::warn("Easy padding in numbers like {:08d}", 12);
    spdlog::critical("Support for int: {0:d};  hex: {0:x};  oct: {0:o}; bin: {0:b}", 42);
    spdlog::info("Support for floats {:03.2f}", 1.23456);
    spdlog::info("Positional args are {1} {0}..", "too", "supported");
    spdlog::info("{:<30}", "left aligned");
    
    spdlog::set_level(spdlog::level::debug); // Set global log level to debug
    spdlog::debug("This message should be displayed..");    
    
    // change log pattern
    spdlog::set_pattern("[%H:%M:%S %z] [%n] [%^---%L---%$] [thread %t] %v");
    
    // Compile time log levels
    // define SPDLOG_ACTIVE_LEVEL to desired level
    SPDLOG_TRACE("Some trace message with param {}", 42);
    SPDLOG_DEBUG("Some debug message");
}

```
---
#### 创建 stdout/stderr 日志记录器对象
```c++
#include "spdlog/spdlog.h"
#include "spdlog/sinks/stdout_color_sinks.h"
void stdout_example()
{
    // create a color multi-threaded logger
    auto console = spdlog::stdout_color_mt("console");    
    auto err_logger = spdlog::stderr_color_mt("stderr");    
    spdlog::get("console")->info("loggers can be retrieved from a global registry using the spdlog::get(logger_name)");
}
```

---
#### 基础文件日志记录器
```c++
#include "spdlog/sinks/basic_file_sink.h"
void basic_logfile_example()
{
    try 
    {
        auto logger = spdlog::basic_logger_mt("basic_logger", "logs/basic-log.txt");
    }
    catch (const spdlog::spdlog_ex &ex)
    {
        std::cout << "Log init failed: " << ex.what() << std::endl;
    }
}
```
---
#### 轮转文件
```c++
#include "spdlog/sinks/rotating_file_sink.h"
void rotating_example()
{
    // Create a file rotating logger with 5 MB size max and 3 rotated files
    auto max_size = 1048576 * 5;
    auto max_files = 3;
    auto logger = spdlog::rotating_logger_mt("some_logger_name", "logs/rotating.txt", max_size, max_files);
}
```

---
#### 按日文件
```c++

#include "spdlog/sinks/daily_file_sink.h"
void daily_example()
{
    // Create a daily logger - a new file is created every day at 2:30 am
    auto logger = spdlog::daily_logger_mt("daily_logger", "logs/daily.txt", 2, 30);
}

```

---
#### 定期刷新
```c++
// periodically flush all *registered* loggers every 3 seconds:
// warning: only use if all your loggers are thread-safe ("_mt" loggers)
spdlog::flush_every(std::chrono::seconds(3));

```

---
#### 秒表
```c++
// Stopwatch support for spdlog
#include "spdlog/stopwatch.h"
void stopwatch_example()
{
    spdlog::stopwatch sw;    
    spdlog::debug("Elapsed {}", sw);
    spdlog::debug("Elapsed {:.3}", sw);       
}

```

---
#### 以十六进制记录二进制数据
```c++
// many types of std::container<char> types can be used.
// ranges are supported too.
// format flags:
// {:X} - print in uppercase.
// {:s} - don't separate each byte with space.
// {:p} - don't print the position on each line start.
// {:n} - don't split the output into lines.
// {:a} - show ASCII if :n is not set.

#include "spdlog/fmt/bin_to_hex.h"

void binary_example()
{
    auto console = spdlog::get("console");
    std::array<char, 80> buf;
    console->info("Binary example: {}", spdlog::to_hex(buf));
    console->info("Another binary example:{:n}", spdlog::to_hex(std::begin(buf), std::begin(buf) + 10));
    // more examples:
    // logger->info("uppercase: {:X}", spdlog::to_hex(buf));
    // logger->info("uppercase, no delimiters: {:Xs}", spdlog::to_hex(buf));
    // logger->info("uppercase, no delimiters, no position info: {:Xsp}", spdlog::to_hex(buf));
}

```

---
#### 多接收器日志记录器——各自使用不同的格式与日志级别
```c++

// create a logger with 2 targets, with different log levels and formats.
// The console will show only warnings or errors, while the file will log all.
void multi_sink_example()
{
    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    console_sink->set_level(spdlog::level::warn);
    console_sink->set_pattern("[multi_sink_example] [%^%l%$] %v");

    auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("logs/multisink.txt", true);
    file_sink->set_level(spdlog::level::trace);

    spdlog::logger logger("multi_sink", {console_sink, file_sink});
    logger.set_level(spdlog::level::debug);
    logger.warn("this should appear in both console and file");
    logger.info("this message should not appear in the console, only in the file");
}
```

---
#### 关于日志事件的用户自定义回调
```c++

// create a logger with a lambda function callback, the callback will be called
// each time something is logged to the logger
void callback_example()
{
    auto callback_sink = std::make_shared<spdlog::sinks::callback_sink_mt>([](const spdlog::details::log_msg &msg) {
         // for example you can be notified by sending an email to yourself
    });
    callback_sink->set_level(spdlog::level::err);

    auto console_sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
    spdlog::logger logger("custom_callback_logger", {console_sink, callback_sink});

    logger.info("some info log");
    logger.error("critical issue"); // will notify you
}
```

---
#### 异步日志记录
```c++
#include "spdlog/async.h"
#include "spdlog/sinks/basic_file_sink.h"
void async_example()
{
    // TODO       
}

```

---
#### 用户自定义类型
```c++
template<>
struct fmt::formatter<my_type> : fmt::formatter<std::string>
{
    auto format(my_type my, format_context &ctx) const -> decltype(ctx.out())
    {
        return format_to(ctx.out(), "[my_type i={}]", my.i);
    }
};

void user_defined_example()
{
    spdlog::info("user defined type: {}", my_type(14));
}

```

---
#### 日志模式中的用户自定义标志
```c++ 
// Log patterns can contain custom flags.
// the following example will add new flag '%*' - which will be bound to a <my_formatter_flag> instance.
#include "spdlog/pattern_formatter.h"
class my_formatter_flag : public spdlog::custom_flag_formatter
{
public:
    void format(const spdlog::details::log_msg &, const std::tm &, spdlog::memory_buf_t &dest) override
    {
        std::string some_txt = "custom-flag";
        dest.append(some_txt.data(), some_txt.data() + some_txt.size());
    }

    std::unique_ptr<custom_flag_formatter> clone() const override
    {
        return std::make_unique<my_formatter_flag>();
    }
};

void custom_flags_example()
{    
    auto formatter = std::make_unique<spdlog::pattern_formatter>();
    formatter->add_flag<my_formatter_flag>('*').set_pattern("[%n] [%*] [%^%l%$] %v");
    spdlog::set_formatter(std::move(formatter));
}

```

---
#### 自定义错误处理器
```c++
void err_handler_example()
{
    // can be set globally or per logger(logger->set_error_handler(..))
    spdlog::set_error_handler([](const std::string &msg) { spdlog::get("console")->error("*** LOGGER ERROR ***: {}", msg); });
    spdlog::get("console")->info("some invalid message to trigger an error {}{}{}{}", 3);
}

```

---
#### syslog
```c++
#include "spdlog/sinks/syslog_sink.h"
void syslog_example()
{
    std::string ident = "spdlog-example";
    auto syslog_logger = spdlog::syslog_logger_mt("syslog", ident, LOG_PID);
    syslog_logger->warn("This is warning that will end up in syslog.");
}
```
---
#### Android 示例
```c++
#include "spdlog/sinks/android_sink.h"
void android_example()
{
    std::string tag = "spdlog-android";
    auto android_logger = spdlog::android_logger_mt("android", tag);
    android_logger->critical("Use \"adb shell logcat\" to view this message.");
}
```

---
#### 从环境变量或 argv 加载日志级别

```c++
#include "spdlog/cfg/env.h"
int main (int argc, char *argv[])
{
    spdlog::cfg::load_env_levels();
    // or from the command line:
    // ./example SPDLOG_LEVEL=info,mylogger=trace
    // #include "spdlog/cfg/argv.h" // for loading levels from argv
    // spdlog::cfg::load_argv_levels(argc, argv);
}
```
之后您就可以：

```console
$ export SPDLOG_LEVEL=info,mylogger=trace
$ ./example
```


---
#### 日志文件打开/关闭事件处理器
```c++
// You can get callbacks from spdlog before/after a log file has been opened or closed. 
// This is useful for cleanup procedures or for adding something to the start/end of the log file.
void file_events_example()
{
    // pass the spdlog::file_event_handlers to file sinks for open/close log file notifications
    spdlog::file_event_handlers handlers;
    handlers.before_open = [](spdlog::filename_t filename) { spdlog::info("Before opening {}", filename); };
    handlers.after_open = [](spdlog::filename_t filename, std::FILE *fstream) { fputs("After opening\n", fstream); };
    handlers.before_close = [](spdlog::filename_t filename, std::FILE *fstream) { fputs("Before closing\n", fstream); };
    handlers.after_close = [](spdlog::filename_t filename) { spdlog::info("After closing {}", filename); };
    auto my_logger = spdlog::basic_logger_st("some_logger", "logs/events-sample.txt", true, handlers);        
}
```

---
#### 替换默认日志记录器
```c++
void replace_global_logger_example()
{
    auto new_logger = spdlog::basic_logger_mt("new_global_logger", "logs/new-default-log.txt", true);
    spdlog::set_global_logger(new_logger);
    spdlog::info("new logger log message");
}
```

---
#### 以美观的颜色记录到 Qt {#log-to-qt-with-nice-colors}
```c++
#include "spdlog/spdlog.h"
#include "spdlog/sinks/qt_sinks.h"
MainWindow::MainWindow(QWidget *parent) : QMainWindow(parent)
{
    setMinimumSize(640, 480);
    auto log_widget = new QTextEdit(this);
    setCentralWidget(log_widget);
    int max_lines = 500; // keep the text widget to max 500 lines. remove old lines if needed.
    auto logger = spdlog::qt_color_logger_mt("qt_logger", log_widget, max_lines);
    logger->info("Some info message");
}
```

---
## 基准测试 {#benchmarks}

以下是在 Ubuntu 64 位、Intel i7-4770 CPU @ 3.40GHz 上完成的部分[基准测试](https://github.com/gabime/spdlog/blob/v2.x/bench/bench.cpp)：

#### 同步模式
```
[info] **************************************************************
[info] Single thread, 1,000,000 iterations
[info] **************************************************************
[info] basic_st         Elapsed: 0.17 secs        5,777,626/sec
[info] rotating_st      Elapsed: 0.18 secs        5,475,894/sec
[info] daily_st         Elapsed: 0.20 secs        5,062,659/sec
[info] empty_logger     Elapsed: 0.07 secs       14,127,300/sec
[info] **************************************************************
[info] C-string (400 bytes). Single thread, 1,000,000 iterations
[info] **************************************************************
[info] basic_st         Elapsed: 0.41 secs        2,412,483/sec
[info] rotating_st      Elapsed: 0.72 secs        1,389,196/sec
[info] daily_st         Elapsed: 0.42 secs        2,393,298/sec
[info] null_st          Elapsed: 0.04 secs       27,446,957/sec
[info] **************************************************************
[info] 10 threads, competing over the same logger object, 1,000,000 iterations
[info] **************************************************************
[info] basic_mt         Elapsed: 0.60 secs        1,659,613/sec
[info] rotating_mt      Elapsed: 0.62 secs        1,612,493/sec
[info] daily_mt         Elapsed: 0.61 secs        1,638,305/sec
[info] null_mt          Elapsed: 0.16 secs        6,272,758/sec
```
#### 异步模式
```
[info] -------------------------------------------------
[info] Messages     : 1,000,000
[info] Threads      : 10
[info] Queue        : 8,192 slots
[info] Queue memory : 8,192 x 272 = 2,176 KB 
[info] -------------------------------------------------
[info] 
[info] *********************************
[info] Queue Overflow Policy: block
[info] *********************************
[info] Elapsed: 1.70784 secs     585,535/sec
[info] Elapsed: 1.69805 secs     588,910/sec
[info] Elapsed: 1.7026 secs      587,337/sec
[info] 
[info] *********************************
[info] Queue Overflow Policy: overrun
[info] *********************************
[info] Elapsed: 0.372816 secs    2,682,285/sec
[info] Elapsed: 0.379758 secs    2,633,255/sec
[info] Elapsed: 0.373532 secs    2,677,147/sec

```

## 文档
文档可在 [wiki](https://github.com/gabime/spdlog/wiki/1.-QuickStart) 页面中查阅。

---

感谢 [JetBrains](https://www.jetbrains.com/?from=spdlog) 捐赠产品许可证支持 **spdlog** 的开发 <a href="https://www.jetbrains.com/?from=spdlog"><img src="assets/logos/jetbrains-variant-4.svg" width="94" align="center" /></a>
