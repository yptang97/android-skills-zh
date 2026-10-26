针对 CPU 调度、线程状态、CPU 争用和频率调节的专家提示。
keywords:
- cpu
- scheduling
- latency
- runnable
- running
- thread state
- governor
- core

## - frequency

- 调试长 slice 时：检查它的线程状态，弄清线程当时在做什么（运行、休眠、阻塞在 I/O 上）。
- 排查延迟问题时调试长 slice：检查它的时长是否由一个或多个长时间运行的子 slice 造成。递归应用此检查。
- 线程被唤醒后到实际运行之间存在延迟时，检查对应 CPU 的「IRQ」轨道，确认是否由中断导致。
- 检查与硬件相关的内核线程是否以实时优先级运行；如果不是，它们可能被抢占。
- 当对主应用包的分析未能揭示根本原因时，扩大到所有线程与进程。搜索同一 CPU 上的其他可运行线程或高优先级内核线程。
- 排查应用启动时，用 SQL 查询汇总主线程上不可中断休眠的原因。
- 检查运行主进程的 CPU 核心的「cpu_frequency」计数器。缺少频率切换事件、没有频率调节，或在高负载计算期间频率一直偏低，都说明 governor 存在瓶颈或停滞（例如 `su_gov` 失败或 governor 滞后）；不要假定核心以最高性能运行。
- 查询原始「ftrace」事件，寻找与 governor 线程相关的日志（例如「su_gov」）。
- 要查找并发问题，搜索处于阻塞状态（`thread_state.state = 'D'`）的关键线程（例如 'RenderThread'），并与调度数据关联以找出唤醒者。
- 比较花在用户态函数与内核（带 `[k]` 前缀的 slice）中的时间。
- 要发现 'catch-up storm'，寻找在 thread_state/cpu_slice 活动中出现长时间空档、随后立即出现高密度突发的线程。
- 通过计算调度延迟来量化调度器争用（使用 `preceding_sched_slice_for_thread` 测量前一个 'Runnable' 状态的持续时间）。查找最大值和高分位数（p95/p99）。
- 如果某个任务出现高调度延迟，检查其他 CPU 是否处于空闲（运行 swapper 或 idle 线程）。
- 检查关键线程的 `cpu_id`；如果它们持续被调度到较慢的核心，说明允许其跑在大核上可能带来性能收益。
- 对表现不佳的线程，分析 'Runnable' 与 'Running' 状态的时间。'Runnable' 时间过长说明 CPU 争用。
- 如果某个 slice 的墙钟时长增加，但 'Running' 时间占比不变，很可能是 CPU 频率偏低。检查 `sched_switch` 以锁定正确的核心。
