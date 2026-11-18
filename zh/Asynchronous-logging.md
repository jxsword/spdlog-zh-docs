## 创建异步日志记录器（async logger）

> 原文：[Asynchronous logging](https://github.com/gabime/spdlog/wiki/Asynchronous-logging)

创建异步日志记录器的方式有多种。无论采用哪种方式，都必须 ```#include spdlog/async.h```：


### 使用 ```<spdlog::async_factory>``` 模板参数：
```c++
#include "spdlog/async.h"
void async_example()
{
    // default thread pool settings can be modified *before* creating the async logger:
    // spdlog::init_thread_pool(8192, 1); // queue with 8k items and 1 backing thread.
    auto async_file = spdlog::basic_logger_mt<spdlog::async_factory>("async_file_logger", "logs/async_log.txt");
}
```

### 使用 ```spdlog::create_async<Sink>```：
```c++
auto async_file = spdlog::create_async<spdlog::sinks::basic_file_sink_mt>("async_file_logger", "logs/async_log.txt");    
```
### 使用 ```spdlog::create_async_nb<Sink>```：
这样创建的日志记录器在队列已满时永远不会阻塞。
```c++
auto async_file = spdlog::create_async_nb<spdlog::sinks::basic_file_sink_mt>("async_file_logger", "logs/async_log.txt");
```

### 直接构造并使用全局线程池（thread pool）
```c++
spdlog::init_thread_pool(queue_size, n_threads);
auto logger = std::make_shared<spdlog::async_logger>("as", some_sink, spdlog::thread_pool(), async_overflow_policy::block);
```

### 直接构造并使用自定义线程池
```c++
auto tp = std::make_shared<details::thread_pool>(queue_size, n_threads);
auto logger = std::make_shared<spdlog::async_logger>("as", some_sink, tp, async_overflow_policy::block);
```
#### 注：上例中的 tp 对象的生命周期必须长于日志记录器对象，因为日志记录器会获取指向 tp 的 weak_ptr。

## 队列已满时的策略
当队列已满时，有 2 种可选的处理方式：
* 阻塞调用方，直到队列中有更多空间（默认行为）
* 丢弃队列中最旧的消息并替换为新消息，而不是等待更多空间。
  使用 ```create_async_nb``` 工厂函数，或在日志记录器的构造函数中指定 ```spdlog::async_overflow_policy```：
```c++
auto logger = spdlog::create_async_nb<spdlog::sinks::basic_file_sink_mt>("async_file_logger", "logs/async_log.txt");
// or directly:
 auto logger = std::make_shared<async_logger>("as", test_sink, spdlog::thread_pool(), spdlog::async_overflow_policy::overrun_oldest);
```

## spdlog 的线程池
默认情况下，spdlog 会创建一个全局线程池，队列大小为 8192，包含 1 个工作线程，为**所有**异步日志记录器提供服务。

这意味着创建和销毁异步日志记录器的开销很小，因为它们既不拥有也不创建任何后台线程或队列——这些均由共享的线程池对象创建和管理。

所有队列槽位都在线程池构造时**预分配**（在 64 位系统上，每个槽位约占用 256 字节）。

线程池的大小和线程数可通过以下方式重置：
```c++
spdlog::init_thread_pool(queue_size, n_threads);
```
请注意，这会丢弃旧的全局线程池（tp）并创建一个新的 tp——这意味着任何使用旧 tp 的日志记录器都将停止工作，因此建议在任何异步日志记录器创建之前调用它。

如果不同的日志记录器必须拥有各自独立的队列，可以创建不同的线程池实例，并将其传递给相应的日志记录器：

```c++
auto tp = std::make_shared<details::thread_pool>(128, 1);
auto logger = std::make_shared<async_logger>("as", some_sink, tp, async_overflow_policy::overrun_oldest);

auto tp2 = std::make_shared<details::thread_pool>(1024, 4);  // create pool with queue of 1024 slots and 4 backing threads
auto logger2 = std::make_shared<async_logger>("as2", some_sink, tp2, async_overflow_policy::block);
```

线程池还提供了其他一些以回调作为参数的构造函数。这些回调会在每个线程创建之后、销毁之前由该线程执行。
```c++
std::function<void()> on_start = []() { /* execute on start */ };
auto on_stop = []() { /* execute on stop */ };
auto tp = std::make_shared<details::thread_pool>(1024, 1, on_start, on_stop);

// init_thread_pool helper also supports optional on_start and on_stop callbacks
spdlog::init_thread_pool(1024, 1, on_start);
spdlog::init_thread_pool(1024, 1, on_start, on_stop);
```

### 消息顺序
默认情况下，spdlog 只创建一个工作线程，由该线程保持队列中消息的顺序。

请注意，当线程池包含多个工作线程时，消息在出队后可能会被重新排序。

如果您希望保持消息顺序，请在线程池中只创建一个工作线程。

#### Windows 相关问题
VS 运行时存在一个缺陷，会导致应用程序在退出时死锁。如果您使用异步日志记录（asynchronous logging），请务必在 main() 退出之前调用 ```spdlog::shutdown()```
（[stackoverflow：使用 vs2012 rc 时，在 main 退出后调用 std::thread join 会挂起](http://stackoverflow.com/questions/10915233/stdthreadjoin-hangs-if-called-after-main-exits-when-using-vs2012-)）。