> 原文：[Makefile-Only](https://github.com/gabime/spdlog/wiki/Makefile-Only)

### Makefile

此库也可以通过 Makefile 使用，如下所示：

Makefile
```Makefile
LDFLAGS += -L/path/to/lib -lspdlog
```

main.cpp
```main.cpp
#define SPDLOG_COMPILED_LIB 1
#include "spdlog/spdlog.h"

// ... lots of amazing code.
```
