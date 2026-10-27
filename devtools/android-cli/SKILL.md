---
name: android-cli
description: 提供安装和使用 `android` CLI 的说明。`android` 命令行工具是 Android 开发的
  关键工具，可帮你创建新的 Android 项目、把 APK 安装到设备和模拟器并在其上启动和运行
  应用、管理和操作 Android 虚拟设备（包括截图和 UI 检查）、管理 Android SDK 组件、
  查询官方 Android 文档，以及发现并安装官方 Android skills。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-25'
  keywords:
  - android-cli
  - sdk
  - emulator
  - skills
  - docs
  - knowledge base
  - project creation
  - screenshots
---

这个 skill 提供使用 `android` CLI 工具的说明。该工具包含多种命令，用于创建项目、运行
应用、与设备交互，以及管理 CLI 环境。

## 安装

如果 android 工具不在 PATH 中，先安装它。安装时运行以下命令：

- Linux x86-64：curl -fsSL https://dl.google.com/android/cli/latest/linux_x86_64/install.sh \| bash
- Linux ARM64：curl -fsSL https://dl.google.com/android/cli/latest/linux_arm64/install.sh \| bash
- Mac Arm：curl -fsSL https://dl.google.com/android/cli/latest/darwin_arm64/install.sh \| bash
- Mac Intel：curl -fsSL https://dl.google.com/android/cli/latest/darwin_x86_64/install.sh \| bash
- Windows：curl -fsSL https://dl.google.com/android/cli/latest/windows_x86_64/install.cmd -o "%TEMP%\\i.cmd" \&\& "%TEMP%\\i.cmd"

## SDK 管理

要管理 Android SDK 和工具的安装，使用 `sdk` 命令。例如：

- `android sdk install <package>[@<version>]...`：安装指定的包。可以指定多个包，用空格分隔。`<version>` 默认取最新版本。例如：`android sdk install platforms/android-30@2 platforms/android-34`
- `android sdk update [<pkg-name>]`：把指定的包或所有包更新到最新版本。
- `android sdk remove <pkg-name>`：从本地 SDK 中移除某个包。
- `android sdk list --all`：列出已安装和可用的 SDK 包。

## 创建项目

用 `create` 命令从模板创建项目。

例如：`android create empty-activity --name="My App" --output=./my-app`

## 与 Android 设备交互

用 `android layout` 命令以 JSON 格式检查 Android 应用的 UI 布局。用 `android screen`
命令目视检查 UI，并获取可视区域的边界坐标。
`android layout` 把 UI 导出为 JSON。`android screen capture -o <file path>` 保存 PNG。
两者在只连接一台设备时会自动选中该设备；连接了多台时，需要传 `--device=<serial>`（用
`adb devices` 列出各设备的 serial）。

### UI 导出

`android layout` 返回屏幕上 UI 元素的 JSON 树。

每个 JSON 对象表示 Android 应用中的一个 UI 元素。可能包含以下属性：
- `text` - 元素包含的任何字面文本
- `resource-id` - 用于引用该元素的 Android 资源 ID
- `content-desc` - 供无障碍工具使用的 UI 元素描述
- `interactions` - 该元素支持的用户交互集合。可能包含以下一项或多项：`CHECKABLE`、`CLICKABLE`、`FOCUSABLE`、`SCROLLABLE`、`LONG-CLICKABLE`、`PASSWORD`
- `state` - 元素所处的状态集合。可能包含 `CHECKED`、`FOCUSED`、`SELECTED` 中的一项或多项
- `bounds` - 元素边界矩形的屏幕坐标，格式为 `[min X,min Y][max X, max Y]`
- `center` - 元素中心的屏幕坐标，格式为 `[x,y]`
- `off-screen` - 如果为 true，表示该元素在 UI 层级中，但不在屏幕范围内；可能需要滚动才能看到。
- `hidden` - 如果为 true，表示该元素在 UI 层级中，但在屏幕上不可见或不可交互。

把 `layout` 作为检查 Android 应用的主要手段。

