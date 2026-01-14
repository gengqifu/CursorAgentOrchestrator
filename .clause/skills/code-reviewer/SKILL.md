---
name: code-reviewer
description: >
  代码审查技能。使用当你已经为某个任务生成了代码文件，需要对代码质量进行自动审查，
  生成审查报告，并更新任务的审查状态与结果。
---

# Code Reviewer Skill

本 Skill 指导 Agent 基于 `mcp-server/src/tools/code_reviewer.py`，
对某个任务关联的代码文件进行基础自动审查，并生成审查报告。

---

## 一、适用场景

- `tasks.json` 中某个任务已经生成了 `code_files`
- 希望快速得到一份自动化的审查结果，用于：
  - 粗筛代码质量
  - 发现明显问题（如 TODO、内容过短、文件不存在等）

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

- **MCP 工具名称**：`review_code`
- **核心实现**：`mcp-server/src/tools/code_reviewer.py`
- **MCP Server 实现**：`mcp-server/src/mcp_server.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/code_reviewer.py`：保留用于向后兼容（已弃用，应通过 MCP Server 调用）

### 2. 前置条件

- 工作区目录存在，且包含：
  - `.agent-orchestrator/requirements/{workspace_id}/workspace.json`
  - `.agent-orchestrator/requirements/{workspace_id}/tasks.json`
- `tasks.json` 中目标 `task_id` 的任务项包含 `code_files` 字段。

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
    "passed": bool,
    "review_report": "<markdown/text 报告>",
    "workspace_id": workspace_id,
}
```

`review_report` 中会包含：

- 每个文件的检查结果：
  - 文件不存在
  - 文件过短
  - 包含 TODO
  - 基础检查通过

---

## 四、标准调用流程

### 步骤 1：通过 MCP Server 调用工具

**架构说明（符合 PDF 文档）**：

根据 PDF 文档架构，本 Skill 通过 **MCP Server** 暴露，作为中央编排服务的一部分：

```
Cursor CLI → MCP Server (中央编排服务) → review_code 工具 → 项目代码仓库
```

**Agent 应该通过 MCP Server 调用 `review_code` 工具**：

**MCP 工具调用**：
```json
{
  "tool": "review_code",
  "arguments": {
    "workspace_id": "req-20240101-120000-user-auth",
    "task_id": "task-001"
  }
}
```

**在 Cursor IDE 中使用**：
```
@agent-orchestrator review_code workspace_id="req-20240101-120000-user-auth" task_id="task-001"
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "task_id": "task-001",
    "passed": true,
    "review_report": "审查报告内容...",
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
> - 核心实现在 `mcp-server/src/tools/code_reviewer.py`

---

## 五、与其他 Skill 的关系

典型链路：

```text
tasks.json → [code-generator] → 代码文件
代码文件 → [code-reviewer] → 审查报告
```

后续可以结合：

- `test-generator` / `test-reviewer`：从测试角度进一步审查质量
- 人工审查：基于自动报告进行人工补充评审

