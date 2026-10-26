目标：判断**待审查文件中**的代码是否让主线程（或调用方同步等待的 Binder 线程）阻塞到足以引发 ANR，并指出具体行号。按顺序走完这些步骤。一个候选只有通过步骤 2、3 和 5 才能成为问题项。唯一的例外是步骤 4（View 线程问题）：它的证明依据是已附加（attached）View 上的非主线程执行，然后再走步骤 5。

## 步骤 1：列出文件中的候选

- **阻塞原语与锁** ：`runBlocking`、阻塞式 future、latch、monitor、`Thread.sleep`、RxJava 的 `blocking*` 操作符，或与后台工作争用的锁。
- **同步 I/O 或重计算** ：网络、磁盘、文件或数据库读写（`SharedPreferences.Editor.commit()`、`ContentResolver.query`、非挂起的 DAO 调用）、位图解码、JSON 或 XML 负载解析、`MediaPlayer.prepare()`，或无界循环。
- **同步 IPC 或缓慢的组件生命周期** ：跨进程 Binder 或 `ContentProvider` 调用，或 `Application`、`Activity`、`Service`、`BroadcastReceiver`、`ContentProvider` 生命周期回调中的重工作。
- **已附加 View 的非主线程修改**（步骤 4）。

## 步骤 2：证明执行线程（强制）

确定每个候选实际由哪个线程执行，而不是靠假设：

- **检查外层作用域** ：检查协程 dispatcher（`lifecycleScope` 和 `viewModelScope` 默认是 Main）、响应式调度器、executor 或 handler，以及 Android 组件回调（`ContentProvider` 查询在跨进程时运行在 Binder 线程上，进程内则运行在调用方线程上）。
- **线程取决于调用方时追踪调用方**：在项目中向上定位调用方（1 到 2 跳）以确认派发线程，并写明已确认的调用链。
- **监听器与回调**：在假设回调运行在工作线程之前，先确认是哪个线程或 executor 派发它。
- **排除未证明的候选**：如果你无法证明该候选运行在主线程或同步等待的 Binder 线程上（对步骤 4 的候选则是无法证明运行在非主线程上），就把它列在「已排除」中，理由写「线程未确认」。

## 步骤 3：证明调用会阻塞

- **已预置数据的内存响应式读取会立即返回** ：对已预置数据的 `BehaviorRelay` 或 `BehaviorSubject` 调用 `blockingFirst()` 或 `getValue()`、`StateFlow.value`，或对 `StateFlow` / 已有数据的 `SharedFlow`（`replay >= 1`）调用 `first()`，都会立即返回内存中的状态。标记之前先检查数据源是如何初始化的。
- **挂起不等于阻塞** ：挂起函数、`delay`，以及协程 `Mutex`/`Semaphore` 会让协程挂起，而不阻塞底层线程。
- **`runBlocking` 只阻塞其调用线程** ：在后台线程上调用 `runBlocking`（即使内部使用 `Dispatchers.Main`）并不阻塞主线程，除非主线程正在等待那个工作线程。
- **短暂有界的等待不算问题项**：单次大约一帧到几帧（几十毫秒到约一百毫秒）的 sleep 或 wait，不在循环中也不在热路径上，只会造成轻微掉帧，不会导致 ANR。不要把它报为问题项；最多在已排除候选中提一句。
- **潜在隐患** ：主线程上的阻塞原语，其内部工作在内存中完成且没有 I/O 或挂起，是 `LOW` 问题项。要说明它为什么当前不会阻塞，以及什么样的改动会让它阻塞。

## 步骤 4：View 线程违规（同步屏障泄漏）

把**已附加** View 上的非主线程 UI 访问视为**同步屏障泄漏型 ANR** 风险，而不仅仅是 `CalledFromWrongThreadException` 崩溃风险。

- **机制** ：`ViewRootImpl.requestLayout()` 会调用 `checkThread()`，但失效路径（`invalidate()` -\> `onDescendantInvalidated()` -\> `scheduleTraversals()`）不会，这就允许后台线程与主线程并发进入 `scheduleTraversals()`。两者都会调用 `mHandler.getLooper().getQueue().postSyncBarrier()` 并覆盖未加同步的 `mTraversalBarrier` 令牌；`doTraversal()` 只移除一个令牌，于是在 `MessageQueue` 中泄漏一个孤立的同步屏障（在 VSYNC 帧之间冻结同步的主线程消息，或在 `MessageQueue.removeSyncBarrier` 处抛出 `IllegalStateException`）。Android 17 修复了这个平台竞态；Android 16 及更早版本仍然脆弱，因此面向这些版本发布的应用仍必须消除该违规。在非主线程上创建或配置**未附加**的 View 不会触发这个竞态。
- **要检查什么** ：后台协程作用域（`Dispatchers.Default`/`IO`）、后台 Rx 调度器、executor 或线程，或在工作线程上被调用的异步回调（例如网络、图片加载、媒体、传感器或 Binder 监听器）内部的 View 或 adapter 修改。
- **检测** ：Android 17 的 `View#registerCalledFromWrongThreadListener`（需要 `compileSdk 37`；调用处用 `Build.VERSION.SDK_INT >= 37` 保护）、`adb shell am compat enable ENFORCE_THREAD_CHECKS_ON_VIEW_ROOT_IMPL_APIS
  <package>`（可调试构建），或 Robolectric 单元测试标志 `-Drobolectric.enforceViewMethodsCalledOnMainThread=true`。
- **修复** ：在**根作用域**修正线程上下文：
  - *协程* ：在 `Dispatchers.Main`（`lifecycleScope` 或 `viewModelScope`）上启动 UI 流程，只把缓慢的 I/O 或计算工作包进 `withContext(Dispatchers.IO)` 或 `Dispatchers.Default`。
  - *线程、executor 与回调* ：在提交后台工作之前，把内存中的 UI 读取和修改留在主线程，或配置上游流、回调 executor 或目标 API 在主线程交付结果（`AndroidSchedulers.mainThread()`、主线程 UI target 或 main executor）。

## 步骤 5：归属与定级

- **归属到缺陷所属的文件**：只有当阻塞语句或非主线程 View 修改源自待审查文件（或源自本文件在主线程调用时无条件阻塞的具体依赖）时，才报告问题项。如果本文件调用的是一个抽象回调或监听器接口，而外部调用方或宿主类选择在其回调实现中阻塞，就把缺陷归属到那个外部文件，并在这里以「归属调用方或宿主文件」排除。
- **严重程度** ：
  - `HIGH`：主路径（启动、生命周期、输入）上的主线程 I/O 或长等待，或已附加 View 的非主线程修改。
  - `MEDIUM`：次要路径上的主线程阻塞，或有界工作停顿数百毫秒。
  - `LOW`：当前在内存中完成的潜在隐患，或只有外部进程才可能触达的 Binder 线程阻塞。

## 输出

1. 先给一行结论：`ANR risk: yes (<highest severity>)` 或 `ANR risk:
   none found in this file`。
2. 对每个问题项：行号范围、执行线程与已确认的调用链、为什么阻塞（对步骤 4 则是为什么会泄漏同步屏障）、严重程度，以及建议的修复。
3. **已排除的候选**：每条一行并给出原因（例如「线程未确认」「已预置的 relay，立即返回」「通过调用方 X 运行在 IO 上」「归属调用方或宿主文件」）。
