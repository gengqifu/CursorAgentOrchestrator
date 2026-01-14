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

## 二、前置条件

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

## 四、调用示例

```python
from src.tools.test_generator import generate_tests

result = generate_tests("workspace-001", "tests/mocks")
assert result["success"] is True
print(result["test_files"], result["test_count"])
```

---

## 五、与其他 Skill 的关系

典型链路：

```text
代码文件 → [test-generator] → 初始测试文件
初始测试文件 → [test-reviewer] → 测试质量审查
```

