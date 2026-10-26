关于图形性能、UI 卡顿、GPU 内存和帧渲染的专家级提示。
keywords:
- graphics
- ui jank
- gpu
- frame
- vsync
- render
- surfaceflinger
- texture

## - 位图

- 排查 UI 卡顿时，检查主线程上耗时较长的 slice；如果像「ConstraintLayout.onMeasure」这样的 slice 耗时很长（例如 \>8ms），它很可能就是卡顿的原因。
- 当 `bitmap_write_to_parcel` slice 的耗时达到毫秒级而不是微秒级时，检查它的子 slice，看时间花在哪里。耗时过长通常指向不够理想的内核操作，例如内存映射（`mmap`）或不必要的数据清零。
- 要获得图形内存使用情况的高层概览，跟踪特定进程（`upid`）的 `gpu_mem_total` 计数器。
- 要找出最大的图形分配，查询 `android_graphics_allocs` 表并按 `size_bytes` 降序排序。把宽和高与设备的显示分辨率做对比。
- 要检测图像同时存在于 CPU 和 GPU 上造成的「双份内存开销」，请查找 `android_graphics_allocs` 中的大 buffer，以及同一时刻大小相近的 CPU 内存分配（`rss_anon_bytes` 或 `heap_graph`）。
- 要找出可能开销很大的中间渲染目标，请查找 `android_graphics_allocs` 中 `usage_bits` 缺少 `COMPOSER_OVERLAY` 标志的大 buffer。
- 要确认某个分配是否真的在屏幕上呈现，把 `buffer_id` 与 SurfaceFlinger 事件关联起来。
- 要判断高图形内存是否正在造成性能问题，检查 `actual_frame_timeline_slice` 中的帧时长。超过 vsync（例如 16.6ms）的时长与 `gpu_mem_total` 尖峰同时出现，说明存在内存压力导致的卡顿。
- 在出现卡顿的图形应用的主线程中，查找频繁出现或耗时较长的 `texture_upload` slice。
- 分析图形渲染线程中 `eglSwapBuffersWithDamageKHR` 或类似 buffer 交换 slice 的时长。持续时间一直很长，说明每帧都在重绘很大的「damage area」。
- 要识别 UI 卡顿，在主进程上把 `actual_frame_timeline` 与 `expected_frame_timeline` 做对比；出现明显偏差说明有丢帧。
