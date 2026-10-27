为了最大程度地发挥 R8 的作用，必须根据构建脚本语言（Kotlin DSL 还是 Groovy DSL）正确配置代码库。

## 1. 应用模块（`com.android.application`）

应用的 `build.gradle` 或 `build.gradle.kts` 文件必须在 `release` 构建类型中，或在应用为发布和性能测试自定义的构建类型中，启用代码压缩和资源压缩。它必须使用优化过的默认文件（`proguard-android-optimize.txt`）。

在 **AGP 9.3 及更高版本**上，`optimization { enable = true }` DSL 块用一个设置就能开启代码压缩（R8）、资源压缩和 `proguard-android-optimize.txt`。当 release 构建类型中存在 `optimization { enable = true }` 时，这三项检查都已满足——**不要**把代码压缩、资源压缩或 `proguard-android-optimize.txt` 报告为缺失，也**不要**建议改回 `isMinifyEnabled` 或 `isShrinkResources`。

**Kotlin DSL --- AGP 9.3 及更高版本（`build.gradle.kts`）**：

    buildTypes {
       release {
           optimization {
               enable = true
           }
           proguardFiles("proguard-rules.pro")
       }
    }

**Kotlin DSL --- 旧版本或 AGP 9.3 之前（`build.gradle.kts`）**：

    buildTypes {
       release {
           isMinifyEnabled = true
           isShrinkResources = true
           proguardFiles(
               getDefaultProguardFile("proguard-android-optimize.txt"),
               "proguard-rules.pro"
           )
       }
    }

**Groovy DSL（`build.gradle`）**：

    buildTypes {
       release {
           minifyEnabled = true
           shrinkResources = true
           proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
       }
    }

## 2. `gradle.properties` 开关

**Full mode**：R8 的 full mode 会启用全部优化。

- **AGP 8.0 及更高版本**：默认启用。确认 `gradle.properties` 中**没有** `android.enableR8.fullMode=false`。
- **AGP 8.0 之前**：确认 `gradle.properties` 中设置了 `android.enableR8.fullMode=true`。

**优化的资源压缩**：如果 AGP 是 8.12 或 8.13，确认 `gradle.properties` 中设置了 `android.r8.optimizedResourceShrinking=true`。从 AGP 9.0 起默认开启。

    android.r8.optimizedResourceShrinking=true