默认情况下，`layout` 只返回有内容或可交互的元素：
- `text` 或 `content-desc` 属性非空的元素
- `interactions` 或 `state` 非空的元素
要返回所有元素，使用 `--full` 标志

如果 `layout` 一直失败，改用 `android screen capture --annotate` 检查应用。

### 截图

`android screen capture -o <file path>`（或 `--output=<file path>`）把当前设备屏幕的 PNG 保存到 `<file path>`。

把 `screen capture` 作为检查 Android 应用的次要手段。
示例：
- 理解屏幕上图像的内容
- 查看 `WebView`（网页内容不一定出现在 UI 导出中）
- 按视觉外观查找某个 UI 元素

**重要**：在任何 `android screen` 命令返回 PNG 图像之后，务必先*目视*检查该图像，再做其他事情。

#### 带标注的截图

`android screen capture --annotate -o <file path>`（或 `-a -o <file path>`）
`android screen resolve --screenshot <path> --string <string>`

`--annotate` 命令会在 UI 元素周围加数字标签和边界框。用该命令定位无法在 `layout` 输出中找到的 UI 元素。

要在输入命令中引用这些标签，用 `screen resolve` 把标签转换成坐标：

`android screen resolve --screenshot <file path> --string "#3"` 返回 `<x coord of region 3> <y coord of region 3>`

为了减少轮次，可以组合 shell 命令：

`adb shell input $(android screen resolve --screenshot screen.png --string "tap #34")`

该命令会点击 `screen.png` 中的 34 号区域。

### 输入

用 `adb shell input` 与 Android 设备交互。
元素的 `"interactions"` 属性说明了可以在该元素上执行哪些交互。

用元素的 `center` 坐标或 `bounds` 坐标与 UI 元素交互：
`json
{
"key": -248568265,
"class": "android.widget.Button",
"bounds": "[138,9][167,38]",
"center": "[152,23]"
}`
要点击这个按钮，执行 `adb shell input tap 152 23`。这会点击中心位置。

    {
      "key": 12487234,
      "class": "com.example.ui.ScrollableList",
      "bounds": "[100,200][400,600]",
      "center": "[250,400]"
    }

要在这个列表上向下滚动，执行 `adb shell input swipe 250 400 250 200 500`。这会从中心向顶部滑动，持续 500ms。

#### 文本输入

要输入文本，确保输入框已获得焦点，然后执行 `adb shell input text "<text>"`。

- **空格（`%s`）：** 用 `%s` 替换空格（Android 会忽略原始空格之后的文本）：`adb shell input text "Hello%sworld"`（输入 `"Hello world"`）。
- **特殊字符：** 转义 shell 元字符（`&`、`$`、`(`、`)`、`!`）：`adb shell input text "AT\&T"` 或 `adb shell input text 'Price:\$10'`。
- **提交 / 回车：** `adb shell input keyevent 66`

### Android 交互规则

1. 输入文本前，务必确认文本输入框的 `"state"` 列表中有 `"FOCUSED"`。
2. 如果元素的 `"interactions"` 列表中有 `"SCROLLABLE"`，在查找缺失的 UI 元素时尝试滚动它。
3. 执行滚动输入时始终缓慢滚动。`adb shell input swipe` 的第 5 个参数控制滚动时长。
4. 内容可能需要时间加载；如果执行操作后 `layout` 缺少信息，等几秒，再执行一次 `layout`，看是否有变化。

## 运行 journey 测试

Journey 测试涉及设备交互；用 `android layout` 和 `android screen` 命令评估 journey。
设备交互的相关说明同样适用。

journey 是用 XML 描述的 Android 应用行为测试。它由一组 `<action>` 元素组成。例如：
`xml
<journey name="My Journey">
<description>
A sample journey to illustrate the format
</description>
<actions>
<action>
Tap the "Home" icon
</action>
<action>
Verify that the app is on its Home screen
</action>
</actions>
</journey>`

按顺序遍历 `<actions>` 列表来评估 journey。逐个评估每个 `<action>` 块。
如果 `<actions>` 列表中的所有元素都成功，则 journey 成功。

