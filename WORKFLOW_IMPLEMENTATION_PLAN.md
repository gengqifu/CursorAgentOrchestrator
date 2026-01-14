# 工作流编排工具实现计划

## 目标

补全缺失功能，形成完整的工作流编排工具，实现流程图中的所有步骤和循环。

## 实现范围

### 核心缺失功能

1. **总编排器询问4个问题** - 新增工具
2. **PRD/TRD确认和修改循环** - 新增工具 + 修改现有工具
3. **任务循环执行机制** - 新增工具
4. **Review通过判断和循环** - 集成到任务循环
5. **询问Mock测试路径** - 新增工具
6. **完整工作流编排工具** - 新增高级工具

## 架构设计

### 1. 用户交互机制

由于 MCP Server 通过 stdio 通信，用户交互需要通过 Cursor Agent 来实现。我们提供两种方案：

#### 方案A：通过 MCP 工具返回交互请求（推荐）

```python
# 工具返回交互请求，由 Agent 处理
{
    "success": True,
    "interaction_required": True,
    "interaction_type": "confirm",  # confirm, question, input
    "message": "请确认PRD是否满意？",
    "options": ["confirm", "modify"],
    "next_action": "generate_prd"  # 如果选择 modify
}
```

#### 方案B：通过状态标记和查询工具

```python
# 设置工作区状态，Agent 查询状态并处理
update_workspace_status(workspace_id, {
    "pending_interaction": {
        "type": "confirm_prd",
        "message": "请确认PRD",
        "options": ["confirm", "modify"]
    }
})

# Agent 查询状态
get_workspace(workspace_id)  # 返回 pending_interaction

# Agent 处理交互后调用
confirm_interaction(workspace_id, action="confirm")
```

**推荐方案A**：更符合 MCP 协议，Agent 可以直接处理交互请求。

### 2. 工作流编排架构

```
┌─────────────────────────────────────────┐
│      execute_full_workflow (高级工具)     │
│  - 统一入口，执行完整工作流                │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                      │
┌───────▼────────┐   ┌────────▼──────────┐
│ 交互工具层      │   │ 执行工具层         │
│ - ask_questions│   │ - execute_tasks    │
│ - confirm_prd   │   │ - execute_task    │
│ - confirm_trd   │   │                   │
│ - ask_test_path │   └───────────────────┘
└────────────────┘
```

## 实现计划

### 阶段1：用户交互工具（优先级：高）

#### 1.1 总编排器询问4个问题工具

**文件**：`mcp-server/src/tools/orchestrator_questions.py`

**功能**：
- 询问4个问题（问题内容待定义）
- 返回答案字典
- 保存到工作区元数据

**MCP 工具**：`ask_orchestrator_questions`

**输入**：
```json
{
    // 不需要 workspace_id，因为这是在创建工作区之前询问
}
```

**输出**：
```json
{
    "success": true,
    "interaction_required": true,
    "interaction_type": "questions",
    "questions": [
        {
            "id": "project_path",
            "question": "请输入项目路径（项目根目录）",
            "type": "text",
            "required": true,
            "placeholder": "/path/to/project"
        },
        {
            "id": "requirement_name",
            "question": "请输入需求名称",
            "type": "text",
            "required": true,
            "placeholder": "用户认证功能"
        },
        {
            "id": "requirement_url",
            "question": "请输入需求URL或文件路径",
            "type": "text",
            "required": true,
            "placeholder": "https://example.com/req.md 或 /path/to/requirement.md"
        },
        {
            "id": "workspace_path",
            "question": "请输入工作区路径（可选，默认使用项目路径下的 .agent-orchestrator）",
            "type": "text",
            "required": false,
            "placeholder": "/path/to/.agent-orchestrator（可选）"
        }
    ]
}
```

**后续调用**（Agent 处理交互后）：
```json
{
    "tool": "submit_orchestrator_answers",
    "arguments": {
        "answers": {
            "project_path": "/path/to/project",
            "requirement_name": "用户认证功能",
            "requirement_url": "https://example.com/req.md",
            "workspace_path": "/path/to/.agent-orchestrator"  // 可选
        }
    }
}
```

