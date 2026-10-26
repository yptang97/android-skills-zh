当你需要自定义 trace 配置时读本文——即需要混合多个数据源，而专门的辅助脚本
覆盖不到的场景。从
`$SKILL_ROOT/recording/workflows/perfetto-trace-recording/references/example-configs/`
中的示例配置开始，然后按下面的说明增删或合并各部分。

## 配置的结构

配置是一个 `TraceConfig` protobuf——权威 schema 见：
<https://raw.githubusercontent.com/google/perfetto/main/protos/perfetto/config/trace_config.proto>
（各数据源的选项消息位于同一仓库的 `protos/perfetto/config/` 下，
例如 `.../ftrace/ftrace_config.proto`）——用 protobuf **文本格式**
书写（约定保存为 `config.pftxt`）：

    buffers {
      size_kb: 32768            # sizes are in KB, not bytes
      fill_policy: RING_BUFFER  # keep newest data; DISCARD keeps oldest
    }
    duration_ms: 10000          # omit to trace until stopped manually

    data_sources {
      config {
        name: "linux.ftrace"    # which producer to enable
        ftrace_config { ... }   # that producer's own options
      }
    }
    # ...more data_sources blocks, one per source...

合并两个配置 = 保留一个 `buffers` 段，把它们的 `data_sources` 块拼接起来。
每个数据源最多只能出现一次（尤其是 `linux.ftrace` 配置：把所有 `ftrace_events`、
`atrace_categories` 和 `atrace_apps` 条目合并到单个块中）。

## 示例配置

位置：
`$SKILL_ROOT/recording/workflows/perfetto-trace-recording/references/example-configs/`

| 文件 | 使用场景 |
|---|---|
| `sched_cpu.pftxt` | CPU 调度 + 频率/空闲（基础层）。 |
| `app_jank.pftxt` | UI 卡顿 / 掉帧：atrace + 帧时间线。 |
| `memory_counters.pftxt` | 系统与各进程内存、LMK 活动。 |
| `java_heap_dump.pftxt` | 单个应用的 Java 堆保留图。 |
| `native_heap.pftxt` | 采样的原生 malloc/free 调用栈（heapprofd）。 |
| `cpu_profile.pftxt` | 周期性 CPU 调用栈采样（traced_perf）。 |
| `long_background.pftxt` | 长时间/现网 trace：环形缓冲区 + 周期性写入。 |

如果只需要独立的堆转储、原生堆分析或 CPU 分析，优先使用
`$SKILL_ROOT/recording/workflows/perfetto-trace-recording/perfetto_trace_recording.md`
中的专用辅助脚本。当一次 trace 必须合并多个数据源时，才使用示例配置。

## 数据源速览

| `name` | 记录什么 | 关键选项 |
|---|---|---|
| `linux.ftrace` | 内核事件和 atrace | `ftrace_events`, `atrace_categories`, `atrace_apps` |
| `linux.process_stats` | 进程/线程名称与统计 | `scan_all_processes_on_start`, `proc_stats_poll_ms` |
| `linux.sys_stats` | 周期性 `/proc` 计数器 | `meminfo_period_ms`, `vmstat_period_ms`, `stat_period_ms` |
| `android.log` | Logcat | `android_log_config { log_ids: ... }` |
| `android.surfaceflinger.frametimeline` | 帧时间线（卡顿） | 无需设置 |
| `android.java_hprof` | Java 堆转储 | `java_hprof_config { process_cmdline: ... }` |
| `android.heapprofd` | 原生堆分析 | `heapprofd_config { sampling_interval_bytes, ... }` |
| `linux.perf` | CPU 调用栈采样 | `perf_event_config { timebase, callstack_sampling }` |
| `android.packages_list` | 包名映射 | 无需设置 |
| `android.power` | 电池计数器 | `android_power_config { battery_poll_ms, ... }` |
| `track_event` | 应用自定义 trace 事件 | `track_event_config { enabled_categories }` |

每个数据源完整、权威的字段列表见生成的
[TraceConfig 参考](https://perfetto.dev/docs/reference/trace-config-proto)；
各数据源的指南位于
[perfetto.dev/docs/data-sources](https://perfetto.dev/docs/data-sources/)。

## 顶层参数

- `duration_ms` - trace 时长。省略它则一直录制，直到录制命令被停止（在 `record_android_trace` 上按 Ctrl-C）。
- `buffers.fill_policy` - `RING_BUFFER` 保留最新数据（关键时刻在末尾时这是正确选择）；`DISCARD` 保留最旧数据。
- 长时间 trace：`write_into_file: true` + `file_write_period_ms` 周期性地把缓冲区写入磁盘，使 trace 能超过内存容量；`flush_period_ms: 30000` 保持应用发出的事件有序；`max_file_size_bytes` 限定输出大小。
- 缓冲区大小的经验法则：32--64 MB（`size_kb: 32768`--`65536`）对大多数 10--30s 的 trace 都绰绰有余；堆转储需要 \~100 MB 或使用 `write_into_file`。

## 常见陷阱

- 所有缓冲区大小都以 **KB** 计（`size_kb: 32768` = 32 MB）；时长以 **ms** 计。
- atrace 数据（类别与应用事件）只会通过 `linux.ftrace` 数据源流入——不存在单独的「atrace」数据源，而且应用的自定义 trace 事件只有在它的包名被列在 `atrace_apps` 中（或 `atrace_apps: "*"`）时才会出现。
- 字段名拼写错误只有在录制时解析配置才会被发现：`record_android_trace -c config.pftxt` 会快速失败并报出指明错误字段的解析错误，可把它当作校验器，修正后重试。
- 文本格式的枚举值是不带引号的标识符（`fill_policy: RING_BUFFER`），字符串要加引号。
