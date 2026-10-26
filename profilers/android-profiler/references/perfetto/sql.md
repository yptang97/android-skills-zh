本文介绍如何使用 `trace_processor` 和 PerfettoSQL 从 Perfetto trace 文件
（`.pftrace`、`.perfetto-trace`、`.pb`）中提取数据。
在引导式工作流之外做临时查询时阅读本文；`$SKILL_ROOT/analysis/workflows` 和
`$SKILL_ROOT/recording/workflows` 下的工作流各自带有自己的查询。

`trace_processor` 二进制是所有其他 Perfetto 分析工具（包括 Perfetto UI）的运行
基础。参考文档：
<https://perfetto.dev/docs/analysis/trace-processor>。
> **前置条件——`trace_processor` 必须可调用。**在运行下面任何 shell 命令之前，
> 先读 `$SKILL_ROOT/references/perfetto/setup.md`。它说明了如何让下文那些裸
> `trace_processor` 命令在当前环境中可用。

## 查询 trace：会话

查询通过**会话**进行：把 trace 一次性载入一个命名的后台会话，然后用 `--remote`
对它执行每个查询。解析 trace 是昂贵的那一步（多 GB 的 trace 需要几十秒）；会话
只付一次这个代价，而任何真实分析都会执行不止一个查询。

    # 1. Load the trace into a background session - once per trace.
    #    Pick a descriptive session name (e.g. derived from the trace file).
    trace_processor server unix --name mysession --daemonize TRACE_FILE

    # 2. Run queries against the warm session: instant, no reparse.
    trace_processor query --remote mysession \
      "SELECT ts, dur, name FROM slice WHERE dur > 5e8 LIMIT 5"

    # 3. When you are completely done with the trace:
    trace_processor server kill mysession

支持在一次调用中用 `;` 分隔多条语句，但只有最后一条可以返回行（例如
`INCLUDE PERFETTO MODULE ...; SELECT ...`）。其余每个 `SELECT` 都单独调用。

会话规则：

- 会话名由 trace_processor 在每用户会话目录中管理——没有端口需要挑选，也不会与其他 agent 或 Perfetto UI 冲突。
- **会话状态在多次 `query --remote` 调用之间保持。**一次调用中执行的 `CREATE PERFETTO TABLE` 或 `INCLUDE PERFETTO MODULE` 在下一次中可见，因此物化中间结果能在多次调用中得到回报。
- 配置 trace 加载的选项（`--full-sort`、`--add-sql-package` 等）属于 `server unix` 调用，不属于 `query --remote`——客户端会拒绝它们并给出说明性错误。
- `--remote` 也接受绝对的 `*.sock` 路径或 `host:port`；名称是最常见的用法。
- 被遗忘的会话会在空闲 30 分钟后自动回收（`--idle-timeout`），但分析结束后请主动杀掉你的会话。

`TRACE_FILE` 可以是本地路径、`http(s)://` URL 或 Perfetto UI 分享链接
（`https://ui.perfetto.dev/#!/?s=<hash>`）——后两种情况下
trace_processor 会替你下载 trace（缓存在 `~/.cache/perfetto/` 或平台等价位置），
并先把分享链接解析成其底层 trace。

对于小 trace 上的一次性临时查询，你*可以*跳过会话
（`trace_processor query TRACE_FILE "..."` 会解析、查询然后退出），但请把这视为
例外：它每次调用都会重新解析 trace，并在调用之间忘记已创建的表和已包含的模块。
默认使用会话。

## 发现 trace 里有什么

PerfettoSQL 自带**内省表函数**，用于浏览已加载的标准库——模块、表/视图、函数、
宏。用它们来了解有哪些可用内容，并在编写自定义逻辑之前确认某个标准库模块是否
已经提供了所需的抽象。

**强制的 schema 检查：**不要猜测列名或连接键。在起草查询之前，始终用朴素的
`LIMIT 0` 查询读取任何具体表、视图或查询结果的精确列 schema。
> **内省接口并非稳定 API。**下面这些 `__intrinsic_*` 名称是 trace processor 的
> 实现细节。因为本参考已加载，agent 在会话中使用它们是合理的，但**不要把
> `__intrinsic_*` 名称固化进提交的脚本、dashboard 或 stdlib 模块**——它们可能
> 在无通知的情况下改变。

    -- 1. List every stdlib module currently available.
    SELECT package, module FROM __intrinsic_stdlib_modules ORDER BY 1, 2;

    -- 2. List the tables/views a specific module exposes
    --    (after INCLUDE PERFETTO MODULE).
    INCLUDE PERFETTO MODULE slices.with_context;
    SELECT name, type, exposed, description
    FROM __intrinsic_stdlib_tables('slices.with_context');

    -- 3. List functions / macros a module exposes.
    SELECT name, return_type, args
    FROM __intrinsic_stdlib_functions('slices.with_context');
    SELECT name, return_type, args
    FROM __intrinsic_stdlib_macros('android.memory.heap_graph.helpers');

    -- 4. Read the column schema of any table, view, or query.
    --    LIMIT 0 returns the result header with no row scan; trace_processor
    --    prints "column N = <name>" lines for each column.
    SELECT * FROM slice LIMIT 0;
    SELECT * FROM thread_or_process_slice LIMIT 0;
    SELECT * FROM (SELECT ts, dur, name FROM slice WHERE dur > 0) LIMIT 0;

