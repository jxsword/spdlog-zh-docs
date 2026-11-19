> 原文：[How to use spdlog in DLLs](https://github.com/gabime/spdlog/wiki/How-to-use-spdlog-in-DLLs)

### 问题

由于 spdlog 是仅头文件（header-only）库，构建共享库并在主程序中使用它时，二者之间不会共享注册表（registry）。
这意味着，调用诸如 ```spdlog::set_level(spdlog::level::level_enum::info)``` 之类的函数将无法更改 DLL 中的日志记录器。

### 变通方法

可行的做法是将日志记录器同时注册到两个注册表中。

```c++
/*
 * Disclaimer:
 *   This was not compiled but extracted from documentation and some code.
 */

// mylibrary.h
// In library, we skip the symbol exporting part

#include <memory>
#include <vector>
#include <spdlog/spdlog.h>
#include <spdlog/logger.h>
#include <spdlog/sinks/stdout_color_sinks.h>

namespace library
{
static const std::string logger_name = "example";

std::shared_ptr<spdlog::logger> setup_logger(std::vector<spdlog::sink_ptr> sinks)
{
    auto logger = spdlog::get(logger_name);
    if(not logger)
    {
        if(sinks.size() > 0)
        {
            logger = std::make_shared<spdlog::logger>(logger_name,
                                                      std::begin(sinks),
                                                      std::end(sinks));
            spdlog::register_logger(logger);
        }
        else
        {
            logger = spdlog::stdout_color_mt(logger_name);
        }
    }

    return logger;
}

void test(std::string message)
{
    auto logger = spdlog::get(logger_name);
    if(logger)
    {
        logger->debug("{}::{}", __FUNCTION__, message);
    }
}

}
```

```c++
// In the main program

#include <mylibrary.h>
#include <spdlog/logger.h>
#include <spdlog/sinks/daily_file_sink.h>
#include <spdlog/sinks/stdout_sinks.h>

int main()
{
    // We assume that we load the library here
    ...

    // Let's use the library
    std::vector<spdlog::sink_ptr> sinks;
    sinks.push_back(std::make_shared<spdlog::sinks::stdout_sink_st>());
    sinks.push_back(std::make_shared<spdlog::sinks::daily_file_sink_st>("logfile", 23, 59));

    auto logger = library::setup_logger(sinks);

    spdlog::set_level(spdlog::level::level_enum::debug); // No effect for the library.
    library::test("Hello World!"); // No logging

    spdlog::register_logger(logger);

    // Now this will also affect the library logger
    spdlog::set_level(spdlog::level::level_enum::debug);

    library::test("Hello World!"); // Hurray !

    return 0;
}
```
