> 原文：[Custom formatting](https://github.com/gabime/spdlog/wiki/Custom-formatting)

每个日志记录器（logger）的接收器（sink）都有一个格式化器（formatter），负责将消息格式化后输出到其目的地。

spdlog 的默认日志格式形如：

```[2014-10-31 23:46:59.678] [my_loggername] [info] Some message```

有 2 种方式可以自定义日志记录器的格式：
* 设置模式字符串（pattern string）（*推荐*）：
```c++
set_pattern(pattern_string);
```
* 或者实现一个自定义格式化器，使其实现 [formatter](https://github.com/gabime/spdlog/blob/v1.x/include/spdlog/formatter.h) 接口，
并调用
```c++
set_formatter(std::make_unique<my_custom_formatter>());
``` 

## 使用 ```set_pattern(..)``` 自定义格式
可以将格式全局应用于**所有已注册的**日志记录器：
```
spdlog::set_pattern("*** [%H:%M:%S %z] [thread %t] %v ***");
```
或应用于某个特定的**日志记录器**对象：
```
some_logger->set_pattern(">>>>>>>>> %H:%M:%S %z %v <<<<<<<<<");
```

或应用于某个特定的**接收器**对象：
```
some_logger->sinks()[0]->set_pattern(">>>>>>>>> %H:%M:%S %z %v <<<<<<<<<");
some_logger->sinks()[1]->set_pattern("..");
```

## 效率
每当用户调用 ```set_pattern("..")``` 时，该库都会将新模式“编译”为一种高效的内部表示——这样即使模式非常复杂，性能依然出色（无需在每次记录日志时重新解析模式）。

## 模式标志（pattern flags）
模式标志采用 ```%flag``` 的形式，与 [strftime](http://www.cplusplus.com/reference/ctime/strftime/) 函数类似：

| flag | 含义| example |
| :------ | :-------: | :-----: |
|`%v`|要记录的实际文本|"some user text"|
|`%t`|线程 ID|"1232"|
|`%P`|进程 ID|"3456"|
|`%n`|日志记录器名称|"some logger name"
|`%l`|消息的日志级别（log level）|"debug", "info", etc|
|`%L`|消息的短日志级别|"D", "I", etc|
|`%a`|缩写的星期名称|"Thu"|
|`%A`|完整的星期名称|"Thursday"|
|`%b`|缩写的月份名称|"Aug"|
|`%B`|完整的月份名称|"August"|
|`%c`|日期和时间的表示形式|"Thu Aug 23 15:35:46 2014"|
|`%C`|2 位数字的年份|"14"|
|`%Y`|4 位数字的年份|"2014"|
|`%D` or `%x`|MM/DD/YY 短日期|"08/23/14"|
|`%m`|月份 01-12|"11"|
|`%d`|月份中的日 01-31|"29"|
|`%H`|24 小时制小时 00-23|"23"|
|`%I`|12 小时制小时 01-12|"11"|
|`%M`|分钟 00-59|"59"|
|`%S`|秒 00-59|"58"|
|`%e`|当前秒的毫秒部分 000-999|"678"|
|`%f`|当前秒的微秒部分 000000-999999|"056789"|
|`%F`|当前秒的纳秒部分 000000000-999999999|"256789123"|
|`%p`|上午/下午（AM/PM）|"AM"|
|`%r`|12 小时制时钟|"02:55:02 PM"|
|`%R`|24 小时制 HH:MM 时间，等价于 %H:%M|"23:55"|
|`%T` or `%X`|ISO 8601 时间格式（HH:MM:SS），等价于 %H:%M:%S|"23:55:59"|
|`%z`|ISO 8601 时区相对 UTC 的偏移量（[+/-]HH:MM）|"+02:00"|
|`%E`|自纪元以来的秒数 |"1528834770"|
|`%%`|% 符号|"%"|
|`%+`|spdlog 默认格式|"[2014-10-31 23:46:59.678] [mylogger] [info] Some message"|
|`%^`|颜色范围起始（只能使用一次）|"[mylogger] [info(green)] Some message"|
|`%$`|颜色范围结束（例如 %^[+++]%$ %v）（只能使用一次）|[+++] Some message|
|`%@`|源文件与行号（请使用 SPDLOG_TRACE(..)、SPDLOG_INFO(...) 等，而非 spdlog::trace(...)），等价于 %g:%#|/some/dir/my_file.cpp:123|
|`%s`|源文件的基名（请使用 SPDLOG_TRACE(..)、SPDLOG_INFO(...) 等）|my_file.cpp|
|`%g`|源文件的完整或相对路径，与 spdlog::source_loc 中所示相同（请使用 SPDLOG_TRACE(..)、SPDLOG_INFO(...) 等）|/some/dir/my_file.cpp|
|`%#`|源代码行号（请使用 SPDLOG_TRACE(..)、SPDLOG_INFO(...) 等）|123|
|`%!`|源函数（请使用 SPDLOG_TRACE(..)、SPDLOG_INFO(...) 等；美化打印请参见 tweakme）|my_func|
|`%o`|自上一条日志消息起经过的时间（毫秒）|456|
|`%i`|自上一条日志消息起经过的时间（微秒）|456734|
|`%u`|自上一条日志消息起经过的时间（纳秒）| 456734789|
|`%O`|自上一条日志消息起经过的时间（秒）|4|

## 对齐 
每个模式标志都可以通过在前面添加一个宽度数字（最大 64）来进行对齐。

使用 `-`（左对齐）或 `=`（居中对齐）来控制对齐方向：


| align | 含义| example | result|
| :------ | :-------: | :-----: |  :-----: |
|`%<width><flag>`|右对齐|`%8l`|"&nbsp;&nbsp;&nbsp;&nbsp;info"|
|`%-<width><flag>`|左对齐|`%-8l`|"info&nbsp;&nbsp;&nbsp;&nbsp;"|
|`%=<width><flag>`|居中对齐|`%=8l`|"&nbsp;&nbsp;info&nbsp;&nbsp;"|

（可选）添加 `!`，以便在结果大小超过指定宽度时截断结果：

| align | 含义| example | result|
| :------ | :-------: | :-----: |  :-----: |
|`%<width>!<flag>`|右对齐或截断|`%3!l`|"inf"|
|`%-<width>!<flag>`|左对齐或截断|`%-2!l`|"in"|
|`%=<width>!<flag>`|居中对齐或截断|`%=1!l`|"i"|

**注：** 要截断函数名，请使用 “!!”。例如，`%10!!` 会将函数名限制为 10 个字符。


## 使用您自己的标志扩展 spdlog
您可以通过继承 [custom_flag_formatter](https://github.com/gabime/spdlog/blob/v1.x/include/spdlog/pattern_formatter.h#L66,#L75) 类并实现 ```clone()``` 和 ```format(...)``` 抽象方法来定义自己的标志。

下面的示例添加了一个新标志 **%***——它将被绑定到一个 <my_formatter_flag> 实例。
```c++ 
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
        return spdlog::details::make_unique<my_formatter_flag>();
    }
};

void custom_flags_example()
{    
    auto formatter = std::make_unique<spdlog::pattern_formatter>();
    formatter->add_flag<my_formatter_flag>('*').set_pattern("[%n] [%*] [%^%l%$] %v");
    spdlog::set_formatter(std::move(formatter));
}

```
**注：** ```clone()``` 方法应返回对象的一份深拷贝；之所以有此要求，是因为 spdlog 会向每个在用的接收器传递该对象的一份新副本（出于性能考虑，这使该对象得以持有状态，而无需担忧跨接收器的竞态条件或线程安全（thread safety）问题）。

**注：** 您也可以通过这种方式覆盖 spdlog 内置的标志。

## 源位置标志（source location flags）
如果您需要使用 `%s`、`%g`、`%#`、`%!` 这类源位置标志，则需要定义以下编译器标志：
```cpp
#define SPDLOG_ACTIVE_LEVEL SPDLOG_LEVEL_TRACE
```

（根据您的需要修改日志级别），并使用这些宏：

```cpp
SPDLOG_LOGGER_TRACE(some_logger, "trace message");
SPDLOG_LOGGER_DEBUG(some_logger, "debug message");
SPDLOG_LOGGER_INFO(some_logger, "info message");
SPDLOG_LOGGER_WARN(some_logger, "warn message");
SPDLOG_LOGGER_ERROR(some_logger, "error message");
SPDLOG_LOGGER_CRITICAL(some_logger, "critical message");
```

**注：** 如果您已将该标志设置为 `SPDLOG_LEVEL_TRACE`，但却看不到任何 trace 和/或 debug 消息，那么很可能属于如下情况：[https://github.com/gabime/spdlog/issues/2764](https://github.com/gabime/spdlog/issues/2764)。此时请将其直接定义为编译器标志。例如，使用 cmake 时：

```cmake
add_compile_definitions(SPDLOG_ACTIVE_LEVEL=SPDLOG_LEVEL_TRACE)
```



