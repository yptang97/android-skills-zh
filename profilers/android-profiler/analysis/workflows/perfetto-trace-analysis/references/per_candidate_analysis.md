使用初始提示词中提供的候选详情（Trace 路径、症状窗口、UTID、System Vitals）
执行下面的协议。

## trace 分析指导原则

遵循这些原则来找出根本原因，确保分析基于数据，并在发现真正瓶颈的过程中
避开陷阱。

1. **通过内省发现做 schema 校验：**在起草查询之前，先读
   `$SKILL_ROOT/references/perfetto/sql.md`，并用 `LIMIT 0` 查询表 schema。

   - **原因：**trace processor 的 schema 会随版本演进；直接内省 schema 可以避免错误假设和语法失败。
2. **以实测数据为依据：**每个论断都要有查出的时间戳、切片时长或计数器值支撑（`[SQL]`）。

   - **原因：**通用的 Android 经验法则无法替代 trace 中的真实指标。当查询返回空结果时，用模糊匹配或更宽的时间窗口来放宽搜索约束。
3. **因果与相关要区分：**验证阻塞方的活跃执行区间与受害者的等待区间确实重叠。

   - **原因：**并发出现的异常只有在执行生命周期相交时才具有因果关联。例如，线程 A 在忙碌、线程 B 在等待，并不必然意味着线程 A 造成了这次等待。
4. **跟随证据：**只要**每一跳都能有意义地解释症状**，就跨线程、进程和内核边界持续追踪依赖链。

   - **原因：**过早停止对阻塞方的遍历，报告的是中间症状而不是真正的起点。
5. **显式报告不确定性：**把未验证的执行路径归为 `[GAP]` 或部分嫌疑。

   - **原因：**透明地报告缺失数据，能让工程师评估概率而不是得到虚假的确定性。
6. **先证据后解释：**在断言平台行为上下文之前，先引用具体检索到的指标和切片时间戳。

   - **原因：**只有锚定在实测 trace 观察之上，上下文解释才可靠。
7. **系统性干扰因素扫描：**在把瓶颈归因于应用软件之前，先确认温度降频、CPU 限频（`cpufreq`）、调度（`sched_slice`）或 LMKD 压力并没有在整个系统范围内均匀地拖慢性能。把这类干扰因素报告为根本原因的修正项。

   - **原因：**软件执行时长不是绝对常量，它受平台和硬件状态调制。硬件降频可以在不增加指令开销的情况下人为拉长墙上时间，从而让健康的代码看起来像低效的瓶颈。

   > 要发现那些会被简单平均值或聚合查询在数学上漏掉的短时异常，请把
   > 症状窗口单独切出来并查看其周边，查询单个事件的尖峰或百分位数。

## 排查步骤

### 步骤 1：配置与基线验证

1. 按 `$SKILL_ROOT/references/perfetto/sql.md` 进行基于会话的查询执行。
2. **建立基线：**
   - **A/B 基线：**如果提供了 `Baseline Trace Path`，先查询那条 trace，以确定预期的切片模式、线程状态和执行预算。
   - **trace 内基线：**如果没有单独提供基线，就在当前 trace 中更早的位置寻找同一操作的正常、无卡顿实例。
   - *如果任何地方都拿不到基线，标记为 `[GAP]` 后继续。*

### 步骤 2：计算时间分布与状态分桶

1. **汇总线程各状态的耗时：**计算症状窗口内在 `Running`、`R`、`S` 和 `D` 状态上花费的确切时长。
2. **排查显著分桶：**针对所有显著的状态分桶（例如占窗口时长 \>= 20% 的），先排查最大的那个。
3. **寻找复合瓶颈：**判断是否存在复合瓶颈（例如「40% CPU 饥饿 + 35% IO 阻塞」）。
4. **排除误报与假线索：**
   - **睡眠（`S`）：**通常无害，除非该睡眠与某个活跃的待履行义务（例如等待中的 binder 回复）重叠。
   - **Running/Runnable（`R`）：**在把延迟单独归因于代码低效之前，先检查 `cpu_frequency`、降频计数器、调度延迟和核心迁移（参见指导原则 7）。
     - 查询 trace 和 `slice` 表，既要看时长最长的切片，也要看重复的微操作或空隙，以免视野过窄。
5. **在状态切换处下钻：**对每个显著分桶，查询线程在进入和退出该状态时正在执行什么。把未跟踪或含义不清的片段标记为 `[GAP]`。不要猜测。

