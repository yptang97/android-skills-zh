当 Android 模块包含自定义 BuildConfig 字段时，需要执行以下步骤以确保构建正确。

### 步骤 1：启用 buildConfig 构建功能

在构建脚本中：

    android {
      buildFeatures {
        buildConfig = true
      }
    }

在应用模块的自定义 build-logic 中：

    extensions.configure<com.android.build.api.dsl.ApplicationExtension> {
      buildFeatures {
        buildConfig = true
      }
    }

在库模块的自定义 build-logic 中：

    extensions.configure<com.android.build.api.dsl.LibraryExtension> {
      buildFeatures {
        buildConfig = true
      }
    }

在使用 `CommonExtension` 的自定义 build-logic 中：

    extensions.configure<com.android.build.api.dsl.CommonExtension> {
      buildFeatures {
        buildConfig = true
      }
    }

### 步骤 2：迁移到新 API

使用 [gradle-recipes](https://developer.android.com/agents/skills/build-system/agp/agp-9-upgrade/references/recipes)
仓库中的 **addCustomBuildConfigFields** recipe。

**重要：**对于类型为 `String` 的 `BuildConfigField`，`value` 字段*必须*把引号作为
String 的一部分包含进去。例如：

    BuildConfigField(
      type = "String",
      value = "\"Some value\"",
      comment = "Optional comment",
    )

如果 `value` 字段没有把引号作为 String 的一部分包含进去，就是**错误**。例如，
`value = "Some value"` **是错误** 。这是因为 `value` 会被逐字写出。
