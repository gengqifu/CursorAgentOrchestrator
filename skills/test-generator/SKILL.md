---
name: test-generator
description: >
  测试生成技能。使用当你已经有项目代码和任务信息，需要为现有代码生成基础的
  Mock/单元测试文件，并整理到指定测试目录下。
---

# Test Generator Skill

本 Skill 指导 Agent 基于 `mcp-server/src/tools/test_generator.py`，
为工作区对应项目生成基础测试文件（通常是 Mock 测试或简单集成测试）。

---

## 一、适用场景

- 已经有一定量的业务代码（可由 `code-generator` 生成）
- 希望：
  - 快速生成一批基础测试骨架文件
  - 为后续手工/AI 完善测试提供起点

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

- **Skill 入口脚本**：`skills/test-generator/scripts/test_generator.py`
- **核心实现**：`mcp-server/src/tools/test_generator.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/test_generator.py`：入口脚本，由 Agent 调用

### 2. 前置条件

- 工作区目录存在（`workspace.json` 可用）
- `project_path` 下有可扫描的 Python 代码结构

---

## 三、输入输出

- 输入：
  - `workspace_id: str`
  - `test_output_dir: str` —— 测试文件输出目录（相对于项目路径或绝对路径）
- 输出（Python dict）：

```python
{
    "success": True,
    "test_files": ["<path>/test_xxx.py", ...],
    "test_count": <int>,
    "workspace_id": workspace_id,
}
```

---

## 四、标准调用流程

### 步骤 1：调用 Skill 脚本

**Agent 应该执行以下命令**：

```bash
python3 skills/test-generator/scripts/test_generator.py \
    <workspace_id> \
    [test_output_dir]
```

**示例**：

```bash
# 使用工作区项目路径下的 tests 目录
python3 skills/test-generator/scripts/test_generator.py req-20240101-120000-user-auth

# 指定测试输出目录
python3 skills/test-generator/scripts/test_generator.py req-20240101-120000-user-auth /path/to/tests
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "test_files": ["/path/to/test_xxx.py", ...],
    "test_count": 5,
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
> - 如果不提供 `test_output_dir`，脚本会自动使用工作区项目路径下的 `tests` 目录
> - 脚本会自动处理导入路径，无需手动设置 PYTHONPATH
> - 脚本输出 JSON 格式，便于 Agent 解析

---

## 五、与其他 Skill 的关系

典型链路：

```text
代码文件 → [test-generator] → 初始测试文件
初始测试文件 → [test-reviewer] → 测试质量审查
```

