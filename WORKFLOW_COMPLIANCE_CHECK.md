# 工作流程符合性检查

根据提供的流程图，检查当前项目实现是否符合完整工作流程。

## 流程图关键步骤

1. 用户输入需求URL
2. **总编排器询问4个问题** ⚠️
3. 创建工作区
4. 生成PRD
5. **用户确认PRD（修改/确认循环）** ⚠️
6. 生成TRD
7. **用户确认TRD（修改/确认循环）** ⚠️
8. 任务分解
9. **循环执行编码任务** ⚠️
   - 代码生成
   - 代码Review
   - **Review通过判断（否→回到代码生成）** ⚠️
   - **还有任务判断（是→继续循环）** ⚠️
10. **询问Mock测试路径** ❌
11. 生成Mock测试
12. 生成覆盖率报告
13. 完成

## 当前实现检查

### ✅ 已完全实现的功能

| 步骤 | 功能 | 实现状态 | 说明 |
|------|------|---------|------|
| 1 | 用户输入需求URL | ✅ | `create_workspace` 接受 `requirement_url` 参数 |
| 3 | 创建工作区 | ✅ | `create_workspace` 工具已实现 |
| 4 | 生成PRD | ✅ | `generate_prd` 工具已实现 |
| 6 | 生成TRD | ✅ | `generate_trd` 工具已实现 |
| 8 | 任务分解 | ✅ | `decompose_tasks` 工具已实现 |
| 9.1 | 代码生成 | ✅ | `generate_code` 工具已实现 |
| 9.2 | 代码Review | ✅ | `review_code` 工具已实现，有 `passed` 判断 |
| 11 | 生成Mock测试 | ✅ | `generate_tests` 工具已实现 |
| 12 | 生成覆盖率报告 | ✅ | `analyze_coverage` 工具已实现 |

### ⚠️ 部分实现的功能

| 步骤 | 功能 | 实现状态 | 缺失部分 |
|------|------|---------|---------|
| 2 | 总编排器询问4个问题 | ❌ | 完全没有实现。需要添加一个工具或机制来询问用户4个问题 |
| 5 | 用户确认PRD（修改/确认循环） | ❌ | 没有确认机制，没有修改循环。PRD生成后直接继续 |
| 7 | 用户确认TRD（修改/确认循环） | ❌ | 没有确认机制，没有修改循环。TRD生成后直接继续 |
| 9 | 循环执行编码任务 | ⚠️ | 有工具，但没有自动循环机制。需要手动逐个调用 |
| 9.3 | Review通过判断（否→回到代码生成） | ⚠️ | `review_code` 有 `passed` 判断，但没有自动循环回到 `generate_code` |
| 9.4 | 还有任务判断（是→继续循环） | ⚠️ | 可以获取任务列表，但没有自动循环机制 |
| 10 | 询问Mock测试路径 | ❌ | `generate_tests` 需要 `test_output_dir` 参数，但没有询问机制 |

## 详细分析

### 1. 总编排器询问4个问题 ❌

**流程图要求**：
- 在创建工作区之前，总编排器应该询问用户4个问题

**当前实现**：
- ❌ 完全没有实现
- `create_workspace` 直接接受参数，没有询问机制

**需要实现**：
```python
# 需要添加一个工具或机制
ask_orchestrator_questions(workspace_id: str) -> dict:
    """询问4个问题，返回答案"""
    # 问题1: ...
    # 问题2: ...
    # 问题3: ...
    # 问题4: ...
```

### 2. PRD/TRD 确认和修改循环 ❌

**流程图要求**：
- PRD生成后，用户需要确认
- 如果选择"修改"，循环回到PRD生成
- 如果选择"确认"，继续到TRD生成
- TRD同样需要确认和修改循环

**当前实现**：
- ❌ 没有确认机制
- PRD/TRD生成后直接继续，没有用户交互

**需要实现**：
```python
# 需要添加确认工具
confirm_prd(workspace_id: str, action: str) -> dict:
    """确认或修改PRD
    action: "confirm" | "modify"
    """
    
confirm_trd(workspace_id: str, action: str) -> dict:
    """确认或修改TRD
    action: "confirm" | "modify"
    """
```

### 3. 任务循环执行机制 ⚠️

**流程图要求**：
- 自动循环执行所有任务
- 每个任务：代码生成 → Review → 判断通过 → 判断还有任务 → 循环

**当前实现**：
- ⚠️ 有单独的工具，但没有自动循环
- 需要手动调用 `generate_code` → `review_code` → 手动判断 → 手动循环

**需要实现**：
```python
# 需要添加一个工作流编排工具
execute_all_tasks(workspace_id: str) -> dict:
    """自动执行所有任务的循环"""
    tasks = task_manager.get_tasks(workspace_id)
    pending_tasks = [t for t in tasks if t["status"] == "pending"]
    
    for task in pending_tasks:
        while True:
            # 1. 生成代码
            generate_code(workspace_id, task["task_id"])
            
            # 2. Review
            review_result = review_code(workspace_id, task["task_id"])
            
            # 3. 判断通过
            if review_result["passed"]:
                break  # 通过，继续下一个任务
            # 否则循环回到代码生成
            
    return {"success": True, "completed_tasks": ...}
```

