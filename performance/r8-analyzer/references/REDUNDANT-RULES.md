本文列出标准 Android 开发和常用库中常见的“错误”或冗余 keep 规则。现代工具链与库已把各自的 consumer keep 规则内嵌在 AAR/JAR 文件中，因此很多手动配置不再必要，甚至会损害代码优化。

*** ** * ** ***

## 案例：全局 Keep 规则

**常见错误：**
`proguard
-dontshrink
-dontobfuscate
-dontoptimize`

**修复方式：**这些 keep 规则会彻底禁用 R8 对整个人代码库的核心优化。必须把它们从代码库中移除。

*** ** * ** ***

## 案例：Android 组件

针对 Activity、Fragment、ViewModel、View、Service 或 BroadcastReceiver 这类 Android 组件所需的 keep 规则是冗余的。AAPT2 和 R8 已包含相应逻辑，会自动保留在 `AndroidManifest.xml` 中声明或在 XML 布局文件中引用的组件。

**常见错误：**
`proguard
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Service
-keep public class * extends android.view.View
-keepclassmembers class * extends android.app.Fragment { public void *(android.view.View); }`

**修复方式：**删除这些手动规则。AAPT2 会自动处理。

*** ** * ** ***

## 案例：官方 Android 与 Kotlin 库

针对 AndroidX、Kotlin 和 Kotlinx 等官方库包的 keep 规则是冗余的，因为它们已内置于这些库本身之中。手动规则往往比严格所需的范围更宽。

**常见错误：**
`proguard
-keep class androidx.** { *; }
-keep class kotlinx.** { *; }
-keep class kotlin.** { *; }`

**修复方式：**删除这些手动规则。改为依赖这些依赖项中打包的 consumer keep 规则。

*** ** * ** ***

## 案例：Gson

### 过于宽泛的数据模型规则

最常见的错误是保留整个包的数据模型（POJO/DTO）；为反序列化而保留数据模型本身完全没有必要。

    -keep class com.example.app.models.** { *; }
    -keep class com.example.app.package.models.* { *; }

### 冗余的接口 \& 适配器规则

为 TypeAdapter 添加的这些规则没有必要，库本身已经覆盖，而且它们会妨碍 R8 有效压缩和优化自定义适配器。R8 能够判断适配器实现是否被使用。全局保留这些规则会阻止移除未使用的适配器实现。

    -keep class * extends com.google.gson.TypeAdapter
    -keep class * implements com.google.gson.TypeAdapterFactory
    -keep class * implements com.google.gson.JsonSerializer
    -keep class * implements com.google.gson.JsonDeserializer

### 不必要的 TypeToken 规则

无需处理泛型类型擦除，Gson 自带的规则已经处理了必要的 `TypeToken` 保留。

    -keep class com.google.gson.reflect.TypeToken { *; }
    -keep class * extends com.google.gson.reflect.TypeToken
    -keep,allowobfuscation,allowshrinking class com.google.gson.reflect.TypeToken

### 内部包与示例包

保留库的内部逻辑会阻止编译器剔除库内的无用代码。

    -keep class com.google.gson.internal.** { *; }
    -keep class com.google.gson.internal.reflect.** { *; }
    -keep class com.google.gson.internal.UnsafeAllocator { *; }
    -keep class com.google.gson.stream.** { *; }

- **保留无用代码：**阻止 R8 移除代码中从未真正使用过的模型。
- **阻止方法剔除：**保留所有 getter、setter、`toString()`、`equals()` 和 `hashCode()` 方法，即使它们从未被调用。
- **阻碍混淆：**阻止类名被混淆，而如果你使用 `@SerializedName`，这对 Gson 来说并无必要。

**修复方式：**

