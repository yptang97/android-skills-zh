---
name: anr-audit-and-fix
description: 审计 Android 代码库中的 ANR 风险，并诊断 ANR 堆栈转储。
  在扫描 Android 代码以查找 ANR 风险或分诊 ANR 堆栈转储时使用这个 skill。
  不要用于非 ANR 的崩溃、掉帧、通用 CPU 性能分析或 Perfetto 系统跟踪。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-16'
  keywords:
  - Android
  - ANR
  - Application Not Responding
  - responsiveness
  - main thread
  - ANR stack dump
  - Sync Barrier Leak
---

选择与用户请求相匹配的执行路径：

## 1. 路径 A：静态代码库 ANR 风险审计

审计源文件或扫描线程阻塞操作时：

- 逐步遵循 [references/risk_analysis_guide.md](references/risk_analysis_guide.md)：列出候选点、**证明执行线程**（当线程取决于调用方时跟踪调用链）、**证明该调用会阻塞**，然后归因并定级。只报告通过这些检查的候选点；把排除掉的单独列出，各附一行原因。
- 评估对已附加 View 的非主线程修改时，不要只把它当作崩溃风险（`CalledFromWrongThreadException`），还要当作**同步屏障泄漏 ANR**风险，并给出各自的证据（非主线程执行，加上已附加的 View）。

## 2. 路径 B：由跟踪驱动的诊断与修复

分析 ANR 跟踪或堆栈转储时：

- 使用 [references/trace_analysis_guide.md](references/trace_analysis_guide.md) 系统诊断，并用 [references/anr_trace_report_template.md](references/anr_trace_report_template.md) 组织报告格式。
- 结论严格基于日志证据。只对 `APP_DEFECT` 或 `APP_RESOURCE_OVERLOAD` 提出应用侧修复（绝不对 `EXTERNAL_BOTTLENECK` 提出）。
