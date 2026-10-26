如果项目中使用了 Paparazzi，请把它升级到 2.0.0-alpha04 或更高版本。

Paparazzi 2.0.0-alpha04 及更低版本与 Gradle 9 并不完全兼容，而 AGP 9 要求使用 Gradle 9。这意味着，如果不做规避处理，使用 Paparazzi v2.0.0-alpha04 及更低版本的项目无法迁移到 AGP 9。

撰写本文时，Paparazzi 还没有更高的版本。也就是说，v2.0.0-alpha04 就是最新的发布版本。

这个问题源于 Paparazzi 使用了 Gradle 的内部类，而这些类经常会在没有预警的情况下以破坏性的方式变动。这个具体问题与 HTML 测试报告有关。要规避它，请关闭这些 HTML 测试报告。下面给出两个示例，一个用于 Kotlin DSL，另一个用于 Groovy DSL。任何应用了 paparazzi 插件（`app.cash.paparazzi`）的模块都必须采用这两种规避方式之一。

Kotlin DSL：

    tasks.withType<Test>().configureEach {
      // https://github.com/cashapp/paparazzi/issues/2111
      reports.html.required = false
    }

Groovy DSL：

    tasks.withType(Test).configureEach {
      // https://github.com/cashapp/paparazzi/issues/2111
      reports.html.required = false
    }
