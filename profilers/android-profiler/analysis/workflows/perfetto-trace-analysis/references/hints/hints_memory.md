针对内存压力、低内存杀手（Low Memory Killer，LMK）和分配的专家提示。
keywords:
- memory
- lmk
- lmkd
- oom
- rss
- swap
- kswapd
- thrashing
- pressure

## - allocation

- 要调查低内存杀进程，查找 `lmk_kill_occurred` ftrace 事件；计数很高说明内存压力严重。
- 当你看到一批 `lmk_kill_occurred` 事件时，在同一时间窗口内查询 `sched_slice` 表中 CPU `wall_duration` 高的进程。失控进程持续占用 CPU 会加剧内存压力。
- 要了解某个进程的内存影响，从 `mem.info` 这类内存计数器查看其 `anon_rss`（Anonymous Resident Set Size，匿名常驻集大小）。
- 检查系统级内存统计中 `swap_used` 是否偏高或快速上升。
- 要确认内存抖动（thrashing），查看 `kswapd` 内核线程是否有高 CPU 占用。
- 要找到 LMKD 的直接触发原因，查找来自压力停滞信息（Pressure Stall Information，PSI）的 `memory_pressure` trace 事件。
- 要发现使用硬件加速器（例如 TPU）的进程「丢失」的内存，查询 `counter` 表中的 `RssFile` 值。如果硬件活跃期间该值显著下降，检查 `kswapd0` 的调度切片。
- 分析与其他硬件共享的内存时，查询 `dma_heap_stat` 和 `dmabuf_total_size` 计数器（旧设备上为 `ion_total_size`），这比 RSS 更准确。
- 注意，如果同一物理页被多次映射，`RssFile` 可能高估内存。
- 调查 OOM 时，先查询进程内存计数器（例如 `mem.rss`）建立基线，再把中位数和第 95 百分位与其历史对比。
- 如果 bitmap 是主要的内存消耗者，查询跨各个 trace 的 `android.graphics.Bitmap` 实例，检查 bitmap 数量是否有离群值。
- 要找出是什么在持有某个对象（例如 bitmap），查询 `heap_graph_reference`，把它的保留路径追溯到 GC 根。要特别注意自定义的应用类。
- 查询 `android_bitmaps` 表，检查 bitmap 的 width 和 height 属性。
- 检查是否存在软件 bitmap，它会同时占用应用堆和图形内存。
- 分析 bitmap 时，检查是否有属性完全相同的多个 `android.graphics.Bitmap` 对象，以找出重复项。
