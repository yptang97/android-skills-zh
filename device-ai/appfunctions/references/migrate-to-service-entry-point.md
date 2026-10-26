按以下系统化流程，把在 1.0.0-alpha09 及更低版本中使用 AppFunctions API 的 Android
应用，迁移到 `1.0.0-alpha10` 引入的编译期 `@AppFunctionServiceEntryPoint` 架构。

*** ** * ** ***

## 架构变化概览

在较低版本的 AppFunctions API 中，例如 `1.0.0-alpha09` 版本：

- 应用需要为核心功能和服务组件分别声明依赖，具体是 `androidx.appfunctions:appfunctions` 和
  `androidx.appfunctions:appfunctions-service`。
- 应用在 `Application` 类上实现 `AppFunctionConfiguration.Provider`。
- 你使用 `AppFunctionConfiguration.Builder().addEnclosingClassFactory(...)` 手动注册外围类的
  实例化。
- 你把 metadata 属性标签直接放在 `<application>` 下。

在引入 `@AppFunctionServiceEntryPoint` 的 `1.0.0-alpha10` 版本中：

- 核心依赖与服务依赖合并为单个运行时构件 `androidx.appfunctions:appfunctions`，不再需要
  独立的 `appfunctions-service` 库。
- 一个继承 `AppFunctionService` 的专用包装类，标注 `@AppFunctionServiceEntryPoint` 注解，
  以及 Hilt 的 `@AndroidEntryPoint` 或替代的依赖注入框架。
- KSP 编译器在 `assets/` 中生成具体的 service 子类和一份 XML metadata schema 文件。
- 系统使用 `AndroidManifest.xml` 中合并后的 `<service>` 与 `app_metadata` 声明来发现并路由
  执行。

### 从 1.0.0-alpha09 到 1.0.0-alpha10 的强制迁移要求

如果只关注新 `@AppFunctionServiceEntryPoint` 架构所要求的强制性 API 变更，迁移包含四项你
必须完成的严格要求：

1. **合并构建依赖**：移除已合并的 `appfunctions-service` 依赖，同时保留核心 `appfunctions` 和 KSP 编译器。
2. **创建 service 包装类**：用继承 `AppFunctionService` 并标注 `@AppFunctionServiceEntryPoint` 的抽象类，替换 `Application` 类上的旧 `AppFunctionConfiguration.Provider`。
3. **注解与 context 解耦**：把 `@AppFunction` 注解移到新的包装类方法上，并去掉 `AppFunctionContext` 参数，因为 `AppFunctionService` 直接继承自 `Context`。
4. **清单注册**：在 `AndroidManifest.xml` 中用 `BIND_APP_FUNCTION_SERVICE`、`AppFunctionService` intent filter 和 metadata 属性标签，注册 KSP 生成的具体 service。

*** ** * ** ***

## 系统化迁移步骤

### 合并 AppFunctions 构建依赖

从模块构建文件（例如 `build.gradle.kts`）和版本目录（例如 `libs.versions.toml`）中移除独立的
`appfunctions-service` 库。在 `1.0.0-alpha10` 版本中，所有核心 service 能力都直接合并进主
`appfunctions` 构件。

    // build.gradle.kts
    dependencies {
        implementation(libs.androidx.appfunctions)
    -   implementation(libs.androidx.appfunctions.service)
        ksp(libs.androidx.appfunctions.compiler)
    }

    # libs.versions.toml
    [versions]
    appfunctions = "1.0.0-alpha10"

    [libraries]
    androidx-appfunctions = { module = "androidx.appfunctions:appfunctions", version.ref = "appfunctions" }
    -   androidx-appfunctions-service = { module = "androidx.appfunctions:appfunctions-service", version.ref = "appfunctions" }
    androidx-appfunctions-compiler = { module = "androidx.appfunctions:appfunctions-compiler", version.ref = "appfunctions" }

> [!NOTE]
> **注意：** 如果项目中的其他依赖使用 `1.0.0-SNAPSHOT` 之类的快照构建，或使用来自 `https://androidx.dev/snapshots/...` 的自定义快照仓库，请在 `settings.gradle.kts` 中保留你的自定义快照仓库配置。否则，标准 Google Maven 仓库会直接解析 `1.0.0-alpha10`。

*** ** * ** ***

### 创建一个继承 `AppFunctionService` 的专用包装 service

不要在独立的业务逻辑类上打注解，也不要实现手动的配置 provider，而是在项目中创建一个抽象
service 包装类，例如 `BaseAppFunctionService`，继承 `AppFunctionService` 并标注
`@AppFunctionServiceEntryPoint`。

#### 使用 Hilt 的推荐做法

