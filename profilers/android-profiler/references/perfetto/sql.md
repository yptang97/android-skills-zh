本参考文档说明如何用 `trace_processor` 和 PerfettoSQL 从 Perfetto trace 文件
（`.pftrace`、`.perfetto-trace`、`.pb`）中提取数据。在引导式工作流之外做临时查询时读它；
`$SKILL_ROOT/analysis/workflows/` 和 `$SKILL_ROOT/recording/workflows/` 下的工作流
各自带有自己的查询。

所有其他 Perfetto 分析工具（包括 Perfetto UI）都运行在 `trace_processor` 二进制之上。
参考文档：<https://perfetto.dev/docs/analysis/trace-processor>。
> **前置条件 --- `trace_processor` 必须可调用。** 在运行下面任何 shell 命令之前，
> 先读 `$SKILL_ROOT/references/perfetto/setup.md`。它说明了如何让下面这些直接写的
> `trace_processor` 命令在当前环境中可用。

## 查询 trace：会话

查询都通过**会话**进行：先把 trace 一次性加载到一个命名的后台会话中，之后每次查询都用
`--remote` 针对它运行。解析 trace 是开销最大的部分（多 GB 的 trace 需要几十秒）；
会话只承担一次这个代价，而每次真正的分析都会跑不止一个查询。

    # 1. Load the trace into a background session --- once per trace.
    #    Pick a descriptive session name (e.g. derived from the trace file).
    trace_processor server unix --name mysession --daemonize TRACE_FILE

    # 2. Run queries against the warm session: instant, no reparse.
    trace_processor query --remote mysession \
      "SELECT ts, dur, name FROM slice WHERE dur > 5e8 LIMIT 5"

    # 3. When you are completely done with the trace:
    trace_processor server kill mysession

一次调用中支持用 `;` 分隔的多条语句。

会话规则：

- 会话名由 trace_processor 在每用户会话目录中管理 --- 不需要挑选端口，也不会与其他 agent 或 Perfetto UI 冲突。
- **会话状态在多次 `query --remote` 调用之间保留。** 在一次调用中执行的 `CREATE PERFETTO TABLE` 或 `INCLUDE PERFETTO MODULE`，在下一次调用中可见，因此在多次调用之间把中间结果物化是划算的。
- 配置 trace 加载的标志（`--full-sort`、`--add-sql-package` 等）属于 `server unix` 调用，不属于 `query --remote` --- 客户端会拒绝它们并给出说明性错误。
- `--remote` 也接受绝对的 `*.sock` 路径或 `host:port`；直接写名称是最常见的用法。
- 被遗忘的会话在空闲 30 分钟后自动回收（`--idle-timeout`），但分析结束后请自行终止会话。

`TRACE_FILE` 可以是本地路径、`http(s)://` URL，或 Perfetto UI
分享链接（`https://ui.perfetto.dev/#!/?s=<hash>`）--- 在后两种情况下，trace_processor 会替你下载 trace（缓存到
`~/.cache/perfetto/` 或平台的对应位置），并先把分享链接解析成其底层 trace。

如果在小 trace 上只做一次性查询，你*可以*跳过会话
（`trace_processor query TRACE_FILE "..."` 会解析、查询然后退出），
但要把这当作例外：它每次调用都会重新解析 trace，并且会在两次调用之间忘掉已创建的表和已 include 的模块。
默认使用会话。

## 了解 trace 中有什么

PerfettoSQL 提供一张可搜索的内建表，其中包含每个已加载的标准库模块、表、视图、函数、表函数和宏。
用它确认标准库是否已经提供了所需的抽象，再决定是否编写自定义逻辑。

