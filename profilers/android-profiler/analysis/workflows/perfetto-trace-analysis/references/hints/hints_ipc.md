针对 IPC、binder 事务和跨进程依赖的专家提示。
keywords:
- ipc
- binder
- transaction
- cross-process
- bottleneck
- service

## - system_server

- 寻找同一进程（`system_server`）在短时间内向不同目标发出多个携带相似数据的出站 binder 事务。这种「binder 风暴」说明缺少多路复用。
- 要跨进程跟踪数据，可用 flow 事件关联 slice，把 slice 的 ID 与 `flow.source_slice_id` 或 `flow.dest_slice_id` 关联起来。
- 要发现 binder 洪泛，查询 `binder_transaction` 表，按线程 ID（`tid`）、`service_name` 和 `method_name` 分组，找出大量完全相同的调用。
- 发现 binder 并发过高时，按 `server_upid` 对事务分组，定位瓶颈所在的服务端进程。
- 要分析某个慢 binder 事务的延迟，用 `binder_transaction` 表中的总 `dur` 减去 `server_dur`，算出花在服务端之外的时间。
- 怀疑某线程存在 binder 洪泛时，把它的 `tid` 与 `cpu_slice` 表关联，检查 CPU 消耗是否偏高。
- 要找出造成 binder 洪泛的代码，先取得问题线程的 `utid`，再用它查询 `stack_profile_callsite`。
- 要找出某个问题函数的调用方，在 `stack_profile_callsite` 中筛选映射到它的帧，然后用 `parent_id` 向上追溯。
- 一个线程上的长 slice 与另一个线程上的 slice 存在因果关联（例如从 `system_server` 到 SystemUI 的 binder 调用），说明存在调度依赖瓶颈。
- 要找出可能导致 UI 卡顿的异步操作，寻找控制进程发出、随后很快返回的 binder 事务，以及紧跟着出现在接收进程中的长 slice。
