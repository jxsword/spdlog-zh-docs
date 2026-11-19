> 原文：[Preventing undefined thread ids in child processes](https://github.com/gabime/spdlog/wiki/Preventing-undefined-thread-ids-in-child-processes)

默认情况下，spdlog 会将线程 id 保存在线程局部存储（thread local storage）中，以在每次调用时节省几微秒的开销；但如果您的程序会 fork，则**必须**在 [tweakme.h](https://github.com/gabime/spdlog/blob/master/include/spdlog/tweakme.h) 中取消 ```SPDLOG_DISABLE_TID_CACHING``` 标志的注释。

这样可避免子进程日志消息中出现未定义的线程 id：

```c++
#define SPDLOG_DISABLE_TID_CACHING
```