**强制 schema 检查：** 不要猜列名或 join key。在编写查询之前，
始终先用一个简单的 `LIMIT 0` 查询，读取任何表、视图或查询结果的确切列 schema。
> **Intrinsic 接口 --- 不是稳定 API。** 下面的 `__intrinsic_*` 名称是 trace processor 的实现细节。
> 由于本文档已加载，agent 在会话中使用它们是合理的，但
> **不要把 `__intrinsic_*` 名称固化到已提交的脚本、仪表盘或 stdlib 模块中** --- 它们可能随时改变。

    -- Search every documented stdlib object. Start with one precise phrase or
    -- API-like term. In a regexp, `|` means alternatives: prefer
    -- `breadth.first|bfs`, not a broad expression such as `breadth|graph|search`.
    WITH search(pattern) AS (VALUES ('precise phrase|api_term'))
    SELECT o.qualified_name, o.object_type, o.short_description
    FROM __intrinsic_stdlib_objects AS o, search AS s
    WHERE o.exposed = 1
      AND regexp(s.pattern, o.summary, 'i')
    ORDER BY regexp(s.pattern, o.qualified_name, 'i') DESC,
             o.qualified_name
    LIMIT 10;

    -- Once a candidate is found, read one human-friendly document containing its
    -- identity, description, arguments, return value, and result columns.
    SELECT o.summary
    FROM __intrinsic_stdlib_objects AS o
    WHERE o.qualified_name =
      'intervals.overlap.intervals_overlap_count_by_group';

    -- Read the runtime schema of any table, view, or query. LIMIT 0 returns the
    -- result header with no row scan.
    SELECT * FROM slice LIMIT 0;
    INCLUDE PERFETTO MODULE slices.with_context;
    SELECT * FROM thread_or_process_slice LIMIT 0;
    SELECT * FROM (SELECT ts, dur, name FROM slice WHERE dur > 0) LIMIT 0;

任何 trace 的有用起点：

| 视图 | 内容 |
|---|---|
| `slice` | Atrace 切片、异步切片，任何在轨道上有时长的事物 |
| `thread` | 每个线程一行 |
| `process` | 每个进程一行 |
| `thread_state` | 调度状态转换（Running、Runnable、Sleeping、……） |
| `sched_slice` | 线程处于 CPU 上的时间段 |
| `counter` | 时间序列计数器采样 |
| `track` | trace 中的每条轨道；通过 `track_id` 与大多数其他表 join |

公共接口的静态参考（不需要运行中的 trace_processor）：<https://perfetto.dev/docs/analysis/sql-tables>。

## 使用标准库

基于 stdlib 模块构建时，大多数有用的查询会*短得多*，而不是自己 join 原始表。生成的 stdlib 参考：
<https://perfetto.dev/docs/analysis/stdlib-docs>。

在引用某个模块定义的视图、表或宏之前，先 include 该模块：

    INCLUDE PERFETTO MODULE slices.with_context;

    SELECT name, dur, thread_name, process_name
    FROM thread_or_process_slice
    WHERE dur > 1e9                     -- slices longer than 1s
    ORDER BY dur DESC
    LIMIT 20;

几个值得了解的常用模块：

- `slices.with_context` --- 与线程 / 进程 join 后的 slice 行。
- `sched.with_context` --- `sched_slice` 与线程 / 进程 join。
- `android.startup.startups` --- 每次应用启动一行。
- `stacks.cpu_profiling` --- 扁平采样和调用图辅助工具。
- `android.memory.heap_graph.dominator_tree` --- Java 堆转储的保留大小分析。
- `android.startup.startup_breakdowns` --- 启动阶段（`android_startup_opinionated_breakdown`）。
- `android.frames.timeline` --- 帧与卡顿（`android_frames`）。
- `android.anrs` --- ANR（`android_anrs`）。
- `android.binder` --- binder 事务（`android_binder_txns`、`android_binder_metrics_by_process`）。
- `android.memory.lmk` --- 低内存杀进程（`android_lmk_events`）。
- `android.cpu.cluster_type` --- big / mid / little CPU 簇（`android_cpu_cluster_mapping`）；与 `linux.cpu.frequency`（`cpu_frequency_counters`）配合使用。
- `android.oom_adjuster` --- 进程重要性随时间的变化：前台、后台、缓存（`android_oom_adj_intervals`）。

模块名直接对应 stdlib 根目录下的文件路径：
`foo.bar` 位于 `foo/bar.sql`。完整列表见上面链接的 stdlib
参考。

## 编写优秀 PerfettoSQL 的技巧

