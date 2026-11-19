> 原文：[Preventing child processes from inheriting open log files](https://github.com/gabime/spdlog/wiki/Preventing-child-processes-from-inheriting-open-log-files)

在 _tweakme.h_ 中，取消注释以下内容，以防止子进程继承日志文件的文件描述符：

```c++
#define SPDLOG_PREVENT_CHILD_FD
```
