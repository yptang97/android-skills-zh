> [!NOTE]
> **注意：** 前缀缓存尚属实验性功能，将来可能变化。该功能目前仅在 Prompt API 支持的部分设备上可用，后续会支持更多设备。我们鼓励你在 Pixel 设备上试用这个 API，了解它能为你的具体使用场景带来多少推理延迟改善。

*前缀缓存*是一项通过存储并复用处理共享且重复出现的提示词前缀部分时产生的中间 LLM 状态，来缩短推理时间的功能。要启用前缀缓存，你只需在 API 请求中把静态前缀与动态后缀分开。

前缀缓存目前仅支持纯文本输入，因此如果你的提示词中包含图像，就不应使用该功能。

实现前缀缓存有两种方式：隐式或显式：

- [隐式（自动）前缀缓存](https://developer.android.com/agents/skills/device-ai/ml-kit-genai-prompt-api/references/prefix-caching#implicit)是一种轻量方式，应用只需定义提示词中共享的那部分。
- [显式（手动）前缀缓存](https://developer.android.com/agents/skills/device-ai/ml-kit-genai-prompt-api/references/prefix-caching#explicit)让应用对缓存有更多控制，包括缓存的创建、查询与删除。

## 隐式使用前缀缓存

要启用前缀缓存，把提示词中共享的部分加到 `promptPrefix` 字段，如下方代码片段所示：

### Kotlin

    val promptPrefix = "Reverse the given sentence: "
    val dynamicSuffix = "Hello World"

    val result = generativeModel.generateContent(
      generateContentRequest(TextPart(dynamicSuffix)) {
        promptPrefix = PromptPrefix(promptPrefix)
      }
    )

### Java

    String promptPrefix = "Reverse the given sentence: ";
    String dynamicSuffix = "Hello World";

    GenerateContentResponse response = generativeModelFutures.generateContent(
        new GenerateContentRequest.Builder(new TextPart(dynamicSuffix))
        .setPromptPrefix(new PromptPrefix(promptPrefix))
        .build())
        .get();

在前面的片段中，`dynamicSuffix` 作为主内容传入，`promptPrefix` 则单独提供。

### 预估性能收益

|---|---|---|
|   | **不使用前缀缓存** | **前缀缓存命中时**（首次使用前缀时可能出现缓存未命中） |
| Pixel 9，300 token 固定前缀加 50 token 动态后缀提示词 | 0.82 秒 | 0.45 秒 |
| Pixel 9，1,000 token 固定前缀加 100 token 动态后缀提示词 | 2.11 秒 | 0.5 秒 |

### 存储注意事项

使用隐式前缀缓存时，缓存文件保存在客户端应用的私有存储中，这会增加应用的存储占用。加密后的缓存文件及其关联元数据（包括原始前缀文本）都会被存储。请注意以下存储方面的事项：

- 缓存数量由 LRU（最近最少使用）机制管理。超过缓存总量上限时，最少使用的缓存会被自动删除。
- 提示词缓存的大小取决于前缀长度。
- 要清除前缀缓存创建的所有缓存，使用
  [`generativeMode.clearImplicitCaches()`](https://developer.android.com/android/reference/kotlin/com/google/mlkit/genai/prompt/GenerativeModel#clearCaches%28%29) 方法。

  > [!NOTE]
  > **注意：** `clearImplicitCaches()` 方法尚属实验性功能，将来可能变化。

## 使用显式缓存管理

Prompt API 包含显式缓存管理方法，让开发者能更精确地控制缓存的创建、搜索、使用与移除。这些手动操作独立于系统的自动缓存处理运行。

下面的示例演示如何初始化显式缓存管理并执行推理：

### Kotlin

    val cacheName = "my_cache"
    val promptPrefix = "Reverse the given sentence: "
    val dynamicSuffix = "Hello World"

    // Create a cache
    val cacheRequest = createCachedContextRequest(cacheName, PromptPrefix(promptPrefix))
    val cache = generativeModel.caches.create(cacheRequest)

    // Run inference with the cache
    val response = generativeModel.generateContent(
      generateContentRequest(TextPart(dynamicSuffix)) {
        cachedContextName = cache.name
      }
    )

### Java

    String cacheName = "my_cache";
    String promptPrefix = "Reverse the given sentence: ";
    String dynamicSuffix = "Hello World";

    // Create a cache
    CachedContext cache = cachesFutures.create(
      new CreateCachedContextRequest.Builder(cacheName, new PromptPrefix(promptPrefix))
      .build())
      .get();

    // Run inference with the cache
    GenerateContentResponse response = generativeModelFutures.generateContent(
      new GenerateContentRequest.Builder(new TextPart(dynamicSuffix))
      .setCachedContextName(cache.getName())
      .build())
      .get();

下面的示例演示如何使用 `generativeModel.caches` 查询、获取和删除显式管理的缓存：

### Kotlin

    val cacheName = "my_cache"

    // Query pre-created caches
    for (cache in generativeModel.caches.list()) {
      // Do something with cache
    }

    // Get specific cache
    val cache = generativeModel.caches.get(cacheName)

    // Delete a pre-created cache
    generativeModel.caches.delete(cacheName)

### Java

    String cacheName = "my_cache";

    // Query pre-created caches
    for (PrefixCache cache : cachesFutures.list().get()) {
      // Do something with cache
    }

    // Get specific cache
    PrefixCache cache = cachesFutures.get(cacheName).get();

    // Delete a pre-created cache
    cachesFutures.delete(cacheName);
