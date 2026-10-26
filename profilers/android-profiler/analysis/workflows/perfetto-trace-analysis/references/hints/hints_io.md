关于 I/O 与存储瓶颈、不可中断睡眠和页缓存的专家提示。
keywords:
- i/o
- storage
- disk
- uninterruptible sleep
- d state
- page fault
- dm-verity
- file

## - 系统调用

- 排查与 I/O 相关的长时间不可中断睡眠状态时，检查名称中包含 "verity" 的重叠切片（dm-verity）。
- 如果线程卡在不可中断睡眠且没有 `blocked_function`，就去找其他可能持有内存锁的线程（例如 "jit-thread-pool"、内存映射操作）。
- 分析长时间不可中断睡眠时，查看线程状态详情中的 `blocked_function`（来自 `sched_blocked_reason` ftrace 事件）。
- 应用启动期间在 `do_page_fault` 上花费大量时间，是 I/O 争用的强烈信号。
- 对于 DM-Verity 这类文件完整性机制，搜索 `dm_verity_fec_prefetch` 之类的事件。
- 要找出某个卡住的应用线程所依赖的具体内核依赖，先定位处于 'D' 状态的线程，再查找紧随其后变为可运行的 kworker 或内核线程。
- 对于 I/O 引起的应用卡顿，分析处理该请求的相关 kworker 线程的调度延迟。
- 要发现低效的文件 I/O，查询 syscall 表，看单个 fd 上是否出现高频的小块顺序 `read()` 或 `pread()` 系统调用。
- 如果线程在 'Uninterruptible Sleep' 中耗费大量时间，检查 `blocked_function` 是否为 `page_cache_readahead`。把唤醒时间戳与 `filemap_add_to_page_cache` ftrace 事件关联起来。
- 按 `inode` 分组对 `filemap_add_to_page_cache` 的计数做聚合，以找出造成 I/O 压力的具体文件。
- 查看 `block_rq_issue` ftrace 事件中的 `nr_sector`，以了解文件预读大小。
- 如果 I/O 问题在后续启动中消失，说明这是「冷启动」问题（正在填充页缓存）。
