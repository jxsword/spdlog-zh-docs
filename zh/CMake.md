### CMake

> 原文：[CMake](https://github.com/gabime/spdlog/wiki/CMake)

该库也可以使用 [CMake](http://www.cmake.org/) 安装。CMake 版本必须为 3.0+，可通过 `--version` 查看：
```bash
> cmake --version
cmake version 3.3.1

CMake suite maintained and supported by Kitware (kitware.com/cmake).
```

### 生成

使用当前（`.`）目录中的 `CMakeLists.txt` 在 `_builds` 目录中生成项目，根据操作系统和所需的生成器运行以下命令之一：
```bash
> cmake -H. -B_builds -DCMAKE_BUILD_TYPE=Release # Default generator is Makefile for *nix platform
> cmake -H. -B_builds -GXcode # Xcode generator on OS X (multi-config, no need for CMAKE_BUILD_TYPE)
> cmake -H. -B_builds -G"Visual Studio 12 2013" # Visual Studio IDE, Windows, multi-config
```

或使用工具链：
```bash
> cmake -H. -B_builds -DCMAKE_TOOLCHAIN_FILE=/path/to/iOS.cmake -GXcode
> cmake -H. -B_builds -DCMAKE_TOOLCHAIN_FILE=/path/to/android.cmake -DCMAKE_BUILD_TYPE=Release
```

若要添加示例，请使用 `SPDLOG_BUILD_EXAMPLE=ON` 选项：
```cmake
> cmake -H. -B_builds -DSPDLOG_BUILD_EXAMPLE=ON -DCMAKE_BUILD_TYPE=Release
```

### 构建/测试

打开生成的项目并运行构建/测试目标。也可以使用命令行：
```
> cmake --build _builds --config Release
> cd _builds && ctest -VV -C Release
```

### 安装

头文件可以与 [config](http://www.cmake.org/cmake/help/v3.3/manual/cmake-packages.7.html#config-file-packages) 文件一起安装，从而让库能够被 `find_package(spdlog CONFIG REQUIRED)` 找到：

```cmake
[spdlog]> cmake -H. -B_builds -DCMAKE_INSTALL_PREFIX=/path/to/install -DCMAKE_BUILD_TYPE=Release
[spdlog]> cmake --build _builds --target install
```

可以通过将 `examples` 作为独立项目构建来验证用法：
```cmake
[spdlog/examples]> cmake -H. -B_builds -DCMAKE_PREFIX_PATH=/path/to/install -DCMAKE_BUILD_TYPE=Release
[spdlog/examples]> cmake --build _builds
```

### 使用 CMake 3.7 为 Android 交叉编译

据反馈，使用 CMake 3.7 进行交叉编译可以正常工作，该版本原生支持通过 Android NDK 和 SDK 配置工具链（https://cmake.org/cmake/help/v3.7/manual/cmake-toolchains.7.html#cross-compiling-for-android）。请注意，spdlog 面向的是更旧版本的 CMake，此示例为社区贡献。

下面是一个使用 Android NDK 配置并构建 spdlog 的示例：
```bash
> git clone https://github.com/gabime/spdlog
> mkdir build
> cd build 
> cmake ../spdlog \
  -DCMAKE_SYSTEM_NAME=Android \
  -DCMAKE_SYSTEM_VERSION=21 \
  -DCMAKE_ANDROID_ARCH_ABI="armeabi-v7a" \
  -DCMAKE_ANDROID_ARM_NEON=ON \
  -DCMAKE_ANDROID_NDK=$HOME/Android/Ndk/android-ndk-r13b/
> cmake --build .
```

示例中使用的 CMake 配置选项的含义请参阅 CMake 文档（上方链接）。

## 通过 ExternalProject_Add 以 git 子模块方式作为静态库使用

如果您想在使用 CMake 的项目中使用静态库（实际生成的文件名为 libspdlogd.a），下面是一个简短的示例。

```bash
cd project_dir\lib
git submodule add https://github.com/gabime/spdlog
cd spdlog
git checkout v1.9.2
...
```

```cmake
ExternalProject_Add(spdlog
    PREFIX spdlog
    SOURCE_DIR ${PROJECT_SOURCE_DIR}/lib/spdlog
    CMAKE_ARGS -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
    -DCMAKE_CXX_COMPILER=${CMAKE_CXX_COMPILER}
    -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}
    -DCMAKE_TOOLCHAIN_FILE=${CMAKE_TOOLCHAIN_FILE}
    -DCMAKE_INSTALL_PREFIX=${STAGING_DIR}
    -DSPDLOG_BUILD_SHARED=OFF
)
```

之后还需要添加：

```cmake
add_dependencies(${PROJECT_NAME} spdlog)
```

最后，像这样使用它：

```cmake
PUBLIC ${STAGING_DIR}/include/ # spdlog
```

在 C++/头文件中可以这样：

```C++
#include "spdlog/spdlog.h"
```

## 在共享库中使用 spdlog

构建共享库时，必须在添加 `spdlog` 子目录之前将 `CMAKE_POSITION_INDEPENDENT_CODE` 设置为 `TRUE`。

完整示例：
```cmake
cmake_minimum_required(VERSION 3.10)

project(cmake_test)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED TRUE)
set(CMAKE_POSITION_INDEPENDENT_CODE TRUE)

add_subdirectory("${CMAKE_SOURCE_DIR}/spdlog")

file(GLOB_RECURSE SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")
add_library(test SHARED ${SOURCES})
target_include_directories(test PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src")

target_link_libraries(test PRIVATE spdlog::spdlog)
```
