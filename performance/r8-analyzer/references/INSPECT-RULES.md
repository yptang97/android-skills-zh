本文列出标准 Android 开发和常用库中常见的「坏」keep 规则或冗余 keep 规则。当前的 Android 工具链和库已经自带了 consumer keep 规则，内嵌在它们的 AAR 或 JAR 文件中，因此很多手工配置是不必要的，甚至会损害代码优化。

## 案例：全局 keep 规则

**常见错误**：

    -dontshrink
    -dontobfuscate
    -dontoptimize
    -keep class !com.example.** { *; }

**修复方式**：全局禁用开关（`-dontshrink`、`-dontobfuscate`、`-dontoptimize`）以及使用 `!` 取反运算符的反向 keep 规则（例如 `-keep class !com.example.ui.** { *; }`，它匹配应用和库中*除*指定包之外的所有类）会在整个代码库范围内禁用 R8 优化。必须把它们从代码库中移除（或替换为针对具体类的窄范围 keep 规则）。

## 案例：Android 组件

针对 Activity、Fragment、ViewModel、View、Service 或 Broadcast receiver 等 Android 组件的 keep 规则通常是冗余的。AAPT2 只会为 `AndroidManifest.xml` 中声明的组件以及 XML 资源（布局、菜单、导航图）中引用的类生成 keep 规则。ViewModel，以及只在代码中创建的 Fragment 或 View，不在 AAPT2 的覆盖范围内，但它们通常也不需要手工规则：AndroidX 库自带它们做反射所需的规则。

**常见错误**：

    -keep public class * extends android.app.Activity
    -keep public class * extends android.app.Service
    -keep public class * extends android.view.View
    -keepclassmembers class * extends android.app.Fragment { public void *(android.view.View); }

**修复方式**：删除这些手写规则。AAPT2 覆盖清单中的组件和 XML 中引用的类；其他类只有存在反射时，才需要规则。

## 案例：官方 Android 与 Kotlin 库

针对 AndroidX、Kotlin 和 Kotlinx 等官方库包名的 keep 规则是冗余的，因为这些规则已经捆绑在库自身中。手写规则往往比实际需要的范围更宽。

**常见错误**：

    -keep class androidx.** { *; }
    -keep class kotlinx.** { *; }
    -keep class kotlin.** { *; }

**修复方式**：删除这些手写规则。依赖这些依赖项中打包的 consumer keep 规则即可。

## 案例：Gson

### 过于宽泛的数据模型规则

最常见的错误是把整个数据模型包（POJO 或 DTO）都保留下来。当被序列化的字段使用 `@SerializedName` 时，在 Gson 2.11 及更高版本上，按包保留模型的规则通常是不必要的，因为 Gson 自带的 keep 规则（从 2.11 起）会保留这些字段。如果 Gson 版本低于 2.11，先升级，然后删除这些规则。如果某个类没有无参构造函数，就为它保留一条窄范围规则。

    -keep class com.example.app.models.** { *; }
    -keep class com.example.app.package.models.* { *; }

### 冗余的接口与适配器规则

这些为 `TypeAdapter` 添加的规则是不必要的，库已经覆盖了它们，而且它们会阻止 R8 有效压缩和优化自定义适配器。R8 能判断适配器实现是否被使用。全局保留它们会阻止移除未使用的适配器实现。

    -keep class * extends com.google.gson.TypeAdapter
    -keep class * implements com.google.gson.TypeAdapterFactory
    -keep class * implements com.google.gson.JsonSerializer
    -keep class * implements com.google.gson.JsonDeserializer

### 不必要的 TypeToken 规则

无需处理泛型擦除；Gson 自身的规则已经处理了必要的 `TypeToken` 保留。

    -keep class com.google.gson.reflect.TypeToken { *; }
    -keep class * extends com.google.gson.reflect.TypeToken
    -keep,allowobfuscation,allowshrinking class com.google.gson.reflect.TypeToken

### 内部包与示例包

保留库的内部逻辑会阻止编译器剥离库内的死代码。

    -keep class com.google.gson.internal.** { *; }
    -keep class com.google.gson.internal.reflect.** { *; }
    -keep class com.google.gson.internal.UnsafeAllocator { *; }
    -keep class com.google.gson.stream.** { *; }

- **保留未使用的代码**：阻止 R8 移除代码中实际从未使用的模型。
- **阻止方法剥离**：保留所有 getter、setter、`toString`、`equals` 和 `hashCode` 方法，即使它们从未被调用。
- **阻止混淆**：阻止类名被混淆；如果你使用了 `@SerializedName`，这对 Gson 是不必要的。

**修复方式**：