任何 trace 都有用的起点：

| 视图 | 里面有什么 |
|---|---|
| `slice` | Atrace 切片、异步切片，以及轨道上任何带时长的东西 |
| `thread` | 每个线程一行 |
| `process` | 每个进程一行 |
| `thread_state` | 状态转换（Running、Runnable、Sleeping 等） |
| `sched_slice` | 线程在 CPU 上的时段 |
| `counter` | 时间序列计数器采样 |
| `track` | trace 中的每条轨道；通过 `track_id` 与其他表连接 |

公共接口的静态参考（无需运行中的 trace_processor）：
<https://perfetto.dev/docs/analysis/sql-tables>。

## 使用标准库

在标准库模块之上构建，比自己去连接原始表能让大多数有用的查询*短得多*。生成的
标准库参考：<https://perfetto.dev/docs/analysis/stdlib-docs>。

在引用某个模块定义的视图、表或宏之前，先包含该模块：

    INCLUDE PERFETTO MODULE slices.with_context;

    SELECT name, dur, thread_name, process_name
    FROM thread_or_process_slice
    WHERE dur > 1e9                     -- slices longer than 1s
    ORDER BY dur DESC
    LIMIT 20;

能回答大多数问题的模块：

| 问题 | 模块（`INCLUDE PERFETTO MODULE ...`） | 主表 |
|---|---|---|
| 带线程/进程名的切片 | `slices.with_context` | `thread_slice`, `process_slice`, `thread_or_process_slice` |
| 切片的精确 CPU 时间 | `slices.cpu_time` | `thread_slice_cpu_time` |
| 每个线程/进程的 CPU 时间 | `sched.with_context` | `sched_with_thread_process` |
| 应用启动及其各阶段 | `android.startup.startups`, `android.startup.startup_breakdowns` | `android_startups`, `android_startup_opinionated_breakdown` |
| 帧与卡顿 | `android.frames.timeline` | `android_frames` |
| ANR | `android.anrs` | `android_anrs` |
| Binder 事务 | `android.binder` | `android_binder_txns`, `android_binder_metrics_by_process` |
| 低内存终止、进程 RSS | `android.memory.lmk`, `linux.memory.process` | `android_lmk_events`, `memory_rss_and_swap_per_process` |
| CPU 频率、簇 | `linux.cpu.frequency`, `android.cpu.cluster_type` | `cpu_frequency_counters`, `android_cpu_cluster_mapping` |
| Java 堆保留大小与图 | `android.memory.heap_graph.dominator_tree`, `graphs.search` | `heap_graph_dominator_tree`, `graph_reachable_bfs!` |
| CPU 采样栈 | `stacks.cpu_profiling` | `cpu_profiling_samples` |
| 区间重叠 / 相交 | `intervals.intersect`, `intervals.overlap` | `_interval_intersect!`, `interval_merge_overlapping!`, `intervals_overlap_count!` |

模块名直接对应 stdlib 根下的文件路径：`foo.bar` 位于 `foo/bar.sql`。完整列表可在
上面链接的 stdlib 参考中浏览。

## 编写优质 PerfettoSQL 的技巧