- **优先用 stdlib。** 如果你发现自己要把 `slice` join 到 `thread_track` 再 join 到 `thread` 再到 `process`，几乎肯定有现成的 stdlib 模块做这件事。写 join 之前先查 stdlib 参考。
- **小心按 `dur > 0` 和 trace 边界过滤。** 有些 slice 的 `dur = -1`（trace 结束时仍未关闭），有些是 `dur = 0`（瞬时事件）。明确表达你要的是哪一种。计算边界框（例如 `ts + dur`）或对时长求和（`SUM(dur)`）时，用 `IIF(dur = -1, trace_end() - ts, dur)` 处理不完整的时长。
- **稳健的状态转换。** 避免用手写时间戳算术（例如 `ts + dur = next.ts`）来 join 相邻事件。依靠标准库模块（例如 `sched.runnable`、`linux.perf.counters`、`intervals.overlap`），它们会安全处理 trace 空隙和抢占。
- **处理标识符：**
  - **join 时使用唯一标识符：** 在 Perfetto 中写 SQL 查询时，必须用 `utid`（唯一线程 ID）或 `upid`（唯一进程 ID）来 join 表，而不是普通的 `tid` 或 `pid`。**为什么有用**：操作系统会复用 `TIDs` 和 `PIDs`，而 `UTIDs` 和 `UPIDs` 在 trace 的生命周期内保持唯一，从而避免错误的 join。
  - `id`、`utid`、`upid`、`track_id` 这类列跨 trace 不稳定，甚至在同一 trace 的不同 trace_processor 运行之间也不稳定。你可以在一条查询**内部**把它们当 join key 用，但在向用户报告结果时，一定要和这些 ID 一起 join 出稳定的名称（`thread.name`、`process.name`、`slice.name`）。
  - **物化昂贵的中间结果。** `CREATE PERFETTO TABLE foo
    AS SELECT ...` 会缓存结果，后续查询不必重做。
  - *`SPAN_JOIN` 注意事项：* 送入 `SPAN_JOIN` 的中间表必须用 `CREATE PERFETTO TABLE` 物化，不能用 `CREATE VIEW`。
- **幂等性。** 确保查询幂等，避免多次执行时出现 "already exists" 错误。
  - 对 Perfetto 对象，始终用 `CREATE OR REPLACE`：`CREATE OR REPLACE
    PERFETTO {TABLE|VIEW|MACRO|FUNCTION}`。
  - 对 SQLite 虚拟表（例如 `SPAN_JOIN`）不支持 `CREATE OR REPLACE`。先显式删除它们：`DROP TABLE IF EXISTS
    my_table; CREATE VIRTUAL TABLE my_table USING SPAN_JOIN(...);`
  - 对标准 SQLite 索引，在前面加上 `DROP INDEX IF EXISTS index_name;`。
- **`SPAN_JOIN` 安全性。** 如果**同一输入表内**的区间重叠，`SPAN_JOIN` 会崩溃。
  始终用 `PARTITIONED {column}` 子句（例如 `PARTITIONED track_id`）隔离区间。
- **在保存的查询中避免 `SELECT *`。** trace processor 的表 schema 可能新增列；把你实际用到的列固定下来。
- **查询慢时用 `EXPLAIN QUERY PLAN`。** 它会显示 SQLite 是否在用索引。计数器和 slice 表在 `ts` 和 `track_id` 上有内置索引；两个都不作为过滤条件的查询会扫描整张表。
- **参数提取：** 用 `EXTRACT_ARG(arg_set_id, 'key')` 获取事件属性，而不是手工 join `args` 表。
- **JSON 解析：** 处理 JSON 文本时，用标准 SQLite JSON 函数（例如 `json_extract()`）提取值。
- **字符串匹配（避免 `LIKE`）。** 用 `GLOB` 或 `regexp()` 代替 `LIKE`。`LIKE` 会造成性能瓶颈，并把下划线（`_`）当通配符，从而引入 bug。
  - **精确匹配：** 用 `=`。
  - **子串匹配：** 用带 `*` 的 `GLOB`（例如 `name GLOB
    '*RenderThread*'`）。
  - **不区分大小写的匹配：** 用 `regexp(pattern, input, 'i')`。它做不区分大小写的部分匹配，不需要 `LOWER()` 或 `*` 通配符（例如 `regexp('renderthread', name, 'i')`）。
- **别名精确性。** 始终给列名加上表或视图别名前缀，即：`{alias}.{column_name}`。

## 常用分析模式

