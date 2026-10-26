提供使用 ADB 在已连接的设备或模拟器上与 AppFunctions 交互的命令，用于 AppFunction 测试与调试。

## 说明

### 场景 1：列出应用功能

当你想查看设备上注册了哪些应用功能时，使用这个场景。

1. **列出所有功能**：要以 JSON 格式查看所有已注册的应用功能，运行 `adb shell cmd app_function list-app-functions`。
2. **按包过滤**：要查看某个特定包的功能，把输出通过管道传给 `grep` 或某个 JSON 工具：`adb shell cmd app_function
   list-app-functions | grep <package_name>`。

### 场景 2：调用应用功能

如果你想测试某个应用功能的执行，使用这个场景。

1. **分析 description**：调用之前，必须阅读 `list-app-functions` 输出中该函数的 `description` 字段。它通常包含关键的使用约束、必需的工作流或消歧规则。
2. **遵循约束**：遵循 description 中的所有指令，例如要求用户消歧，或先调用另一个工具。
3. **格式化参数**：把 `--parameters` 参数格式化为一个合法的 JSON 字符串，表示该函数的输入参数。
4. **执行函数**：使用 `adb shell cmd app_function execute-app-function
   --package <PACKAGE_NAME> --function <SERVICE_CLASS_NAME#FUNCTION_NAME>
   --parameters '<PARAMETERS_JSON>'`。
5. **处理响应**：该命令以 JSON 字符串返回结果。要得到精简的 YAML 输出，使用 `--brief-yaml`。

### 场景 3：管理功能状态

如果你需要在测试时启用或停用某个应用功能，使用这个场景。

1. **设置启用状态**：使用 `adb shell cmd app_function set-enabled
   --package <PACKAGE_NAME>
   --function <SERVICE_CLASS_NAME#FUNCTION_NAME>
   --state <enable|disable|default>`。

## 关键约束

### 遵循 metadata 中的描述

**强制要求**：应用功能 metadata 中的 `description` 字段是一组给 LLM 的指令。如果 description 说要“与用户消歧”或“先调用另一个函数”，你必须在执行前完成这些步骤。

### JSON 转义

**关键**：通过 `adb shell` 传入 JSON 时，始终用单引号包住 JSON 字符串，以防 shell 解释特殊字符或空格。示例：`--parameters '{"key": "value"}'`。

### 设备可用性

`app_function` 服务必须在设备上可用。如果返回 `cmd: Can't find
service: app_function`，说明该设备不支持此功能。

## 示例

### 示例 1：检查已连接设备上应用功能服务是否可用

    adb shell cmd app_function help

如果执行上述命令返回帮助页，就使用其中提供的命令和参数来指导 ADB 交互测试工具的交互。

### 示例 2：列出所有已注册的应用功能

     adb shell cmd app_function list-app-functions

### 示例 3：执行一个“发送消息”函数

     adb shell cmd app_function execute-app-function \
     --package com.example.messaging \
     --function
    'com.example.messaging.appfunctions.MessagingAppFunctionService#sendMessage' \
     --parameters '{"recipient": "Alice", "message": "Hello!"}'

### 示例 4：停用某个特定函数

     adb shell cmd app_function set-enabled --package com.example.app \
     --function 'com.example.app.appfunctions.SomeAppFunctionService#someFunction'
    --state disable

## 故障排查

### 错误：“Unknown command”

**原因**：你很可能在使用较旧版本的说明。

**解决方案**：用“示例 1”查找受支持的命令。

### 错误：“Function not found”

**原因**：函数 ID 或包名不正确。

**解决方案**：运行 `list-app-functions`，在 JSON 输出中搜索相关标识符。
