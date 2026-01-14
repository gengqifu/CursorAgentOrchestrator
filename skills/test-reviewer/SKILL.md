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

- **Skill 入口脚本**：`skills/test-reviewer/scripts/test_reviewer.py`
- **核心实现**：`mcp-server/src/tools/test_reviewer.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/test_reviewer.py`：入口脚本，由 Agent 调用

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

### 步骤 1：调用 Skill 脚本

**Agent 应该执行以下命令**：

```bash
python3 skills/test-reviewer/scripts/test_reviewer.py \
    <workspace_id> \
    [test_files...]
```

**示例**：

```bash
# 自动查找工作区项目路径下的测试文件
python3 skills/test-reviewer/scripts/test_reviewer.py req-20240101-120000-user-auth

# 指定测试文件列表
python3 skills/test-reviewer/scripts/test_reviewer.py req-20240101-120000-user-auth tests/test_xxx.py tests/test_yyy.py
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
> - 如果不提供 `test_files`，脚本会自动查找工作区项目路径下 `tests/` 目录中的 `test_*.py` 文件
> - 脚本会自动处理导入路径，无需手动设置 PYTHONPATH
> - 脚本输出 JSON 格式，便于 Agent 解析

---

## 五、与其他 Skill 的关系

典型链路：

```text
代码 → [test-generator] → 测试文件
测试文件 → [test-reviewer] → 测试质量报告
```

