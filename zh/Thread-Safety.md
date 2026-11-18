## 非线程安全（thread safe）的函数

> 原文：[Thread Safety](https://github.com/gabime/spdlog/wiki/Thread-Safety)

以下函数**不应**在同一个日志记录器（logger）对象上被多个线程并发调用：
* ```set_error_handler(log_err_handler);``` 
* ```logger::sinks()``` - 返回对非线程安全 vector 的引用，因此请勿并发修改它（例如 ```logger->sinks().push_back(new_sink);```） 

注：此限制适用于所有类型的日志记录器（“_mt” 或 “_st”）。

### 日志记录器
要创建**线程安全**的日志记录器，请使用 _mt 工厂函数。

例如：
```c++
auto logger = spdlog::basic_logger_mt(...);
```

要创建**单线程**的日志记录器，请使用 _st 工厂函数。

例如：
```c++
auto logger = spdlog::basic_logger_st(...);
```

### 接收器（sink）
- **线程安全的接收器：**以 ```_mt``` 结尾的接收器（例如 ```daily_file_sink_mt```）
- **非线程安全的接收器：**以 ```_st``` 结尾的接收器（例如 ```daily_file_sink_st```）