### 步骤 3：领域与提示发现

1. 对 `$SKILL_ROOT/analysis/workflows/perfetto-trace-analysis/references/hints/` 下各文件的 frontmatter（`category:`、`description:`、`keywords:`）做递归搜索，找出与当前整体排查状态（例如观察到的受害者、受影响的子系统和中间进程）匹配的提示文件。
2. 在步骤 4 的排查中阅读并应用所有*匹配*到的提示文件——其中包含经过专家审核的诊断方法和指南，对发现不易察觉的瓶颈至关重要。在步骤 6 的输出中把所有已应用的提示文件列在 `Applied Hints` 下。

### 步骤 4：穷尽式根本原因遍历

1. **沿依赖链追到叶子：**如果受害者线程被阻塞或在等待另一个线程或进程，就跨进程边界沿着唤醒者和服务端链继续追踪，直到叶子节点。不要停在中间唤醒者上（参见指导原则 4）。

   - **动态注入提示：**如果遍历进入新的子系统或进程，就在 `$SKILL_ROOT/analysis/workflows/perfetto-trace-analysis/references/hints/` 中做一次针对性的 frontmatter 搜索，看是否有新的适用提示。
   - **状态分桶的退出状态：**每次状态分桶排查都应以三种状态之一收尾：*终态根本原因*、*被另一线程阻塞*或*部分嫌疑*。

     **每个状态分桶的决策矩阵：**

     | 结果 / 发现 | 动作 | 判断标准 \& 示例 |
     |---|---|---|
     | **被另一线程阻塞** | **继续遍历** | 跨线程和进程边界沿唤醒者/依赖链追踪，找出阻塞方当时在等什么。 |
     | **终态：物理瓶颈** | **停止并分类** | 温度降频、GPU 饱和、存储或 I/O 瓶颈。 |
     | **终态：软件低效** | **停止并分类** | 代码做了不成比例的工作（例如主线程上的同步磁盘 I/O、分配抖动）。 |
     | **终态：调度 / 平台** | **停止并分类** | 后台 CPU 配额、cgroup 上限、前台服务限制。 |
     | **终态：外部服务阻塞** | **停止并分类** | 平台层面的争用且没有更多可追的跳（例如 `system_server` 锁、`SurfaceFlinger` 限流）。 |
     | **部分嫌疑** | **停止并标记 `[GAP]`** | 因数据缺失而无法验证的路径。 |

2. **下结论前做一次系统性扫描：**发现应用层代码低效并不终止排查。应用指导原则 7 去核实平台层面的干扰因素是否同时在扩展后的症状窗口*周边*拖慢了性能。把发现的干扰因素报告为共同根本原因或时长修正项。

### 步骤 5：为负载补充上下文

确定机械层面的瓶颈之后，查询 trace 以找出触发它的高层用户功能、UI 操作或
具体负载。要解释*为什么*，而不只是*是什么*，以确保给出的建议对工程师来说
清晰且可执行。

### 步骤 6：输出格式

严格按照以下 schema 输出排查结果：

    # Investigation Result

    - **Candidate:** [Package / Thread / Classification]
    - **Symptom Window:** [Start TS] - [End TS] ([Duration ms])
    - **Budget (Expected Duration):** [If known / applicable, else "N/A"]
    - **Applied Hints:** [List of matched hint files used]

    ## Primary Finding

    - **Classification:** [Hardware | Software/Code | System Exhaustion | Scheduling Policy | External Dependency]
    - **Details and Reasoning:** `___`
    - **Explained Duration:** `[X ms (Y% of window)]`
    - **Evidence SQL or Backing Data:** `___`
    - **Dependency Chain:** `[Root to Leaf Dependency Chain with UTIDs, UPIDs, and Timestamps]`
    - **Root Cause Conclusion:** `___`

    ## Other Findings / Partial Suspects

    - **Status:** [Partial Suspect | Low Confidence Suspicion | Terminal Root Cause]
    - *(same fields as Primary Finding)*

    ## Verification Checklist

    - [ ] All claims tagged (`[SQL]` / `[GAP]` / `[INFERRED]`)
    - [ ] Total explained duration accounts for the majority of the symptom window
    - [ ] Unexplored state buckets: [None / list with reasons]
    - [ ] Workload contextualized (specific UI actions/slices identified)
