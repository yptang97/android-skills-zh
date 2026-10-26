分析 Perfetto trace，找出用户应用或系统 Android 应用性能问题的根本原因
（例如卡顿、应用启动、内存或延迟阻塞）。
keywords:
- perfetto
- trace
- jank
- startup
- latency
- stall
- thread

## - 瓶颈

使用本工作流诊断常见的 Android 性能问题：卡顿、应用启动延迟、延迟尖峰或
线程阻塞。

按顺序执行以下步骤：

## 步骤 1：识别症状与目标

与用户确认以下信息（提问、给出选项）：

- *症状是什么*：他们想排查掉帧、卡顿、启动延迟、ANR、应用崩溃、系统崩溃，还是内存压力？
- *受害者是谁：*他们在哪里观察到该症状？例如「`com.example.sample` 中出现掉帧」。
- *基线 trace：*如果提供了多个 trace 文件（A/B trace 对比），确认哪一个是基线。你会在步骤 3 中把两者都传给子代理，它们会用基线 trace 来确定预期行为。

> **必须有输入 trace：**确认用户已提供 trace 文件路径
> 或 URL（例如 `.pftrace`、`.perfetto-trace` 或 Perfetto UI 链接）。如果
> 没有提供，暂停并向用户索取后再继续。
> **规则：**
>
> - 如果症状未知，暂停并与用户一起澄清。
> - 如果症状已知但受害者/时间戳未知，进入步骤 2（分诊）以发现候选。

## 步骤 2：系统级分诊

启动一个子代理，使用下面的提示词模板运行分诊：

    Trace Path: [path of the trace with the issue]
    Goal: Identify all candidate bottlenecks for [symptom] in
    [package or entire system]
    Execution: Read
    `$SKILL_ROOT/analysis/workflows/perfetto-trace-analysis/references/triage.md`
    and follow its instructions.

根据分诊输出：

- 如果没有找到候选，向用户索取具体的时间戳或症状。
- 如果存在多个候选，把最严重的 3 个实例呈现给用户，并确认要排查哪一个（或多个）。用户可以选一个或多个。

## 步骤 3：并行排查各候选

对每个已确认的候选，用下面的提示词并行启动专门的子代理：

    Trace path: [path]
    Baseline Trace Path: [path, if provided, else "None"]
    Candidate Info: [package_name, `utid`, `upid`, render_thread_utid,
    process_name, thread_name]
    Symptom Window: [start_ts, end_ts, duration]
    Expanded Symptom Window: [expanded_start_ts to end_ts, if applicable]
    System Vitals: [payload from Step 2]
    Execution Protocol: Read
    `$SKILL_ROOT/analysis/workflows/perfetto-trace-analysis/references/per_candidate_analysis.md`
    and follow it end-to-end.

等所有代理完成后再进入步骤 4。

## 步骤 4：最终汇总与报告

把子代理的发现汇总成一份最终报告，包含：

1. **小结与分类：**归类根本原因（硬件、软件/代码、调度策略、系统资源耗尽、外部依赖）。
2. **依赖链：**从症状到根本原因的完整因果路径，包含线程名、`UTID/UPID`、阻塞状态和时间戳。
3. **证据标签：**为每个论断打标签：`[SQL]`（trace 数据支撑）、`[INFERRED]`（逻辑推断）或 `[GAP]`（未跟踪或数据缺失）。
4. **平台上下文：**在解释平台行为时，引用观察到的切片名称、数值和时间戳。**不好的说法：**「SurfaceFlinger 在 vsync 附近做了 X」**好的解释：**「`SurfaceFlinger` 在 `ts=142.3ms` 的合成切片在 `ts=138.1ms` 的 vsync 信号之后 `4ms` 才运行，与 X 相符」。
5. **部分嫌疑：**已经排查但未得到终态根本原因的次要分支或未验证路径，按证据强度排序。即使已找到终态根本原因，也要报告部分嫌疑。

   > 如果证据在多个可能原因之间分布均匀，就把每个嫌疑连同其支撑数据一起报告，
   > 让工程师能够评估概率，而不是得到虚假的确定性。不要武断地选定一个赢家。
6. **建议的后续步骤：**扫描 `$SKILL_ROOT/analysis/workflows/` 下各工作流的 frontmatter，根据发现推荐匹配的专门工作流。