**返回结果**（提交答案后）：
```json
{
    "success": true,
    "workspace_id": "req-20240101-120000-user-auth",
    "message": "工作区已创建，可以开始生成PRD"
}
```

**注意**：`submit_orchestrator_answers` 内部会调用 `create_workspace`，所以不需要单独创建工作区。

#### 1.2 PRD确认工具

**文件**：`mcp-server/src/tools/prd_confirmation.py`

**功能**：
- 检查PRD是否已生成
- 返回确认请求
- 处理确认/修改操作

**MCP 工具**：
- `check_prd_confirmation` - 检查是否需要确认
- `confirm_prd` - 确认PRD
- `modify_prd` - 标记需要修改PRD

**流程**：
```python
# 1. 生成PRD后调用
check_prd_confirmation(workspace_id)
# 返回: {"interaction_required": true, "prd_path": "...", "message": "请确认PRD"}

# 2. Agent 处理用户选择后调用
if action == "confirm":
    confirm_prd(workspace_id)
    # 返回: {"success": true, "next_step": "generate_trd"}
else:
    modify_prd(workspace_id)
    # 返回: {"success": true, "next_step": "generate_prd"}  # 循环回到PRD生成
```

#### 1.3 TRD确认工具

**文件**：`mcp-server/src/tools/trd_confirmation.py`

**功能**：同PRD确认，但针对TRD

**MCP 工具**：
- `check_trd_confirmation`
- `confirm_trd`
- `modify_trd`

#### 1.4 询问Mock测试路径工具

**文件**：`mcp-server/src/tools/test_path_question.py`

**功能**：
- 在所有任务完成后，询问测试路径
- 返回默认路径建议

**MCP 工具**：`ask_test_path`

**输入**：
```json
{
    "workspace_id": "req-xxx"
}
```

**输出**：
```json
{
    "success": true,
    "interaction_required": true,
    "interaction_type": "input",
    "message": "请输入Mock测试输出目录路径",
    "default_path": "/path/to/project/tests/mock",
    "workspace_id": "req-xxx"
}
```

**后续调用**（Agent 处理交互后）：
```json
{
    "tool": "submit_test_path",
    "arguments": {
        "workspace_id": "req-xxx",
        "test_output_dir": "/path/to/tests/mock"
    }
}
```

### 阶段2：任务执行工具（优先级：高）

#### 2.1 单个任务执行工具（带Review循环）

**文件**：`mcp-server/src/tools/task_executor.py`

**功能**：
- 执行单个任务：代码生成 → Review → 判断通过
- 如果Review不通过，循环回到代码生成
- 支持最大重试次数

**MCP 工具**：`execute_task`

**输入**：
```json
{
    "workspace_id": "req-xxx",
    "task_id": "task-001",
    "max_review_retries": 3
}
```

**输出**：
```json
{
    "success": true,
    "task_id": "task-001",
    "status": "completed",  // 或 "needs_fix"（达到最大重试次数）
    "review_passed": true,
    "review_count": 1,
    "code_files": ["..."],
    "workspace_id": "req-xxx"
}
```

**实现逻辑**：
```python
def execute_task(workspace_id: str, task_id: str, max_review_retries: int = 3) -> dict:
    retry_count = 0
    
    while retry_count < max_review_retries:
        # 1. 生成代码
        code_result = generate_code(workspace_id, task_id)
        
        # 2. Review
        review_result = review_code(workspace_id, task_id)
        
        # 3. 判断通过
        if review_result["passed"]:
            return {
                "success": True,
                "task_id": task_id,
                "status": "completed",
                "review_passed": True,
                "review_count": retry_count + 1,
                "code_files": code_result["code_files"]
            }
        
        retry_count += 1
        logger.warning(f"Review未通过，重试 {retry_count}/{max_review_retries}")
    
    # 达到最大重试次数
    return {
        "success": True,
        "task_id": task_id,
        "status": "needs_fix",
        "review_passed": False,
        "review_count": retry_count,
        "message": "达到最大重试次数，需要手动修复"
    }
```

