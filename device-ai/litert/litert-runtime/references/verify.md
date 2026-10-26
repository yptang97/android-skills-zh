## 先取得参考输出

把源模型针对某组固定输入产生的输出保存在它自己的框架里，或者在开发机上用 Python 包
`ai-edge-litert` 从同一个 `.tflite` 文件得到（使用同样的 `CompiledModel` API：
`CompiledModel.from_file(path)`，然后写入、运行、读取）。`litert-samples` 里的
`qwen3_tts` recipe 就以 `dump_*_ref.py` 的形式提供这类源模型导出结果。
这份输出是每个在运行 Android 的设备上执行的运行的基准真值。

## 先 CPU，再 GPU

先用 `Accelerator.CPU` 运行这组固定输入，并与参考输出比较；
如果这里就出现差异，问题在模型文件或预处理，而不在设备。
接着用 `Accelerator.GPU` 运行，并从两方面比较：

1. **数值**：计算与参考导出之间的最大绝对差和 Pearson 相关系数。
2. **任务结果**：检查任务层面的结果是否一致（top-1 argmax、分割掩码或输出文本）。因为 GPU 用 FP16 计算，最低有效位会略有变化，而任务结果不应该改变。

## 诊断指标

- **首次推理慢**：GPU shader 编译发生在第一次执行期间。辅助构造函数的预热调用会吸收这部分开销；绝不要把第一次运行计入计时指标。
- **为 GPU 执行计时**：在 GPU 上，要把 `model.run` 和 `readFloat` 一起测量，因为输出缓冲区回读正是应用等待 GPU 完成的地方。

## 仅在设备上出现的失败

- **`CompiledModel.create` 搭配 `Accelerator.GPU` 抛出 `Failed to compile
  model`**：由 GPU 不支持的算子引起（Logcat 会记录 `Following operations are not supported by GPU delegate`）。在 `Accelerator.CPU` 上运行模型，或重新导出不含该算子的模型。
- **`NaN` 或损坏的数值只在 `Accelerator.GPU` 上出现**：由模型中的 FP16 范围溢出引起。在 `Accelerator.CPU` 上运行模型，或用 FP16 安全的图改写重新导出。
- **加载超过 100
  MB 的未量化 FP32 模型时进程终止**：设备 RAM 不足。加载前先量化或拆分模型。

## 记录

记录设备型号、LiteRT 版本、加速器、最大绝对差和任务结果（在应用的 `README` 里每台设备一行）。当
`Accelerator.CPU` 运行结果与参考输出不同时，检查模型本身（例如转换后或量化后的模型精度、GPU 算子
驻留情况，或 FP16 范围溢出这类仅在设备上出现的失败）。
