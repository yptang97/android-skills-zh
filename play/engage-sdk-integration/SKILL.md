---
name: engage-sdk-integration
description: 帮助开发者集成、调试并解决 Play Engage SDK 实现问题。适用于添加 Engage SDK 支持、生成发布代码、
  把数据类映射到实体，或修复 SDK 相关错误时。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-17'
  keywords:
  - android
  - engage
  - engage sdk
  - play engage library
  - google play
---

这个 skill 会指导你把 Play Engage SDK 集成到 Android 应用中。它确保代码遵循强制规定的结构，并为每个垂直领域使用所需的 Engage 实体。

## 工作流

按以下步骤协助开发者：

1. **确定垂直领域与 cluster：**

   - 根据 **[references/schemas/](references/schemas)**，询问开发者的应用属于哪个垂直领域。
   - 确认集成是针对 TV 还是移动端。如果集成针对 TV，还要阅读 [patterns.md](references/patterns.md) 中与 TV 相关的章节。
   - 用 **[references/schemas/](references/schemas)** 目录下的 `{VERTICAL}.md` 确定对应的 Engage 实体和 `client` 类名。JSON 中的 `client` 字段给出完整类名。例如 `com.google.android.engage.food.service.AppEngageFoodClient`。
   - **注意：**初始化 client 类需要一个 `Context` 参数。例如 `AppEngageFoodClient(context)`。
   - 公共实体请始终参考 [common.md](references/common.md)。
   - 询问开发者想从该垂直领域支持的 cluster 类型中发布哪一种。
   - 在 **[references/schemas/](references/schemas)** 目录的 `{VERTICAL}.md` 中，找到指定 cluster 要调用的方法。每个方法都会说明它期望的请求。
   - 从 [requests.md](references/requests.md) 获取请求结构，从 [clusters.md](references/clusters.md) 获取 cluster。然后提出并使用数据来源，正确地填充请求结构中的字段，同时填充所需的实体和 cluster。
2. **生成结构化的样板代码：**

   - 为所有与 Engage 相关的代码新建一个目录。目录命名要与现有代码库的命名约定一致。
   - 使用 [patterns.md](references/patterns.md) 中的模板生成以下类：
     - `Constants`：保存常量值，例如重试次数和发布类型。
     - `ItemToEntityConverter`：把应用的本地模型转换为 Engage 的 Entity 模型。
     - `ClusterRequestFactory`：构造发布请求。
     - `EngageWorker`：使用 WorkManager 处理实际的发布以及发布错误。
     - `EngagePublisher`：编排周期任务和一次性任务。
     - `EngageBroadcastReceiver`：监听 AppEngageService 的 intent，并从 `EngagePublisher` 启动一次性发布任务。**重要**：要实现**静态注册**和**动态注册**两种方式，包括在 `EngageBroadcastReceiver` 类中的 companion object 里实现 `register` 方法。
3. **建议实体映射：**

   - 请开发者提供他们的本地模型 schema（例如数据类或 JSON 片段）。
   - 如果他们没有提供，就以 **[references/schemas/](references/schemas)** 目录下 `{VERTICAL}.md` 中的实体作为参考给出。
   - 确定本地模型后，建议到对应 Engage 实体的映射。
   - 使用 [patterns.md](references/patterns.md) 中的 `ItemToEntityConverter` 模式生成转换逻辑，并加到已生成的 `{ENGAGE_CODE_DIR}/ItemToEntityConverter` 中。
4. **建议数据来源：**

   - 请开发者提供你要发布的实际数据的来源。
   - 确定数据来源后，用它按应用的本地模型 schema 获取数据。
   - 使用 `{ENGAGE_CODE_DIR}/ItemToEntityConverter` 把这些数据转换为 Engage 实体。
   - 把得到的 Engage 实体模型数据交给 `{ENGAGE_CODE_DIR}/
     ClusterRequestFactory`，以获取 cluster 请求。
   - 在 `{ENGAGE_CODE_DIR}/EngageWorker` 中，用上一步得到的请求，调用从 **[references/schemas/](references/schemas)** 目录的 `{VERTICAL}.md` 中得到的对应 cluster 发布方法。
5. **Gradle 与清单更新：**

   - 建议对 `build.gradle` 和 `AndroidManifest.xml` 的更新。
   - 移动应用请使用 [patterns.md](references/patterns.md)。
   - TV 应用请使用 [patterns.md](references/patterns.md) 中与 TV 相关的章节。
   - 从 [patterns.md](references/patterns.md) 中给出 `build.gradle` 或 `build.gradle.kts` 所需的 `implementation` 依赖。
   - 给出 `AndroidManifest.xml` 所需的 `<receiver>` 和 `<service>` 声明。
   - 注意：除 TV 外，没有任何垂直领域专属的 import。对于其他所有垂直领域，`com.google.android.engage:engage-core:1.6.0` 就足够了。
