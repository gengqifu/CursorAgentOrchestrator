---
name: code-generator
description: >
  代码生成技能。使用当你已有任务列表（tasks.json）和工作区信息，需要针对某个任务
  生成功能代码文件和对应测试文件，并更新任务状态与关联文件路径。
---

# Code Generator Skill

本 Skill 指导 Agent 基于 `mcp-server/src/tools/code_generator.py`，
为指定工作区和任务 ID 生成功能代码与基础测试文件，并更新任务状态。

---

## 一、适用场景

- 已经通过 Task Decomposer 生成 `tasks.json`
- 希望针对某个 `task_id`：
  - 生成一份实现该任务的代码文件
  - 生成一份基础测试文件（如 `tests/test_xxx.py`）
  - 更新任务状态为 `"completed"`，并记录 `code_files`

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

- **MCP 工具名称**：`generate_code`
- **核心实现**：`mcp-server/src/tools/code_generator.py`
- **MCP Server 实现**：`mcp-server/src/mcp_server.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/code_generator.py`：保留用于向后兼容（已弃用，应通过 MCP Server 调用）

### 2. 前置条件

- 工作区目录存在，且包含：
  - `.agent-orchestrator/requirements/{workspace_id}/workspace.json`
  - `.agent-orchestrator/requirements/{workspace_id}/tasks.json`
- `tasks.json` 中包含目标 `task_id` 的任务项。

---

## 三、输入输出

- 输入：
  - `workspace_id: str`
  - `task_id: str`
- 输出（Python dict）：

```python
{
    "success": True,
    "task_id": "task-001",
    "code_files": ["<project_path>/task_001.py", "<project_path>/tests/test_task_001.py"],
    "workspace_id": workspace_id,
}
```

同时会：

- 在项目代码目录生成实现文件和测试文件
- 更新 `tasks.json` 中对应任务：
  - `status = "completed"`
  - `code_files` 列表包含生成的文件路径

---

## 四、标准调用流程

### 步骤 1：通过 MCP Server 调用工具

**架构说明（符合 PDF 文档）**：

根据 PDF 文档架构，本 Skill 通过 **MCP Server** 暴露，作为中央编排服务的一部分：

```
Cursor CLI → MCP Server (中央编排服务) → generate_code 工具 → 项目代码仓库
```

**Agent 应该通过 MCP Server 调用 `generate_code` 工具**：

**MCP 工具调用**：
```json
{
  "tool": "generate_code",
  "arguments": {
    "workspace_id": "req-20240101-120000-user-auth",
    "task_id": "task-001"
  }
}
```

**在 Cursor IDE 中使用**：
```
@agent-orchestrator generate_code workspace_id="req-20240101-120000-user-auth" task_id="task-001"
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "task_id": "task-001",
    "code_files": ["/path/to/task_001.py", "/path/to/tests/test_task_001.py"],
    "workspace_id": "req-20240101-120000-user-auth"
}
```

失败时：
```json
{
    "success": false,
    "error": "错误信息",
    "error_type": "TaskNotFoundError"
}
```

> **注意**：
> - 本工具通过 MCP Server 暴露，符合 PDF 文档架构
> - 返回 JSON 格式，便于 Agent 解析
> - 核心实现在 `mcp-server/src/tools/code_generator.py`

---

## 五、与其他 Skill 的关系

典型链路：

```text
TRD.md → [task-decomposer] → tasks.json
tasks.json + workspace → [code-generator] → 代码 + 测试
                                      ↓
                               [code-reviewer] / [test-generator]
```

