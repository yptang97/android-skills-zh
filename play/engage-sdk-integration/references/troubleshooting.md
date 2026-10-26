本指南帮助你解决 Play Engage SDK 集成过程中常见的编译、导入和沙箱相关错误。

## 1. 确保 agent 在沙箱中的编译安全

在沙箱化或临时工作区（例如评测环境或自动化 presubmit）中执行编译时，你必须遵循以下规则，以避免容器崩溃和卡死：

- **使用完整编译**：运行 `./gradlew compileDebugUnitTestSources --no-daemon` 或 `./gradlew assembleDebug --no-daemon`。
- **不要使用编译捷径**：避免使用 `./gradlew :app:compileDebugKotlin` 之类的命令或其他仅编译的任务。这些捷径会绕过清单合并和资源打包，从而掩盖命名空间冲突或 XML 语法错误这类关键错误。
- **不要运行完整测试或构建**：不要运行 `./gradlew test` 或 `./gradlew build`。这些任务会触发重量级测试环境（需要模拟器）并执行完整构建，很容易导致 FUSE 文件系统挂载崩溃，并耗尽沙箱的 CPU 和内存。
- **始终使用 --no-daemon**：始终追加 `--no-daemon`，防止后台 JVM 进程泄漏并锁住沙箱中的文件。

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

## 4. 解决沙箱特有的构建与测试失败

在评测沙箱中编译或运行测试时（尤其是在 Now in Android 这类大型项目上），你可能会遇到特定环境下的失败：

- **Android SDK 36 的 Jlink 错误**：如果构建在 Java 编译阶段因 `android-36` 的 `JdkImageTransform` 报 `jlink` 错误而失败，就在 Gradle 命令前加上 `JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64`，强制使用 JDK 17。
- **缺少 ANDROID_HOME**：如果 lint 或测试任务因缺少 SDK 而失败，就显式设置环境变量 `ANDROID_HOME=/usr/local/google/home/shashvatgupta/Android/Sdk`（或工作站上对应的路径）。
- **Roborazzi 截图不匹配**：无头环境或沙箱容器渲染可能与本地基准图不同，导致 Roborazzi 截图测试断言失败。在测试命令后追加 `-Proborazzi.test.verify=false` 来绕过这些视觉检查。
- **Robolectric 不支持 SDK 36**：如果截图测试因实验性 SDK 36 在 `DefaultSdkProvider` 中抛出 `java.lang.UnsupportedOperationException` 而失败，就把出错测试文件里的 `@Config` 注解改成把 SDK 固定为 34（例如 `@Config(..., sdk = [34])`）。
