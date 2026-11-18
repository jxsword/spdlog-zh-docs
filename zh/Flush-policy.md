> 原文：[Flush policy](https://github.com/gabime/spdlog/wiki/Flush-policy)

默认情况下，spdlog 会让底层的 libc 在其认为合适的时机自行刷新（flush），以获得良好的性能。您可以使用以下选项来覆盖这一行为：


### 手动刷新
您可以使用 ```logger->flush()``` 函数来指示日志记录器（logger）刷新其内容。该日志记录器继而会对每个底层接收器（sink）调用 ```flush()``` 函数。

**注：** 如果使用异步日志记录器（async logger），```logger->flush()``` 会向队列投递一条消息以请求执行刷新操作，因此该函数会立即返回。这与 spdlog 的某些旧版本不同（旧版本会同步等待消息被接收且刷新完成后才返回）。目前，在关闭程序之前无需显式调用 ```logger->flush()``` 或 ```spdlog::shutdown()```，该操作会在程序退出时随对象销毁自动完成。但是，如果您想在调用 ```abort()``` 或 ```_exit(-1)``` 这类“立即”退出函数之前手动刷新所有异步日志记录器，请在这类函数之前调用 ```spdlog::shutdown()```。

### 基于严重级别的刷新
您可以设置触发自动刷新的最低日志级别（log level）。

例如，每当有 error 或更严重级别的日志消息被记录时，就会触发刷新：
```c++
my_logger->flush_on(spdlog::level::err); 
```

### 基于时间间隔的刷新
spdlog 支持设置刷新间隔。这一功能由一个单独的工作线程（worker thread）实现，它会周期性地对每个日志记录器调用 flush()。


例如，为所有已注册的日志记录器开启间隔为 5 秒的周期性刷新：
```c++
spdlog::flush_every(std::chrono::seconds(5));
```

**注** 仅在线程安全的日志记录器上使用此功能，因为周期性刷新是由另一个线程执行的。
