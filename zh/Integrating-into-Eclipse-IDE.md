> 原文：[Integrating into Eclipse IDE](https://github.com/gabime/spdlog/wiki/Integrating-into-Eclipse-IDE)

这篇简短的指南可以帮助您开始在 Eclipse IDE 中集成 C++ **spdlog** 库。
整个配置由 5 个简单的步骤组成。

注：我们可以使用 git clone。当然可以 :)<br>
注：在许多情况下，建议选择一个名为 '_ThirdParty_' 或 '_libs_' 的父文件夹，或选择任何其他一眼便能看出其中存放第三方文件的名称。我们选择了一个名为 '_ThirdParty_' 的文件夹作为父文件夹……

1) 我们将先前从[项目页面](https://github.com/gabime/spdlog)下载的压缩包内容复制/解压到新建或已有的项目中。您也可以从 [github](https://github.com/gabime/spdlog) 克隆它

2) 从菜单栏选择 `Project > Properties > C/C+ Build > GCC C++ Compiler > Preprocessor`，您需要在此处通过点击 Add 按钮（定义符号 `-D`）添加一个定义，并添加以下定义 `SPDLOG_COMPILED_LIB`。注意，务必保持字母的大小写原样不变！

3) 然后点击 `Includes`（我们仍在此处：` Project > Properties > C/C++ Build > GCC C++ Compiler`），并添加 **spdlog** 库头文件所在文件夹的路径。
例如：`thirdParty/spdlog/include`

4) 点击 `apply and close`。

5) 点击 `Project > Indexer > rebuild`


祝编码愉快 ;) 