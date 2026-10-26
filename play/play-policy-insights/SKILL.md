---
name: play-policy-insights
description: 自动审计器，用于按 Google Play 政策各领域核验 Android 应用。它把静态代码分析结果与 Play 商店声明交叉比对，生成确定性的合规报告，识别未声明的数据收集、架构风险，以及「权限与 API 卫生」「用户账户与身份」「数据安全与隐私」等领域中缺失的披露。
license: Complete terms in LICENSE.txt
metadata:
  author: Google LLC
  last-updated: '2026-07-13'
  keywords:
  - account deletion
  - accessibility api
  - all files access
  - audio recording
  - audit
  - compliance
  - contacts access
  - data disclosure
  - data safety
  - data safety label
  - data transmission
  - demo credentials
  - exact alarm
  - foreground services
  - location access
  - login credentials
  - manifest hygiene
  - package visibility
  - permissions hygiene
  - photo and video access
  - photopicker
  - play policy
  - pre-submission audit
  - privacy policy
  - prominent disclosure
  - restricted permissions
  - scoped storage
  - sms and call log
  - static analysis
  - target sdk
  - user consent
---

# Play Policy Insights：数据安全、登录凭据与受限权限

你必须针对三个具体的政策领域审计 Android 应用。你必须检查数据安全、演示登录凭据和受限权限。

## 路径解析

*   **repo_root**：包含这个 `SKILL.md` 的目录的绝对路径。
*   **app_dir**:: 包含应用代码的目录的绝对路径。
*   **temp_dir**：工作区根目录下的临时目录的绝对路径。
    其位置为 `.scratch/play_policy_insights_<uuid>`。**目录约束
    要求**：你必须把所有文件系统写入、中间产物和日志严格限制在该目录内。
    这样可以避免依赖系统级临时路径或用户主目录，从而确保该 skill 在不同
    执行环境（包括本地 harness 与 CI/CD 流水线）中保持可移植且安全。

## 关键要求

-   **执行模式感知**：在开始阶段 2 之前，先判断你的执行环境是否提供把任务
    派生或委派给通用子代理的工具（例如常被命名为 `invoke_agent`、
    `delegate_task` 或 `spawn_worker` 的工具，使用 'generalist' 或
    'coding_agent' 这类通用 agent 配置）。

-   如果**有**，你必须使用**模式 A（委派）**。

-   如果**没有**，使用**模式 B（顺序自执行）**。你必须阅读为子代理准备的
    提示词文件，按其中的指令执行，并把预期的输出文件写入磁盘。

-   **子代理编排：**

    -   如果使用「模式 A（委派）」，请等待子代理返回「SUCCESS」确认，以判断
        它们已完成。

    -   **幂等与超时保障**：如果子代理失败或超时，你必须在重试之前核验其
        目标输出文件（例如 `<temp_dir>/worker_<goal_name>.json`）是否存在且
        完整。如果文件存在且包含合法 JSON，就把这次执行视为 **SUCCESS**
        并继续。否则最多重试三次。

-   **快速失败要求：** 阶段 1 的自动审计是唯一可信来源。如果
    `orchestrator.py` 失败，你必须立即停止并说明失败原因。不要把人工审计
    当作兜底方案。

## 两阶段流程

### 阶段 1：事实收集与分类

1.  **初始化与分类**：
    -   运行 `python3 <repo_root>/scripts/orchestrator.py init <app_dir>`。
    -   该命令会创建临时环境、执行静态分析、梳理代码库、确定审计目标，并为
        每个审计目标生成给子代理的提示词，以及给指定的评审者和汇总者
        子代理的提示词。
    -   你必须等待（最多 5 分钟）该脚本执行结束。
2.  **记录环境信息**：记下 JSON 输出中的 `temp_dir` 与
    `activated_goals` 取值。阶段 2 会用到它们。
3.  **评估目标**：如果 `activated_goals` 为空，跳到阶段 2 的步骤 3
    （汇总）。否则继续到阶段 2 的步骤 1（详细分析）。

### 阶段 2：面向目标的审计

先确定你的执行能力，然后选择模式 A 或模式 B 之一继续。

#### 模式 A：具备委派能力的编排模式（并行）

