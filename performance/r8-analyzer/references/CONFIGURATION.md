要实现 R8 效用的最大化，代码库必须依据构建脚本语言（Kotlin DSL 还是 Groovy DSL）正确配置。

## 1. 应用模块（`com.android.application`）

应用的 `build.gradle` 或 `build.gradle.kts` 文件必须在 `release` 构建类型中启用代码压缩与资源压缩，或者在应用为发布和性能测试自定义的构建类型中启用。它必须使用优化过的默认文件（`proguard-android-optimize.txt`）。

**Kotlin DSL（`build.gradle.kts`）：**

    buildTypes {
       getByName("release") {
           isMinifyEnabled = true
           isShrinkResources = true
           proguardFiles(
               getDefaultProguardFile("proguard-android-optimize.txt"),
               "proguard-rules.pro"
           )
       }
    }

**Groovy DSL（`build.gradle`）：**

    buildTypes {
       release {
           minifyEnabled = true
           shrinkResources = true
           proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
       }
    }

## 2. `gradle.properties` 标志

**Full Mode：**R8 Full Mode 会启用全部优化

- **AGP 8.0+**：默认启用。确保**不要**出现 `android.enableR8.fullMode=false`。
- **AGP 8.0 之前**：用 `android.enableR8.fullMode=true` 显式启用。

**优化的资源压缩：**如果项目的 AGP 版本低于 9.0 且高于 8.6，请显式启用新的资源压缩器：

    android.r8.optimizedResourceShrinking=true