6. **调试与验证**：

   - **自检清单**：在认为工作完成之前，你必须确认已实现以下全部内容：
     - \[ \] 在 `AndroidManifest.xml` 中（`<application>` 标签内）**静态**注册 `EngageBroadcastReceiver`。
     - \[ \] 在 `Application` 类或主 `Activity` 类中调用 `EngageBroadcastReceiver.register(context)`，从而**动态**注册 `EngageBroadcastReceiver`。
     - \[ \] 在 `EngageBroadcastReceiver` 的 `companion object` 中实现 `register` 方法，以处理动态注册。
     - \[ \] 在 `EngageWorker` 中处理空数据列表（例如删除 cluster，而不是发布空数据）。
     - \[ \] 所有 Gradle 编译都使用了 `--no-daemon`。
   - 执行一次 Gradle sync。
   - 如果出现错误（例如 import 失败、namespace 冲突或编译错误），阅读 **[references/troubleshooting.md](references/troubleshooting.md)** 来解决。
   - 执行一次 Gradle 编译。你必须运行 `./gradlew compileDebugUnitTestSources --no-daemon` 或 `./gradlew assembleDebug --no-daemon`。编译规则以及关于快速编译捷径的警告见 **[references/troubleshooting.md](references/troubleshooting.md)**。重复这一步直到编译成功。
7. **用户检查清单：**代码生成结束时，通知用户过一遍这份清单，确认集成已完成并符合预期：

   - \[ \] 确认所有与 Engage 相关的文件都已在 `{ENGAGE_CODE_DIR}/` 中创建：
     - `Constants`
     - `ItemToEntityConverter`
     - `ClusterRequestFactory`
     - `EngageWorker`
     - `{cluster_type}Publisher`
     - `EngageBroadcastReceiver`
   - \[ \] 确认在 `{ENGAGE_CODE_DIR}/ItemToEntityConverter` 中正确填充模型的字段，从而把应用的本地模型转换为 Engage 实体。
   - \[ \] 确认 `ItemToEntityConverter` 中所有图片 URI 指向的图片都符合该垂直领域严格的宽高比要求（例如 16:9、1:1、2:3）。
   - \[ \] 确认 `{ENGAGE_CODE_DIR}/EngageWorker` 使用了步骤 4 中确定的数据来源。
   - \[ \] 确认在 `Application` 类或 `MainActivity` 中调用了 `EngageBroadcastReceiver.register(context)`，以动态注册该 receiver。
   - \[ \] 确认 `AndroidManifest.xml` 中包含 `EngageBroadcastReceiver` 的静态 `<receiver>` 声明，并带有必要的 intent action。
   - **重要**：明确指导开发者在自定义 `Application` 类的 `onCreate()`（或主 activity 的 `onCreate()`）中调用 `EngageBroadcastReceiver.register(context)`，以动态注册该 receiver。强调**静态和动态**两种注册都是集成生效所必需的。

## 参考资料

- **FAQ：**[Engage FAQ](references/android/guide/playcore/engage/faq.md) - 开发者常见问题的解答请参考这份文档。

- **垂直领域专属指南：**

  - [美食垂直领域](references/android/guide/playcore/engage/food.md)
  - [观看垂直领域](references/android/guide/playcore/engage/watch.md)
  - [收听垂直领域](references/android/guide/playcore/engage/listen.md)
  - [阅读垂直领域](references/android/guide/playcore/engage/read.md)
  - [购物垂直领域](references/android/guide/playcore/engage/shopping.md)
  - [社交垂直领域](references/android/guide/playcore/engage/social.md)
  - [旅行垂直领域](references/android/guide/playcore/engage/travel.md)
  - [健康与健身垂直领域](references/android/guide/playcore/engage/healthandfitness.md)
  - [其他垂直领域](references/android/guide/playcore/engage/otherverticals.md)
  - [TV 快速上手](references/android/guide/playcore/engage/tv/getting-started.md)
  - [TV 推荐](references/android/guide/playcore/engage/tv/recommendations.md)
  - [TV 继续观看](references/android/guide/playcore/engage/tv/continue-watching/index.md)
  - [TV 权益](references/android/guide/playcore/engage/tv/entitlements.md)
- **垂直领域专属 schema：**

  - [美食 schema](references/schemas/food.md)
  - [观看 schema](references/schemas/watch.md)
  - [收听 schema](references/schemas/listen.md)
  - [阅读 schema](references/schemas/read.md)
  - [购物 schema](references/schemas/shopping.md)
  - [社交 schema](references/schemas/social.md)
  - [旅行 schema](references/schemas/travel.md)
  - [TV schema](references/schemas/tv.md)
  - [其他 schema](references/schemas/other.md)
