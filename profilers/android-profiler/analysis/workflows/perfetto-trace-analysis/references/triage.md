按顺序执行以下步骤：

## 1. 验证数据完整性

查询 `stats` 表，检查 CPU 与数据丢失指标。如果存在丢弃的事件，就提醒用户结论
可能不完整，并在后续以 `[GAP]` 意识继续。

## 2. 运行高层系统指标

运行指标以检测影响系统健康的系统性问题（温度降频、LMK、binder 争用）。
> **前置条件：**确认 `trace_processor` 可用（参见
> `$SKILL_ROOT/references/perfetto/setup.md`），并按 `$SKILL_ROOT/references/perfetto/sql.md`
> 启动一个常驻后台会话
> （`trace_processor server unix --name <session> --daemonize [trace_file]`），
> 使所有分诊和候选查询共用同一次内存内解析。

针对 `--remote <session>` 查询下面的标准库视图（或通过
`trace_processor [trace_file] --run-metrics [comma_separated_metrics]`
运行一次性指标）：

### 分诊快速参考

`--run-metrics` 可用的关键指标：`android_startup`、`android_cpu`、
`android_mem`、`android_lmk`、`android_binder`、`android_surfaceflinger`、
`android_gpu`。

| 症状 / 问题 | 需要检查什么 | 有用的 Perfetto 表 |
|---|---|---|
| **应用启动** | 主线程、类加载、bindApplication | `android.startup.startups`（`android_startups`）, `slice` |
| **应用卡顿** | 主线程、RenderThread | `actual_frame_timeline_slice`, `slice`, `thread_state` |
| **系统卡顿** | SurfaceFlinger、HWC 合成 | `actual_frame_timeline_slice`, `slice` |
| **应用 / 系统崩溃** | `Process crashed` 或 `tombstoned` | `slice`, `process` |
| **ANR** | 主线程、`system_server` watchdog | `thread_state`, `slice` |
| **帧时序问题** | `DrawFrame` 或 `doFrame` 切片 | `slice`, `actual_frame_timeline_slice` |
| **内存压力 / LMK** | LMKD 终止、RSS 增长、kswapd | `counter`, `sched_slice` |

## 3. 确定目标与症状窗口

1. 定位具体问题的起始时间（`ts`）、持续时长（`dur`）和结束时间戳（`ts + dur`）。
2. **向上游扩展：**检查第一个阻塞事件是否由*在症状窗口之前*就已开始的等待造成。等待（例如 binder 服务端、内存回收或内核锁中的等待）往往比用户可见的掉帧或延迟尖峰早数百毫秒发生。
   - 找出受害者在症状窗口内的第一次非 Running 状态转换。
   - 沿着唤醒者（waker）链追溯。如果阻塞事件明显早于症状窗口开始，就把调查窗口向上游扩展以覆盖该起点。如果链条级联到另一个进程中的起点（例如某个 binder 服务端在卡顿前 `500ms` 就阻塞了），**记下**扩展后的窗口，并在输出中把该上游等待记录为共同候选。
3. **输出**分诊摘要，使用下面定义的格式。

## 4. 最终输出格式

按以下格式输出分诊摘要：

    ## Trace Metadata
    - **Device Model:** `[String, e.g., Pixel 7 Pro]`
    - **Android Build:** `[String, e.g., TQ2A.230505.002]`

    ## System Vitals Summary
    - **Status:** `[Nominal | Degraded | Critical]`
    - **Flags Raised:** *(Only list systemic issues that are actually detected)*
      - **Metric:** `[String, e.g., thermal_throttling, lmkd, binder_contention]`
      - **Description:** `[e.g., 'Thermal throttling during symptom window']`

    ## Candidate(s)
    *(Provide this block for each identified candidate)*
    - **Issue Classification:** `[String, e.g., Startup, Jank, ANR_Input, Crash]`
    - **Package Name:** `[String]`
    - **Process Name:** `[String]`
    - **Thread Name:** `[String]`
    - **UPID:** `[Integer]`
    - **Target UTID:** `[Integer]` *(The primary thread)*
    - **Render Thread UTID:** `[Integer or N/A]` *(If issue is jank)*
    - **Symptom Window:** `[Start TS] - [End TS] ([Duration ms])`
    - **Expanded Window:** `[Expanded Start TS] - [End TS] ([Expanded Duration ms] or "None")`
    - **Severity Note:** `[String, e.g., '150ms missed frame - worst instance']`
