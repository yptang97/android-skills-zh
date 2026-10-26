    > **概述**：**`<APP_DEFECT | APP_RESOURCE_OVERLOAD | EXTERNAL_BOTTLENECK>`**<>/span>
     (`<Diagnosis>`) -- `<1-line conclusion and exact trace evidence to inspect>`

    ### 1. trace 有效性与上下文
    - **进程**：`<package or unknown>`（PID：`<pid>`，前台：`<Yes/No>`）
    - **ANR 触发方式**：`<Subject>`
    - **无响应线程**：`<tid=1 | binder:<tid> (ContentProvider) | <handler
      or goAsync worker thread> (BroadcastReceiver)>`
    - **用户可感知的 ANR**：**`<Yes | No>`**（`<Foreground UI freeze / Foreground
      termination | Silent background term>ination`）
    - **抓取时机**：`<Immediate | Delayed Snapshot>`（`<stack trustworthy |
      b>ypassed`）

    ### 2. 系统健康状况评估
    - **指标**：`<Key PSI avg10, CPU %, iowait %, page faults, or lock state>`
    - **判定**：**`<APP_DEFECT | APP_RESOURCE_OVERLOAD | EXTERNAL_BOTTLENECK>`**
    - **影响因素**：`<None | EXTERNAL (<process or metric>) | APP (<thread or workload>)>`

    ### 3. 根因分析
    - **无响应线程状态**：`<Thread state and top blocking frame>`
    - **阻塞链 / 阻塞机制**：`<Lock holder tid=N / UI race / Sync I/O /
      Binder target>`
    - **次要 / 叠加线程**：`<state=D I/O, native hooks, or None>`
    - **诊断**：**`<Concise root-cause label, e.g., View Threading Violation
      (Sync Barrier Leak [Confirmed | probable]), Lock Contention, Deadlock,
      Main-Thread Blocking Call / I/O / Compute, IPC Stall, Async Lifecycle
      Timeout, External Starvation, or Indeterminate (Delayed Snapshot)>`**

    ### 4. 修复
    1. **代码修复**：`<Concrete fix for APP_DEFECT / APP_RESOURCE_OVERLOAD, or "N/A
       -- No application code change required (External system bottleneck)">`
    2. **预防**：`<Architectural safeguard, or "N/A -- No application code
       change required (External system bottleneck)">`
