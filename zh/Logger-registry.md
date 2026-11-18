> 原文：[Logger registry](https://github.com/gabime/spdlog/wiki/Logger-registry)

spdlog 维护一个全局（每个进程一份）的注册表（registry），其中保存着已创建的日志记录器（logger）。

其目的在于让日志记录器能够从项目的任何位置轻松访问，而无需将其到处传递。

```c++
spdlog::get("logger1")->info("hello");
.. 
.. 
some other source file..
..
auto l = spdlog::get("logger1");
l->info("hello again");
```

如果未找到相应的日志记录器，则会返回一个空的共享指针。您可以使用 `if(l)` 来检查指针 `l` 的有效性。

### 注册新的日志记录器
通常无需注册日志记录器，因为它们会被自动注册。

要注册手动创建的日志记录器（即非由 spdlog.h 工厂函数创建的日志记录器），请使用 ```register_logger(std::shared_ptr<logger>)``` 函数：
```c++
spdlog::register_logger(some_logger);
```
该函数会使用其名称来注册 ```some_logger```。

### 注册表冲突
如果尝试使用注册表中已存在的名称进行注册，spdlog 将抛出 ```spdlog::spdlog_ex``` 异常。

### 从注册表中移除日志记录器
可以使用 “drop()” 函数从注册表中移除日志记录器。

如果没有其他指向该日志记录器的 shared_ptr 存在，则该日志记录器会被关闭，其所有资源都将被释放。
```c++
spdlog::drop("logger_name");
//or remove them all
spdlog::drop_all()
```
