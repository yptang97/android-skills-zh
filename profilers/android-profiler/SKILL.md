---
name: android-profiler
description: '记录并分析 Android 性能数据，诊断用户应用、系统应用和系统服务中的性能
  瓶颈，即使用户没有明确提到性能分析或 trace 也会启用。适用场景：录制系统 trace、
  CPU 调用栈、Vulkan GPU/DRM 内存或 Java/原生堆分析；分析 Perfetto trace 以定位
  UI 卡顿、掉帧、ANR 或应用启动延迟问题；排查 CPU 瓶颈、IPC/Binder 风暴或线程
  调度阻塞；诊断耗电、modem 电源轨和内核唤醒锁；调试内存压力、低内存终止
  （LMK）、OOM、内存泄漏和分配抖动；执行 A/B 基线 trace 对比以找出性能回退；
  对 Android trace 执行临时的 PerfettoSQL 查询。'
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-22'
  keywords:
  - android performance
  - debugging
  - profiling
  - recording
  - trace analysis
  - memory leaks
  - bottleneck
  - jank
  - SQL
---

你的首要职责是弄清用户想做什么（消除歧义），找到对应的正确指令（工作流发现），
并逐步执行（遵循执行计划）。如果请求不明确，先与用户一起确定执行计划，再继续。

## 前置条件与配置

在执行任何工作流之前，先阅读 [`references/env_setup.md`](references/env_setup.md)。
其中定义了 `$SKILL_ROOT` 应该设为什么——本 skill 中其他所有路径都以它为基准。

## 意图消歧

不要猜测用户的意图。如果用户请求不清楚，在继续之前**询问用户**想做什么。

## 录制

把所有录制请求都交给
[recording/recording_orchestrator](recording/recording_orchestrator.md) 处理。它定义了适用于所有录制
工作流的指南，以及预检或依赖检查，并确保你具备继续所需的配置。阅读该
orchestrator，并根据用户想录制的内容（例如系统 trace 或堆转储）执行它描述的计划。

## 分析

把所有分析请求都交给
[analysis/analysis_orchestrator](analysis/analysis_orchestrator.md) 处理。
