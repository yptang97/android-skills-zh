关于生成 AppFunctions 的 Kotlin 实现、处理系统级配置和管理构建依赖的专项指令。

## 指令

### 步骤 1：配置 Gradle 依赖和 KSP

把以下内容添加到 `build.gradle.kts`。App Functions 需要 KSP（Kotlin
Symbol Processing）插件。

1. **版本检查**：使用来自 maven.google.com 的库版本 `1.0.0-alpha10` 或更高。


```kotlin
implementation(libs.androidx.appfunctions)
ksp(libs.androidx.appfunctions.compiler)
```

<br />

<br />

<br />

### 步骤 2：设置应用元数据 XML

通过定义 `res/xml/app_metadata.xml` 向 LLM 描述应用的能力。


```xml
<AppFunctionAppMetadata xmlns:appfn="http://schemas.android.com/apk/androidx.appfunctions"
    appfn:description="This app manages user tasks and reminders.
    Operational Patterns:
    - Use 'createTask' to add new tasks or reminders with titles and content.
    Constraints:
    - Title or content must be non-null when creating a task."
    appfn:displayDescription="@string/user_visible_description" />
```

<br />

在 `AndroidManifest.xml` 的 `<application>` 标签内注册服务并引用应用元数据：


```xml
<service
    android:name="com.example.snippets.ai.TaskAppFunctionService"
    android:permission="android.permission.BIND_APP_FUNCTION_SERVICE"
    android:exported="true"
    tools:targetApi="36">
    <property
        android:name="android.app.appfunctions.schema"
        android:value="app_functions_schema.xsd" />
    <property
        android:name="android.app.appfunctions.v2"
        android:value="task_app_function_service.xml" />
    <intent-filter>
        <action android:name="android.app.appfunctions.AppFunctionService" />
    </intent-filter>
</service>
<property
    android:name="android.app.appfunctions.app_metadata"
    android:resource="@xml/app_metadata" />
```

<br />

### 步骤 3：实现函数

为 AppFunctions 生成 Kotlin 代码时，你必须遵守以下规则：

1. **注解**：
   - 用 `@AppFunction(isDescribedByKDoc = true)` 注解函数。
   - 用 `@AppFunctionSerializable(isDescribedByKDoc = true)` 注解关联的数据类。
2. **参数策略**：
   - **具体性**：保持参数具体。状态对象必须无歧义。
   - **可选性**：如果某个参数并非必需，就把它设为带默认值的可选参数。
3. **执行与线程**：
   - 使用 `suspend` 函数。
   - 为避免阻塞 Android UI 线程，始终在后台调度器上运行 AppFunction 实现，例如 `withContext(Dispatchers.IO)`。
4. **支持的类型**：
   - **基本类型**：`Int`、`Long`、`Float`、`Double`、`Boolean`
   - **数组**：`IntArray`、`LongArray`、`FloatArray`、`DoubleArray`、`BooleanArray`
   - **原生类型**：`String`、`PendingIntent`、`Uri`、`LocalTime`、`LocalDate`、`LocalDateTime`、`Instant`。日期和时间字段优先使用 `LocalDateTime` 或 `Instant`。
   - **自定义对象**：用 `@AppFunctionSerializable` 注解的类。
   - **集合**：任意受支持的非基本类型的 `List`
5. **默认值**：
   - 使用与该类型空状态一致的默认值，例如 `Int` 用 `0`、可空对象用 `null`、`List` 用 `emptyList()`。
6. **错误处理**：
   - 抛出 `androidx.appfunctions.AppFunctionException` 的子类，向调用方报告错误。
7. **安全**：
   - 不要暴露高度敏感的用户数据，例如密码或财务信息。
   - 不要在缺少确认步骤的情况下暴露不可逆的破坏性操作。

### 步骤 4：配置依赖注入和 service entry point

在 1.0.0-alpha10 及更高版本中，App Functions 使用编译期的
`@AppFunctionServiceEntryPoint` 架构。创建一个继承 `AppFunctionService` 并标注
`@AppFunctionServiceEntryPoint` 的抽象类。KSP 会生成具体的服务类和 XML schema。

#### 使用 Hilt 的推荐做法

用 `@AndroidEntryPoint` 注解你的服务，并使用标准的
`@Inject internal lateinit var` 注入数据仓库或用例：


```kotlin
@RequiresApi(36)
@AndroidEntryPoint
@AppFunctionServiceEntryPoint(
    serviceName = "ConfigAppFunctionServiceHeader",
    appFunctionXmlFileName = "config_app_function_service_header",
)
abstract class BaseAppFunctionServiceHeader : AppFunctionService() {
    @Inject internal lateinit var messageRepository: MessageRepository

    @AppFunction(isDescribedByKDoc = true)
    internal suspend fun send(
        name: String,
        endpointValue: String,
        messageBody: String,
    ): MessageResult {
        return messageRepository.send(name, endpointValue, messageBody)
    }
}
```