- **优先用标准库。**如果你发现自己要把 `slice` 连到 `thread_track` 再连到 `thread` 再连到 `process`，那几乎肯定已有标准库模块替你做了这件事。写连接之前先查标准库参考。
- **谨慎处理 `dur > 0` 与 trace 边界。**有些切片的 `dur = -1`（到 trace 结束时仍未闭合），有些是 `dur = 0`（瞬时事件）。要明确你指的是哪一种。计算边界盒（例如 `ts + dur`）或累加时长（`SUM(dur)`）时，用下面的写法处理不完整时长：`IIF(dur = -1, trace_end() - ts, dur)`。
- **稳健地处理状态转换。**不要用人工时间戳算术（例如 `ts + dur = next.ts`）来拼接相邻事件。依靠标准库模块（例如 `sched.runnable`、`linux.perf.counters`、`intervals.overlap`），它们会安全地处理 trace 空隙和抢占。
- **处理标识符：**
  - **连接时使用唯一标识符：**在 Perfetto 中编写 SQL 查询时，必须用 `utid`（唯一线程 ID）或 `upid`（唯一进程 ID）来连接表，而不是普通的 `tid` 或 `pid`。**为什么有用**：操作系统会回收 `TIDs` 和 `PIDs`，而 `UTIDs` 和 `UPIDs` 在整个 trace 生命周期内保持唯一，从而避免错误连接。
  - `id`、`utid`、`upid`、`track_id` 这类列在不同 trace 之间、甚至同一 trace 的不同 trace_processor 运行之间都不稳定。你可以在查询**内部**把它们当作连接键使用，但在向用户报告结果时，务必同时连出稳定名称（`thread.name`、`process.name`、`slice.name`）。
  - **物化昂贵的中间结果。**`CREATE PERFETTO TABLE foo AS SELECT ...` 会缓存结果，使后续查询不必重做。
  - *`SPAN_JOIN` 注意事项：*喂给 `SPAN_JOIN` 的中间表必须用 `CREATE PERFETTO TABLE` 物化，不能用 `CREATE VIEW`。
- **幂等性。**确保查询是幂等的，以避免多次执行时出现「already exists」错误。

  - 对 Perfetto 对象，始终使用 `CREATE OR REPLACE`：`CREATE OR REPLACE PERFETTO {TABLE|VIEW|MACRO|FUNCTION}`。
  - 对 SQLite 虚拟表（例如 `SPAN_JOIN`），不支持 `CREATE OR REPLACE`。要先显式删除：

      DROP TABLE IF EXISTS my_table;
      CREATE VIRTUAL TABLE my_table USING SPAN_JOIN(...);

  - 对标准 SQLite 索引，先加上 `DROP INDEX IF EXISTS index_name;`。
- **`SPAN_JOIN` 的安全性。**如果**同一输入表内**的区间相互重叠，`SPAN_JOIN` 会崩溃。始终使用 `PARTITIONED {column}`（例如 `PARTITIONED track_id`）子句来隔离区间。

- **在保存的查询中避免 `SELECT *`。**trace processor 的表 schema 可能新增列；请固定写出你实际使用的列。

- **查询慢时使用 `EXPLAIN QUERY PLAN`。**它会显示 SQLite 是否在用索引。计数器表和切片表在 `ts` 和 `track_id` 上有内置索引；两个都不做过滤的查询会全表扫描。

- **提取参数：**用 `EXTRACT_ARG(arg_set_id, 'key')` 读取事件属性，而不是手工连接 `args` 表。

- **解析 JSON：**处理 JSON 文本时，使用标准 SQLite JSON 函数（例如 `json_extract()`）提取值。

- **字符串匹配（避免 `LIKE`）。**用 `GLOB` 代替 `LIKE`。`LIKE` 会造成性能瓶颈，并把下划线（`_`）当作通配符，从而引入 bug。

  - **精确匹配：**使用 `=`。
  - **子串匹配：**使用带 `*` 的 `GLOB`（例如 `name GLOB '*RenderThread*'`）。
  - **不区分大小写匹配：**使用 `LOWER(name) GLOB`，并确保搜索串全为小写（例如 `LOWER(name) GLOB '*renderthread*'`）。当 trace 中的大小写不一致时（例如 `WakeLock` 与 `wakelock`）使用这种写法。
- **别名要精确。**始终给列名加上表别名或视图别名前缀，即：`{alias}.{column_name}`。

## 常见分析模式

- **计算时间重叠与 CPU 时间：**

  1. **主要方法（强制）：**在编写自定义区间逻辑之前，始终先搜标准库。例如，要得到某个切片的精确 CPU 执行时间，不要手算；而应查阅文档并使用 `slices.cpu_time` 模块。
  2. **兜底方法（仅在确认没有适用的标准库模块或
     `SPAN_JOIN` 时使用）：**如果必须手算两组时间区间 `[start1, end1]` 与 `[start2, end2]` 之间的重叠时长：
     - **条件：**当 `start1 < end2` 且 `start2 < end1` 时，两区间重叠。
     - **时长：**重叠时长按 `MIN(end1, end2) - MAX(start1, start2)` 计算。
     - **重要：**未闭合的 Perfetto 切片时长为 -1（`dur = -1`）。在套用此逻辑之前，始终用 `ts + IIF(dur = -1, trace_end() - ts, dur)` 计算有效结束时间。