- **计算时间重叠 \& CPU 时间：**
  1. **首选方法（强制）：** 在写自定义区间逻辑之前，始终先搜索标准库。例如，要得到某个 slice 确切的 CPU 执行时间，不要自己算；而是搜索文档并使用 `slices.cpu_time` 模块。
  2. **后备方法（仅在你确认没有适用的 stdlib 模块或
     `SPAN_JOIN` 时使用）：** 如果你必须计算两组时间区间 `[start1, end1]` 与 `[start2, end2]` 之间的自定义重叠时长：
  3. **条件：** 当 `start1 < end2` 且 `start2
     < end1` 时，区间重叠。
  4. **时长：** 重叠时长按 \`MIN(end1, end2)
  5. MAX(start1, start2)\` 计算。
  6. **重要：** 不完整的 Perfetto slice 时长为 -1（`dur = -1`）。套用上述逻辑之前，始终用 `ts +
     IIF(dur = -1, trace_end() - ts, dur)` 计算有效结束时间。
- **窗口大小：** 查找某个特定时间戳附近的事件时，先把窗口大小设为 100ms。
- **总时长：** 要计算匹配某个名称模式（例如 `*{name_pattern}*`）的 slice 所花的总时间，必须对它们的时长求和。**为什么有用**：这有助于量化某个函数或特性在多次调用中对性能的总影响。下面是一个示例查询（注意对不完整 slice 的安全处理）：`sql
  SELECT
  count(*) as total_count,
  sum(IIF(slice.dur = -1, trace_end() - slice.ts, slice.dur)) / 1000000.0 as total_dur_ms
  FROM slice
  WHERE slice.name GLOB '*{name_pattern}*';`

## 分析工作流（标准操作流程）

为确保准确与高效，遵循以下步骤：

1. **调研 \& 剖析：** 确定核心问题和所需的数据点。
2. **强制 schema 校验：** 在 `__intrinsic_stdlib_objects` 中跨模块、表、视图、函数、表函数和宏做全局搜索。过滤 `exposed = 1`。使用一个精确的、不区分大小写的 regexp，优先按 qualified name 匹配排序，并使用 `LIMIT 10`。找到候选后读它的 `summary`；其中包含全部参数、列、返回值和描述性元数据。
   - **意图检查：** 在起草手写算术或自定义 join 之前，必须确认 stdlib 对象是否已经提供了所需的抽象。
   - **重要：** 涉及重叠、交集或区间边界时，在写自定义时间戳算术之前先搜索全局对象表。
3. **起草 \& 校验循环（最多 3 轮）：**

   - \[ \] **起草：** 只用已验证的 schema。确保非 prelude 模块写有 `INCLUDE PERFETTO
     MODULE`。
   - \[ \] **验证幂等性：** 对虚拟表使用 `CREATE OR REPLACE` 或 `DROP TABLE IF
     EXISTS`。
   - \[ \] **检查精确性：** 是否所有列都带了别名前缀（例如 `s.name`）？是否在用 `utid`/`upid` 做 join？
   - \[ \] **字符串匹配：** 是否用了 `=`、`GLOB` 或不区分大小写的 `regexp(..., ..., 'i')` 而不是 `LIKE`？
   - \[ \] **Span Join 检查：** 如果用 `SPAN_JOIN`，表是否已 `PARTITIONED` 并物化？
   - \[ \] **执行：** 针对会话运行：`trace_processor query --remote SESSION "QUERY"`。

   **执行规则：**
   - **文件使用：** 如果你必须创建 SQL 文件来执行查询（例如因为查询过长或转义问题），
   必须把它们创建在 `/tmp/` 目录下。
   - **失败韧性：** 查询失败时调试并修复 SQL 语法和逻辑错误。
   不要为了通过校验而简化分析意图。
   例如，如果要求计算重叠或交集，你就必须修正交集数学。不要用互不相干的查询
   （例如返回各自独立的总时长）来替代。
4. **清理 \& 收尾：**

   - 显式返回并说明最终验证过的 SQL，并向用户解释结果。
   - **保存分析报告。** 在工作目录写一个 markdown 文件（默认 `perfetto_analysis_report.md`），包含：调查的问题、分析的 trace 文件、带具体数字的发现、最终验证过的查询（以便重跑分析），以及未决问题 / 后续步骤。在最终消息中把该文件指给用户。
   - 结束前删除在 `/tmp/` 中创建的任何临时 SQL 文件。

## 更多资料

- 语言导览：<https://perfetto.dev/docs/analysis/perfetto-sql-getting-started>
- trace processor 参考：<https://perfetto.dev/docs/analysis/trace-processor>
- 生成的表参考：<https://perfetto.dev/docs/analysis/sql-tables>
- 生成的 stdlib 参考：<https://perfetto.dev/docs/analysis/stdlib-docs>