### 4. Review通过判断和循环 ⚠️

**流程图要求**：
- Review后判断是否通过
- 如果"否"，循环回到代码生成
- 如果"是"，继续判断是否还有任务

**当前实现**：
- ✅ `review_code` 返回 `passed: bool`
- ❌ 没有自动循环回到 `generate_code`
- ❌ 没有自动判断是否还有任务

**需要实现**：
- 见上面的 `execute_all_tasks` 工具

### 5. 询问Mock测试路径 ❌

**流程图要求**：
- 在所有编码任务完成后，询问用户Mock测试路径

**当前实现**：
- ❌ 没有询问机制
- `generate_tests` 需要 `test_output_dir` 参数，但必须由调用者提供

**需要实现**：
```python
# 需要添加询问工具
ask_test_path(workspace_id: str) -> dict:
    """询问用户Mock测试路径"""
    # 可以通过 MCP 协议与用户交互
    # 或者返回默认路径建议
```

## 符合性总结

### ✅ 符合的部分（9/13）

1. ✅ 用户输入需求URL
2. ✅ 创建工作区
3. ✅ 生成PRD
4. ✅ 生成TRD
5. ✅ 任务分解
6. ✅ 代码生成
7. ✅ 代码Review（有判断逻辑）
8. ✅ 生成Mock测试
9. ✅ 生成覆盖率报告

### ❌ 不符合的部分（4/13）

1. ❌ **总编排器询问4个问题** - 完全缺失
2. ❌ **PRD确认和修改循环** - 完全缺失
3. ❌ **TRD确认和修改循环** - 完全缺失
4. ❌ **询问Mock测试路径** - 完全缺失

### ⚠️ 部分符合的部分（4/13）

1. ⚠️ **循环执行编码任务** - 有工具，但无自动循环
2. ⚠️ **Review通过判断** - 有判断，但无自动循环
3. ⚠️ **还有任务判断** - 可获取任务列表，但无自动循环
4. ⚠️ **工作流编排** - 需要手动调用各个工具，没有统一的编排机制

## 建议改进方案

### 方案1：添加工作流编排工具（推荐）

添加一个高级工作流工具，自动执行完整流程：

```python
# mcp-server/src/tools/workflow_orchestrator.py

def execute_full_workflow(workspace_id: str, requirement_url: str) -> dict:
    """执行完整工作流程"""
    # 1. 询问4个问题（需要实现）
    questions_result = ask_orchestrator_questions(workspace_id)
    
    # 2. 创建工作区
    workspace_id = create_workspace(...)
    
    # 3. PRD循环
    while True:
        prd_result = generate_prd(workspace_id, requirement_url)
        # 询问用户确认（需要实现）
        confirm = ask_user_confirm("PRD", prd_result["prd_path"])
        if confirm == "confirm":
            break
        # 否则循环
    
    # 4. TRD循环
    while True:
        trd_result = generate_trd(workspace_id, prd_result["prd_path"])
        confirm = ask_user_confirm("TRD", trd_result["trd_path"])
        if confirm == "confirm":
            break
    
    # 5. 任务分解
    tasks_result = decompose_tasks(workspace_id, trd_result["trd_path"])
    
    # 6. 任务循环
    execute_all_tasks(workspace_id)
    
    # 7. 询问测试路径
    test_path = ask_test_path(workspace_id)
    
    # 8. 生成测试
    generate_tests(workspace_id, test_path)
    
    # 9. 生成覆盖率报告
    analyze_coverage(workspace_id, ...)
    
    return {"success": True}
```

### 方案2：保持当前架构，添加缺失工具

保持当前的工具式架构，但添加缺失的交互工具：

1. `ask_orchestrator_questions` - 询问4个问题
2. `confirm_prd` / `confirm_trd` - 确认和修改循环
3. `execute_all_tasks` - 任务循环执行
4. `ask_test_path` - 询问测试路径

### 方案3：通过 Cursor Agent 实现工作流编排

不在 MCP Server 层面实现工作流，而是通过 Cursor Agent 的智能编排能力：

- Agent 根据流程图自动调用各个工具
- Agent 处理确认和循环逻辑
- MCP Server 只提供基础工具

**优点**：
- 保持 MCP Server 简单
- 利用 Agent 的智能决策能力

**缺点**：
- 需要 Agent 理解完整工作流
- 可能不如显式工作流工具可靠

## 结论

**当前实现符合度：约 69%（9/13 完全符合，4/13 部分符合）**

主要缺失：
1. 用户交互机制（询问问题、确认、询问路径）
2. 自动循环机制（任务循环、Review循环）
3. 工作流编排（统一的工作流执行工具）

**建议**：
- 短期：添加缺失的交互工具（`ask_orchestrator_questions`, `confirm_prd`, `confirm_trd`, `ask_test_path`）
- 中期：添加任务循环执行工具（`execute_all_tasks`）
- 长期：考虑添加完整工作流编排工具（`execute_full_workflow`）

或者采用方案3，通过 Cursor Agent 的智能编排能力来实现工作流，保持 MCP Server 的工具式架构。
