本指南帮助你解决 Play Engage SDK 集成过程中常见的编译、导入和依赖错误。

## 1. 用完整构建任务验证编译

验证 Play Engage SDK 集成时，请运行完整的编译任务，而不是只编译 Kotlin 的捷径：

- **使用完整编译**：运行 `./gradlew compileDebugUnitTestSources` 或 `./gradlew assembleDebug`（再加上项目相关的测试任务）。
- **不要使用编译捷径**：绝不要使用 `./gradlew :app:compileDebugKotlin` 之类的命令或其他仅编译的任务。这些捷径会绕过清单合并和资源打包，从而掩盖命名空间冲突或 XML 语法错误这类关键错误。

## 2. 解决缺失的导入

如果你在升级 SDK 版本（例如升级到 1.6.0），或者在初次编译时遇到 `Unresolved reference` 错误，请确认已添加正确的 import 语句：

| 类名 | 包名或 import 语句 | 备注 |
|---|---|---|
| `ImageTheme` | `import com.google.android.engage.common.datamodel.ImageTheme` |   |
| `PlatformSpecificUri` | `import com.google.android.engage.common.datamodel.PlatformSpecificUri` |   |
| `DisplayTimeWindow` | `import com.google.android.engage.common.datamodel.DisplayTimeWindow` |   |
| `RatingSystem` | `import com.google.android.engage.video.datamodel.RatingSystem` | 注意：它在 `video.datamodel` 下，不在 `common.datamodel` 下。 |

## 3. 解决命名空间冲突

你可能会收到类似下面这样的错误信息：

    Namespace 'com.google.android.engage' is used in multiple modules and/or libraries: com.google.android.engage:engage-core:1.6.0, com.google.android.engage:engage-tv:1.1.0

出现这个冲突是因为两个包声明了相同的命名空间。
\* **解决办法**：从你的 `build.gradle` 或 `build.gradle.kts` 中移除显式声明的 `engage-core` 依赖，*只*保留 `engage-tv`。`engage-tv` 库会自动以传递依赖的方式引入兼容版本的 `engage-core`。