- 对于应用启动请求，包含 `android.startup.startups` 模块并查询
  `android_thread_slices_for_all_startups`（或 `android_startups`）。

- 把 `counter_track` 与 `counter` 连接，以取得特定名称计数器的值。

- 查询 CPU 频率计数器时，包含 `linux.cpu.frequency` 模块并使用
  `cpu_frequency_counters` 表。

- **窗口大小：**查找特定时间戳附近的事件时，先用 100ms 作为窗口大小。

- **总时长：**要计算匹配某个名称模式（例如 `*{name_pattern}*`）的所有切片的总耗时，
  必须把它们的时长求和。**为什么有用**：这有助于量化某个函数或功能在多次调用中
  对性能的总影响。下面是一个示例查询（注意对不完整切片的安全处理）：

      SELECT
        count(*) as total_count,
        sum(IIF(slice.dur = -1, trace_end() - slice.ts, slice.dur)) / 1e6
          as total_dur_ms
      FROM slice
      WHERE slice.name GLOB '*{name_pattern}*';

- **CPU 簇与频率分析：**

  - 用 `INCLUDE PERFETTO MODULE android.cpu.cluster_type;`（`android_cpu_cluster_mapping`）给 CPU 核分簇（big、mid、little），并用 `INCLUDE PERFETTO MODULE linux.cpu.frequency;` 计算按时间加权的频率。
- **Binder 事务分析：**

  - 使用 `android_binder_txns` 或 `android_binder_metrics_by_process` 这类标准库视图（`INCLUDE PERFETTO MODULE android.binder;`）查询跨进程 Binder 调用，并按进程名（`client_process`、`server_process`、`process_name`）分组。

## 分析工作流（标准操作流程）

为确保准确与高效，请遵循以下步骤：

1. **研究与拆解：**确定核心问题和所需的数据点。
2. **强制的 schema 校验：**通过 `__intrinsic_stdlib_modules` 定位相关模块，通过 `__intrinsic_stdlib_tables('module_name')` 定位其表。核实列名和类型。
   - **意图检查：**在起草手工算术或自定义连接之前，必须确认标准库模块是否已经提供了所需抽象。

- **重要：**如果你的查询需要计算区间之间的重叠、相交或边界，必须先全局搜索 `__intrinsic_stdlib_modules`（例如 `WHERE module GLOB '*overlap*'`），再考虑编写 `MIN()/MAX()` 或 `IIF(dur = -1...)` 逻辑。

1. **起草与校验循环（最多 3 轮）：**

- \[ \] **起草：**只使用已验证的 schema。确保非 prelude 模块都写了 `INCLUDE PERFETTO MODULE`。
- \[ \] **验证幂等性：**对虚拟表使用 `CREATE OR REPLACE` 或 `DROP TABLE IF EXISTS`。
- \[ \] **检查精度：**是否所有列都带了别名前缀（例如 `s.name`）？是否按 `utid`/`upid` 连接？
- \[ \] **字符串匹配：**是否用 `GLOB` 或 `=` 代替了 `LIKE`？
- \[ \] **Span Join 检查：**如果使用 `SPAN_JOIN`，表是否已 `PARTITIONED` 并物化？
- \[ \] **执行：**对会话运行：`trace_processor query --remote SESSION "QUERY"`。

**执行规则：**

- **文件使用：**如果必须创建 SQL 文件来执行查询（例如因查询过长或转义问题），必须把它们建在 `/tmp/` 目录下。
- **失败韧性：**查询失败时调试并修正 SQL 语法与逻辑错误。不要为了通过校验而简化分析意图。例如，如果要求计算重叠或相交，你必须修正相交的算法，不要用互不相干的查询（例如返回各自独立的总时长）来绕过。

1. **清理与收尾：**

- 显式返回并说明最终校验过的 SQL，并向用户解释结果。
- **保存分析报告。**在工作目录中写一个 markdown 文件（默认 `perfetto_analysis_report.md`），包含：所调查的问题、分析的 trace 文件、带具体数字的发现、最终校验过的查询（以便重跑分析），以及未决问题 / 后续步骤。在最终消息中指引用户去看它。
- 完成之前，删除在 `/tmp/` 中创建的任何临时 SQL 文件。

## 进一步查阅

- 语言导览：<https://perfetto.dev/docs/analysis/perfetto-sql-getting-started>
- trace processor 参考：<https://perfetto.dev/docs/analysis/trace-processor>
- 生成的表参考：<https://perfetto.dev/docs/analysis/sql-tables>
- 生成的标准库参考：<https://perfetto.dev/docs/analysis/stdlib-docs>