1.  **详细分析**：对 `activated_goals` 中的每个目标（例如
    `permissions_and_apis`、`data_safety_part_1`、`data_safety_part_2`），
    委派给一个子代理。**并发上限：** 你不得同时派生超过
    3 个子代理。先派生第一批（最多 3 个），等它们完成后，再派生下一批。重复
    该过程直到所有目标完成。传入以下提示词：`"Read your instructions from
    <temp_dir>/prompt_worker_<goal_name>.md and execute. MANDATORY: You must
    use your file-writing capabilities to save your final JSON findings directly
    to the file system at <temp_dir>/worker_<goal_name>.json. You are strictly
    forbidden from outputting the JSON in your chat response. To minimize
    context usage, your final response must be exactly 'SUCCESS' and nothing
    else."` **校验**：确认每个
    `<temp_dir>/worker_<goal_name>.json` 都存在且包含合法 JSON。如果
    子代理失败或超时，但合法的 JSON 输出文件已在磁盘上，则不要重试，按正常
    流程继续。只有当文件缺失或无效时，才重试对应的工作单元（最多三次）。
2.  **汇总发现**：执行 Python 汇总命令：
   `python3 <repo_root>/scripts/orchestrator.py aggregate <temp_dir>`。该命令
   会生成 `aggregated_findings.json`，并返回一个包含 `critic_chunks` 的
   JSON 对象，表示需要核验的块数量（例如
   `{"temp_dir": "...", "critic_chunks": 2}`）。
3.  **并行评审**：对从 1 到 `critic_chunks` 的每个块索引 `i`，委派给一个
   子代理。**并发上限：** 你不得同时派生超过 3 个评审子代理。像上面那样按
   每 3 个一组分批。传入以下提示词：
   `"Read your instructions from <temp_dir>/prompt_critic_<i>.md and execute. MANDATORY: You must use your file-writing capabilities to save your final JSON findings directly to the file system at <temp_dir>/critic_output_<i>.json. You are strictly forbidden from outputting the JSON in your chat response. To minimize context usage, your final response must be exactly 'SUCCESS' and nothing else."`
   **校验**：在继续之前，确认每个 `<temp_dir>/critic_output_<i>.json` 都存在
   且包含合法 JSON。如果它失败或超时，但合法的 JSON 文件就在，则按正常
   流程继续。否则重试该特定评审块。
4.  **进入收尾阶段**（见下方步骤 4）

#### 模式 B：不具备委派能力的编排模式（顺序执行）

1.  **详细分析**：对 `activated_goals` 中的每个目标，依次执行：
    -   读取 `<temp_dir>/prompt_worker_<goal_name>.md` 的内容。
    -   你自己执行该文件中的指令。
    -   **关键**：你必须严格按提示词要求格式化发现内容，并保存到
        `<temp_dir>/worker_<goal_name>.json`。**不要**在思考过程或对话中
        概括发现内容；直接进入下一项任务。
    -   **校验**：在进入下一个目标之前，确认
        `<temp_dir>/worker_<goal_name>.json` 存在。
2.  **汇总发现**：执行 Python 汇总命令：
   `python3 <repo_root>/scripts/orchestrator.py --aggregate <temp_dir>`。
   该命令会生成 `aggregated_findings.json`，并返回一个包含
   `critic_chunks` 的 JSON 对象，表示需要核验的块数量。
3.  **顺序评审**：对从 1 到 `critic_chunks` 的每个块索引 `i`，依次执行：
    -   读取 `<temp_dir>/prompt_critic_<i>.md` 的内容。
    -   你自己执行这些步骤，并把发现内容保存到
      `<temp_dir>/critic_output_<i>.json`。
    -   **校验**：在进入下一个块之前，确认
      `<temp_dir>/critic_output_<i>.json` 存在。
4.  **进入收尾阶段**（见下方步骤 4）

#### 收尾（两种模式通用）

4.  **呈现发现**：运行 `python3 <repo_root>/scripts/generate_report.py <temp_dir>`。
    该命令会生成 `<temp_dir>/compliance_report.md`。把这个输出文件呈现给用户。
5.  **停止**：审计已完成。等待后续指令。
