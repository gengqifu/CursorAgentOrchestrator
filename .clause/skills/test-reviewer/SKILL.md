---
name: test-reviewer
description: >
  测试审查技能。使用当你已有一批测试文件（单元测试或集成测试），需要对测试质量、
  覆盖内容、基本结构进行快速审查，并生成报告。
---

# Test Reviewer Skill

本 Skill 指导 Agent 基于 `mcp-server/src/tools/test_reviewer.py`，
对一组测试文件进行基础审查，输出测试质量报告。

---

## 一、适用场景

- 已经存在测试文件（可由 `test-generator` 或人工编写）
- 希望：
  - 快速评估测试是否存在明显问题
  - 确认是否有“空测试”、“未断言”等情况

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

- **MCP 工具名称**：`review_tests`
- **核心实现**：`mcp-server/src/tools/test_reviewer.py`
- **MCP Server 实现**：`mcp-server/src/mcp_server.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/test_reviewer.py`：保留用于向后兼容（已弃用，应通过 MCP Server 调用）

### 2. 前置条件

- 工作区目录存在
- 传入的 `test_files` 路径列表有效（可以为空列表）

---

## 三、输入输出

- 输入：
  - `workspace_id: str`
  - `test_files: list[str]` —— 测试文件路径列表
- 输出（Python dict）：

```python
{
    "success": True,
    "passed": bool,
    "review_report": "<text/markdown 报告>",
    "workspace_id": workspace_id,
}
```

当 `test_files` 为空时：

- 返回 `passed=False` 或对应提示
- `review_report` 应说明“未提供测试文件”或等价信息

---

## 四、标准调用流程

### 步骤 1：通过 MCP Server 调用工具

**架构说明（符合 PDF 文档）**：

根据 PDF 文档架构，本 Skill 通过 **MCP Server** 暴露，作为中央编排服务的一部分：

```
Cursor CLI → MCP Server (中央编排服务) → review_tests 工具 → 项目代码仓库
```

**Agent 应该通过 MCP Server 调用 `review_tests` 工具**：

**MCP 工具调用**：
```json
{
  "tool": "review_tests",
  "arguments": {
    "workspace_id": "req-20240101-120000-user-auth",
    "test_files": ["tests/test_xxx.py", "tests/test_yyy.py"]
  }
}
```

**在 Cursor IDE 中使用**：
```
@agent-orchestrator review_tests workspace_id="req-20240101-120000-user-auth" test_files=["tests/test_xxx.py", "tests/test_yyy.py"]
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
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
    "error_type": "ErrorType"
}
```

> **注意**：
> - 本工具通过 MCP Server 暴露，符合 PDF 文档架构
> - 返回 JSON 格式，便于 Agent 解析
> - 核心实现在 `mcp-server/src/tools/test_reviewer.py`

---

## 五、与其他 Skill 的关系

典型链路：

```text
代码 → [test-generator] → 测试文件
测试文件 → [test-reviewer] → 测试质量报告
```

