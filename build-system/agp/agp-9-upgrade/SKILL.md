---
name: agp-9-upgrade
description: 把 Android 项目升级或迁移到 Android Gradle Plugin（AGP）9。不要用这个
  skill 迁移 Kotlin Multiplatform（KMP）项目。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-18'
  keywords:
  - Android Gradle Plugin 9
  - AGP 9
  - AGP Upgrade
  - AGP Migration
  - New AGP DSL
  - Migrate to built-in Kotlin
---

## 迁移指南

AGP 9 相比 AGP 8 有许多重大变更，其中不少是破坏性变更，详见 [AGP 9 迁移指南](references/android/build/releases/agp-9-0-0-release-notes.md)。

## 要求

如果用户要求更新或迁移到 AGP 9，先检查项目使用的 AGP 版本。如果低于 9，停下来，
请用户在 Android Studio 中运行 AGP Upgrade Assistant 更新到最新稳定版 AGP，
并在完成后予以确认。用户也可能要求跳过这一要求；如果属于这种情况，
你应在 AGP 9 迁移过程中把 AGP 版本更新到最新稳定版。具体做法见
[AGP 9 迁移指南](references/android/build/releases/agp-9-0-0-release-notes.md)。

每个 AGP 版本对其他工具（例如 Gradle、JDK 和 Kotlin）都有自己的兼容性要求。
各版本的版本说明都会包含一张**兼容性**表格，列明这些工具的最低版本。

不要用这个 skill 处理 KMP 项目，它们不受支持。

## 步骤

如果 AGP 已经是 9 或更高版本，则执行以下操作：

### 步骤 1：更新依赖

如果项目使用 KSP（`com.google.devtools.ksp`），确保其版本为 2.3.6 或更高。

如果项目使用 Hilt，确保其版本为 2.59.2 或更高。

### 步骤 2：迁移到内置 Kotlin

详见[该指南](references/android/build/migrate-to-built-in-kotlin.md)。

### 步骤 3. 迁移到新的 AGP DSL

详见[该指南](references/android/build/releases/agp-9-0-0-release-notes.md)。

另请参阅 [gradle-recipes](references/recipes.md)，了解如何把旧代码迁移为兼容 AGP 9
和新 DSL 的代码。

### 步骤 4. 把 kapt 迁移到 KSP 或 legacy-kapt

如果项目使用 KSP（`com.google.devtools.ksp`）或 kapt（`org.jetbrains.kotlin.kapt`），
详见 [KSP、kapt 与 legacy-kapt](references/ksp-kapt.md) 中的迁移步骤。

### 步骤 5. BuildConfig

如果任何 Android 模块包含自定义 BuildConfig 字段，详见 [BuildConfig](references/buildconfig.md)。

### 步骤 6. 更新 gradle.properties

迁移完成后，检查 gradle.properties。移除以下标志：

1. android.builtInKotlin
2. android.newDsl
3. android.uniquePackageNames
4. android.enableAppCompileTimeRClass

此外，删除你创建的所有临时文件。

## 指南

- 绝不编写或运行 python 脚本。
- 检查外部依赖时，只在万不得已的情况下才搜索 Gradle 依赖缓存。
- 绝不要把 `android.disallowKotlinSourceSets=false` 加入 `gradle.properties`。
- 验证变更时不要运行 `clean` 任务。这纯属浪费时间。

## 验证

迁移完成后，验证以下各项：

1. Gradle IDE sync 成功。
2. `./gradlew help` 成功。
3. `./gradlew build --dry-run` 成功。

## 故障排查

Paparazzi v2.0.0-alpha04 及更低版本与 AGP 9 存在兼容问题。详情见
[references/paparazzi-gradle-9.md](references/paparazzi-gradle-9.md)。