#### 2.2 所有任务循环执行工具

**文件**：`mcp-server/src/tools/task_executor.py`（扩展）

**功能**：
- 获取所有待处理任务
- 循环执行每个任务
- 返回执行结果统计

**MCP 工具**：`execute_all_tasks`

**输入**：
```json
{
    "workspace_id": "req-xxx",
    "max_review_retries": 3,
    "task_ids": null  // null表示执行所有pending任务
}
```

**输出**：
```json
{
    "success": true,
    "total_tasks": 5,
    "completed_tasks": 4,
    "failed_tasks": 1,
    "task_results": [
        {"task_id": "task-001", "status": "completed", "review_count": 1},
        {"task_id": "task-002", "status": "completed", "review_count": 2},
        {"task_id": "task-003", "status": "needs_fix", "review_count": 3}
    ],
    "workspace_id": "req-xxx"
}
```

**实现逻辑**：
```python
def execute_all_tasks(
    workspace_id: str,
    max_review_retries: int = 3,
    task_ids: list[str] | None = None
) -> dict:
    task_manager = TaskManager()
    
    # 获取任务列表
    if task_ids:
        tasks = [task_manager.get_task(workspace_id, tid) for tid in task_ids]
    else:
        all_tasks = task_manager.get_tasks(workspace_id)
        tasks = [t for t in all_tasks if t.get("status") == "pending"]
    
    results = []
    completed = 0
    failed = 0
    
    for task in tasks:
        task_id = task["task_id"]
        result = execute_task(workspace_id, task_id, max_review_retries)
        results.append(result)
        
        if result["status"] == "completed":
            completed += 1
        else:
            failed += 1
    
    return {
        "success": True,
        "total_tasks": len(tasks),
        "completed_tasks": completed,
        "failed_tasks": failed,
        "task_results": results,
        "workspace_id": workspace_id
    }
```

### 阶段3：完整工作流编排工具（优先级：中）

#### 3.1 完整工作流执行工具

**文件**：`mcp-server/src/tools/workflow_orchestrator.py`

**功能**：
- 统一入口，执行完整工作流
- 处理所有交互和循环
- 返回工作流执行结果

**MCP 工具**：`execute_full_workflow`

**输入**：
```json
{
    "project_path": "/path/to/project",
    "requirement_name": "用户认证功能",
    "requirement_url": "https://example.com/req",
    "max_review_retries": 3,
    "auto_confirm": false  // 是否自动确认（跳过交互）
}
```

**输出**：
```json
{
    "success": true,
    "workspace_id": "req-xxx",
    "workflow_steps": [
        {"step": "ask_questions", "status": "completed"},
        {"step": "create_workspace", "status": "completed"},
        {"step": "generate_prd", "status": "completed"},
        {"step": "confirm_prd", "status": "completed", "action": "confirm"},
        {"step": "generate_trd", "status": "completed"},
        {"step": "confirm_trd", "status": "completed", "action": "confirm"},
        {"step": "decompose_tasks", "status": "completed", "task_count": 5},
        {"step": "execute_tasks", "status": "completed", "completed": 4, "failed": 1},
        {"step": "ask_test_path", "status": "completed"},
        {"step": "generate_tests", "status": "completed"},
        {"step": "analyze_coverage", "status": "completed", "coverage": 85.5}
    ],
    "interactions_required": [
        // 如果 auto_confirm=false，返回需要交互的步骤
    ]
}
```

