> 原文：[FAQ](https://github.com/gabime/spdlog/wiki/FAQ)

## 日志文件保持为空

出于性能考虑，日志条目不会立即刷新（flush）到文件，而是要等累计记录满 BUFSIZ 字节（该值在 libc 中定义）后才会刷新。

您可以使用以下任一方法强制刷新：
```c++
my_logger->flush();                            // flush now
my_logger->flush_on(spdlog::level::info);      // auto flush when "info" or higher message is logged
spdlog::flush_on(spdlog::level::info);         // auto flush when "info" or higher message is logged on all loggers
spdlog::flush_every(std::chrono::seconds(5));  // flush periodically every 5 seconds (caution: must be _mt logger)
```
详情请参阅[刷新策略](https://github.com/gabime/spdlog/wiki/7.-Flush-policy)。

## 如何在编译期（compile time）移除所有调试语句？
在包含 spdlog.h 之前，将 ```SPDLOG_ACTIVE_LEVEL``` 定义为所需的日志级别（log level），并使用 SPDLOG_ 系列宏：

```c++
#define SPDLOG_ACTIVE_LEVEL SPDLOG_LEVEL_INFO // All DEBUG/TRACE statements will be removed by the pre-processor
#include "spdlog/spdlog.h"
...
SPDLOG_DEBUG("debug message to default logger"); // removed at compile time
SPDLOG_LOGGER_TRACE(my_logger, "trace message"); // removed at compile time
SPDLOG_INFO("info message to default logger");   // included
```

请注意，此方法会在编译期移除这些调试语句，
但在运行时仍需设置所需的日志级别，才能看到它们。

## 如何使用外部 fmt 库替代内置 fmt 库？

要使用外部 fmt 库，必须定义 ```SPDLOG_FMT_EXTERNAL``` 宏。

如果使用 CMake 构建 spdlog，则必须定义 CMake 变量 ```SPDLOG_FMT_EXTERNAL``` 或 ```SPDLOG_FMT_EXTERNAL_HO```（仅头文件（header-only）的 fmt）。
```SPDLOG_FMT_EXTERNAL``` 宏会在通过 CMake 添加 spdlog 时被自动定义。

## 没有实参时格式字符串（format string）的编译期检查不生效

如果只传入格式字符串，编译期检查不会生效。
这是因为在此情形下，出于性能考虑，设计上并未使用格式化器（formatter）（[#3056](https://github.com/gabime/spdlog/issues/3056)）。

```c++
spdlog::info("{}{}", 1, 2); // OK
spdlog::info("{}{}{}", 1, 2); // Compile error.

spdlog::info("{}"); // OK.
```

## Windows 下应用程序退出时异步日志记录（asynchronous logging）挂起

在 main 函数末尾调用 ```spdlog::shutdown();```。

## Windows DLL 下异步日志记录挂起

请确保不要在 **DllMain** 中创建异步日志记录器（async logger）或线程池（thread pool）（例如在 DLL 内使用静态日志记录器变量）。

## 如何在共享库中使用 spdlog？

详情请参阅[如何在 DLL 中使用 spdlog](https://github.com/gabime/spdlog/wiki/How-to-use-spdlog-in-DLLs)。

## 在共享库中使用时检测到内存泄漏

异步日志记录器与 ```spdlog::flush_every()``` 会创建一个工作线程（worker thread）。

在共享库中使用它们时，必须在共享库从内存中卸载之前调用 ```spdlog::shutdown();```。
否则，与该线程相关联的对象可能无法被释放。


## 使用自定义格式时颜色不显示

您需要使用 ```%^ ``` 和 ```%$``` 将想要着色的部分括起来。

例如 ```spdlog::set_pattern(“%^[%l]%$ %v”);```。

## 使用自定义格式时源信息不显示

一些自定义格式模式（例如 ```%@```、```%s```、```%g```、```%#```、```%!```）会输出源信息。

要使这些模式生效，必须使用编译期日志级别宏。

例如：
```cpp

#define SPDLOG_ACTIVE_LEVEL SPDLOG_LEVEL_INFO 
#include "spdlog/spdlog.h"
#include "spdlog/sinks/stdout_sinks.h"

void source_info_example()
{
    auto console = spdlog::stdout_logger_mt("console");
    spdlog::set_default_logger(console);
    spdlog::set_pattern("[source %s] [function %!] [line %#] %v");

    SPDLOG_LOGGER_INFO(console, "log with source info"); // Console: "[source example.cpp] [function source_info_example] [line 10] log with source info"
    SPDLOG_INFO("global log with source info"); // Console: "[source example.cpp] [function source_info_example] [line 11] global logger with source info"

    console->info("source info is not printed"); // Console: "[source ] [function ] [line ] source info is not printed"
}
```

## WinAPI `min`/`max` 宏定义

在 Windows 上将 spdlog 的仅头文件发行版与内置 fmt 库一同使用时，您最终会经由内置 fmt 库包含 `Windows.h`。
要防止 WinAPI 中 `min`/`max` 宏的定义所引发的错误，您可以采取以下任一措施：

- 用括号将 `min()` 或 `max()` 调用括起来：`(std::max)(n1, n2)`，或
- 在包含 spdlog.h 之前定义 `NOMINMAX` 宏，或
- 使用外部 fmt 库（构建 spdlog 时指定 `-DSPDLOG_FMT_EXTERNAL=ON`）

详情请参阅 [#1553](https://github.com/gabime/spdlog/issues/1553) 或 [fmt#1508](https://github.com/fmtlib/fmt/issues/1508)。

## 将默认日志记录器切换为 `stderr`

您可以调用 `set_default_logger()` 传入一个新的 `stderr` 日志记录器。如果您希望日志格式保持不变，应将名称指定为空字符串，但这会与最初的默认日志记录器产生冲突，因为它已占用了该名称。要解决此问题，请先将默认日志记录器替换为一个使用其他任意名称的日志记录器&hellip;

```c++
#include "spdlog/sinks/stdout_color_sinks.h"
#include "spdlog/spdlog.h"
int main()
{
    // Replace the default logger with a (color, single-threaded) stderr logger
    // (but first replace it with an arbitrarily-named logger to prevent a name clash)
    spdlog::set_default_logger( spdlog::stderr_color_st( "some_arbitrary_name" ) );
    spdlog::set_default_logger( spdlog::stderr_color_st( "" ) );
    spdlog::info("This message will go to stderr");
}
```

## 如何强制输出日志消息（忽略日志级别过滤）

您可以使用 `spdlog::level::off` 强制输出日志消息（[讨论](https://github.com/gabime/spdlog/discussions/2640)）。

```cpp
logger.set_level(spdlog::level::error);

logger.warn("This message is not output.");

logger.log(spdlog::level::off, "This message is output.");
```

请注意，这种方式不会触发基于日志级别的刷新（`logger.flush_on(spdlog::level)`）。

## GCC 标准库兼容性问题

如果您使用 GCC 编译器构建如下所示的简单代码并得到 `std::bad_alloc`，则可能说明您使用的是不兼容的标准库。

```cpp
#include "spdlog/spdlog.h"

int main(int argc, char *argv[])
{
    spdlog::info("Test message.");

    return 0;
}
```

`std::bad_alloc` 大多在传入悬空指针或未以空字符结尾的字符串时发生。
但是，仅在 GCC 下，当 spdlog 与应用程序使用了不同的标准库（例如 `libstdc++` 与 `libstdc++11`）时，也可能报告此错误。
在使用包管理器时，此类问题的报告更为常见。
如果您使用包管理器，请检查您的 ABI 设置。

详情请参阅 [#2286](https://github.com/gabime/spdlog/issues/2286) 或 [#2290](https://github.com/gabime/spdlog/issues/2290)。