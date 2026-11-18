> 原文：[Default logger](https://github.com/gabime/spdlog/wiki/Default-logger)

为方便使用，spdlog 会创建一个默认的全局日志记录器（logger）（输出到 stdout，带颜色、多线程）。

您只需直接调用 ```spdlog::info(..), spdlog::debug(..), etc``` 即可轻松使用它。

其实例可被替换为任意其他日志记录器（shared_ptr）：
```c++
spdlog::set_default_logger(some_other_logger);
spdlog::info("Use the new default logger");
```


