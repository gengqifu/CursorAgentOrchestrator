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

## 二、前置条件

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

## 四、调用示例

```python
from src.tools.code_generator import generate_code

result = generate_code("workspace-001", "task-001")
assert result["success"] is True
print(result["code_files"])
```

---

## 五、与其他 Skill 的关系

典型链路：

```text
TRD.md → [task-decomposer] → tasks.json
tasks.json + workspace → [code-generator] → 代码 + 测试
                                      ↓
                               [code-reviewer] / [test-generator]
```

