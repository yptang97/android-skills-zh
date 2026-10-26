keep 规则示例的分类汇总，包括要查找的代码模式（imports/用法）
以及对应的建议规则。

### 1. 反射：按名称加载的类

**场景：** 库或应用使用字符串名称动态加载一个类

- **查找：**
  `Class.forName("...")`,
  `getDeclaredConstructor().newInstance()`，或是用于动态加载的接口。

- **示例代码：**
  `kotlin
  val taskClass = Class.forName(className)
  val task = taskClass.getDeclaredConstructor().newInstance() as StartupTask`

- **建议的 keep 规则：**
  \`\`\`proguard

  -keep class \* implements com.example.library.StartupTask {
  (); } \`\`\`

### 2. 反射：通过 `::class.java` 传入的类

**场景：** 应用把类引用直接传给库函数。

- **查找：** 作为参数传入的 `::class.java`（Kotlin）或 `.class`（Java）。
- **示例代码：**
  `kotlin
  fun <T> register(clazz: Class<T>) { }
  // Usage:
  register(MyService::class.java)`

- **建议的 keep 规则：**
  \`\`\`proguard

  # Keep the class itself (R8 usually handles this, but explicit rules ensure stability)

  -keep class com.example.app.MyService {
  (); } \`\`\`

### 3. 基于注解的反射（方法/类）

**场景：** 使用自定义注解标记方法或类，
以便通过反射执行。

**查找：** 自定义 `@interface` 定义，以及按注解过滤的
`getDeclaredMethods()`。
**示例代码：**
`kotlin
annotation class ReflectiveExecutor
// Logic: find methods annotated with @ReflectiveExecutor and invoke them`

- **建议的 keep 规则：** \`\`\`proguard # Keep the annotation itself -keep @interface com.example.library.ReflectiveExecutor

# Keep members of any class annotated with this specific annotation
-keepclassmembers class \* {
@com.example.library.ReflectiveExecutor \*;
}
\`\`\`

### 4. 可选依赖（软依赖）

**场景：** 核心库检查
classpath 中是否存在某个可选模块。

- **查找：** 围绕 `Class.forName()`、用于切换功能的 `try-catch` 块。
- **示例代码：** \`\`\`kotlin private const val VIDEO_TRACKER_CLASS = "com.example.analytics.video.VideoEventTracker"

try {
Class.forName(VIDEO_TRACKER_CLASS).getDeclaredConstructor().newInstance()
} catch (e: ClassNotFoundException) { /\* skip feature \*/ }
\`\`\`

- **建议的 keep 规则：** `proguard
  # Preserve the optional class so the check doesn't fail due to shrinking
  -keep class com.example.analytics.video.VideoEventTracker {
  <init>();
  }`

### 5. 访问私有成员

**场景：** 使用反射访问未通过公共 API 暴露的
内部字段或方法。

- **查找：** `getDeclaredField("...")` 或 `getDeclaredMethod("...")`，后面跟着 `isAccessible = true`。
- **示例代码：**
  `kotlin
  val secretField = instance::class.java.getDeclaredField("secretMessage")
  secretField.isAccessible = true`

- **建议的 keep 规则：**
  \`\`\`proguard

  # Specifically keep the private field/method by name and type

  -keepclassmembers class com.example.LibraryClass {
  private java.lang.String secretMessage;
  }
  \`\`\`

### 6. Parcelable（手动实现）

**场景：** 不使用 `@Parcelize`
注解而实现 `Parcelable`。

- **查找：** `implements Parcelable` 以及静态的 `CREATOR` 字段。
- **示例代码：**
  `kotlin
  class MyData : Parcelable {
  // Manual implementation with CREATOR field
  }`

- **建议的 keep 规则：**
  *（注意：如果使用 `import kotlinx.parcelize.Parcelize`，R8/ProGuard 规则会
  自动生成。如果是手动实现，使用以下规则：）*
  `proguard
  -keepclassmembers class * implements android.os.Parcelable {
  static android.os.Parcelable$Creator CREATOR;
  }`

### 7. 枚举与混淆

**场景：** 应用间接使用 `Enum.valueOf("STRING_NAME")`（例如通过 JSON
反序列化），而枚举名称被混淆。

- **查找：** ProGuard 文件中多余的通用 Enum keep 规则。
- **示例代码：**
  \`\`\`proguard

  # Unnecessary rule

  -keepclassmembers enum \* { \*; }
  \`\`\`
- **建议的 keep 规则：**
  \*（注意：默认的 `proguard-android-optimize.txt` 已经包含针对 Enum 的最佳
  规则（保留 `values()` 和 `valueOf(String)`）。任何额外
  的 Enum 手动规则都是多余的。）# No manual rule needed. Use default
  proguard-android-optimize.txt.