1. 在用于序列化和反序列化的数据类字段上使用 `@SerializedName`。
2. Gson（**2.11.0 及更高版本**）自带规则（[查看 Gson 内嵌的 ProGuard 规则](https://github.com/google/gson/blob/main/gson/src/main/resources/META-INF/proguard/gson.pro)）。捆绑的 keep 规则会保留带 `@SerializedName` 注解的字段。如果你的版本低于 2.11，先升级到 Gson 2.11，因为它含有必要的 keep 规则，然后再删除针对 Gson 序列化和反序列化所用类的 keep 规则。如果某个类没有无参构造函数，就为它保留一条窄范围规则。

## 案例：Retrofit

Retrofit 从 2.10.0 及更高版本起就自带 consumer keep 规则（2.9.0 已覆盖 `@GET`/`@POST` 接口规则），所以针对该库或依赖 Retrofit 的类的任何 keep 规则都会妨碍优化过程。

### 整库保留

这是危害最大的 Retrofit 规则，因为它禁用了整个库的任何压缩。

    -keep class retrofit2.** { *; }
    -keep class retrofit2.api.** { *; }
    -keep class com.package.example.retrofit.api.** { *; }

### 手写的注解 keep

Retrofit 的 consumer 规则会自动保留带 `@GET`、`@POST`、`@DELETE`、`@PUT`、`@HEAD`、`@OPTIONS` 和 `@PATCH` 注解的接口，这些手写规则因此已无必要。

    -keepclasseswithmembers class * { @retrofit2.http.* <methods>; }

### 冗余的网络响应与适配器规则

网络响应和第三方适配器包装（例如 RxJava）常被开发者出于谨慎过度保留。

    -keep,allowobfuscation,allowshrinking class retrofit2.Response
    -keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation
    -keep class retrofit2.adapter.rxjava2.Result { *; }

**修复方式**：确认你使用的是 Retrofit 2.10.0 及更高版本。Retrofit 从 2.9.0 起就捆绑了检测其自身 HTTP 注解（`@GET`、`@POST`）的规则（[查看 Retrofit 内嵌的 ProGuard 规则](https://github.com/square/retrofit/blob/master/retrofit/src/main/resources/META-INF/proguard/retrofit2.pro)），从 2.10.0 起还会保留 `retrofit2.Response` 和 `kotlin.coroutines.Continuation`。它会自动保留运行所需的方法签名。

## 案例：Kotlin 协程

Kotlin 协程开箱即高度优化，内嵌了 R8 规则（`kotlinx-coroutines-core` 和 `kotlinx-coroutines-android` 都包含自己的规则）。

### 整库协程规则

保留 `kotlinx.coroutines` 下的所有内容对应用体积极为不利，因为协程包含大量未被使用的内部 API。

    -keepclassmembers class kotlinx.coroutines.** { *; }

### 冗余的内部 continuation

这些低层协程元素由库自身的 consumer 规则安全保留。手工添加它们会阻止 R8 执行内部优化（例如移除未使用的 continuation 或内联）。

    -keepclassmembers class kotlin.coroutines.SafeContinuation { *; }

### Dispatcher 与异常处理器规则

有时开发者注意到旧版 Android 上因缺少类而导致的崩溃，于是加上这些规则；但如果你使用的是较新版本的 Kotlin 协程，这些情况已被自动处理，或根本不成问题。`kotlinx-coroutines-core` 会保留 `MainDispatcherFactory` 和 `CoroutineExceptionHandler`，`kotlinx-coroutines-android` 会保留 `AndroidExceptionPreHandler` 和 `AndroidDispatcherFactory`。

    -keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
    -keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
    -keepnames class kotlinx.coroutines.android.AndroidExceptionPreHandler {}
    -keepnames class kotlinx.coroutines.android.AndroidDispatcherFactory {}

**修复方式**：移除所有宽泛的 `kotlinx` keep 规则。Kotlin 协程（**1.7.0 及更高版本**）自带必要的 keep 规则（[查看协程内嵌的 ProGuard 规则](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-core/jvm/resources/META-INF/proguard/coroutines.pro)）。

## 案例：Parcelable 与枚举

**常见错误**：遗留项目里常含有手写的 `Parcelable` 或 `enum` keep 规则：

    -keep class * implements android.os.Parcelable { public static final android.os.Parcelable$Creator *; }
    -keepclassmembers enum * { *; }

**修复方式**：

1. 默认的 ProGuard 文件 `proguard-android-optimize.txt` 已经包含所有 `Parcelable` `CREATOR` 字段和 `enum` 方法（`values` 和 `valueOf`）所需的 keep 规则。
2. **删除所有手写的 Parcelable 和枚举规则**：删除这些手写 keep 规则，不要提出任何替代规则。
3. *（Parcelable 可选）*：使用 `kotlin-parcelize` 插件和 `@Parcelize` 注解，避免手写 `writeToParcel` 样板代码。
4. **理想规则**：**无。** 删除所有手写的 `Parcelable` 和 `enum` keep。

## 案例：Room 数据库

**常见错误**：手工保留 DAO 接口或生成的 `_Impl` 类。

    -keep class * extends androidx.room.RoomDatabase
    -keep class *_*Impl { *; }

**修复方式**：Room 会为它生成的代码生成自己的 ProGuard 规则。手写规则是冗余的，并且会阻止 R8 优化数据库访问层。

- **理想规则**：**无。** 删除所有手写的 Room 或 DAO keep。

## 小结

如果你已把库更新到文中提到的版本，那么你的 `proguard-rules.pro` 中不应再包含本文提到的这些库的任何 keep 规则。
