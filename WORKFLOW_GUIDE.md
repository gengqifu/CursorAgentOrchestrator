# 完整工作流使用指南

> 本文档介绍如何使用 `execute_full_workflow` 工具执行完整的开发工作流，从需求输入到代码完成和覆盖率分析。

## 目录

- [概述](#概述)
- [工作流步骤](#工作流步骤)
- [使用模式](#使用模式)
- [使用示例](#使用示例)
- [工作流状态管理](#工作流状态管理)
- [常见问题](#常见问题)

## 概述

`execute_full_workflow` 是一个端到端的工作流编排工具，可以自动执行从需求输入到代码完成和覆盖率分析的完整流程。它整合了以下8个步骤：

1. **提交答案并创建工作区** - 基于初始问题创建开发工作区
2. **PRD 生成和确认** - 生成产品需求文档并确认
3. **TRD 生成和确认** - 生成技术设计文档并确认
4. **任务分解** - 将 TRD 分解为独立的开发任务
5. **任务执行循环** - 执行所有任务（代码生成 → Review → 重试循环）
6. **询问测试路径** - 获取测试输出目录路径
7. **生成测试** - 生成测试文件
8. **生成覆盖率报告** - 分析代码覆盖率并生成报告

## 工作流步骤

### 步骤1：提交答案并创建工作区

- **工具**: `submit_orchestrator_answers`
- **输入**: `project_path`, `requirement_name`, `requirement_url`
- **输出**: `workspace_id`

### 步骤2：PRD 生成和确认

- **工具**: `generate_prd` → `confirm_prd`（自动确认模式）或 `check_prd_confirmation`（交互模式）
- **输入**: `workspace_id`, `requirement_url`
- **输出**: `prd_path`
- **交互模式**: 支持 PRD 修改循环（`modify_prd` → 重新生成 → `confirm_prd`）

### 步骤3：TRD 生成和确认

- **工具**: `generate_trd` → `confirm_trd`（自动确认模式）或 `check_trd_confirmation`（交互模式）
- **输入**: `workspace_id`
- **输出**: `trd_path`
- **交互模式**: 支持 TRD 修改循环（`modify_trd` → 重新生成 → `confirm_trd`）

### 步骤4：任务分解

- **工具**: `decompose_tasks`
- **输入**: `workspace_id`
- **输出**: `tasks_json_path`, `task_count`

### 步骤5：任务执行循环

- **工具**: `execute_all_tasks`
- **输入**: `workspace_id`, `max_review_retries`
- **输出**: `total_tasks`, `completed_tasks`, `failed_tasks`, `task_results`
- **功能**: 自动执行所有待处理任务，每个任务包括代码生成和 Review 循环

### 步骤6：询问测试路径

- **工具**: `ask_test_path` → `submit_test_path`
- **输入**: `workspace_id`
- **输出**: `test_path`（保存到工作区元数据）
- **交互模式**: 在交互模式下会询问用户测试路径

### 步骤7：生成测试

- **工具**: `generate_tests`
- **输入**: `workspace_id`, `test_output_dir`
- **输出**: `test_files`, `test_count`

### 步骤8：生成覆盖率报告

- **工具**: `analyze_coverage`
- **输入**: `workspace_id`, `project_path`
- **输出**: `coverage`, `coverage_report_path`

## 使用模式

### 自动确认模式 (`auto_confirm=True`)

**特点**:
- 自动确认 PRD 和 TRD
- 使用默认测试路径
- 无需用户交互，一次性完成所有步骤
- 适合自动化场景和 CI/CD 流程

**使用示例**:

```bash
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/req \
  auto_confirm=true
```

**返回结果**:

```json
{
  "success": true,
  "workspace_id": "req-xxx",
  "workflow_steps": [
    {"step_name": "提交答案并创建工作区", "status": "completed"},
    {"step_name": "PRD 生成和确认", "status": "completed"},
    {"step_name": "TRD 生成和确认", "status": "completed"},
    {"step_name": "任务分解", "status": "completed"},
    {"step_name": "任务执行循环", "status": "completed"},
    {"step_name": "询问测试路径", "status": "completed"},
    {"step_name": "生成测试", "status": "completed"},
    {"step_name": "生成覆盖率报告", "status": "completed"}
  ],
  "final_status": {
    "success": true,
    "coverage": 85.5
  }
}
```

### 交互模式 (`auto_confirm=False`)

**特点**:
- 在关键步骤暂停，等待用户确认或输入
- 支持 PRD/TRD 修改循环
- 支持工作流中断和恢复
- 适合需要人工审核的场景

**交互点**:

1. **初始问题**（如果未提供初始参数）:
   - `interaction_type`: `"questions"`
   - 需要提供 `interaction_response` 包含 `project_path`, `requirement_name`, `requirement_url`

2. **PRD 确认**:
   - `interaction_type`: `"prd_confirmation"`
   - 需要提供 `interaction_response` 包含 `action`（`"confirm"` 或 `"modify"`）

3. **TRD 确认**:
   - `interaction_type`: `"trd_confirmation"`
   - 需要提供 `interaction_response` 包含 `action`（`"confirm"` 或 `"modify"`）

4. **测试路径询问**:
   - `interaction_type`: `"question"`
   - 需要提供 `interaction_response` 包含 `answer`（测试路径）

**使用示例**:

```bash
# 第一次调用：开始工作流
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/req \
  auto_confirm=false

# 返回结果（PRD 确认请求）
{
  "success": true,
  "interaction_required": true,
  "interaction_type": "prd_confirmation",
  "prd_path": "/path/to/PRD.md",
  "prd_preview": "PRD 预览内容..."
}

# 第二次调用：确认 PRD
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'

# 返回结果（TRD 确认请求）
{
  "success": true,
  "interaction_required": true,
  "interaction_type": "trd_confirmation",
  "trd_path": "/path/to/TRD.md",
  "trd_preview": "TRD 预览内容..."
}

# 第三次调用：确认 TRD
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'

# 返回结果（测试路径询问）
{
  "success": true,
  "interaction_required": true,
  "interaction_type": "question",
  "question": {
    "text": "请输入测试输出目录路径",
    "default": "/path/to/project/tests/mock"
  }
}

# 第四次调用：提供测试路径
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"answer": "/path/to/tests"}'

# 返回结果（工作流完成）
{
  "success": true,
  "workspace_id": "req-xxx",
  "workflow_steps": [...],
  "final_status": {...}
}
```

## 使用示例

### 示例1：自动确认模式（完整流程）

```bash
# 一次性完成所有步骤
@agent-orchestrator execute_full_workflow \
  project_path=/Users/username/my-project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/requirement.md \
  auto_confirm=true \
  max_review_retries=3
```

### 示例2：交互模式（PRD 修改循环）

```bash
# 第一次调用：生成 PRD
@agent-orchestrator execute_full_workflow \
  project_path=/Users/username/my-project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/requirement.md \
  auto_confirm=false

# 返回 PRD 确认请求，用户选择修改
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "modify"}'

# 系统重新生成 PRD，再次返回确认请求
# 用户确认
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'

# 继续后续流程...
```

### 示例3：恢复中断的工作流

```bash
# 如果工作流中断，可以通过 workspace_id 恢复
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'
```

## 工作流状态管理

### 状态存储

工作流状态保存在 `workspace.json` 的 `workflow_state` 字段中：

```json
{
  "workflow_state": {
    "current_step": 3,
    "steps": {
      "1": {"name": "提交答案并创建工作区", "status": "completed"},
      "2": {"name": "PRD 生成和确认", "status": "completed"},
      "3": {"name": "TRD 生成和确认", "status": "in_progress"}
    },
    "last_updated": "2026-01-16T10:30:00"
  }
}
```

### 步骤跳过

如果工作流中断后恢复，已完成步骤会自动跳过：

- 检查 `workflow_state` 中的步骤状态
- 如果步骤状态为 `"completed"`，则跳过该步骤
- 从第一个未完成的步骤继续执行

### 工作流恢复

**恢复方式**:
1. 提供 `workspace_id`（必需）
2. 提供 `interaction_response`（如果当前步骤需要交互）
3. 保持 `auto_confirm` 模式与之前一致

**示例**:

```bash
# 恢复工作流（继续 TRD 确认）
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'
```

## 常见问题

### Q1: 工作流中断后如何恢复？

**A**: 使用 `workspace_id` 和 `interaction_response` 恢复：

```bash
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'
```

### Q2: 如何修改 PRD 或 TRD？

**A**: 在交互模式下，当收到 PRD/TRD 确认请求时，提供 `{"action": "modify"}`：

```bash
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "modify"}'
```

系统会重新生成 PRD/TRD，然后再次返回确认请求。

### Q3: 自动确认模式和交互模式有什么区别？

**A**:
- **自动确认模式**: 自动确认所有步骤，无需用户交互，适合自动化场景
- **交互模式**: 在关键步骤暂停，等待用户确认或输入，适合需要人工审核的场景

### Q4: 如何查看工作流状态？

**A**: 使用 `get_workflow_status` 工具：

```bash
@agent-orchestrator get_workflow_status workspace_id=req-xxx
```

### Q5: 工作流执行失败怎么办？

**A**: 工作流会在失败的步骤记录错误信息，可以通过 `workflow_steps` 查看：

```json
{
  "workflow_steps": [
    {
      "step_name": "任务执行循环",
      "status": "failed",
      "result": {
        "error": "任务执行失败：..."
      }
    }
  ]
}
```

修复问题后，可以通过 `workspace_id` 恢复工作流，失败的步骤会重新执行。

### Q6: 如何自定义测试路径？

**A**: 在交互模式下，当收到测试路径询问时，提供自定义路径：

```bash
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"answer": "/custom/test/path"}'
```

### Q7: 工作流支持多Agent并行吗？

**A**: 支持。多个 Agent 可以：
- 查询工作流状态（`get_workflow_status`）
- 检查阶段是否可以开始（`check_stage_ready`）
- 并行处理不同的任务（通过 `execute_task`）

但 `execute_full_workflow` 本身是单 Agent 执行的完整流程。

### Q8: 如何设置 Review 重试次数？

**A**: 使用 `max_review_retries` 参数：

```bash
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/req \
  auto_confirm=true \
  max_review_retries=5
```

默认值为 3。

## 相关文档

- [TOOLS.md](mcp-server/TOOLS.md) - 所有工具的详细说明
- [CURSOR_INTEGRATION.md](mcp-server/CURSOR_INTEGRATION.md) - Cursor 集成指南
- [ARCHITECTURE.md](mcp-server/ARCHITECTURE.md) - 系统架构说明