journey 是应用的测试用例。journey XML 是唯一事实来源；如果应用与 journey 不一致，则视为应用失败。
此外，如果应用退出、崩溃或卡死，journey 评估停止，journey 失败。

**重要** - 严格按照所写内容执行每一步，并且各步骤之间相互独立！如果某个 action 要求 `"tap the first search result"`，
你必须找到搜索结果并点击第一条。即使你认为自己知道该 action 的意图，也必须这样做。

### 执行操作

有些 `<action>` 元素指明要对运行中的 Android 应用执行 UI 交互。执行该交互，并确认应用没有
崩溃或出现意外行为。这是你为一个 `<action>` 应该做的*唯一*验证。

如果无法按指定方式执行该交互，journey 失败。
示例：
`<action>Click the red button</action>`
如果你判断 UI 中不存在红色按钮，journey 失败。

如果 `<action>` 的文本指明了多个操作，把它拆成子 action 并逐个评估：
示例：
`<action>Search for soda and add the first result to the cart</action>`
应评估为：
`<action>Search for soda</action>
<action>Add the first result to the cart</action>`

如果 `<action>` 中包含的内容不是 UI 交互的说明，提示用户该 journey 格式有误并提前退出，
同时说明具体错误。

### 验证预期

以 "check" 或 "verify" 开头的 `<action>` 元素描述对 Android 应用当前状态的预期。确定应用的当前
状态，并检查是否满足这些预期。

通过检查设备当前屏幕来确定应用当前状态，不要与屏幕交互。
示例：
`<action>Check if "Switch 2" is visible on the screen</action>`
这只需检查当前屏幕，不需要滚动或交互。如果 "Switch 2" 当前不可见，该 action 失败。

如果预期未满足，把该 `<action>` 标记为失败，journey 评估随即结束。单个 `<action>` 可能包含
多个预期。
示例：
`<action>Verify that the app is on the Home screen, the Home icon is blue, and the temperature is displayed</action>`
只要以下任一项为假，该 `<action>` 就失败：
- 应用处于 Home 屏幕
- 存在 Home 图标，且为蓝色
- 显示了温度

### 处理失败

运行 journey 时，把它当作测试来评估。失败是可以接受的，而且常常是预期的。正确报告失败才是首要任务。

把调试和排错降到最低；假设工具每次给出的输出都是正确的。目标是判断*当前*的 Android 应用能否正确处理
journey 中列出的*当前*步骤。关于修复缺陷、澄清或其他改进的建议应保留到最后的 journey 评估小结中。

### 小结

评估完整个 journey 后，输出一个 markdown（.md）文件描述结果。

文件应使用以下格式：

    # Journey: <Name of the journey>

    ## Results

      <!-- Append "✅" to the action header if the instruction was evaluated or "❌" if the instruction could not be evaluated -->
    ### Action: Click the blue button ✅
    - **Commands**:
      <!-- A list of the ADB commands executed while evaluating the instruction -->
      - `adb shell input swipe 490 200 500 500 500`
      - `adb shell input tap 45 920`

      <!-- Failure reasons, feedback, or other useful information -->
    - **Comment**: The journey step doesn't specify that the button requires scrolling to see

    ### Action: Check if "Switch 2" is visible on the screen ✅
    - **Screenshot**: [switch_2_screenshot.png](path/to/screenshot)
    - **Comment**: Confirmed both in layout and visually

    ### Action: The home screen is shown ❌
    - **Comment**: The settings page was shown

    <!-- Append nothing to the action header if the action was not evaluated because the journey execution ended early -->
    ### Action: Swipe down to view active notifications

## 文档搜索

`docs` 命令在 Android Knowledge Base 中搜索权威、高质量的 Android 开发者
文档。只要提供几个关键词，该工具就会返回包含 Android API 或库用法示例与指导的高质量
文章。用它获取如何完成 Android 特定任务的补充信息，或进一步了解 Android API、
surface、库或设备。

始终用该工具获取关于 Android 概念的最新信息。典型的使用场景有：
- 查找 API 的迁移指南。
- 查找 API 的示例。
- 查找 Android API 的最新信息。
- 查找 Android 概念的最佳实践。

