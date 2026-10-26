通过 Android 上的 Perfetto 辅助脚本记录 Java/原生堆转储、系统跟踪或自定义配置。
keywords:
- perfetto
- record
- system trace
- heap dump
- memory leak

## - 自定义配置

> \[!IMPORTANT\] **范围：** 本指南**仅适用于在
> Android 设备上记录跟踪** 。其他平台（Linux、macOS 或 Chrome）请参阅
> [perfetto.dev/docs](https://perfetto.dev/docs/) 上的平台文档。

与其直接运行原始的 `adb` 命令，不如使用官方的 Perfetto 辅助
脚本。它们会自动处理推送配置、启动跟踪
守护进程、拉取跟踪文件，并可选在浏览器中打开。

开始前请确保已启用**开发者选项**和 **USB 调试**，并且设备
已通过 USB 连接。

*** ** * ** ***

## 0. 下载辅助脚本

从官方 Perfetto 仓库下载辅助脚本：

    TOOLS_URL="https://raw.githubusercontent.com/google/perfetto/main/tools"

    # Java Heap Dump (ART)
    curl -O "$TOOLS_URL/java_heap_dump" && chmod +x java_heap_dump

    # Native Heap Profiling (heapprofd)
    curl -O "$TOOLS_URL/heap_profile" && chmod +x heap_profile

    # CPU Stack Sampling (traced_perf)
    curl -O "$TOOLS_URL/cpu_profile" && chmod +x cpu_profile

    # General Tracing (Ftrace, ATrace, custom configs)
    curl -O "$TOOLS_URL/record_android_trace" && chmod +x record_android_trace

*** ** * ** ***

## 1. 内存跟踪

使用这些工具分析内存泄漏、对象滞留、C/C++ 分配，或
系统级内存计数器。

### A. Java 堆转储（ART）

抓取某个进程中所有 Java 对象的快照，用于排查内存泄漏。
参考文档：<https://perfetto.dev/docs/data-sources/java-heap-profiler>。

    # Trigger a Java heap dump for a specific app
    ./java_heap_dump -n YOUR_APP_PACKAGE_NAME -o ./heap_dump.perfetto-trace

### B. 原生 C/C++ 堆内存分析（heapprofd）

跟踪 C/C++ 内存分配（malloc/free）以定位原生泄漏。参考
文档：<https://perfetto.dev/docs/data-sources/native-heap-profiler>。

    # Profile native allocations for a specific app
    ./heap_profile -n YOUR_APP_PACKAGE_NAME

    # Profile with custom sampling interval (default is 4096 bytes)
    ./heap_profile -n YOUR_APP_PACKAGE_NAME -i 2048

### C. 系统级内存计数器

随时间跟踪 RSS、Swap 和进程统计。参考文档：
<https://perfetto.dev/docs/data-sources/memory-counters-sys-stats>。

**注意：**要记录内存计数器，你必须通过
`record_android_trace` 使用自定义配置（见第 4 节）。

*** ** * ** ***

## 2. 栈采样 / 调用栈分析（traced_perf）

通过周期性采样调用栈，定位 C/C++ 或 Rust 代码中的 CPU 热点。
参考文档：<https://perfetto.dev/docs/data-sources/cpu-profiler>。

    # Profile CPU usage by sampling callstacks at 100Hz (default) for 10 seconds
    ./cpu_profile -n YOUR_APP_PACKAGE_NAME -d 10000

    # Profile at a custom frequency (e.g., 200Hz)
    ./cpu_profile -n YOUR_APP_PACKAGE_NAME -f 200

*** ** * ** ***

## 3. 系统跟踪（CPU、调度、\& ATrace）

排查卡顿、缓慢的转场、CPU 调度和系统调用。参考
文档：<https://perfetto.dev/docs/data-sources/ftrace>。

你可以直接在命令行指定时长、缓冲区大小和
类别：

    # Record scheduling, frequency, and window manager events for 5 seconds
    ./record_android_trace -t 5s -b 32mb sched gfx wm -a YOUR_APP_PACKAGE_NAME

常用类别：`sched`（CPU 调度）、`freq`（CPU 频率）、`gfx`
（图形）、`am`（Activity Manager）、`wm`（Window Manager）、`view`（View
System）。

*** ** * ** ***

## 4. 自定义配置（混搭数据源）

如果你需要自定义的数据源组合（例如把 Java 堆转储
与 ftrace 结合），或者需要命令行参数未提供的控制项（环形缓冲区、
长时间跟踪、按计数器轮询），请自行合成配置：

1. **阅读配置参考：**`$SKILL_ROOT/recording/workflows/perfetto-trace-recording/references/trace_config_reference.md` 说明了配置结构与数据源，并指向 `$SKILL_ROOT/recording/workflows/perfetto-trace-recording/references/example-configs/` 下的示例配置，你可以基于它们起步并合并。其他数据源请查阅官方指南 <https://perfetto.dev/docs/data-sources/>。
2. **保存配置：**把合成出的文本配置写入本地文件（例如 `config.pftxt`）。
3. **执行跟踪：**用通用记录脚本 `record_android_trace` 运行跟踪（专用脚本不接受自定义配置）：

    ./record_android_trace -c config.pftxt -o ./my_trace.perfetto-trace

如果配置中有拼写错误，运行会立即失败并给出指出错误字段名的
解析错误——修正配置后重试。
