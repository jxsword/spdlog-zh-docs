> 原文：[Sinks](https://github.com/gabime/spdlog/wiki/Sinks)

接收器（sink）是真正将日志写入其目标的对象。每个接收器应当只负责单一目标（例如文件、控制台、数据库），并且每个接收器都拥有自己私有的格式化器（formatter）对象实例。

每个日志记录器（logger）都包含一个由一个或多个```std::shared_ptr<sink>```组成的 vector。每次记录日志时（若日志级别符合要求），日志记录器都会对其中每一个调用 ```"sink(log_msg)"``` 函数。


spdlog 的接收器带有 _mt（多线程，multi threaded）或 _st（单线程，single threaded）后缀，用于表明其线程安全（thread safety）属性。
单线程接收器不能同时被多个线程使用，但由于不采用任何加锁操作，它们的速度更快。


### 可用接收器

***注*** 这里仅列出部分接收器。完整的接收器列表请访问 [sinks 目录](https://github.com/gabime/spdlog/tree/v1.x/include/spdlog/sinks/)。


***注：*** 从 1.5.0 版本开始，spdlog 会在需要时自动创建日志文件所在的文件夹。在此之前，必须手动创建这些文件夹。
***

**rotating_file_sink** 

达到最大文件大小后，将关闭当前文件、将其重命名，并创建一个新文件。最大文件大小与最大文件数均可在构造函数中配置。

```c++
// create a thread safe sink which will keep its file size to a maximum of 5MB and a maximum of 3 rotated files.
#include "spdlog/sinks/rotating_file_sink.h"
...
auto file_logger = spdlog::rotating_logger_mt("file_logger", "logs/mylogfile", 1048576 * 5, 3);
```
或者手动创建接收器，并将其传递给日志记录器：
```c++
#include "spdlog/sinks/rotating_file_sink.h"
...
auto rotating = make_shared<spdlog::sinks::rotating_file_sink_mt> ("log_filename", 1024*1024, 5, false);
auto file_logger = make_shared<spdlog::logger>("my_logger", rotating);
```

***
**daily_file_sink**

每天在指定时间创建一个新的日志文件，并在文件名中附加时间戳。

```c++
#include "spdlog/sinks/daily_file_sink.h"
..
auto daily_logger = spdlog::daily_logger_mt("daily_logger", "logs/daily", 14, 55);
```
将创建一个线程安全的接收器，它会在每天的 14:55 创建一个新的日志文件。

***注：*** 从 1.5.0 版本开始，spdlog 会在需要时自动创建日志文件所在的文件夹。在此之前，必须手动创建这些文件夹。

***注：*** 
启动时不会删除旧的日志文件，即使这些文件若是在运行时创建，本应早已被清理。轮转（rotation）与删除只发生在运行时，而不会发生在创建接收器时。

***
**simple_file_sink** 

一个简单的文件接收器，仅向给定的日志文件写入，没有任何限制。

***
```c++
#include "spdlog/sinks/basic_file_sink.h"
...
auto logger = spdlog::basic_logger_mt("mylogger", "log.txt");
```
***注：*** 从 1.5.0 版本开始，spdlog 会在需要时自动创建日志文件所在的文件夹。在此之前，必须手动创建这些文件夹。

***
**stdout_sink/stderr_sink** 

```c++
#include "spdlog/sinks/stdout_sinks.h"
...
auto console = spdlog::stdout_logger_mt("console");
auto err_console = spdlog::stderr_logger_st("console");
```

**stdout_sink/stderr_sink（带颜色）**  

```c++
#include "spdlog/sinks/stdout_color_sinks.h"
...
auto console = spdlog::stdout_color_mt("console");
auto err_console = spdlog::stderr_color_st("console");
```

或者直接创建这些接收器：
```c++
auto sink = std::make_shared<spdlog::sinks::stdout_color_sink_mt>();
```

***
**ostream_sink** 

```c++
#include "spdlog/sinks/ostream_sink.h "
...
std::ostringstream oss;
auto ostream_sink = std::make_shared<spdlog::sinks::ostream_sink_mt> (oss);
auto logger = std::make_shared<spdlog::logger>("my_logger", ostream_sink);
```

***
**null_sink**:

空接收器（null sink），直接丢弃其日志——可用于调试，或作为参考实现。

```c++
#include "spdlog/sinks/null_sink.h"
...
auto logger = spdlog::create<spdlog::sinks::null_sink_st>("null_logger");
```

***
**syslog_sink** 

POSIX syslog(3) 接收器，将其日志发送给 syslog。 
```c++
#include "spdlog/sinks/syslog_sink.h"
...
auto syslog_sink = std::make_shared<spdlog::sinks::syslog_sink_mt>("my_ident", LOG_PID);
auto syslog_logger = std::make_shared<spdlog::logger>("logger_name", syslog_sink);
```

**systemd_sink** 

将日志发送给 systemd 的接收器
```c++
#include "spdlog/sinks/systemd_sink.h"
...
auto systemd_sink = std::make_shared<spdlog::sinks::systemd_sink_st>();
auto systemd_logger = std::make_shared<spdlog::logger>("logger_name", systemd_sink);
```

***
**dist_sink** ([sinks/dist_sink.h](https://github.com/gabime/spdlog/tree/master/include/spdlog/sinks/dist_sink.h)):

将日志消息分发给一组其他接收器：

```c++
#include "spdlog/sinks/dist_sink.h"

...
auto dist_sink = make_shared<spdlog::sinks::dist_sink_st>();
auto sink1 = make_shared<spdlog::sinks::stdout_sink_st>();
auto sink2 = make_shared<spdlog::sinks::simple_file_sink_st>("mylog.log");

dist_sink->add_sink(sink1);
dist_sink->add_sink(sink2);
```

***
**msvc_sink** 
Windows 调试接收器（使用 OutputDebugStringA 记录日志）：

```c++
#include "spdlog/sinks/msvc_sink.h"
auto sink = std::make_shared<spdlog::sinks::msvc_sink_mt>();
auto logger = std::make_shared<spdlog::logger>("msvc_logger", sink);
```

***
**dup_filter_sink**
重复消息移除接收器。
若当前消息与上一条完全相同，且时间间隔小于 "max_skip_duration"，则跳过该消息。

示例：
```c++
#include "spdlog/sinks/dup_filter_sink.h"

auto dup_filter = std::make_shared<dup_filter_sink_st>(std::chrono::seconds(5));
dup_filter->add_sink(std::make_shared<stdout_color_sink_mt>());
spdlog::logger l("logger", dup_filter);
l.info("Hello");
l.info("Hello");
l.info("Hello");
l.info("Different Hello");
```
将产生如下输出：
```
[2019-06-25 17:50:56.511] [logger] [info] Hello
[2019-06-25 17:50:56.512] [logger] [info] Skipped 3 duplicate messages..
[2019-06-25 17:50:56.512] [logger] [info] Different Hello
```

***
**ringbuffer_sink**

ringbuffer 接收器将最近的日志消息保存在内存中。
要取回日志消息，可调用 `spdlog::sinks::ringbuffer_sink::last_formatted(size_t)`。

示例：
```c++
#include "spdlog/sinks/ringbuffer_sink.h"

auto ringbuffer_sink = std::make_shared<spdlog::sinks::ringbuffer_sink_mt>(128);

std::vector<spdlog::sink_ptr> sinks;
sinks.push_back(std::make_shared<spdlog::sinks::basic_file_sink_mt>("path/to/log.txt"));
sinks.push_back(ringbuffer_sink);

auto logger = std::make_shared<spdlog::logger>("logger_name", std::begin(sinks), std::end(sinks));

for (int i = 0; i < 256; ++i) {
    logger->info("Log message {}", i);
}

// Retrieve all log messages. `log_message` contains 128 messages.
std::vector<std::string> log_messages = ringbuffer_sink->last_formatted();
// Retrieve a maximum of 64 log messages.
std::vector<std::string> log_messages = ringbuffer_sink->last_formatted(64);
```
***
**qt_sink**

qt_sink 可以将日志消息输出到 QTextBrowser、QTextEdit 等组件……

示例：
```c++
#include "spdlog/sinks/qt_sinks.h"
auto logger = spdlog::qt_logger_mt("QLogger",ui->textBrowser);
logger->info("hello QTextBrowser");
logger->warn("this msg from spdlog");
```
![image](https://user-images.githubusercontent.com/40905056/191399533-8bcd7159-82cd-4221-9288-defcbde27df5.png)


### 实现您自己的接收器

要实现您自己的接收器，需要实现这个简单的 [sink](https://github.com/gabime/spdlog/tree/v1.x/include/spdlog/sinks/sink.h) 接口。

推荐的做法是继承 [base_sink](https://github.com/gabime/spdlog/tree/v1.x/include/spdlog/sinks/base_sink.h) 类。
该类已经处理了线程加锁，使实现线程安全的接收器变得非常容易。

这种情况下，您只需实现受保护的 "sink_it_(..)" 与 flush_(..) 函数即可：
```c++
#include "spdlog/sinks/base_sink.h"

template<typename Mutex>
class my_sink : public spdlog::sinks::base_sink <Mutex>
{
...
protected:
    void sink_it_(const spdlog::details::log_msg& msg) override
    {

    // log_msg is a struct containing the log entry info like level, timestamp, thread id etc.
    // msg.payload (before v1.3.0: msg.raw) contains pre formatted log

    // If needed (very likely but not mandatory), the sink formats the message before sending it to its final destination:
    spdlog::memory_buf_t formatted;
    spdlog::sinks::base_sink<Mutex>::formatter_->format(msg, formatted);
    std::cout << fmt::to_string(formatted);
    }

    void flush_() override 
    {
       std::cout << std::flush;
    }
};

#include "spdlog/details/null_mutex.h"
#include <mutex>
using my_sink_mt = my_sink<std::mutex>;
using my_sink_st = my_sink<spdlog::details::null_mutex>;
```

### 在日志记录器创建后添加接收器：
从 spdlog v1.x 起，提供了一个返回接收器 vector 的非 const 引用的函数，允许您手动向其中追加（push back）接收器。没有任何互斥锁保护接收器 vector（出于性能影响，这一点显而易见），因此它是**非线程安全的**！另请参阅：https://github.com/gabime/spdlog/wiki/1.1.-Thread-Safety

```c++
inline std::vector<spdlog::sink_ptr> &spdlog::logger::sinks()
{
    return sinks_;
}
```

```c++
spdlog::get("myExistingLogger")->sinks().push_back(myNewSink);
```