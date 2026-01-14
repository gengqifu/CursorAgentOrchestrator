---
name: task-decomposer
description: >
  任务分解技能。使用当你已经有标准化 TRD 文档和工作区信息，需要将 TRD 中的实现方案
  拆分为结构化的任务列表（tasks.json），为后续代码生成与审查提供任务粒度。
---

# Task Decomposer Skill

本 Skill 指导 Agent 基于现有实现 `mcp-server/src/tools/task_decomposer.py`，
将某个工作区下的 TRD 文档拆分为结构化的任务列表 `tasks.json`。

---

## 一、适用场景

在以下场景使用本 Skill：

- 已经完成 TRD 生成（`TRD.md` 存在）
- 希望将 TRD 中的功能/模块拆分为一组可执行的任务
- 需要为后续 `code-generator`、`code-reviewer` 等 Skill 准备任务级输入

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

- **MCP 工具名称**：`decompose_tasks`
- **核心实现**：`mcp-server/src/tools/task_decomposer.py`
- **MCP Server 实现**：`mcp-server/src/mcp_server.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/task_decomposer.py`：保留用于向后兼容（已弃用，应通过 MCP Server 调用）

### 2. 前置条件

- 工作区目录存在，且包含：
  - `.agent-orchestrator/requirements/{workspace_id}/workspace.json`
  - `.agent-orchestrator/requirements/{workspace_id}/TRD.md`
- Python 环境 3.9+，依赖已安装。

---

## 三、输入输出

- 输入：
  - `workspace_id: str`
  - `trd_path: str` （通常为工作区目录下的 `TRD.md`）
- 输出（Python dict）：

```python
{
    "success": True,
    "tasks_json_path": "<绝对路径>/tasks.json",
    "task_count": <int>,
    "workspace_id": workspace_id,
}
```

并在工作区目录生成/更新 `tasks.json`，内容大致为：

```json
{
  "workspace_id": "req-xxx",
  "tasks": [
    {
      "task_id": "task-001",
      "description": "实现 XXX 功能",
      "status": "pending"
    }
  ]
}
```

---

## 四、标准调用流程

### 步骤 1：通过 MCP Server 调用工具

**架构说明（符合 PDF 文档）**：

根据 PDF 文档架构，本 Skill 通过 **MCP Server** 暴露，作为中央编排服务的一部分：

```
Cursor CLI → MCP Server (中央编排服务) → decompose_tasks 工具 → 项目代码仓库
```

**Agent 应该通过 MCP Server 调用 `decompose_tasks` 工具**：

**MCP 工具调用**：
```json
{
  "tool": "decompose_tasks",
  "arguments": {
    "workspace_id": "req-20240101-120000-user-auth",
    "trd_path": "/path/to/TRD.md"  // 可选，默认从工作区获取
  }
}
```

**在 Cursor IDE 中使用**：
```
# 使用工作区的默认 TRD.md
@agent-orchestrator decompose_tasks workspace_id="req-20240101-120000-user-auth"

# 指定 TRD 路径
@agent-orchestrator decompose_tasks workspace_id="req-20240101-120000-user-auth" trd_path="/path/to/TRD.md"
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "tasks_json_path": "/path/to/.agent-orchestrator/requirements/req-xxx/tasks.json",
    "task_count": 5,
    "workspace_id": "req-20240101-120000-user-auth"
}
```

失败时：
```json
{
    "success": false,
    "error": "错误信息",
    "error_type": "ValidationError"
}
```

> **注意**：
> - 本工具通过 MCP Server 暴露，符合 PDF 文档架构
> - 如果不提供 `trd_path`，工具会自动使用工作区的 `TRD.md`
> - 返回 JSON 格式，便于 Agent 解析
> - 核心实现在 `mcp-server/src/tools/task_decomposer.py`

---

## 五、与其他 Skill 的关系

典型流程：

```text
PRD.md  →  [trd-generator]  →  TRD.md  →  [task-decomposer]  →  tasks.json
                                         ↓
                                 [code-generator 等后续 Skill]
```

