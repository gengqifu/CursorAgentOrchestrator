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

## 二、前置条件

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

## 四、调用示例

```python
from src.tools.test_reviewer import review_tests

result = review_tests("workspace-001", ["tests/test_xxx.py"])
assert result["success"] is True
print(result["passed"])
print(result["review_report"])
```

---

## 五、与其他 Skill 的关系

典型链路：

```text
代码 → [test-generator] → 测试文件
测试文件 → [test-reviewer] → 测试质量报告
```

