本页介绍如何完成以下操作：

- 把项目配置为使用 Prompt API
- 提供纯文本输入并获取响应
- 提供图像输入并附上相关文本输入，获取响应

有关 Prompt API 的更多细节，参见 Kotlin（[com.google.mlkit.genai.prompt](https://developer.android.com/android/reference/kotlin/com/google/mlkit/genai/prompt/package-summary)）和
Java（[com.google.mlkit.genai.prompt.java](https://developer.android.com/android/reference/com/google/mlkit/genai/prompt/java/package-summary)、
[com.google.mlkit.genai.prompt](https://developer.android.com/android/reference/com/google/mlkit/genai/prompt/package-summary)）的参考文档。

## 配置项目

> [!NOTE]
> **注意：** 此 API 需要 Android API 级别 26 或更高。

在 `build.gradle` 配置中把 ML Kit Prompt API 添加为依赖：

    implementation("com.google.mlkit:genai-prompt:1.0.0-beta2")

如果你需要用 Structured Output API 让响应符合特定格式，
需要配置 KSP 并添加额外依赖。详情见
[生成结构化输出](https://developer.android.com/agents/skills/device-ai/prompt-api/references/structured-output)。

## 实现生成式模型

要在项目中实现这些代码，按以下步骤操作：

- 创建一个 `generativeModel` 对象：

  ### Kotlin

      // Get a GenerativeModel instance
      val generativeModel = Generation.getClient()

  ### Java

      // Get a GenerativeModel instance
      GenerativeModelFutures generativeModelFutures = GenerativeModelFutures
          .from(Generation.INSTANCE.getClient());

- 检查 Gemini Nano 是 `AVAILABLE,`、`DOWNLOADABLE` 还是 `UNAVAILABLE`。然后，
  如果可下载，就下载该功能：

  ### Kotlin

      val status = generativeModel.checkStatus()
      when (status) {
          FeatureStatus.UNAVAILABLE -> {
              // Gemini Nano not supported on this device or device hasn't fetched the latest configuration to support it
          }

          FeatureStatus.DOWNLOADABLE -> {
              // Gemini Nano can be downloaded on this device, but is not currently downloaded
              generativeModel.download().collect { status ->
                  when (status) {
                      is DownloadStatus.DownloadStarted ->
                          Log.d(TAG, "starting download for Gemini Nano")

                      is DownloadStatus.DownloadProgress ->
                          Log.d(TAG, "Nano ${status.totalBytesDownloaded} bytes downloaded")

                      DownloadStatus.DownloadCompleted -> {
                          Log.d(TAG, "Gemini Nano download complete")
                          modelDownloaded = true
                      }

                      is DownloadStatus.DownloadFailed -> {
                          Log.e(TAG, "Nano download failed ${status.e.message}")
                      }
                  }
              }
          }

          FeatureStatus.DOWNLOADING -> {
              // Gemini Nano currently being downloaded
          }

          FeatureStatus.AVAILABLE -> {
              // Gemini Nano currently downloaded and available to use on this device
          }
      }

  ### Java

      ListenableFuture<Integer> status = generativeModelFutures.checkStatus();
      Futures.addCallback(generativeModelFutures.checkStatus(), new FutureCallback<>() {
          @Override
          public void onSuccess(Integer featureStatus) {
              switch (featureStatus) {
                  case FeatureStatus.AVAILABLE -> {
                      // Gemini Nano currently downloaded and available to use on this device
                  }
                  case FeatureStatus.UNAVAILABLE -> {
                      // Gemini Nano not supported on this device or device hasn't fetched the latest configuration to support it
                  }
                  case FeatureStatus.DOWNLOADING -> {
                      // Gemini Nano currently being downloaded
                  }
                  case FeatureStatus.DOWNLOADABLE -> {
                      generativeModelFutures.download(new DownloadCallback() {
                          @Override
                          public void onDownloadStarted(long l) {
                              Log.d(TAG, "starting download for Gemini Nano");
                          }
                          @Override
                          public void onDownloadProgress(long l) {
                              Log.d(TAG, "Nano " + l + " bytes downloaded");
                          }
                          @Override
                          public void onDownloadCompleted() {
                              Log.d(TAG, "Gemini Nano download complete");
                          }
                          @Override
                          public void onDownloadFailed(@NonNull GenAiException e) {
                              Log.e(TAG, "Nano download failed: " + e.getMessage());
                          }
                      });
                  }
              }
          }
          @Override
          public void onFailure(@NonNull Throwable t) {
              // Failed to check status
          }
      }, ContextCompat.getMainExecutor(context));

## 提供纯文本输入

### Kotlin

    val response = generativeModel.generateContent("Write a 3 sentence story about a magical dog.")

### Java

    GenerateContentResponse response = generativeModelFutures.generateContent(
      new GenerateContentRequest.Builder(
        new TextPart("Write a 3 sentence story about a magical dog."))
      .build())
      .get();

也可以添加可选参数：

### Kotlin

    val response = generativeModel.generateContent(
        generateContentRequest(
            TextPart("Write a 3 sentence story about a magical dog."),
        ) {
            // Optional parameters
            temperature = 0.2f
            topK = 10
            candidateCount = 3
        },
    )

### Java

    GenerateContentRequest.Builder requestBuilder =
            new GenerateContentRequest.Builder(
                    new TextPart("Write a 3 sentence story about a magical dog."));
    requestBuilder.setTemperature(.2f);
    requestBuilder.setTopK(10);
    requestBuilder.setCandidateCount(3);

    GenerateContentResponse response =
            generativeModelFutures.generateContent(requestBuilder.build()).get();

有关可选参数的更多信息，见[可选
配置](https://developer.android.com/agents/skills/device-ai/ml-kit-genai-prompt-api/references/get-started#optional-configurations)。

## 提供多模态（图像与文本）输入

在 `generateContentRequest()` 函数中把图像和文本输入打包在一起，
文本提示词是与该图像相关的问题或命令。你可以在同一个请求中打包多张图像和文本。

### Kotlin

    val response = generativeModel.generateContent(
        generateContentRequest(ImagePart(bitmap), TextPart(textPrompt)) {
            // optional parameters
            ...
        },
    )

### Java

    GenerateContentResponse response = generativeModelFutures.generateContent(
        new GenerateContentRequest.Builder(
            new ImagePart(bitmap),
            new TextPart("textPrompt"))
        // optional parameters
        .build())
    .get();

## 处理推理结果

- 运行推理并取回结果。对纯文本提示和多模态提示，你都可以选择等待
  完整结果，或在生成过程中流式返回响应。

  - 这种方式使用非流式推理，即从 AI 模型取回完整结果后
    再返回：

  ### Kotlin

      // Call the AI model to generate content and store the complete
      // in a new variable named 'response' once it's finished
      val response = generativeModel.generateContent("Write a 3 sentence story about a magical dog")

  ### Java

      GenerateContentResponse response = generativeModelFutures.generateContent(
              new GenerateContentRequest.Builder(
                      new TextPart("Write a 3 sentence story about a magical dog."))
                      .build())
              .get();

  - 以下代码片段是使用流式推理的示例，流式推理会在结果生成过程中
    分块取回：

  ### Kotlin

      // Streaming inference
      var fullResponse = ""
      generativeModel.generateContentStream("Write a 3 sentence story about a magical dog").collect { chunk ->
          val newChunkReceived = chunk.candidates[0].text
          print(newChunkReceived)
          fullResponse += newChunkReceived
      }

  ### Java

      // Streaming inference
      StringBuilder fullResponse = new StringBuilder();
      generativeModelFutures.generateContent(new GenerateContentRequest.Builder(
          (new TextPart("Write a 3 sentence story about a magical dog"))).build(),
              chunk -> {
                  Log.d(TAG, chunk);
                  fullResponse.append(chunk);
              });

有关流式与非流式推理的更多信息，见[流式
与非流式](https://developer.android.com/ml-kit/genai#streaming-vs-non)。

## 延迟优化

为优化首次推理调用，你的应用可以选择调用
`warmup()`。这会把 Gemini Nano 加载到内存中并初始化运行时
组件。

## 可选配置

在每个 `GenerateContentRequest` 中，你可以设置以下可选
参数：

- `temperature`：控制 token 选择中的随机程度。
- `seed`：用于生成稳定且确定性的结果。
- `topK`：控制结果的随机性和多样性。
- `candidateCount`：请求返回的不重复响应数量。注意实际响应数可能与 `candidateCount` 不同，因为重复的响应会被自动移除。
- `maxOutputTokens`：定义响应中可生成的 token 上限。

关于设置可选配置的更多指引，见
[`GenerateContentRequest`](https://developer.android.com/android/reference/kotlin/com/google/mlkit/genai/prompt/GenerateContentRequest)。

## 支持的功能与限制

- 输入必须少于 4000 个 token（约 3000 个英文单词）。更多信息见 [`countTokens`](https://developer.android.com/android/reference/com/google/mlkit/genai/prompt/GenerativeModel#countTokens(com.google.mlkit.genai.prompt.GenerateContentRequest)) 参考。
- 应避免需要长输出（超过 4K token）的使用场景。
- AICore 对每个应用强制执行推理配额。更多信息见[每应用
  配额](https://developer.android.com/ml-kit/genai#quota-per)。
