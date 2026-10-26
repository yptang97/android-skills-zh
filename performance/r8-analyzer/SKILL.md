---
name: r8-analyzer
description: 分析 Android 构建文件和 R8 keep 规则，识别冗余内容、覆盖整个包的宽泛规则，以及把库的 consumer keep 规则包含在内的规则。适用于开发者想优化应用体积、移除冗余或过于宽泛的 keep 规则，或排查 Proguard 配置的场景。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-09-22'
  keywords:
  - R8
  - proguard
  - keep rules
  - app size
  - optimization
---

## 步骤 1. 配置项检查

- 检查 `build.gradle`、`build.gradle.kts` 和 `gradle.properties`。
- 使用 [references/CONFIGURATION.md](references/CONFIGURATION.md) 找出缺失的优化项。
- **AGP**：如果版本低于 9.0，建议迁移到 9.0 以获得[构建期性能提升](references/android/topic/performance/app-optimization/enable-app-optimization.md)。
- **Full Mode**：确认 `android.enableR8.fullMode=false` 已从 gradle.properties 中移除。

## 步骤 2. 分析路径选择

- 检查 `build.gradle`、`build.gradle.kts`、`gradle.properties` 和
  `libs.versions.toml`，获取 AGP 与 R8 版本。

- **如果 AGP \>= 9.3.0**：进入**路径 A（独立任务）**。

- **如果 AGP \< 9.3.0 且 R8 \>= 9.3.7-dev**：进入**路径 B（量化）**。

- 如果上述条件都不满足，进入**路径 C（启发式）**。

### 路径 A：独立 Gradle 任务（AGP \>= 9.3.0）

- **步骤 1：运行独立任务**：运行 `./gradlew :app:analyzeReleaseR8Config` 来评估 R8 配置。你必须等待该命令执行完成后再继续。
- **步骤 2：转换为 JSON**：报告生成在 `app/build/reports/r8/r8-config-analyzer-release.pb`。你必须显式运行转换脚本，执行：`python3 .agents/skills/r8-analyzer/scripts/convert_pb_to_json.py`。等待该命令执行完成。
- **步骤 3：分析**：你必须显式运行分析脚本，执行：`python3 .agents/skills/r8-analyzer/scripts/analyze.py`。它会输出 `tmp/keepradius/analysis_result.txt`。等待该命令执行完成。

### 路径 B：生成量化数据（R8 \>= 9.3.7-dev 且 AGP \< 9.3.0）

- **步骤 1：检查前提**：Python 和 `protobuf` 包是必需的。
- **步骤 2：生成并分析**：你必须运行 [references/CONFIGURATION-ANALYZER.md](references/CONFIGURATION-ANALYZER.md) 中描述的 shell 命令，使用 R8 配置分析器生成 proto 文件，把它转换为 JSON 并分析结果。
- **步骤 3：分析**：你必须确保分析过程产出 `tmp/keepradius/analysis_result.txt`，其中包含评分和规则影响指标。

### 路径 C：启发式评估与建议（R8 \< 9.3.7-dev）

*（仅在无法生成量化数据时使用）*

- **步骤 1：人工评估**：检查 `proguard-rules.pro`。
- **步骤 2：库规则检查**：把规则与 [references/REDUNDANT-RULES.md](references/REDUNDANT-RULES.md) 对比。对随库捆绑的规则建议**移除**。
- **步骤 3：自定义规则检查**：使用 [references/KEEP-RULES-IMPACT-HIERARCHY.md](references/KEEP-RULES-IMPACT-HIERARCHY.md) 和 [references/REFLECTION-GUIDE.md](references/REFLECTION-GUIDE.md) 排定优先级并评估。对宽泛规则（例如覆盖整个包的规则）建议**精简**。
- **步骤 4：验证**：对任何建议的改动，建议使用 [UI Automator](references/android/training/testing/other-components/ui-automator.md) 编写 Macrobenchmark 测试。然后进入步骤 3。

## 步骤 3. 生成报告

- **格式**：严格遵循 [references/REPORT_FORMAT.md](references/REPORT_FORMAT.md)。
- **输入**：如果使用路径 A，直接从生成的分析文件 analysis.txt 中提取指标（评分、影响、示例类）；如果使用路径 B，则从人工排查结果中提取。
- **输出**：只在对话中输出原始 Markdown 报告。不要输出对话性填充内容（例如「这是你的报告……」）。不要提供 [references/REPORT_FORMAT.md](references/REPORT_FORMAT.md) 所定义章节之外的任何建议、后续步骤或其他文字。不要提及分析配置所用的路径。

## 约束

- **严格限制输出**：最终输出必须严格是 Markdown 报告，不得包含其他内容。
- **不改代码**：只做调研和建议；不要修改文件。
- **不要冗余**：不要解释 R8 的收益，也不要在报告中引用 skill 内部文件。
- **聚焦**：如果没有发现问题或条目，就省略相关章节（例如 Subsumed Rules、Configuration）。
