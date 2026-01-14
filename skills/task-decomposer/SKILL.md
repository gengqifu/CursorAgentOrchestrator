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

- **Skill 入口脚本**：`skills/task-decomposer/scripts/task_decomposer.py`
- **核心实现**：`mcp-server/src/tools/task_decomposer.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/task_decomposer.py`：入口脚本，由 Agent 调用

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

### 步骤 1：调用 Skill 脚本

**Agent 应该执行以下命令**：

```bash
python3 skills/task-decomposer/scripts/task_decomposer.py \
    <workspace_id> \
    [trd_path]
```

**示例**：

```bash
# 使用工作区的默认 TRD.md
python3 skills/task-decomposer/scripts/task_decomposer.py req-20240101-120000-user-auth

# 指定 TRD 路径
python3 skills/task-decomposer/scripts/task_decomposer.py req-20240101-120000-user-auth /path/to/TRD.md
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
> - 如果不提供 `trd_path`，脚本会自动使用工作区的 `TRD.md`
> - 脚本会自动处理导入路径，无需手动设置 PYTHONPATH
> - 脚本输出 JSON 格式，便于 Agent 解析

---

## 五、与其他 Skill 的关系

典型流程：

```text
PRD.md  →  [trd-generator]  →  TRD.md  →  [task-decomposer]  →  tasks.json
                                         ↓
                                 [code-generator 等后续 Skill]
```

