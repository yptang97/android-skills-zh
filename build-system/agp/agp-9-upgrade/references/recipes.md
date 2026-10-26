迁移到 AGP 的新 DSL 后，任何依赖旧 DSL 的 Gradle 代码（插件或构建脚本中的逻辑）都会失效。这类代码必须迁移。

## 指南

- **不要**在网上搜索这类做法的示例。**只**使用 **gradle-recipes** 仓库中的示例。
- **不要**在迁移后的代码中使用 AGP 内部实现。
- **要**在迁移后的代码中只使用公开 API。

有些情况下，旧代码存在一对一的替代写法。部分示例见 [AGP 9.0.0 版本说明](https://developer.android.com/build/releases/agp-9-0-0-release-notes)。

另一些情况下没有直接的一对一替代写法。这时 [gradle-recipes 仓库](https://github.com/android/gradle-recipes) 是很好的资源。你可以检出它的某个 AGP 9.x 分支，例如 `agp-9.0`、`agp-9.1` 或 `agp-9.2`。这些分支包含针对 Android 项目中常见情况的示例方案。下表列出各 AGP 版本对应的示例方案兼容情况。

## 兼容性对照表

| AGP 版本 | gradle-recipes 分支 |
|---|---|
| 9.0.x | agp-9.0 |
| 9.1.x | agp-9.1 |
| 9.2.x | agp-9.2 |

## 示例方案与使用场景

下表把使用场景与示例方案对应起来。

| 示例方案 | 使用场景 |
|---|---|
| addCustomBuildConfigFields | 添加自定义 BuildConfig 字段 |
| listenToArtifacts | 重命名 APK |

下面给出各使用场景的更多细节。

### 添加自定义 BuildConfig 字段

详细指南见 [BuildConfig](https://developer.android.com/agents/skills/build-system/agp/agp-9-upgrade/references/buildconfig)。

### 重命名 APK

在旧 DSL 中，重命名 APK 非常简单。示例如下：

    android {
      applicationVariants.all {
        outputs.all {
          val output = this as com.android.build.gradle.api.ApkVariantOutput
          val fileName = output.outputFileName
          if (fileName.contains("release")) {
            output.outputFileName = "my-cool-new-name.apk"
          }
        }
      }
    }

不过，在 AGP 9 和新 DSL 中，`applicationVariants` 已不再可用。你必须改用 `androidComponents.onVariants` API 响应构件的创建。完整示例见 **gradle-recipes** 仓库中的 `listenToArtifacts` 示例方案。