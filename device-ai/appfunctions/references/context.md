定义 Android AppFunctions skill 套件的统一语言。

## 架构与版本

`AppFunctionServiceEntryPoint` API：
这套编译期 AppFunctions 架构从 1.0.0-alpha10 版本引入。用一个包装 service 扩展 `AppFunctionService`，并为它加上 `@AppFunctionServiceEntryPoint` 注解。随后 KSP 会生成 XML 元数据，并在编译期完成 service 路由。

旧版手动 provider API：
这套已废弃的 AppFunctions 架构适用于 1.0.0-alpha09 及更早版本。应用在 `Application` 类上实现 `AppFunctionConfiguration.Provider`。方法需要把 `AppFunctionContext` 作为第一个参数。项目依赖独立的 `appfunctions-service` 库。

## 模式

Service 入口点模式：
1.0.0-alpha10 版本引入了这种架构模式。你直接在扩展 `AppFunctionService` 的抽象类中声明 `@AppFunction` 方法。该类使用 `@AppFunctionServiceEntryPoint` 和 `@AndroidEntryPoint` 注解。这些注解让你可以直接注入数据源或仓库，无需中间的业务逻辑委派层。
