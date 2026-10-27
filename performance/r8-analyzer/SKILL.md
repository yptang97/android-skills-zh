---
name: r8-analyzer
description: 分析 Android 构建文件和 R8 keep 规则，识别冗余内容、覆盖整个包的宽泛规则，以及把库的 consumer keep 规则包含在内的规则。当开发者想优化 Android 应用的体积、移除冗余或过于宽泛的 keep 规则，或排查 ProGuard 配置问题时，使用这个 skill。不适用于一般 Gradle 构建错误、Compose UI 性能或运行时 CPU 性能分析。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-10-24'
  keywords:
  - R8
  - proguard
  - keep rules
  - app size
  - optimization
  - shrinking
  - minification
  - obfuscation
---

## 步骤 1. 配置项检查

- 检查 `build.gradle`、`build.gradle.kts` 和 `gradle.properties`。
- 使用 [references/CONFIGURATION.md](references/CONFIGURATION.md) 找出缺失的优化项。
- **AGP**：如果版本低于 9.3，建议迁移到 9.3，以获得简化的 [`optimization {}` DSL](references/android/topic/performance/app-optimization/enable-app-optimization.md) 和 Configuration Analyzer 任务。
- **Full mode**：确认 `android.enableR8.fullMode=false` 已从 `gradle.properties` 文件中移除。

## 步骤 2. 分析路径选择

- 检查 `build.gradle`、`build.gradle.kts`、`settings.gradle`、`settings.gradle.kts`、`gradle.properties` 和 `libs.versions.toml`，获取 AGP 与 R8 版本。在 `settings.gradle(.kts)` 中固定（pin）的 R8 版本会替换 AGP 自带的 R8。
- 找出 app 模块（通常是 `app`）以及启用了 R8 的构建变体（通常是 `release`）。下面的命令把它们记作 `<module>` 和 `<Variant>`，例如 `:app:minifyReleaseWithR8`。
- 辅助脚本位于这个 skill 的 `scripts/` 目录。下面的命令中，`<skill_dir>` 指这个 skill 的目录。所有命令都在项目根目录下运行。

- **如果 AGP \>= 9.3.0**：进入**路径 A（独立任务）**。

- **如果 AGP \< 9.3.0**：进入**路径 B（量化）**。

### 路径 A：独立 Gradle 任务（AGP \>= 9.3.0）

- **步骤 1：检查前置条件**：必须安装 Python 和 6.33.4 或更高版本的 `protobuf` 包（由 [`scripts/keep_radius_pb2.py`](scripts/keep_radius_pb2.py) 使用）。用 `pip install "protobuf>=6.33.4"` 安装；低于 6.33.4 的版本在导入时会以 `VersionError` 或 `ImportError` 失败。
- **步骤 2：在启用 R8 的构建上运行独立任务**：针对你在选择路径时找到的模块和变体，运行 `./gradlew :<module>:analyze<Variant>R8Config`（例如 `./gradlew :app:analyzeReleaseR8Config`）。它会在 `<module>/build/reports/r8/` 生成报告（例如 `app/build/reports/r8/r8-config-analyzer-release.pb`）。你必须等这条命令执行完成后才能继续。
- **步骤 3：转换为 JSON**：你必须显式运行转换脚本 [`scripts/convert_pb_to_json.py`](scripts/convert_pb_to_json.py)，即执行 `python3 <skill_dir>/scripts/convert_pb_to_json.py`，参数为 `<module>/build/reports/r8` 和 `tmp/keepradius/keepruleradius.json`。等待这条命令执行完成。
- **步骤 4：分析**：你必须显式运行分析脚本 [`scripts/analyze.py`](scripts/analyze.py)，即执行 `python3 <skill_dir>/scripts/analyze.py tmp/keepradius/keepruleradius.json`。它会输出 `tmp/keepradius/analysis_result.txt`。等待这条命令执行完成。

### 路径 B：调用 R8 release 构建（AGP \< 9.3.0）

- **步骤 1：检查前置条件**：必须安装 Python 和 6.33.4 或更高版本的 `protobuf` 包：`pip install "protobuf>=6.33.4"`。
- **步骤 2：生成并分析**：你必须运行 [references/FULL_BUILD_CONFIG_ANALYZER.md](references/FULL_BUILD_CONFIG_ANALYZER.md) 中描述的 shell 命令，把 `settings.gradle(.kts)` 中的 R8 版本临时更新为 9.4.34 或更高版本（以便 R8 生成报告），在 `tmp/r8analysis/` 生成 proto 报告，把它转换为 `tmp/r8analysis/keepruleradius.json`，分析结果，然后还原对 `settings.gradle(.kts)` 的临时改动。
- **步骤 3：分析**：确认分析过程输出了 `tmp/r8analysis/analysis_result.txt`，其中包含评分和规则影响指标。

## 步骤 3. 生成报告

- **格式**：严格遵循 [references/REPORT_FORMAT.md](references/REPORT_FORMAT.md)。
- **冗余规则**：把 keep 规则与 [references/INSPECT-RULES.md](references/INSPECT-RULES.md) 对照检查。如果某条 keep 规则命中了 [references/INSPECT-RULES.md](references/INSPECT-RULES.md) 中的模式，就把该参考文档里的指引和修复建议连同影响指标一起写入。
- **输入**：如果使用路径 A，直接从生成的文件 `tmp/keepradius/analysis_result.txt` 中提取指标（评分、影响、示例类、规则来源）；如果使用路径 B，则从 `tmp/r8analysis/analysis_result.txt` 提取。
- **输出**：Gradle 运行期间给出简短的进度更新是可以的；最终消息只有报告。只在对话中输出原始 Markdown 报告。不要输出对话性填充内容（例如「这是你的报告……」）。不要提供 [references/REPORT_FORMAT.md](references/REPORT_FORMAT.md) 所定义章节之外的任何建议、后续步骤或其他文字。不要提及分析配置时所用的路径。

## 约束

- **严格限制输出**：最终输出必须严格是 Markdown 报告，不得包含其他内容。
- **不改代码**：只做调研和建议；不要修改项目文件。只在 `tmp/` 下创建文件（分析输出、settings 备份以及任何临时脚本），永远不要写报告文件。唯一的例外是路径 B 在项目尚未固定（pin）R8 9.4.34 或更高版本时所需的 `settings.gradle(.kts)` 中的临时 R8 `classpath`：交互运行时先征得用户同意，并在分析完成后还原（见 [references/FULL_BUILD_CONFIG_ANALYZER.md](references/FULL_BUILD_CONFIG_ANALYZER.md)）。如果确实需要这处改动，但用户不同意，或要求你不要修改构建文件，就不带评分地报告规则层面和构建文件层面的发现，并说明原因。
- **不要占位评分**：绝不要把 `N/A%` 当作评分输出。
- **不要冗余**：不要解释 R8 的收益，也不要在报告中引用 skill 内部文件。
- **聚焦**：如果没有发现问题或条目，就省略相关章节（例如 Subsumed Rules、Configuration）。
