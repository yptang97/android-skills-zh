迁移到内置 Kotlin 时，需要重点考虑 `kapt` 以及 `org.jetbrains.kotlin.kapt`（也就是 `kotlin("kapt")`）插件的使用情况。
目标是把尽可能多的 `kapt` 用法迁移到 `ksp`。

迁移 `kapt` 时按以下步骤操作：

## 1. 移除所有对 `org.jetbrains.kotlin.kapt` 插件的引用

`org.jetbrains.kotlin.kapt`（也就是 `kotlin("kapt")`）插件与内置 Kotlin
不兼容。迁移到内置 Kotlin 时请移除它。

## 2. 检查每一处 `kapt` 用法

检查每一处 `kapt` 用法，确认它是否兼容 `ksp`。要判断某个依赖是否兼容
`ksp`，请查看该依赖的 jar。jar 中必须存在文件
`services/com.google.devtools.ksp.processing.SymbolProcessorProvider` 才算兼容
`ksp`。如果没有这个文件，则该依赖**不兼容** `ksp`。

例如，`androidx.room:room-compiler` 库从 2.3.0-beta02 版本起兼容 KSP。
我们可以在 Gradle 缓存目录中找到该 jar 文件来验证，在 Linux 和 Mac 上该目录通常位于
`~/.gradle/caches/modules-2/files-2.1/`。在这个例子中，
`androidx.room:room-compiler` 依赖位于
`~/.gradle/caches/modules-2/files-2.1/androidx.room/room-compiler/`。

更一般地说，你可以在
`~/.gradle/caches/modules-2/files-2.1/group-name/artifact-name/` 下找到某个依赖。

## 3. 尽可能迁移到 KSP

对于每一处兼容 `ksp` 的 `kapt` 用法，改用 `ksp`。上一步已经说明了如何检查兼容性。

## 4. 应用 legacy-kapt

如果某个 Gradle 模块中有 `kapt` 依赖因不兼容（见步骤 2）而无法迁移到 `ksp`，
那就保留该依赖不动，改为应用 `com.android.legacy-kapt` 插件。