**实现逻辑**：
```python
def execute_full_workflow(
    project_path: str,
    requirement_name: str,
    requirement_url: str,
    max_review_retries: int = 3,
    auto_confirm: bool = False
) -> dict:
    workflow_steps = []
    interactions_required = []
    
    # 1. 询问4个问题（在创建工作区之前）
    if not auto_confirm:
        questions_result = ask_orchestrator_questions()
        if questions_result.get("interaction_required"):
            interactions_required.append({
                "step": "ask_questions",
                "interaction": questions_result
            })
            return {"interactions_required": interactions_required}
        # 等待答案提交...
    
    # 2. 提交答案并创建工作区（submit_orchestrator_answers 内部会调用 create_workspace）
    # 注意：如果 auto_confirm=true，需要提供默认答案或从参数中获取
    if auto_confirm:
        # 从参数中获取答案
        answers = {
            "project_path": project_path,
            "requirement_name": requirement_name,
            "requirement_url": requirement_url,
            "workspace_path": None  # 可选，使用默认值
        }
    else:
        # 从交互结果中获取答案（需要等待用户提交）
        answers = submitted_answers  # 从 submit_orchestrator_answers 返回
    
    workspace_result = submit_orchestrator_answers(answers)
    workspace_id = workspace_result["workspace_id"]
    workflow_steps.append({
        "step": "ask_questions",
        "status": "completed"
    })
    workflow_steps.append({
        "step": "create_workspace",
        "status": "completed",
        "workspace_id": workspace_id
    })
    
    # 3. PRD循环
    prd_retry = 0
    while prd_retry < 3:  # 最大3次修改
        prd_result = generate_prd(workspace_id, requirement_url)
        workflow_steps.append({"step": "generate_prd", "status": "completed"})
        
        if auto_confirm:
            confirm_prd(workspace_id)
            break
        
        confirm_result = check_prd_confirmation(workspace_id)
        if confirm_result.get("interaction_required"):
            interactions_required.append({
                "step": "confirm_prd",
                "interaction": confirm_result
            })
            return {"interactions_required": interactions_required}
        
        # 等待确认...
        if confirm_action == "confirm":
            break
        prd_retry += 1
    
    # 4. TRD循环（类似PRD）
    # ...
    
    # 5. 任务分解
    tasks_result = decompose_tasks(workspace_id, trd_path)
    workflow_steps.append({
        "step": "decompose_tasks",
        "status": "completed",
        "task_count": tasks_result["task_count"]
    })
    
    # 6. 任务循环
    tasks_exec_result = execute_all_tasks(workspace_id, max_review_retries)
    workflow_steps.append({
        "step": "execute_tasks",
        "status": "completed",
        "completed": tasks_exec_result["completed_tasks"],
        "failed": tasks_exec_result["failed_tasks"]
    })
    
    # 7. 询问测试路径
    if not auto_confirm:
        test_path_result = ask_test_path(workspace_id)
        if test_path_result.get("interaction_required"):
            interactions_required.append({
                "step": "ask_test_path",
                "interaction": test_path_result
            })
            return {"interactions_required": interactions_required}
        # 等待路径提交...
    
    # 8. 生成测试
    tests_result = generate_tests(workspace_id, test_output_dir)
    workflow_steps.append({"step": "generate_tests", "status": "completed"})
    
    # 9. 生成覆盖率报告
    coverage_result = analyze_coverage(workspace_id, project_path)
    workflow_steps.append({
        "step": "analyze_coverage",
        "status": "completed",
        "coverage": coverage_result["coverage"]
    })
    
    return {
        "success": True,
        "workspace_id": workspace_id,
        "workflow_steps": workflow_steps,
        "interactions_required": interactions_required
    }
```

## 文件结构

```
mcp-server/src/tools/
├── orchestrator_questions.py      # 新增：询问4个问题
├── prd_confirmation.py            # 新增：PRD确认和修改
├── trd_confirmation.py            # 新增：TRD确认和修改
├── test_path_question.py          # 新增：询问测试路径
├── task_executor.py               # 新增：任务执行（带循环）
├── workflow_orchestrator.py       # 新增：完整工作流编排
├── prd_generator.py               # 现有：PRD生成（可能需要小修改）
├── trd_generator.py               # 现有：TRD生成（可能需要小修改）
└── ...                            # 其他现有工具

mcp-server/src/mcp_server.py       # 修改：注册新工具
```

## 测试计划

### 单元测试

1. **orchestrator_questions.py**
   - `test_ask_orchestrator_questions`
   - `test_submit_orchestrator_answers`