<br />

#### 使用其他依赖注入框架或 service locator 的框架无关做法

虽然推荐使用 Hilt，但很多 Android 应用会用其他依赖注入框架（例如 Koin、Anvil
或手写的 Service Locator）实现 AppFunctions。由于 `AppFunctionService` 继承自
Android 的 `android.app.Service`（因此也继承了 `Context`），你可以通过
`applicationContext` 在属性 getter 中或服务生命周期执行期间直接访问应用的 DI
容器：


```kotlin
@RequiresApi(36)
@AppFunctionServiceEntryPoint(
    serviceName = "ServiceLocatorConfigAppFunctionService",
    appFunctionXmlFileName = "service_locator_config_app_function_service",
)
abstract class BaseAppFunctionServiceLocator : AppFunctionService() {
    // Example using a manual Service Locator / Application container
    private val messageRepository by lazy {
        (applicationContext as AppFunctionApplication).appContainer.messageRepository
    }
    // Or with Koin / alternative DI locators:
    // private val messageRepository: MessageRepository by inject()

    @AppFunction(isDescribedByKDoc = true)
    internal suspend fun send(
        name: String,
        endpointValue: String,
        messageBody: String,
    ): MessageResult {
        return messageRepository.send(name, endpointValue, messageBody)
    }
}
```

<br />

### 步骤 5：架构整洁

不要试图让 `AppFunction` 类或方法做到与操作系统无关——App Functions 本身就是
`androidx.appfunctions` 中 Android 平台集成的一部分。为了架构整洁，应在
`@AppFunction` 方法内使用应用已有的功能（例如已有的仓库、用例或领域编排器）
来执行行为，而不是围绕 OS 服务创建多余的抽象层。

<br />

## 关键约束

### 可序列化类的 KSP 合规性

**关键约束**：对 `@AppFunctionSerializable` 数据类，只有当 KDoc 以内联形式直接
写在每个属性定义上时，KSP 才会提取其中的文档。不要使用类级别的 `@param` 或
`@property` 标签。

### 包完整性

配置 API 和 `@AppFunction` 注解位于 `androidx.appfunctions`。

## 示例

### 示例：带内联 KDoc 的可序列化类


```kotlin
/** The parameter to create the task. */
@AppFunctionSerializable(isDescribedByKDoc = true)
data class CreateTaskParams(
    /** The title of the task. */
    val title: String?,
    /** The content of the task. */
    val content: String?,
)

/** The user-created task. */
@AppFunctionSerializable(isDescribedByKDoc = true)
data class Task(
    /** The ID of the task. */
    val id: String,
    /** The title of the task. */
    val title: String,
    /** The content of the task. */
    val content: String,
)
```

<br />

<br />

### 示例：实现细节


```kotlin
@RequiresApi(36)
@AndroidEntryPoint
@AppFunctionServiceEntryPoint(
    serviceName = "TaskAppFunctionService",
    appFunctionXmlFileName = "task_app_function_service",
)
abstract class BaseTaskAppFunctionService : AppFunctionService() {
    @Inject internal lateinit var taskRepository: TaskRepository

    /**
     * Creates a task based on [createTaskParams].
     *
     * @param createTaskParams The parameter to describe how to create the task.
     */
    @AppFunction(isDescribedByKDoc = true)
    suspend fun createTask(
        createTaskParams: CreateTaskParams,
    ): Task = withContext(Dispatchers.IO) {
        // Developers can use predefined exceptions to let the agent know
        // why it failed.
        if (createTaskParams.title == null && createTaskParams.content == null) {
            throw AppFunctionInvalidArgumentException("Title or content should be non-null")
        }

        val id = taskRepository.createTask(
            createTaskParams.title,
            createTaskParams.content
        )

        return@withContext taskRepository
            .getTask(id)
            ?.toTask()
            ?: throw AppFunctionElementNotFoundException("Task not found for ID = $id")
    }

    // Maps internal TaskEntity
    private fun TaskEntity.toTask() = Task(id = id, title = title, content = description)
}
```

<br />

<br />

## 故障排查

### 错误：「AppFunction unavailable」或「Metadata missing」

**原因**：AppSearch 索引未能正确提取 schema。

**解决方案**：

1. 确认 `@AppFunctionSerializable` 类使用内联 KDoc 注释，而不是类级别的 `@param` 标签。
2. 检查 `assets/<appFunctionXmlFileName>.xml` 文件是否存在于 APK 中。
3. 确认 `ksp("androidx.appfunctions:appfunctions-compiler")` 依赖已正确应用。
4. 确保 `ksp` 参数 `appfunctions:aggregateAppFunctions` 设为 `"true"`。