用 `@AndroidEntryPoint` 标注 service，并使用标准的 `@Inject internal lateinit var` 注入数据
仓库或用例：


```kotlin
@RequiresApi(36)
@AndroidEntryPoint
@AppFunctionServiceEntryPoint(
    serviceName = "MyAppFunctionService",
    appFunctionXmlFileName = "my_app_function_service", // Do NOT include .xml extension
)
abstract class BaseAppFunctionService : AppFunctionService() {
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

#### 框架无关的做法：使用替代的依赖注入框架或 service locator

虽然推荐 Hilt，但许多 Android 应用会用 Koin、Anvil 或手动 Service Locator 等替代依赖注入
框架来实现 AppFunctions。由于 `AppFunctionService` 继承自 Android 的
`android.app.Service`，因而也继承自 `Context`，你可以通过 `applicationContext` 在属性
getter 中或 service 生命周期执行期间直接访问应用的 DI 容器：


```kotlin
@RequiresApi(36)
@AppFunctionServiceEntryPoint(
    serviceName = "ServiceLocatorMyAppFunctionService",
    appFunctionXmlFileName = "service_locator_my_app_function_service",
)
abstract class ServiceLocatorBaseAppFunctionService : AppFunctionService() {
    // Example using a manual Service Locator or Application container
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

> [!IMPORTANT]
> **重要：** `appFunctionXmlFileName` 参数（例如 `"my_app_function_service"`）不能包含 `.xml` 扩展名，因为 KSP 编译器会自动追加 `.xml`。传入 `"my_app_function_service.xml"` 会让资源被命名为 `"my_app_function_service.xml.xml"`。

*** ** * ** ***

### 简化方法签名并解耦 context

从核心方法中移除旧的 `AppFunctionContext` 参数。当方法需要 Android `Context` 时（例如构造
`PendingIntent`），直接从 `AppFunctionService` 包装类访问 `this`，因为该包装类本身就继承自
`android.content.Context`。

    -   suspend fun makeCall(appFunctionContext: AppFunctionContext, contactName: String?): PendingIntent
    +   suspend fun makeCall(contactName: String?): PendingIntent

*** ** * ** ***

### 移除旧的配置 provider

更新 `Application` 类，移除 `AppFunctionConfiguration.Provider` 及其相关的 builder 入口点：

    -   abstract class BaseChatApplication : Application(), AppFunctionConfiguration.Provider { ... }
    +   abstract class BaseChatApplication : Application()

*** ** * ** ***

### 避免多余的抽象层

不要试图让 `AppFunction` 类或方法与操作系统无关——AppFunctions 通过 `androidx.appfunctions`
包，本身就是 Android 平台集成的一部分。为了架构整洁，请在 `@AppFunction` 方法内使用已有的
应用功能来执行行为，例如现有仓库、用例或领域编排器，而不是在 OS service 之外再创建多余的
抽象层。

*** ** * ** ***

### 合并 service 与 metadata 的清单声明

在模块清单中注册 KSP 生成的 service 声明和 `app_metadata` 属性，例如在
`src/main/AndroidManifest.xml` 的 `<application>` 标签内：


```xml
<service
    android:name="com.example.snippets.ai.MyAppFunctionService"
    android:permission="android.permission.BIND_APP_FUNCTION_SERVICE"
    android:exported="true"
    tools:targetApi="36">
    <property
        android:name="android.app.appfunctions.schema"
        android:value="app_functions_schema.xsd" />
    <property
        android:name="android.app.appfunctions.v2"
        android:value="my_app_function_service.xml" />
    <intent-filter>
        <action android:name="android.app.appfunctions.AppFunctionService" />
    </intent-filter>
</service>
<property
    android:name="android.app.appfunctions.app_metadata"
    android:resource="@xml/app_metadata" />
```

<br />

*** ** * ** ***

## 验证与故障排查

1. **清理重建并部署**：`bash
   ./gradlew clean installDebug`
2. **验证 AppSearch 发现 / 索引**：运行以下 ADB 命令，确认系统成功发现并索引了你的函数：
   `bash
   adb shell cmd app_function list-app-functions`
   *如果你的包没有出现，请确认 `android.app.appfunctions.v2`
   与 `assets/` 中生成的确切资源名一致。*

3. **使用 ADB 验证执行**：
   `bash
   adb shell "cmd app_function execute-app-function \
   --package com.example.chatapp \
   --function 'com.example.chatapp.appfunctions.BaseAppFunctionService#send' \
   --parameters '{\"name\": \"Alice\", \"endpointValue\": \"1\", \"messageBody\": \"Hello Alice!\"}'"`