2. **prd_confirmation.py**
   - `test_check_prd_confirmation`
   - `test_confirm_prd`
   - `test_modify_prd`

3. **trd_confirmation.py**
   - 同PRD确认测试

4. **test_path_question.py**
   - `test_ask_test_path`
   - `test_submit_test_path`

5. **task_executor.py**
   - `test_execute_task_success`
   - `test_execute_task_review_failed_retry`
   - `test_execute_task_max_retries`
   - `test_execute_all_tasks`

6. **workflow_orchestrator.py**
   - `test_execute_full_workflow_auto_confirm`
   - `test_execute_full_workflow_with_interactions`
   - `test_execute_full_workflow_prd_modify_loop`

### 集成测试

1. 完整工作流测试（自动确认模式）
2. 完整工作流测试（交互模式）
3. PRD修改循环测试
4. TRD修改循环测试
5. 任务Review循环测试

## 实现顺序

### 第1周：用户交互工具

1. Day 1-2: `orchestrator_questions.py` + 测试
2. Day 3-4: `prd_confirmation.py` + 测试
3. Day 5: `trd_confirmation.py` + 测试
4. Day 6-7: `test_path_question.py` + 测试

### 第2周：任务执行工具

1. Day 1-3: `task_executor.py` + 测试
2. Day 4-5: 集成到 MCP Server
3. Day 6-7: 集成测试

### 第3周：完整工作流编排

1. Day 1-3: `workflow_orchestrator.py` + 测试
2. Day 4-5: 集成到 MCP Server
3. Day 6-7: 端到端测试 + 文档更新

## 注意事项

### 1. 交互处理

- MCP Server 通过 stdio 通信，无法直接与用户交互
- 需要通过返回 `interaction_required` 标记，由 Agent 处理交互
- Agent 处理交互后，调用相应的提交工具

### 2. 状态管理

- 使用工作区元数据存储交互状态
- 使用 `workspace.json` 的 `workflow_state` 字段跟踪工作流进度

### 3. 错误处理

- 每个步骤都要有错误处理
- 工作流中断时，保存当前状态，支持恢复

### 4. 并发安全

- 使用文件锁保护工作流状态更新
- 多个 Cursor 终端不能同时执行同一工作流

### 5. 4个问题的定义

**已确认**：总编排器询问的4个问题如下：

1. **项目路径** (`project_path`)
   - 类型：文本输入
   - 说明：目标项目的根目录路径
   - 示例：`/path/to/project`

2. **需求名称** (`requirement_name`)
   - 类型：文本输入
   - 说明：需求的名称或描述
   - 示例：`用户认证功能`

3. **需求URL** (`requirement_url`)
   - 类型：文本输入（URL或文件路径）
   - 说明：需求文档的URL或本地文件路径
   - 示例：`https://example.com/req.md` 或 `/path/to/requirement.md`

4. **工作区路径** (`workspace_path`, 可选)
   - 类型：文本输入（可选）
   - 说明：`.agent-orchestrator` 目录的路径，如果不提供则使用项目路径下的默认位置
   - 示例：`/path/to/.agent-orchestrator`（可选）

**注意**：这4个问题实际上对应 `create_workspace` 工具的参数，应该在创建工作区之前询问。

## 文档更新

1. 更新 `mcp-server/TOOLS.md` - 添加新工具说明
2. 更新 `mcp-server/CURSOR_INTEGRATION.md` - 添加工作流使用示例
3. 更新 `mcp-server/ARCHITECTURE.md` - 添加工作流编排说明
4. 更新 `README.md` - 添加完整工作流说明
5. 创建 `WORKFLOW_GUIDE.md` - 工作流使用指南

## 验收标准

1. ✅ 所有新工具都有单元测试，覆盖率 >= 90%
2. ✅ 完整工作流可以自动执行（auto_confirm=true）
3. ✅ 完整工作流支持交互模式（auto_confirm=false）
4. ✅ PRD/TRD修改循环正常工作
5. ✅ 任务Review循环正常工作
6. ✅ 所有文档已更新
7. ✅ 端到端测试通过
