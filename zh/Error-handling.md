> 原文：[Error handling](https://github.com/gabime/spdlog/wiki/Error-handling)

Spdlog 在记录日志时**不会**抛出异常（自版本 [39cdd08](https://github.com/gabime/spdlog/tree/39cdd08a5475c63959174747a140de86c24e4849) 起）。 

在构造日志记录器（logger）或接收器（sink）时可能会抛出异常，因为这类失败被视为致命错误。

如果在记录日志的过程中发生错误，该库会向 stderr 打印一条错误消息。
为避免错误消息刷满屏幕，每个日志记录器的速率被限制为每分钟 1 条消息。

可以通过调用 ```spdlog::set_error_handler(new_handler_fun)``` 或 ```logger->set_error_handler(new_handler_fun)``` 来更改此行为：

**全局更改错误处理器（error handler）：**

```c++
    spdlog::set_error_handler([](const std::string& msg) {
        std::cerr << "my err handler: " << msg << std::endl;
    });
```


**针对特定日志记录器：**

```c++
    critical_logger->set_error_handler([](const std::string& msg) {
        throw std::runtime_error(msg);
    });

```

**默认错误处理器**

`_default_err_handler` 将使用以下代码打印错误
```c++
    fmt::print(stderr, "[*** LOG ERROR ***] [{}] [{}] {}\n", date_buf, name(), msg);
```