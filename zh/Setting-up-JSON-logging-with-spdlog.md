> 原文：[Setting up JSON logging with spdlog](https://github.com/gabime/spdlog/wiki/Setting-up-JSON-logging-with-spdlog)

我们尚未在任何地方见过 spdlog 的 json 示例，因此想分享一下我们的做法。同时拥有人类可读的日志和基于 json 的机器可读日志并不困难。

```cpp
// Set up the opening brace and an array named "log"
// we're setting a global format here but as per the docs you can set this on an individual log as well
spdlog::set_pattern(set_pattern("{\n \"log\": [");

auto mylogger = spdlog::basic_logger_mt("json_logger", "mylog.json");
mylogger->info(""); // this initializes the log file with the opening brace and the "log" array as above

// We have some extra formatting on the log level %l below to keep color coding when dumping json to the console and we use a full ISO 8601 time/date format
std::string jsonpattern = {"{\"time\": \"%Y-%m-%dT%H:%M:%S.%f%z\", \"name\": \"%n\", \"level\": \"%^%l%$\", \"process\": %P, \"thread\": %t, \"message\": \"%v\"},"};

spdlog::set_pattern(jsonpattern);
```

之后，您就可以像平常一样记录任何想要的日志，例如：

```cpp
mylogger->info(“We have started.”);
```

这将生成一条结构如下的日志条目，只是全部内容会位于同一行：

```json
{
     "time": "2021-01-10T13:44:14.567117-07:00",
     "name": "json_logger",
     "level": "info",
     "process": 6828,
     "thread": 23392,
     "message": "We have started."
}
```

您需要自行确保写入日志消息的内容是有效的 json；如有必要，可以使用完整的 json 对象把消息组织得任意复杂。大多数 C++ json 库都能导出可被解析为 json 的 std::string，然后将其作为参数传给 spdlog；也可以像本例这样直接使用纯文本消息。

日志记录完毕后，您需要闭合 "log" 数组。我们还会自己 drop 该日志记录器来完成清理：

```cpp
auto mylogger = spdlog::get("json_logger");

// All we're doing below is setting the same log format, without the "," at the end
std::string jsonlastlogpattern = { "{\"time\": \"%Y-%m-%dT%H:%M:%S.%f%z\", \"name\": \"%n\", \"level\": \"%^%l%$\", \"process\": %P, \"thread\": %t, \"message\": \"%v\"}" };
spdlog::set_pattern(jsonlastlogpattern);

// below is our last log entry
mylogger->info("Finished.");

// set the last pattern to close out the "log" json array and the closing brace
spdlog::set_pattern("]\n}");

// this writes out the closed array to the file
mylogger->info("");
spdlog::drop("json_logger");
```

最终得到的日志文件大致如下（我们的初始化与 drop 操作是在与实际工作不同的线程上执行的，因此线程 id 各不相同）：

```json
{
   "log": [
      {
         "time": "2021-01-10T13:44:14.567117-07:00",
         "name": "json_logger",
         "level": "info",
         "process": 6828,
         "thread": 23392,
         "message": "We have started."
      },
      {
         "time": "2021-01-10T13:44:23.932518-07:00",
         "name": "json_logger",
         "level": "info",
         "process": 6828,
         "thread": 8048,
         "message": "We are doing something."
      },
      {
         "time": "2021-01-10T13:44:26.927726-07:00",
         "name": "json_logger",
         "level": "info",
         "process": 6828,
         "thread": 8048,
         "message": "Look a number 123.456"
      },
      {
         "time": "2021-01-10T13:44:29.631340-07:00",
         "name": "json_logger",
         "level": "info",
         "process": 6828,
         "thread": 23392,
         "message": "Finished."
      }
   ]
}
```

请留意编译时启用的最低日志级别：如果禁用了 "info"，就需要改用更高的严重级别来写入初始 json 并在结束时闭合它。
