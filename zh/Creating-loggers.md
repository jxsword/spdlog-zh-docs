> 原文：[Creating loggers](https://github.com/gabime/spdlog/wiki/Creating-loggers)

每个日志记录器（logger）都包含一个由一个或多个 ```std::shared_ptr<spdlog::sink>``` 组成的 vector。

每次记录日志时（若日志级别符合要求），日志记录器都会对其中每一个调用 ```sink(log_msg)``` 函数。

spdlog 的接收器（sink）带有 `_mt`（多线程，multi threaded）或 `_st`（单线程，single threaded）后缀，用于表明其线程安全（thread safety）属性。
单线程接收器不能同时被多个线程使用，但由于不采用任何加锁操作，它们的速度可能更快。

### 使用工厂函数创建日志记录器

```c++
//Create and return a shared_ptr to a multithreaded console logger.
#include "spdlog/sinks/stdout_color_sinks.h"
auto console = spdlog::stdout_color_mt("some_unique_name");
```
这将创建一个控制台日志记录器，以 “some_unique_name” 作为 ID 将其注册到 spdlog 的全局注册表（registry）中，并将其作为 shared_ptr 返回。

### 使用 spdlog::get("...") 访问日志记录器
可以从任何位置使用线程安全的 ```spdlog::get("logger_name")``` 访问日志记录器，它会返回一个共享指针。


**注**：```spdlog::get``` 可能会拖慢您的代码，因为它需要锁定互斥量，所以请谨慎使用。建议保存返回的 ```shared_ptr<spdlog::logger>``` 并直接使用它，至少在热点代码路径中应当如此。

一种好的做法是持有一个 ```shared_ptr<spdlog::logger>``` 类型的私有成员，并在构造函数中对其进行设置：

```c++
class MyClass
{
private:
   std::shared_ptr<spdlog::logger> _logger;
public:
   MyClass()
   {
     //set _logger to some existing logger
     _logger = spdlog::get("some_logger");
     //or create directly
     //_logger = spdlog::rotating_file_logger_mt("my_logger", ...);
   }
};
```

**注 2：** 手动创建的日志记录器（即您直接构造的日志记录器，参见[手动创建日志记录器](#creating-loggers-manually)）不会被自动注册，因此通过 ```get("...")``` 调用将找不到它们。

如果您想注册这类日志记录器，请使用 ```register_logger(...)``` 函数：

```c++
spdlog::register_logger(my_logger);
...
auto the_same_logger = spdlog::get("mylogger");
```

### 创建轮转文件日志记录器
```c++
//Create rotating file multi-threaded logger
#include "spdlog/sinks/rotating_file_sink.h"
auto file_logger = spdlog::rotating_logger_mt("file_logger", "logs/mylogfile", 1048576 * 5, 3);
...
auto same_logger= spdlog::get("file_logger");
```

### 创建异步日志记录器（asynchronous logger）
```c++
#include "spdlog/async.h"
void async_example()
{
    // default thread pool settings can be modified *before* creating the async logger:
    // spdlog::init_thread_pool(8192, 1); // queue with 8k items and 1 backing thread.
    auto async_file = spdlog::basic_logger_mt<spdlog::async_factory>("async_file_logger", "logs/async_log.txt");
    // alternatively:
    // auto async_file = spdlog::create_async<spdlog::sinks::basic_file_sink_mt>("async_file_logger", "logs/async_log.txt");
   
}
```
对于异步日志记录（asynchronous logging），spdlog 使用一个共享的全局线程池（thread pool），并配有专用的消息队列。

为此，它会在消息队列中创建固定数量的**预分配槽位**（在 64 位系统上每个槽位约 256 字节），这一数量可通过 ```spdlog::init_thread_pool(queue_size, backing_threads_count)``` 修改。

当尝试记录一条日志消息而队列已满时，调用方将会阻塞（默认行为），直到有槽位可用（默认），或者立即用新消息覆盖队列中最旧的消息（如果该日志记录器在构造时指定了 ```async_overflow_policy==overrun_oldest```）。  

### 手动创建日志记录器 {#creating-loggers-manually}
```c++
auto sink = std::make_shared<spdlog::sinks::stdout_sink_mt>();
auto my_logger = std::make_shared<spdlog::logger>("mylogger", sink);

// Optionally register the logger.  This is only needed if you want to access it with spdlog::get("mylogger")
spdlog::register_logger(my_logger);
```

> [!NOTE]
> 工厂函数会在内部为日志记录器设置全局状态，例如日志级别。
> 手动创建的日志记录器不会具有这些全局状态。
> 如果您想为某个日志记录器设置全局状态，请调用 `spdlog::initialize_logger()`。

### 创建具有多个接收器的日志记录器
```c++
std::vector<spdlog::sink_ptr> sinks;
sinks.push_back(std::make_shared<spdlog::sinks::stdout_sink_st>());
sinks.push_back(std::make_shared<spdlog::sinks::daily_file_sink_st>("logfile", 23, 59));
auto combined_logger = std::make_shared<spdlog::logger>("name", begin(sinks), end(sinks));
//register it if you need to access it globally
spdlog::register_logger(combined_logger);
```

### 创建写入同一输出文件的多个文件日志记录器
如果您希望让不同的日志记录器写入同一个输出文件，那么它们必须共享同一个接收器。否则可能会得到奇怪的结果。 
```c++
auto sharedFileSink = std::make_shared<spdlog::sinks::basic_file_sink_mt>("fileName.txt");
auto firstLogger = std::make_shared<spdlog::logger>("firstLoggerName", sharedFileSink);
auto secondLogger = std::make_unique<spdlog::logger>("secondLoggerName", sharedFileSink);
```