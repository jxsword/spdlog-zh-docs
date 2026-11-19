> 原文：[Windows unicode filenames](https://github.com/gabime/spdlog/wiki/Windows-unicode-filenames)

spdlog 在 Windows 下支持 Unicode 文件名。 
要启用此功能，请取消注释 
```c++
#define SPDLOG_WCHAR_FILENAMES
```
这一行（位于 ```tweakme.h``` 文件中），并在指定文件名时使用 SPDLOG_FILENAME_T（或 L..）宏：

```c++
auto file_logger = spd::rotating_logger_mt("file_logger", L"logs/mylogfile", 1048576 * 5, 3);
auto file_logger2 = spd::rotating_logger_mt("file_logger2", SPDLOG_FILENAME_T("logs/mylogfile2"), 1048576 * 5, 3);
```
