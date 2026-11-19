> 原文：[Note for adding sinks on the fly](https://github.com/gabime/spdlog/wiki/Note-for-adding-sinks-on-the-fly)

我们当时需要在日志中添加一个回调接收器（callback sink），以便将日志消息（log message）重新处理为不同的格式（json 和 MQTT），同时保留原有的日志记录。由于当时对 C++ 标准了解得不够透彻，我们发现了一个小陷阱。要添加接收器（sink），请务必注意在日志记录器（logger）中访问 `sinks()` 的方式。下面这种写法是行不通的：

```cpp
auto sinks = log_->sinks();
sinks.push_back(std::make_shared<spdlog::sinks::callback_sink<std::mutex> >([this](const spdlog::details::log_msg& msg) {this->LogCallback(msg);}));
```

`"auto sinks = ..."` 得到的是 sinks 向量的一个副本，因此您实际上并没有修改日志记录器中的 sinks 向量。C++ 编译器实际上完全是在按 C++ 标准行事：`"auto var = xyz"` 得到的绝不会是引用，它调用的是右侧（RHS）对象的拷贝构造函数。

您需要使用 `auto&`，或者使用 `common.h` 中原本定义的 sink_ptr 类型，但得到的必须是对该向量的引用。

```cpp
auto& sinks = log_->sinks();
sinks.push_back( .....etc
```

希望这能为其他人省去一小时抓耳挠腮的烦恼。

---

详情请参阅 [#3014](https://github.com/gabime/spdlog/issues/3014)