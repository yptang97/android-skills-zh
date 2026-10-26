## 1. 结构分析 \& 映射

**确定** XML 元素与 Compose 对应项之间的**精确映射**。你需要判断：

- 替换 XML 标签层级的确切 `@Composable` 函数（例如 `ConstraintLayout`、`Column`、`LazyColumn`）。
- 复现 XML 属性所需的具体参数和 `Modifier` 扩展（例如 `layout_width`、`padding`、`elevation`）。
- 交互元素合适的状态管理策略。

## 2. 迁移执行

**把 XML 布局代码转换为 Jetpack Compose**，在利用 Compose 声明式特性的同时，确保视觉层级和布局逻辑保持不变。

## 3. 主题 \& 设计系统一致性

**不要使用硬编码值。**样式遵循以下规则：

- **Token 对齐：**把 XML 的尺寸、颜色和样式属性与现有的 Compose `Theme`（例如 `MaterialTheme.colorScheme` 或自定义设计系统的 token）相互对照。
- **复用优先于新建：**如果当前 Compose 主题中已有匹配的值，就复用它们。如果某个值缺失但设计上需要，请在主题结构中定义它，而不要在 Composable 中硬编码。
- **项目一致性：**你**必须**严格遵守项目中现有的代码约定、命名规范和实现模式。**优先**使用项目专用的可复用组件，而不是通用的 Material 默认实现。

## 4. 组件分层 \& 复用性

评估该 XML 布局是否是基础层级的设计系统组件（在整个应用中以特定角色被复用）。如果是：

- **创建可复用的 composable：**不要只是把代码内联进去，而是定义一个全新的独立 `@Composable`。
- **参数化：**为可变数据（文本、颜色、样式）暴露具体的参数，布局相关的定制用 `Modifier` 实现。
- **功能对齐 \& 限制：**确保新 composable 强制实施与原始 XML 组件相同的 UI 约束，在保持预期灵活性的同时防止未授权的样式覆盖。

迁移前的示例：

    <style
        name="Widget.Rounded.Button"
        parent="Widget.Button.Borderless">
        <item name="android:fontFamily">sans-serif-medium</item>
        <item name="android:minWidth">@dimen/min_width</item>
        <item name="android:paddingStart">@dimen/padding_2</item>
        <item name="android:paddingEnd">@dimen/padding_2</item>
        <item name="cornerRadius">8dp</item>
    </style>

迁移后的示例：


```kotlin
@Composable
fun RoundedBorderlessButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    TextButton(
        onClick, modifier
            .defaultMinSize(minWidth = dimensionResource(R.dimen.min_width))
            .padding(
                start = dimensionResource(R.dimen.padding_2),
                end = dimensionResource(R.dimen.padding_2)
            ), enabled, shape = RoundedCornerShape(8.dp),
        colors = ButtonDefaults.textButtonColors(
            contentColor = MaterialTheme.colorScheme.primary
        )
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium.copy(
                fontFamily = FontFamily.SansSerif,
                fontWeight = FontWeight.Medium
            )
        )
    }
}
```

<br />

*** ** * ** ***

## 5. 输出要求

- 提供完整的 Kotlin 文件内容。
- 包含必要的 import。
- 为复杂转换添加解释映射逻辑的文档注释（`/** ... */`）。