1. 在数据类的每个字段上使用 `@SerializedName`，以确保该字段在 R8 优化后被保留
2. 现代 Gson（**v2.11.0+**）已内置自己的规则（[查看 Gson 内置的
   ProGuard
   规则](https://github.com/google/gson/blob/main/gson/src/main/resources/META-INF/proguard/gson.pro)）。内置的 keep 规则会保留带 `@SerializedName` 注解的字段。如果你仍在使用旧版本，请升级到 Gson 2.11，因为它带有必要的 keep 规则，并删除那些针对用于 Gson 序列化和反序列化的类所写的 keep 规则

*** ** * ** ***

## 案例：Retrofit

Retrofit 从 2.9.0 起就已自带 consumer keep 规则，因此任何针对该库或依赖 Retrofit 的类的 keep 规则都会损害优化过程。

### 一刀切保留整个库

这是危害最大的 Retrofit 规则，因为它会禁用整个库的任何压缩。

    -keep class retrofit2.** { *; }
    -keep class retrofit2.api.** { *; }
    -keep class com.package.example.retrofit.api.** { *; }

### 手动保留注解

Retrofit 的 consumer 规则会自动保留带有 `@GET`、`@POST`、`@DELETE`、`@PUT`、`@HEAD`、`@OPTIONS`、`@PATCH` 注解的接口，使这些手动规则变得多余。

`-keepclasseswithmembers class * { @retrofit2.http.* <methods>; }`

### 冗余的网络响应与适配器规则

出于谨慎，开发者常常过度保留网络响应和第三方适配器包装（例如 RxJava）。

    -keep,allowobfuscation,allowshrinking class retrofit2.Response
    -keep class retrofit2.adapter.rxjava2.Result { *; }

修复：确认你使用的是 Retrofit 2.9.0 及以上版本。从 2.9.0 起，Retrofit 内置了能识别自身 HTTP 注解（@GET、@POST）的规则（[查看 Retrofit 内置的 ProGuard
规则](https://github.com/square/retrofit/blob/master/retrofit/src/main/resources/META-INF/proguard/retrofit2.pro)）。它会自动保留工作所需的方法签名。

*** ** * ** ***

## 案例：Kotlin 协程

Kotlin 协程开箱即带有高度优化的内置 R8 规则（`kotlinx-coroutines-core` 已包含自己的规则）。

### 一刀切覆盖整个协程库的规则

保留 `kotlinx.coroutines` 下的所有内容会严重损害应用体积，因为协程中包含大量并未使用的内部 API。

`-keepclassmembers class kotlinx.coroutines.** { *; }`

### 冗余的内部续体

这些底层协程元素由库自身的 consumer 规则安全保留。手动添加它们会阻止 R8 执行内部优化（例如移除未使用的续体或内联）。

    -keepclassmembers class kotlin.coroutines.SafeContinuation { *; }
    -keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation

### 调度器与异常处理器规则

开发者有时会在旧版 Android 上遇到与 Missing Classes 相关的崩溃，于是添加这些规则；但如果你使用的是较新版本的协程，这些问题会被自动处理，或者根本不存在。

    -keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
    -keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
    -keepnames class kotlinx.coroutines.android.AndroidExceptionPreHandler {}
    -keepnames class kotlinx.coroutines.android.AndroidDispatcherFactory {}

**修复**：移除任何宽泛的 `kotlinx` keep 规则。协程（**v1.7.0+**）已内置必要的 keep 规则（[查看协程内置的 ProGuard
规则](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-core/jvm/resources/META-INF/proguard/coroutines.pro)）。

*** ** * ** ***

## 案例：Parcelable

**常见错误：**遗留项目常常包含 `-keep class * implements
android.os.Parcelable { public static final android.os.Parcelable$Creator *; }`。

**修复方式：**

1. 添加 `kotlin-parcelize` 插件。
2. **使用 `@Parcelize`：**用 `@Parcelize` 注解替代手写的 `writeToParcel` 逻辑。
3. **删除所有 Parcelable 规则：**该插件会自动生成所需的规则。
4. 默认的 proguard 文件 `proguard-android-optimize.txt` 已包含保留所有 Parcelable 类所需的 keep 规则
5. **理想规则：** **无。**删除所有手写的 Parcelable keep 规则。

*** ** * ** ***

## 案例：Room 数据库

**常见错误：**手动保留 DAO 接口或生成的 `_Impl` 类。

    -keep class * extends androidx.room.RoomDatabase
    -keep class *_*Impl { *; }

**修复方式：**Room 会为其生成的代码自行生成 ProGuard 规则。手动规则是冗余的，并且会阻止 R8 优化数据库访问层。

- **理想规则：** **无。**删除所有手写的 Room 或 DAO keep 规则。

*** ** * ** ***

## 小结

如果你已把库更新到上述版本，你的 `proguard-rules.pro` 中不应再包含任何针对本文提到的库的 keep 规则。