## 运行 APK

用 `run` 命令运行 Android 应用。

## 管理模拟器

用 `android emulator` 命令管理 Android Virtual Devices（AVD）

## 管理 skills

用 `android skills` 命令管理面向 Android 的 agent skills。

## 更新 CLI

用 `android update` 命令更新 Android CLI。

## `android help` 输出

    Usage: android [-Vhv] [--sdk=PARAM] [COMMAND]
      -h, --help       Shows the help message for the specified command
          --sdk=PARAM  Path to the Android SDK
      -v, --verbose    Enable verbose output for troubleshooting
      -V, --version    Print version information and exit
    Commands:
      analyze     Analyzes the file(s) (AAB, APK, JAR, AAR) at the given location(s)
                  and reports back all available details
      auth        Authentication commands. Log in to and out of Google services for
                  Android CLI
      build       Build android artifacts
      completion  Installs shell autocomplete configuration for Android CLI in the
                  current user profile
      create      Creates a new Android project from available templates. You can
                  specify the project name, output directory, `minSdk` value, and
                  dry-run execution
      describe    Analyzes an Android project to generate descriptive metadata. This
                  command identifies and outputs the paths to JSON files that detail
                  the project's structure, including build targets and their
                  corresponding output artifact locations (such as APKs). This
                  information enables other tools and commands to locate build
                  artifacts efficiently
      device      Manage Android devices. Mirror connected devices or emulators in a
                  desktop window and manage remote physical device reservations
      docs        Searches and fetches developer documentation from the official
                  Android Knowledge Base
      emulator    Manages Android Virtual Devices (AVDs). Includes commands to
                  start, stop, list, and view details about emulators
      help        Shows the help information for a specified command
      info        Prints environment information including SDK location and
                  configuration variables
      init        Initializes the environment for Android CLI. Sets up required
                  configurations, directories, and default skills
      input       Interact with Android apps by performing gestures and key events
                  on UI elements
      install     Installs an Android app (one or more APKs) on a connected device
                  or emulator without activating any components, using incremental
                  optimizations for faster deployment than `adb`
      layout      Returns the layout tree of an app
      preview     Renders Jetpack Compose @Preview functions to PNG images and
                  optionally exports component tree JSON files. Runs without a
                  device or an IDE
      profiler    Profiles Android apps, games, and devices
      run         Deploys and launches an Android app on a connected device or
                  emulator
      screen      Captures and inspects the screen of a connected Android device or
                  emulator
      sdk         Manages the Android SDK installation. Includes commands to
                  install, update, remove, and list available and installed SDK
                  packages
      signals     Queries app stability and field telemetry from Crashlytics
      skills      Manages Android CLI skills. Includes commands to install, remove,
                  list, and search for skills by keyword
      studio      Connects Android CLI to a running Android Studio instance to
                  analyze files, find declarations and usages, render Compose
                  previews, and look up library versions
      update      Updates Android CLI to the latest version

    analyze
              Usage: android analyze [-h] [--analysis=PARAM] [--format=PARAM] <path>
              Analyzes the file(s) (AAB, APK, JAR, AAR) at the given location(s) and
              reports back all available details
              
              Options:
                    --analysis=PARAM  Analysis category to filter output (basic,
                                      optimization). Supports comma-separated values
                                      (default: all)
                -f, --format=PARAM    Output format: json, textproto. If omitted,
                                      output is formatted for human readability
                -h, --help            Shows the help message for the specified
                                      command
              
              android options:
                    --sdk=PARAM       Path to the Android SDK
                -v, --verbose         Enable verbose output for troubleshooting
                -V, --version         Print version information and exit
              
              Positional Parameters:
                <path>  Path to the target file(s) to analyze (AAB, APK, JAR, AAR)

    auth
              Usage: android auth [-h] [COMMAND]
              Authentication commands. Log in to and out of Google services for
              Android CLI
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                login   Log in to Google services for Android CLI
                logout  Log out from Google services for Android CLI
                status  Prints the currently signed-in account

    build
              Usage: android build [-h] [<reference>] [-- <build_args>]
              Build android artifacts
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              
              Positional Parameters:
                <reference>      Build reference ([system://][path]?[target])
                -- <build_args>  Arguments passed verbatim to the build system. Use
                                 -- to separate from other arguments

    completion
              Usage: android completion [-h] [<shell>]
              Installs shell autocomplete configuration for Android CLI in the
              current user profile
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              
              Positional Parameters:
                <shell>  If provided, prints the completion configuration script for
                         the specified shell without installing it. Supports Bash
                         and Zsh

    create
              Usage: android create [-h] [--application-id=PARAM] [--force] [--list]
                                    [--min-sdk=PARAM] [--name=PARAM] [--namespace=PARAM]
                                    [--output=PARAM] [<template-name>]
              Creates a new Android project from available templates. You can
              specify the project name, output directory, `minSdk` value, and
              dry-run execution
              
              Options:
                    --application-id=PARAM  The app ID for the app, for example
                                            `com.example.myapp`
                    --force                 Allow creating the project in a
                                            non-empty directory, overwriting
                                            existing files
                -h, --help                  Shows the help message for the specified
                                            command
                    --list                  List all available templates
                    --min-sdk=PARAM         The `minSdk` value supported by the app
                                            (the default value is defined in the
                                            template)
                    --name=PARAM            The name of the app, for example `My
                                            Application`
                    --namespace=PARAM       The namespace for resources and package
                                            name for Kotlin source files
                -o, --output=PARAM          The destination project directory path
                                            (the default value is `.`)
              
              android options:
                    --sdk=PARAM             Path to the Android SDK
                -v, --verbose               Enable verbose output for
                                            troubleshooting
                -V, --version               Print version information and exit
              
              Positional Parameters:
                <template-name>  The template name

    describe
              Usage: android describe [-h] [--project_dir=PARAM]
              Analyzes an Android project to generate descriptive metadata. This
              command identifies and outputs the paths to JSON files that detail the
              project's structure, including build targets and their corresponding
              output artifact locations (such as APKs). This information enables
              other tools and commands to locate build artifacts efficiently
              
              Options:
                -h, --help               Shows the help message for the specified
                                         command
                    --project_dir=PARAM  The project directory to describe
              
              android options:
                    --sdk=PARAM          Path to the Android SDK
                -v, --verbose            Enable verbose output for troubleshooting
                -V, --version            Print version information and exit

    device
              Usage: android device [-h] [COMMAND]
              Manage Android devices. Mirror connected devices or emulators in a
              desktop window and manage remote physical device reservations
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                hub     Launches a desktop window for real-time screen mirroring and
                        interactive control of a connected Android device or
                        emulator
                remote  Manage remote physical devices. Includes commands to list,
                        reserve, connect to, and manage remote device reservations

    docs
              Usage: android docs [-h] [COMMAND]
              Searches and fetches developer documentation from the official Android
              Knowledge Base
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                fetch   Fetches an Android documentation article from a URL starting
                        with `kb://`
                search  Searches Android documentation. Enclose keywords in quotes

    emulator
              Usage: android emulator [-h] [COMMAND]
              Manages Android Virtual Devices (AVDs). Includes commands to start,
              stop, list, and view details about emulators
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                create  Creates a virtual device
                list    Lists available virtual devices
                remove  Deletes a virtual device
                start   Launches the specified virtual device. This command returns
                        when the emulator is fully started and ready to use
                stop    Stops the specified virtual device

    help
              Usage: android help [-h] [COMMAND]
              Shows the help information for a specified command
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              
              Positional Parameters:
                COMMAND  The command to show help for

    info
              Usage: android info [-h] [<field>]
              Prints environment information including SDK location and
              configuration variables
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              
              Positional Parameters:
                <field>  The specific field to print the value of (sdk, version,
                         launcher_version). If omitted, prints all fields

    init
              Usage: android init [-h]
              Initializes the environment for Android CLI. Sets up required
              configurations, directories, and default skills
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit

    input
              Usage: android input [-h] [--device=PARAM] [COMMAND]
              Interact with Android apps by performing gestures and key events on UI
              elements
              
              Options:
                    --device=PARAM  Device serial number or emulator ID (as reported
                                    by 'adb devices')
                -h, --help          Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM     Path to the Android SDK
                -v, --verbose       Enable verbose output for troubleshooting
                -V, --version       Print version information and exit
              Commands:
                key     Press a hardware button, navigation key, or Android keycode
                scroll  Scroll a container element, optionally until a target
                        element appears
                swipe   Swipe from a UI element matching a selector in a given
                        direction
                tap     Tap on a UI element matching a selector
                text    Type text into a UI element matching a selector

    install
              Usage: android install [-h] [--apks=PARAM] [--device=PARAM] [--install-options=PARAM]
                                     [--use-delta-install] [<apks_or_reference>] [--
                                     <build_args>]
              Installs an Android app (one or more APKs) on a connected device or
              emulator without activating any components, using incremental
              optimizations for faster deployment than `adb`
              
              Options:
                    --apks=PARAM             The paths to the APKs, comma separated
                    --device=PARAM           The device serial number
                -h, --help                   Shows the help message for the
                                             specified command
                    --install-options=PARAM  Additional options or flags to pass to
                                             package manager install (for example,
                                             `-g`, `-d`)
                    --use-delta-install      Use fast delta install (speeds up
                                             incremental updates by transferring
                                             only modified code and resources;
                                             default: `true`)
              
              android options:
                    --sdk=PARAM              Path to the Android SDK
                -v, --verbose                Enable verbose output for
                                             troubleshooting
                -V, --version                Print version information and exit
              
              Positional Parameters:
                <apks_or_reference>  APK file path(s) or a build reference
                                     ([system://][path]?[target])
                -- <build_args>      Arguments passed verbatim to the build system.
                                     Use -- to separate from other arguments

    layout
              Usage: android layout [-dhp] [--device=PARAM] [--flat] [--full] [--no-idle]
                                    [--output=PARAM]
              Returns the layout tree of an app
              
              Options:
                    --device=PARAM  The device serial number
                -d, --diff          Deprecated; no-op flag. Will be removed in a
                                    future release
                    --flat          Returns a flat list instead of a tree
                    --full          Returns the full tree, including non-interactive
                                    and hidden elements
                -h, --help          Shows the help message for the specified command
                    --no-idle       Don't wait for layout idle state when fetching
                                    layout
                -o, --output=PARAM  Writes the layout to the specified file or
                                    directory. If omitted, prints to standard output
                -p, --pretty        Pretty-prints the returned JSON
              
              android options:
                    --sdk=PARAM     Path to the Android SDK
                -v, --verbose       Enable verbose output for troubleshooting
                -V, --version       Print version information and exit

    preview
              Usage: android preview [-h] [COMMAND]
              Renders Jetpack Compose @Preview functions to PNG images and
              optionally exports component tree JSON files. Runs without a device or
              an IDE
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                list    Lists available Jetpack Compose @Preview functions in a
                        target
                render  Builds a target and renders its Jetpack Compose @Preview
                        functions to PNG images and optional component tree JSON
                        files

    profiler
              Usage: android profiler [-h] [COMMAND]
              Profiles Android apps, games, and devices
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                heapdump     Capture Android JVM heap dump snapshots (requires API
                             29+)
                session      Manage profiling sessions of any type: list them, query
                             their status, or terminate them
                systemtrace  System tracing tools. Captures CPU scheduling, thread
                             slices, frame lifecycle, GPU counters, and Vulkan
                             timing into a Perfetto trace file

    run
              Usage: android run [-h] [--activity=PARAM] [--apks=PARAM] [--debug] [--device=PARAM]
                                 [--install-options=PARAM] [--type=PARAM] [--use-delta-install]
                                 [<apks_or_reference>] [-- <build_args>]
              Deploys and launches an Android app on a connected device or emulator
              
              Options:
                    --activity=PARAM         The activity name
                    --apks=PARAM             The paths to the APKs, comma separated
                    --debug                  Run in debug mode
                    --device=PARAM           The device serial number
                -h, --help                   Shows the help message for the
                                             specified command
                    --install-options=PARAM  Additional options or flags to pass to
                                             package manager install (for example,
                                             `-g`, `-d`)
                    --type=PARAM             The component type (`ACTIVITY`,
                                             `WATCH_FACE`, `TILE`, `COMPLICATION`,
                                             `DECLARATIVE_WATCH_FACE`,
                                             `WEAR_WIDGET`)
                    --use-delta-install      Use fast delta install (speeds up
                                             incremental updates by transferring
                                             only modified code and resources;
                                             default: `true`)
              
              android options:
                    --sdk=PARAM              Path to the Android SDK
                -v, --verbose                Enable verbose output for
                                             troubleshooting
                -V, --version                Print version information and exit
              
              Positional Parameters:
                <apks_or_reference>  APK file path(s) or a build reference
                                     ([system://][path]?[target])
                -- <build_args>      Arguments passed verbatim to the build system.
                                     Use -- to separate from other arguments

    screen
              Usage: android screen [-h] [COMMAND]
              Captures and inspects the screen of a connected Android device or
              emulator
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                capture  Outputs the device screen to a PNG
                resolve  Targets UI elements visually. Substitutes bounding box
                         coordinates from an annotated screenshot into a string,
                         replacing all instances of `#N` with the center coordinates
                         of the bounding box labeled `N`

    sdk
              Usage: android sdk [-h] [--ignore-outdated-xmls] [--platform=PARAM]
                                 [COMMAND]
              Manages the Android SDK installation. Includes commands to install,
              update, remove, and list available and installed SDK packages
              
              Options:
                -h, --help                  Shows the help message for the specified
                                            command
                    --ignore-outdated-xmls  When installing or updating packages, do
                                            not update other packages' XML files
                    --platform=PARAM        Target platform `<os>_<arch>` (for
                                            example, `linux_x86_64`, `mac_arm64`, or
                                            `windows_x86`); defaults to the current
                                            host
              
              android options:
                    --sdk=PARAM             Path to the Android SDK
                -v, --verbose               Enable verbose output for
                                            troubleshooting
                -V, --version               Print version information and exit
              Commands:
                install  Installs SDK packages
                list     Lists installed and available SDK packages
                remove   Removes packages from the SDK
                update   Updates one or all packages to the latest version

    signals
              Usage: android signals [-h] [COMMAND]
              Queries app stability and field telemetry from Crashlytics
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                context  Lists accessible Crashlytics projects and apps
                crashes  Lists, describes, and analyzes field-reported crash, ANR,
                         and non-fatal issues
                heaps    Lists, describes, and downloads heap dumps collected on
                         low-memory events

    skills
              Usage: android skills [-h] [COMMAND]
              Manages Android CLI skills. Includes commands to install, remove,
              list, and search for skills by keyword
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                add     Installs a specific skill by its ID to your environment
                find    Searches for available skills in the repository matching a
                        keyword
                list    Lists installed and available skills
                remove  Removes an installed skill by its ID
                update  Updates installed skills

    studio
              Usage: android studio [-h] [COMMAND]
              Connects Android CLI to a running Android Studio instance to analyze
              files, find declarations and usages, render Compose previews, and look
              up library versions
              
              Options:
                -h, --help       Shows the help message for the specified command
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
              Commands:
                analyze-file            Analyzes a file in Android Studio
                check                   Checks the status of running Android Studio
                                        instances
                find-declaration        Finds the declaration of a symbol
                find-usages             Finds usages of a symbol
                open-file               Opens a file in Android Studio
                render-compose-preview  Renders a Compose preview in Android Studio
                version-lookup          Looks up the latest available versions of
                                        Maven artifacts, Android versions, and SDK
                                        tools

    update
              Usage: android update [-h] [--url=PARAM]
              Updates Android CLI to the latest version
              
              Options:
                -h, --help       Shows the help message for the specified command
                    --url=PARAM  The URL to download the update from
              
              android options:
                    --sdk=PARAM  Path to the Android SDK
                -v, --verbose    Enable verbose output for troubleshooting
                -V, --version    Print version information and exit
