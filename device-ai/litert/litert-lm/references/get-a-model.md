本文件把模型相关的工作分给 agent 和用户。agent 只写应用代码。用户负责挑选、下载和转换模型文件。

## 从 litert-community 选择文件

Hugging Face 的 `litert-community` 每个模型一个仓库，例如
`litert-community/gemma-4-E2B-it-litert-lm` 和 `litert-community/Qwen3-0.6B`。
用前者的 `gemma-4-E2B-it.litertlm`，或后者的 `Qwen3-0.6B.litertlm`；两者都能在 CPU 和 GPU 上运行。

仓库中的其他文件是同一模型的其他构建版本：

- 其他量化方案和上下文长度。Qwen3 模型卡会列出每个文件的量化方式、以 token 计的上下文长度和文件大小。
- Web 构建版本，带 `-web` 后缀。
- 针对单一芯片的构建版本，以芯片命名，例如 `_Google_Tensor_G5` 或 `.mediatek.mt6993`。这些是 NPU 构建版本，本 skill 不涉及。

用户没有指定文件时，用本节提到的两个文件之一。不要选 Web 构建或 NPU 构建。

## 编写应用内下载代码

下载 URL 是 `https://huggingface.co/<repo>/resolve/main/<file>`。在应用中编写下载代码时，遵循这些规则：

- 把文件写入 `filesDir`；应用使用 `DownloadManager` 时则写入 `getExternalFilesDir(null)`。
- 把路径传给引擎之前，用模型卡上的大小核对下载文件的大小。
- 绝不把文件放进 `assets/` 或 APK 里。
- 绝不在 agent 自己的会话中下载模型文件。文件从数百 MB 到几 GB 不等。

## 没有 .litertlm 文件时

本 skill 不做模型转换。告诉用户转换是在工作站上单独完成的一步，绝不在应用内进行。用户用
`litert-torch` 导出模型，用 `ai-edge-quantizer` 量化，再用 `litert-lm` 包里的
`litert_lm_builder` 把 tokenizer 和元数据打包成 `.litertlm` 文件。
