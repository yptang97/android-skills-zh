---
name: ml-kit-genai-prompt-api
description: 分析 Android 代码库以实现 ML Kit GenAI Prompt API。使用
  这个 skill 在端侧向 Gemini Nano 发送自然语言请求，配合 Prompt API 使用结构化
  输出，实现前缀缓存，优化当前提示词，或
  应用最佳实践。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-03'
  keywords:
  - ML Kit
  - Prompt API
  - Structured Output
  - Prefix Caching
  - Gemini Nano
---

这个 skill 提供在 Android 应用中集成和优化 ML
Kit GenAI Prompt API 的分步指导。

## 前置条件

- Android API 级别必须为 26 或更高。如果 `minSdk` 低于 26，请把它更新为 26。
- 把 ML Kit GenAI Prompt API 依赖（`com.google.mlkit:genai-prompt`）添加到应用级的 `build.gradle` 文件，版本至少为 `1.0.0-beta4`。
- 如果使用了 `com.google.mlkit:genai-schema-compiler` 依赖，且 KSP 插件版本低于 2.3.6，请把它更新为 2.3.6。

## 详细步骤

### 1. 提示词优化

要为 ML Kit Prompt API 优化提示词，请遵循
[提示词优化指南](https://developer.android.com/agents/skills/device-ai/prompt-api/references/prompt-optimization)。

### 2. 前缀缓存优化

如果提示词超过 200 个单词，请实现[前缀缓存 API](https://developer.android.com/agents/skills/device-ai/prompt-api/references/prefix-caching)。

### 3. 生命周期与最佳实践

- 在调用第一次推理之前，模型必须已完全下载并可用。请遵循[实现生成式模型](https://developer.android.com/agents/skills/device-ai/prompt-api/references/get-started)指南，在推理前确认模型的 `FeatureStatus` 为 `AVAILABLE`。
- 在 `Activity`、
  `Fragment` 或 `ViewModel` 被销毁时，调用 `close()` 释放 ML Kit 实例。示例：


  ```kotlin
  // Instantiating model in activity, fragment, or ViewModel
      val generativeModel = Generation.getClient()

  // When activity, fragment, or ViewModel is destroyed
      generativeModel.close()
  ```

  <br />

### 4. 结构化输出

在实现或重构提示词以使用结构化输出时，遵循
以下规则：

1. **检查 API 可用性：**使用 `isStructuredOutputFeatureAvailable()` 确认设备支持结构化输出功能。完整说明请参阅[结构化输出 API 指南](https://developer.android.com/agents/skills/device-ai/prompt-api/references/structured-output)。
2. **返回类型：**从函数签名返回 `@Generable` 类型对象，
   而不是返回 `String` 或 JSON 字符串。

   例如：

       fun parseEmail(email: String): String {
           ... 
       }

   应重构为：

       fun parseEmail(email: String): ParsedEmail? {
           ...
       }

3. **示例：**

   这是重构前的示例代码：


   ```kotlin
   suspend fun parseEmail(email: String): String {
       val parseEmailPrompt = "Parse this email and return the sender, title, and short summary of the email less than 10 words: "

       val parsedEmail = generativeModel.generateContent(parseEmailPrompt + email)

       return parsedEmail.candidates[0].text
   }
   ```

   <br />

   这是使用 Structured Output API 后的示例代码：


   ```kotlin
   @Generable
   data class ParsedEmail(
       @Guide(description = "Sender of the email")
       var sender: String = "",

       @Guide(description = "Title of the email")
       var title: String = "",

       @Guide(description = "Summary of the email less than 10 words")
       var summary: String = ""
   )

   suspend fun parseEmail(email: String): ParsedEmail? {
       val parseEmailPrompt =
           "Parse this email: $email"

       val baseRequest = GenerateContentRequest.Builder(TextPart(parseEmailPrompt)).build()
       val typedRequest = generateTypedContentRequest(baseRequest, ParsedEmail::class)
       val typedResponse = generativeModel.generateContent(typedRequest)
       return typedResponse.candidates[0].response
   }
   ```

   <br />
