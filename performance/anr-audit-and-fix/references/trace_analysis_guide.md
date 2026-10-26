使用以下规则诊断 ANR 跟踪，并用
[references/anr_trace_report_template.md](https://developer.android.com/agents/skills/performance/anr-audit-and-fix/references/anr_trace_report_template) 组织输出格式。

*** ** * ** ***

## 1. 飞行前上下文检查

- **进程匹配**：确认转储的进程（`--- pid N at ...` / `Cmd line:` 头部）与 ANR 的 `Subject` 匹配。`Input dispatching timed out` 类型的 subject 往往不带包名或 PID；此时记录 `unknown`，不要中止分析。
- **捕获延迟（`Immediate` 与 `Delayed Snapshot`）**：
  - `Immediate`：转储在 ANR 时间戳处捕获（无响应线程的堆栈反映卡死状态）。
  - `Delayed Snapshot (unresponsive thread stack bypassed)`：ANR 与转储的时间戳之间有显著滞后，或者 `Debug Store` 记录到一条缓慢的主线程 `LooperMsg`，它在转储之前刚刚完成，而无响应线程此时已在 `nativePollOnce` 中空闲。**不要因此就断定没有 bug，也不要把一个已完成的慢事务误判为同步屏障泄漏。**
  - `Debug Store` 仅在 Android 15 及以上存在（旧设备上缺失不构成信号）。它的 `LooperMsg` 条目会记录缓慢（超过 2 秒）的 `ActivityThread$H` 消息（例如 Activity 生命周期事务或 `BIND_APPLICATION`），而 receiver、service 的启动或绑定回调使用单独的 `Debug
    Store` 标签，通用的 `Handler.post` runnable 不会被记录。因此一条已完成的 `LooperMsg` 直接指出了缓慢的主线程回调：报告 `Indeterminate (Delayed Snapshot)`，并按第 2 节归因（除非存在外部资源饥饿，否则为 `APP_DEFECT`）。
- **用户可感知的 ANR**：
  - **`Yes`（`Foreground UI freeze / Foreground termination`）**：任何 `Input
    dispatching timed out` 类型的 ANR，或任何组件、service、job、启动 ANR 且 **`Foreground: Yes`**（杀掉前台进程会终止用户可见的应用）。
  - **`No`（`Silent background termination`）**：后台组件或 watchdog ANR 且 **`Foreground: No`**。

*** ** * ** ***

## 2. 归因判定

始终给出一个单一的主 **`Verdict`**（绝不要输出 `"Shared"` 或
`"Mixed"`）。把任何次要的环境或应用侧争用记录在
**`Contributing Factor`**（`None | EXTERNAL (<process or metric>) | APP
(<thread or workload>)`）中。

判定的作用是告诉开发者应用里是否存在需要修复的东西。按以下顺序评估各判定，止于第一个证据成立的判定；如有更低层级的解释，用一行 `Contributing Factor` 记录。优先级不会在没有真实应用侧证据的情况下把某个判定提级。

1. **`APP_DEFECT`**（应用代码、锁、生命周期契约或线程化 bug）。当无响应线程（`tid=1`，ContentProvider ANR 的 `binder:` 线程，或广播接收器的自定义 `Handler` 或 `goAsync()` 工作线程）存在具体的应用侧阻塞依赖或契约违规时成立，与后台系统负载无关：
   - 无响应线程上的直接 I/O 或重计算、对进程内或跨进程工作的同步等待（例如 `Future.get()`、latch、同步 SDK 初始化、可避免的同步 Binder 调用、持有者正在 CPU 上**实际执行**应用工作的锁/monitor/futex，或持有者在等待无响应线程所占资源的死锁），或泄漏了同步屏障的 View 线程化违规（第 3 节）。即使被等待的工作因应用自身造成的 CPU、GC 或内存压力而变慢，这仍属 `APP_DEFECT`；主要修复是移除阻塞依赖，而负载问题写入 `Contributing Factor: APP (<thread or workload>)`。*（区分在 `<0x...>` 上的 `Blocked`
     与 `MessageQueue.nativePollOnce` 中正常的 `Native` 空闲轮询。）*
   - **边界情况**：当锁或 GC 等待的目标线程（锁持有者或 GC 守护线程，且应用自身堆并未耗尽）本身被外部负载饿死（在运行队列上等待，或处于内核 I/O 的 `state=D`）时，**只有在设备确实已饱和**的情况下才不认定为应用侧证据；此时继续看后面的判定。如果 CPU 总量仍有富余，而持有者仍无法被调度，是因为应用把它跑在比等待中的无响应线程低得多的优先级上，那就是应用自己造成的优先级反转：仍判为 `APP_DEFECT`。
2. **`APP_RESOURCE_OVERLOAD`**（由目标应用驱动的系统资源争用）。当设备 CPU、内存或 I/O 饱和（或因大量缺页而抖动），且目标应用是主要资源驱动者时成立（例如既是 CPU 占用大户，又伴随大量缺页、GC 抖动，或线程数多达数百的过度创建）。如果目标应用占总 CPU 的份额很低，而 `kswapd0` 或其他进程占主导——即使冷启动代码换页产生数百次缺页，或存在常规的框架/SDK 线程池——则继续看 `EXTERNAL_BOTTLENECK`。在目标应用是主要驱动者时，其他进程也有负载并不会降低该判定；把它们记录在 `Contributing Factor: EXTERNAL (<process or metric>)` 中。
3. **`EXTERNAL_BOTTLENECK`**（`External Starvation`；目标应用是被动受害者）。仅在判定 1 和判定 2 都不成立时适用：其他进程或内核使 CPU、内存或 I/O 饱和，而目标应用消耗的 CPU 可忽略或很低，且没有应用侧阻塞依赖（包括冷启动时的类、库或 provider 初始化卡在磁盘等待中，或在系统 I/O 与内存压力下被饿死，或应用线程被挂起在内核 cgroup freezer 通道中）。
   - **严格禁止修复的规则**：当 Verdict 为 `EXTERNAL_BOTTLENECK` 时，**绝不要提出应用代码修复或防御性绕过方案**。把第 4 节的两个字段都填为 `N/A -- No application code change required (External system
     bottleneck)`。

*** ** * ** ***

## 3. 根因与特殊的取证模式

- **`Sync Barrier Leak` 与 `Indeterminate` 与 `Async Lifecycle Timeout`**（当 `tid=1` 处于 `nativePollOnce`、`dispatchVsync` 或渲染 VSYNC 帧时）：
  - *先做排除*：
  - 所有线程都挂起在内核 cgroup freezer 通道 -\> **`EXTERNAL_BOTTLENECK`**（`External Starvation`）。
  - `Debug Store` 显示有覆盖 ANR 时间窗口的已完成慢 `LooperMsg`，或转储捕获被显著延迟 -\> **`Indeterminate (Delayed
    Snapshot)`**（Verdict 按第 2 节的证据给出；若无外部或资源过载证据，则为 `APP_DEFECT`）。
  - 异步组件契约未完成（`BroadcastReceiver.goAsync()` 未调用 `PendingResult.finish()`、`JobService` 超时，或 `SHORT_SERVICE` 超过期限却未调用 `Service.stopSelf()`）-\> **`Async Lifecycle Timeout`**。只有在跟踪能证明时才这样判定（例如 `Debug Store` 中的 `GoAsync` 或 job-stop 记录，或 `Subject:` 行中命名的 `SHORT_SERVICE` 超时）；**绝不要从空的 `Debug Store` 推断异步契约泄漏**。
  - *机制*：`ViewRootImpl.requestLayout()` 会调用 `checkThread()`，但失效路径（`invalidate()` -\> `onDescendantInvalidated()` -\> `scheduleTraversals()`）不会，从而使后台线程能与主线程并发进入 `scheduleTraversals()`。两者都会调用 `mHandler.getLooper().getQueue().postSyncBarrier()` 并覆盖未加同步保护的 `mTraversalBarrier` 令牌；`doTraversal()` 只移除最新的那个令牌，于是在 `MessageQueue` 中泄漏了一个孤儿同步屏障（`Message.target == null`）。同步消息在该屏障后面饿死，而异步 VSYNC 帧仍继续执行。Android 17 修复了这个平台竞态；Android 16 及更早版本仍有此问题，因此评估这一模式时要检查跟踪中的 Android 版本。
  - *ANR subject 特征*：后台组件超时（`Broadcast of
    Intent`、`executing service`）以及 `Input dispatching timed out (Application
    does not have a focused window)`，因为窗口焦点请求同样是同步的主线程消息，会饿死在泄漏的屏障之后。仅有“无焦点窗口”的 subject 并不构成同步屏障的证据（例如伴生代码或窗口状态显式设置了 `FLAG_NOT_FOCUSABLE`）；请套用下面的判据。
  - **`View Threading Violation (Sync Barrier Leak [Confirmed])`**：转储中抓到了后台线程修改 UI view/`ViewRootImpl`，或者 `tid=1` 正在主动渲染 VSYNC 帧（`doFrame -> doTraversal`），同时一条同步消息（`Debug Store` 中的 `SchRcv`）与一个空转的后台工作线程一起饿死。
  - **`View Threading Violation (Sync Barrier Leak [probable])`**：当违规的后台线程已经退出时，**不要**仅靠排除法下结论。必须有**佐证的 VSYNC 渲染证据**（例如 `tid=1` 被抓在 `dispatchVsync` 中，或 `main` 与 `RenderThread` 上上下文切换和 CPU 计时上升，表明同步消息饿死期间异步渲染仍在继续）、即时捕获、`tid=1` 处于 `nativePollOnce`（空闲或正在派发 VSYNC）、`Debug
    Store` 为空或不存在，且 `tid=1` 上没有任何锁、IPC 或 `state=D` 的 I/O 等待。
  - *修复与检测*：在**根作用域**把所有 View 修改限制在主线程（在 `Dispatchers.Main` 或 `lifecycleScope` 上启动，只把慢 I/O 包进 `withContext(Dispatchers.IO)`）。当违规调用点不在堆栈上时，审计后台回调，并用以下手段定位：Android 17 的兼容性检查（`adb shell am compat
    enable ENFORCE_THREAD_CHECKS_ON_VIEW_ROOT_IMPL_APIS <package>`，仅限 debuggable 构建）、Android 17 的 `View#registerCalledFromWrongThreadListener`（需要 `compileSdk 37`；调用处用 `Build.VERSION.SDK_INT >= 37` 保护）用于生产遥测、Robolectric 单元测试标志 `-Drobolectric.enforceViewMethodsCalledOnMainThread=true`，或查找 `MessageQueue.removeSyncBarrier` 处 `IllegalStateException` 的崩溃日志。
- **无响应线程被阻塞或缺失**：
  - 如果无响应线程在锁上处于 `Blocked`，先找出持有者线程并诊断它在做什么（应用工作、GC、I/O、在等待无响应线程所占的锁，或是低优先级线程被饿死），而不是只看等待线程自己的帧；修复方案由持有者的工作负载决定。
  - 如果 `DALVIK THREADS` 中没有 `tid=1`，先在 `DALVIK THREADS` 的 `(not attached)` 条目里定位主线程（`sysTid == PID`），再下任何结论；它的帧（例如 VM 拆除时等待其他线程）揭示了实际的停滞点。
- **无堆栈跟踪（堆栈转储超时或线程堆栈缺失）**：
  - 用内核 `Waiting Channels`（`sysTid=<tid> <wchan>` 行）和 `/proc` 统计来区分：
  - **外部饥饿（`EXTERNAL_BOTTLENECK`）**：系统 I/O 或内存压力严重，主线程（`sysTid == PID`）处于内核磁盘或文件系统等待中，且应用 CPU 占用可忽略。
  - **内部 futex 争用（`APP_DEFECT` / `Lock Contention`）**：主线程和一群应用工作线程停在 `futex_*` 等待通道中，同时应用在主动消耗 CPU。
  - **应用侧过载（`APP_RESOURCE_OVERLOAD`）**：应用在 CPU 或缺页上占主导，但没有内部 futex 队列。
  - **ART `Signal Catcher` 与自定义 `SIGQUIT` 拦截**：ART 内置的 `Signal Catcher` 线程通常等待在 `sigtimedwait` / `do_sigtimedwait` 中。**绝不要**仅凭它下结论；只有当另有一个应用线程也出现在信号等待通道中时，才判定为自定义 `SIGQUIT` 拦截。
- **次要或叠加线程（`Secondary / Compounding Threads`）**：
  - 扫描工作线程并报告并发的加剧因素（或 `None`）：内核磁盘同步（`fsync`/`fdatasync` 中的 `state=D`）、ART/GC/信号路径中的第三方 JNI 或 C/C++ 钩子、自定义信号等待线程、无界线程池，或滥用线程优先级。
