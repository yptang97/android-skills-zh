把自然语言的数据意图转换为语法合法的 PerfettoSQL 查询，并在提供了 trace 文件时对其执行这些查询。当你需要
起草、调试或执行查询，从 Android Perfetto trace 中通过 trace_processor 提取
slice、线程或内存数据时，使用这个工作流。
keywords:
- Perfetto SQL
- SQL Guidelines
- SQL Best Practices
- Ad-hoc Query
- Trace Processor
- SPAN_JOIN

## - 幂等性

使用这个工作流来编写、调试或执行 PerfettoSQL 查询：

- **对 trace 执行：**如果提供了 trace 文件的路径或 URL，先在 `$SKILL_ROOT/references/perfetto/setup.md` 中确认环境前置条件，然后遵循 `$SKILL_ROOT/references/perfetto/sql.md` 中定义的会话执行工作流与实践。
- **静态编写或调试查询：**如果未附加 trace，使用 `$SKILL_ROOT/references/perfetto/sql.md` 中的语法、schema 指南和标准库最佳实践来起草、优化或调试查询。