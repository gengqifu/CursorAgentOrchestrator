# Agent Orchestrator 完整工作计划

## 项目目标

补全缺失功能，形成完整的工作流编排工具，实现流程图中的所有步骤和循环，使总编排器能够完整协调整个开发流程。

## 总编排器的作用

总编排器是 MCP Server 的核心组件，负责：

1. **工作流协调与编排**
   - 协调整个开发流程：从需求输入到代码完成
   - 管理步骤顺序：PRD → TRD → 任务分解 → 代码生成 → Review → 测试 → 覆盖率
   - 处理循环：PRD/TRD修改循环、Review重试循环、任务执行循环

2. **请求路由与分发**
   - 接收来自 Cursor CLI 的 MCP 请求
   - 路由到对应的工具（基础设施工具或 SKILL 工具）
   - 统一错误处理和响应格式

3. **状态管理**
   - 跟踪工作流进度
   - 管理工作区状态
   - 支持工作流中断和恢复

4. **用户交互协调**
   - 询问4个问题（项目路径、需求名称、需求URL、工作区路径）
   - 处理PRD/TRD确认和修改
   - 询问测试路径等交互

5. **决策与条件判断**
   - Review通过判断
   - 是否还有任务判断
   - 循环终止条件判断

## 已确认的4个问题

1. **项目路径** (`project_path`) - 必填
   - 目标项目的根目录路径
   - 示例：`/path/to/project`

2. **需求名称** (`requirement_name`) - 必填
   - 需求的名称或描述
   - 示例：`用户认证功能`

3. **需求URL** (`requirement_url`) - 必填
   - 需求文档的URL或本地文件路径
   - 示例：`https://example.com/req.md` 或 `/path/to/requirement.md`

4. **工作区路径** (`workspace_path`) - 可选
   - `.agent-orchestrator` 目录的路径
   - 如果不提供，默认使用项目路径下的 `.agent-orchestrator` 目录

## 完整工作流程

```
1. 询问4个问题 (ask_orchestrator_questions)
   ↓
2. 提交答案并创建工作区 (submit_orchestrator_answers)
   - 内部调用 create_workspace
   ↓
3. 生成PRD (generate_prd)
   ↓
4. PRD确认循环 (check_prd_confirmation → confirm_prd / modify_prd)
   - 如果 modify → 回到步骤3
   - 如果 confirm → 继续
   ↓
5. 生成TRD (generate_trd)
   ↓
6. TRD确认循环 (check_trd_confirmation → confirm_trd / modify_trd)
   - 如果 modify → 回到步骤5
   - 如果 confirm → 继续
   ↓
7. 任务分解 (decompose_tasks)
   ↓
8. 任务循环执行 (execute_all_tasks)
   - 对每个任务：
     a. 代码生成 (generate_code)
     b. 代码Review (review_code)
     c. Review通过判断
       - 如果否 → 回到 a（最多重试3次）
       - 如果是 → 继续
     d. 判断是否还有任务
       - 如果是 → 继续下一个任务
       - 如果否 → 继续
   ↓
9. 询问Mock测试路径 (ask_test_path)
   ↓
10. 生成Mock测试 (generate_tests)
   ↓
11. 生成覆盖率报告 (analyze_coverage)
   ↓
12. 完成
```

## 实现范围

### 需要新增的工具（8个）

1. **orchestrator_questions.py** - 总编排器询问4个问题
2. **prd_confirmation.py** - PRD确认和修改循环
3. **trd_confirmation.py** - TRD确认和修改循环
4. **test_path_question.py** - 询问Mock测试路径
5. **task_executor.py** - 任务执行（带Review循环）
6. **workflow_status.py** - 工作流状态查询（多Agent支持）
7. **stage_dependency_checker.py** - 状态依赖检查（多Agent支持）
8. **workflow_orchestrator.py** - 完整工作流编排

### 需要修改的文件

1. **mcp_server.py** - 注册新工具
2. **workspace_manager.py** - 可能需要添加工作流状态管理
3. **config.py** - 可能需要添加工作流相关配置

## 详细实现计划

### 阶段1：用户交互工具（第1周）

#### 1.1 orchestrator_questions.py

**文件**：`mcp-server/src/tools/orchestrator_questions.py`

**功能**：
- 询问4个问题（项目路径、需求名称、需求URL、工作区路径）
- 返回交互请求
- 处理答案提交并创建工作区

**MCP 工具**：
- `ask_orchestrator_questions` - 询问4个问题
- `submit_orchestrator_answers` - 提交答案并创建工作区

**实现细节**：

```python
def ask_orchestrator_questions() -> dict:
    """询问4个问题。
    
    Returns:
        包含交互请求的字典
    """
    return {
        "success": True,
        "interaction_required": True,
        "interaction_type": "questions",
        "questions": [
            {
                "id": "project_path",
                "question": "请输入项目路径（项目根目录）",
                "type": "text",
                "required": True,
                "placeholder": "/path/to/project"
            },
            {
                "id": "requirement_name",
                "question": "请输入需求名称",
                "type": "text",
                "required": True,
                "placeholder": "用户认证功能"
            },
            {
                "id": "requirement_url",
                "question": "请输入需求URL或文件路径",
                "type": "text",
                "required": True,
                "placeholder": "https://example.com/req.md 或 /path/to/requirement.md"
            },
            {
                "id": "workspace_path",
                "question": "请输入工作区路径（可选，默认使用项目路径下的 .agent-orchestrator）",
                "type": "text",
                "required": False,
                "placeholder": "/path/to/.agent-orchestrator（可选）"
            }
        ]
    }

def submit_orchestrator_answers(answers: dict) -> dict:
    """提交答案并创建工作区。
    
    Args:
        answers: 包含4个问题答案的字典
    
    Returns:
        包含 workspace_id 的字典
    """
    # 验证答案
    # 创建工作区（调用 WorkspaceManager.create_workspace）
    # 返回 workspace_id
```

**测试用例**：
- `test_ask_orchestrator_questions` - 测试询问问题
- `test_submit_orchestrator_answers_success` - 测试提交答案成功
- `test_submit_orchestrator_answers_missing_required` - 测试缺少必填项
- `test_submit_orchestrator_answers_invalid_path` - 测试无效路径

#### 1.2 prd_confirmation.py

**文件**：`mcp-server/src/tools/prd_confirmation.py`

**功能**：
- 检查PRD是否已生成
- 返回确认请求
- 处理确认/修改操作

**MCP 工具**：
- `check_prd_confirmation` - 检查是否需要确认PRD
- `confirm_prd` - 确认PRD
- `modify_prd` - 标记需要修改PRD

**实现细节**：

```python
def check_prd_confirmation(workspace_id: str) -> dict:
    """检查是否需要确认PRD。
    
    Args:
        workspace_id: 工作区ID
    
    Returns:
        包含确认请求的字典
    """
    # 检查PRD是否已生成
    # 返回交互请求

def confirm_prd(workspace_id: str) -> dict:
    """确认PRD。
    
    Args:
        workspace_id: 工作区ID
    
    Returns:
        确认结果
    """
    # 更新工作区状态
    # 标记PRD已确认

def modify_prd(workspace_id: str) -> dict:
    """标记需要修改PRD。
    
    Args:
        workspace_id: 工作区ID
    
    Returns:
        修改标记结果
    """
    # 更新工作区状态
    # 标记PRD需要重新生成
```

**测试用例**：
- `test_check_prd_confirmation_prd_exists` - 测试PRD存在时的确认请求
- `test_check_prd_confirmation_prd_not_exists` - 测试PRD不存在时的错误
- `test_confirm_prd_success` - 测试确认PRD成功
- `test_modify_prd_success` - 测试修改PRD成功
- `test_prd_modify_loop` - 测试PRD修改循环

#### 1.3 trd_confirmation.py

**文件**：`mcp-server/src/tools/trd_confirmation.py`

**功能**：同PRD确认，但针对TRD

**MCP 工具**：
- `check_trd_confirmation`
- `confirm_trd`
- `modify_trd`

**测试用例**：同PRD确认

#### 1.4 test_path_question.py

**文件**：`mcp-server/src/tools/test_path_question.py`

**功能**：
- 在所有任务完成后，询问测试路径
- 返回默认路径建议
- 处理路径提交

**MCP 工具**：
- `ask_test_path` - 询问测试路径
- `submit_test_path` - 提交测试路径

**实现细节**：

```python
def ask_test_path(workspace_id: str) -> dict:
    """询问Mock测试路径。
    
    Args:
        workspace_id: 工作区ID
    
    Returns:
        包含交互请求的字典
    """
    # 获取工作区信息
    # 生成默认路径建议
    # 返回交互请求

def submit_test_path(workspace_id: str, test_output_dir: str) -> dict:
    """提交测试路径。
    
    Args:
        workspace_id: 工作区ID
        test_output_dir: 测试输出目录
    
    Returns:
        提交结果
    """
    # 验证路径
    # 保存到工作区元数据
```

**测试用例**：
- `test_ask_test_path_success` - 测试询问测试路径
- `test_submit_test_path_success` - 测试提交测试路径成功
- `test_submit_test_path_invalid` - 测试无效路径

### 阶段2：任务执行工具（第2周）

#### 2.1 task_executor.py

**文件**：`mcp-server/src/tools/task_executor.py`

**功能**：
- 执行单个任务：代码生成 → Review → 判断通过
- 如果Review不通过，循环回到代码生成
- 支持最大重试次数
- 执行所有任务循环

**MCP 工具**：
- `execute_task` - 执行单个任务（带Review循环）
- `execute_all_tasks` - 执行所有任务

**实现细节**：

```python
def execute_task(
    workspace_id: str,
    task_id: str,
    max_review_retries: int = 3
) -> dict:
    """执行单个任务（带Review循环）。
    
    Args:
        workspace_id: 工作区ID
        task_id: 任务ID
        max_review_retries: 最大Review重试次数
    
    Returns:
        执行结果
    """
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

def execute_all_tasks(
    workspace_id: str,
    max_review_retries: int = 3,
    task_ids: list[str] | None = None
) -> dict:
    """执行所有任务。
    
    Args:
        workspace_id: 工作区ID
        max_review_retries: 最大Review重试次数
        task_ids: 任务ID列表，None表示执行所有pending任务
    
    Returns:
        执行结果统计
    """
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

**测试用例**：
- `test_execute_task_success` - 测试任务执行成功
- `test_execute_task_review_failed_retry` - 测试Review失败重试
- `test_execute_task_max_retries` - 测试达到最大重试次数
- `test_execute_all_tasks_success` - 测试执行所有任务成功
- `test_execute_all_tasks_partial_failure` - 测试部分任务失败

### 阶段3：多Agent支持工具（第3周）

#### 3.1 workflow_status.py

**文件**：`mcp-server/src/tools/workflow_status.py`

**功能**：
- 查询工作流状态和进度
- 返回各阶段完成情况
- 标识可以开始的阶段和被阻塞的阶段

**MCP 工具**：
- `get_workflow_status` - 获取工作流状态

**实现细节**：

```python
def get_workflow_status(workspace_id: str) -> dict:
    """获取工作流状态。
    
    Args:
        workspace_id: 工作区ID
    
    Returns:
        工作流状态字典
    """
    workspace_manager = WorkspaceManager()
    task_manager = TaskManager()
    
    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    status = workspace.get("status", {})
    files = workspace.get("files", {})
    
    # 获取任务信息
    tasks = task_manager.get_tasks(workspace_id)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]
    
    # 构建阶段状态
    stages = {
        "prd": {
            "status": status.get("prd_status", "pending"),
            "file": files.get("prd_path"),
            "ready": True  # PRD没有前置依赖
        },
        "trd": {
            "status": status.get("trd_status", "pending"),
            "file": files.get("trd_path"),
            "ready": status.get("prd_status") == "completed"
        },
        "tasks": {
            "status": status.get("tasks_status", "pending"),
            "file": files.get("tasks_json_path"),
            "task_count": len(tasks),
            "ready": status.get("trd_status") == "completed"
        },
        "code": {
            "status": status.get("code_status", "pending"),
            "completed_tasks": len(completed_tasks),
            "pending_tasks": len(pending_tasks),
            "total_tasks": len(tasks),
            "ready": status.get("tasks_status") == "completed"
        },
        "test": {
            "status": status.get("test_status", "pending"),
            "ready": len(pending_tasks) == 0 and len(completed_tasks) > 0
        },
        "coverage": {
            "status": "pending",
            "ready": status.get("test_status") == "completed"
        }
    }
    
    # 计算可以开始的阶段
    next_available_stages = [
        stage_name for stage_name, stage_info in stages.items()
        if stage_info["ready"] and stage_info["status"] in ["pending", "needs_regeneration"]
    ]
    
    # 计算被阻塞的阶段
    blocked_stages = [
        stage_name for stage_name, stage_info in stages.items()
        if not stage_info["ready"] and stage_info["status"] == "pending"
    ]
    
    return {
        "success": True,
        "workspace_id": workspace_id,
        "stages": stages,
        "next_available_stages": next_available_stages,
        "blocked_stages": blocked_stages,
        "workflow_progress": {
            "completed_stages": len([s for s in stages.values() if s["status"] == "completed"]),
            "total_stages": len(stages),
            "progress_percentage": round(
                len([s for s in stages.values() if s["status"] == "completed"]) / len(stages) * 100,
                2
            )
        }
    }
```

**测试用例**：
- `test_get_workflow_status_initial` - 测试初始状态
- `test_get_workflow_status_prd_completed` - 测试PRD完成后的状态
- `test_get_workflow_status_all_completed` - 测试所有阶段完成
- `test_get_workflow_status_partial_progress` - 测试部分进度

#### 3.2 stage_dependency_checker.py

**文件**：`mcp-server/src/tools/stage_dependency_checker.py`

**功能**：
- 检查阶段是否可以开始
- 验证前置阶段依赖
- 返回详细的依赖信息

**MCP 工具**：
- `check_stage_ready` - 检查阶段是否可以开始

**实现细节**：

```python
# 阶段依赖定义
STAGE_DEPENDENCIES = {
    "prd": [],  # PRD没有前置依赖
    "trd": ["prd"],
    "tasks": ["trd"],
    "code": ["tasks"],
    "test": ["code"],
    "coverage": ["test"]
}

def check_stage_ready(workspace_id: str, stage: str) -> dict:
    """检查阶段是否可以开始。
    
    Args:
        workspace_id: 工作区ID
        stage: 阶段名称（"prd", "trd", "tasks", "code", "test", "coverage"）
    
    Returns:
        检查结果字典
    """
    if stage not in STAGE_DEPENDENCIES:
        raise ValidationError(f"未知阶段: {stage}")
    
    workspace_manager = WorkspaceManager()
    workspace = workspace_manager.get_workspace(workspace_id)
    status = workspace.get("status", {})
    
    # 获取前置阶段
    required_stages = STAGE_DEPENDENCIES[stage]
    
    # 检查前置阶段状态
    completed_stages = []
    pending_stages = []
    in_progress_stages = []
    
    for req_stage in required_stages:
        req_status = status.get(f"{req_stage}_status", "pending")
        if req_status == "completed":
            completed_stages.append(req_stage)
        elif req_status == "in_progress":
            in_progress_stages.append(req_stage)
        else:
            pending_stages.append(req_stage)
    
    # 判断是否可以开始
    ready = (
        len(pending_stages) == 0 and
        len(in_progress_stages) == 0 and
        len(completed_stages) == len(required_stages)
    )
    
    # 检查文件是否存在（对于有文件依赖的阶段）
    file_ready = True
    files = workspace.get("files", {})
    
    if stage == "trd":
        file_ready = files.get("prd_path") is not None and Path(files["prd_path"]).exists()
    elif stage == "tasks":
        file_ready = files.get("trd_path") is not None and Path(files["trd_path"]).exists()
    elif stage == "code":
        file_ready = files.get("tasks_json_path") is not None and Path(files["tasks_json_path"]).exists()
    
    return {
        "success": True,
        "stage": stage,
        "ready": ready and file_ready,
        "reason": (
            "前置阶段已完成，可以开始" if (ready and file_ready)
            else f"前置阶段未完成: {', '.join(pending_stages + in_progress_stages)}"
            if not ready
            else "依赖文件不存在"
        ),
        "required_stages": required_stages,
        "completed_stages": completed_stages,
        "pending_stages": pending_stages,
        "in_progress_stages": in_progress_stages,
        "file_ready": file_ready
    }
```

**测试用例**：
- `test_check_stage_ready_prd` - 测试PRD阶段（无依赖）
- `test_check_stage_ready_trd_with_prd_completed` - 测试TRD阶段（PRD已完成）
- `test_check_stage_ready_trd_with_prd_pending` - 测试TRD阶段（PRD未完成）
- `test_check_stage_ready_code_with_tasks_completed` - 测试代码阶段（任务已完成）
- `test_check_stage_ready_invalid_stage` - 测试无效阶段

#### 3.3 修改现有工具添加状态检查

**需要修改的文件**：
- `trd_generator.py` - 添加PRD状态检查
- `task_decomposer.py` - 添加TRD状态检查
- `code_generator.py` - 添加任务状态检查
- `test_generator.py` - 添加代码状态检查

**修改示例**：

```python
# trd_generator.py
def generate_trd(workspace_id: str, prd_path: str) -> dict:
    """生成 TRD 文档。"""
    workspace_manager = WorkspaceManager(config=config)
    workspace = workspace_manager.get_workspace(workspace_id)
    
    # ✅ 新增：检查PRD状态
    if workspace["status"].get("prd_status") != "completed":
        raise ValidationError("PRD尚未完成，无法生成TRD。请先完成PRD生成。")
    
    # ✅ 新增：检查PRD文件存在
    prd_file = Path(prd_path)
    if not prd_file.exists():
        raise ValidationError(f"PRD 文件不存在: {prd_path}")
    
    # ✅ 新增：标记TRD为进行中
    workspace_manager.update_workspace_status(
        workspace_id,
        {"trd_status": "in_progress"}
    )
    
    try:
        # ... 生成TRD逻辑 ...
        
        # ✅ 新增：标记TRD为已完成
        workspace_manager.update_workspace_status(
            workspace_id,
            {"trd_status": "completed"}
        )
    except Exception as e:
        # ✅ 新增：标记TRD为失败
        workspace_manager.update_workspace_status(
            workspace_id,
            {"trd_status": "failed"}
        )
        raise
```

### 阶段4：完整工作流编排（第4周）

#### 4.1 workflow_orchestrator.py

**文件**：`mcp-server/src/tools/workflow_orchestrator.py`

**功能**：
- 统一入口，执行完整工作流
- 处理所有交互和循环
- 支持自动确认模式和交互模式
- 返回工作流执行结果

**MCP 工具**：
- `execute_full_workflow` - 执行完整工作流

**实现细节**：

```python
def execute_full_workflow(
    project_path: str | None = None,
    requirement_name: str | None = None,
    requirement_url: str | None = None,
    workspace_path: str | None = None,
    max_review_retries: int = 3,
    auto_confirm: bool = False
) -> dict:
    """执行完整工作流。
    
    Args:
        project_path: 项目路径（如果auto_confirm=True则必填）
        requirement_name: 需求名称（如果auto_confirm=True则必填）
        requirement_url: 需求URL（如果auto_confirm=True则必填）
        workspace_path: 工作区路径（可选）
        max_review_retries: 最大Review重试次数
        auto_confirm: 是否自动确认（跳过交互）
    
    Returns:
        工作流执行结果
    """
    workflow_steps = []
    interactions_required = []
    workspace_id = None
    
    # 1. 询问4个问题（在创建工作区之前）
    if not auto_confirm:
        questions_result = ask_orchestrator_questions()
        if questions_result.get("interaction_required"):
            interactions_required.append({
                "step": "ask_questions",
                "interaction": questions_result
            })
            return {
                "success": True,
                "interactions_required": interactions_required
            }
        # 等待答案提交...
        # 注意：在实际实现中，这需要等待Agent处理交互后再次调用
        # 这里假设答案已经通过 submit_orchestrator_answers 提交
        return {"interactions_required": interactions_required}
    
    # auto_confirm=True 时，使用提供的参数
    if not all([project_path, requirement_name, requirement_url]):
        raise ValidationError("auto_confirm=True时，project_path、requirement_name、requirement_url都是必填的")
    
    answers = {
        "project_path": project_path,
        "requirement_name": requirement_name,
        "requirement_url": requirement_url,
        "workspace_path": workspace_path
    }
    
    # 2. 提交答案并创建工作区
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
    max_prd_retries = 3
    while prd_retry < max_prd_retries:
        prd_result = generate_prd(workspace_id, requirement_url)
        workflow_steps.append({
            "step": "generate_prd",
            "status": "completed",
            "prd_path": prd_result["prd_path"],
            "retry": prd_retry
        })
        
        if auto_confirm:
            confirm_prd(workspace_id)
            break
        
        confirm_result = check_prd_confirmation(workspace_id)
        if confirm_result.get("interaction_required"):
            interactions_required.append({
                "step": "confirm_prd",
                "interaction": confirm_result
            })
            return {
                "success": True,
                "workspace_id": workspace_id,
                "workflow_steps": workflow_steps,
                "interactions_required": interactions_required
            }
        
        # 等待确认...
        # 这里假设已经通过 confirm_prd 或 modify_prd 处理
        # 如果 modify，prd_retry += 1，继续循环
        # 如果 confirm，break
        break  # 简化，实际需要根据确认结果决定
    
    # 4. TRD循环（类似PRD）
    trd_retry = 0
    max_trd_retries = 3
    prd_path = prd_result["prd_path"]
    while trd_retry < max_trd_retries:
        trd_result = generate_trd(workspace_id, prd_path)
        workflow_steps.append({
            "step": "generate_trd",
            "status": "completed",
            "trd_path": trd_result["trd_path"],
            "retry": trd_retry
        })
        
        if auto_confirm:
            confirm_trd(workspace_id)
            break
        
        confirm_result = check_trd_confirmation(workspace_id)
        if confirm_result.get("interaction_required"):
            interactions_required.append({
                "step": "confirm_trd",
                "interaction": confirm_result
            })
            return {
                "success": True,
                "workspace_id": workspace_id,
                "workflow_steps": workflow_steps,
                "interactions_required": interactions_required
            }
        
        break  # 简化
    
    # 5. 任务分解
    trd_path = trd_result["trd_path"]
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
        "failed": tasks_exec_result["failed_tasks"],
        "task_results": tasks_exec_result["task_results"]
    })
    
    # 7. 询问测试路径
    if not auto_confirm:
        test_path_result = ask_test_path(workspace_id)
        if test_path_result.get("interaction_required"):
            interactions_required.append({
                "step": "ask_test_path",
                "interaction": test_path_result
            })
            return {
                "success": True,
                "workspace_id": workspace_id,
                "workflow_steps": workflow_steps,
                "interactions_required": interactions_required
            }
        # 等待路径提交...
        test_output_dir = None  # 需要从 submit_test_path 获取
    else:
        # 使用默认路径
        workspace = workspace_manager.get_workspace(workspace_id)
        project_path_obj = Path(workspace["project_path"])
        test_output_dir = str(project_path_obj / "tests" / "mock")
    
    # 8. 生成测试
    tests_result = generate_tests(workspace_id, test_output_dir)
    workflow_steps.append({
        "step": "generate_tests",
        "status": "completed",
        "test_count": tests_result["test_count"]
    })
    
    # 9. 生成覆盖率报告
    workspace = workspace_manager.get_workspace(workspace_id)
    coverage_result = analyze_coverage(workspace_id, workspace["project_path"])
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

**测试用例**：
- `test_execute_full_workflow_auto_confirm` - 测试自动确认模式
- `test_execute_full_workflow_with_interactions` - 测试交互模式
- `test_execute_full_workflow_prd_modify_loop` - 测试PRD修改循环
- `test_execute_full_workflow_trd_modify_loop` - 测试TRD修改循环
- `test_execute_full_workflow_task_review_loop` - 测试任务Review循环
- `test_execute_full_workflow_partial_failure` - 测试部分失败场景

## 文件结构

```
mcp-server/src/tools/
├── orchestrator_questions.py      # 新增：询问4个问题
├── prd_confirmation.py            # 新增：PRD确认和修改
├── trd_confirmation.py            # 新增：TRD确认和修改
├── test_path_question.py          # 新增：询问测试路径
├── task_executor.py               # 新增：任务执行（带循环）
├── workflow_status.py             # 新增：工作流状态查询（多Agent支持）
├── stage_dependency_checker.py    # 新增：状态依赖检查（多Agent支持）
├── workflow_orchestrator.py       # 新增：完整工作流编排
├── prd_generator.py               # 现有：PRD生成（需修改：添加状态检查）
├── trd_generator.py               # 现有：TRD生成（需修改：添加状态检查）
├── task_decomposer.py             # 现有：任务分解（需修改：添加状态检查）
├── code_generator.py              # 现有：代码生成（需修改：添加状态检查）
├── code_reviewer.py               # 现有：代码审查
├── test_generator.py              # 现有：测试生成（需修改：添加状态检查）
├── test_reviewer.py               # 现有：测试审查
└── coverage_analyzer.py           # 现有：覆盖率分析

mcp-server/src/mcp_server.py       # 修改：注册新工具
```

## 实现时间表

### 第1周：用户交互工具

**Day 1-2: orchestrator_questions.py**
- [ ] 实现 `ask_orchestrator_questions`
- [ ] 实现 `submit_orchestrator_answers`
- [ ] 编写单元测试（4个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 3-4: prd_confirmation.py**
- [ ] 实现 `check_prd_confirmation`
- [ ] 实现 `confirm_prd`
- [ ] 实现 `modify_prd`
- [ ] 编写单元测试（5个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 5: trd_confirmation.py**
- [ ] 实现 `check_trd_confirmation`
- [ ] 实现 `confirm_trd`
- [ ] 实现 `modify_trd`
- [ ] 编写单元测试（5个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 6-7: test_path_question.py**
- [ ] 实现 `ask_test_path`
- [ ] 实现 `submit_test_path`
- [ ] 编写单元测试（3个测试用例）
- [ ] 测试覆盖率 >= 90%
- [ ] 集成到 MCP Server

### 第2周：任务执行工具

**Day 1-3: task_executor.py**
- [ ] 实现 `execute_task`（带Review循环）
- [ ] 实现 `execute_all_tasks`
- [ ] 编写单元测试（5个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 4-5: 集成到 MCP Server**
- [ ] 在 `mcp_server.py` 中注册新工具
- [ ] 更新 `list_tools` 函数
- [ ] 更新 `call_tool` 函数
- [ ] 编写集成测试

**Day 6-7: 集成测试和文档**
- [ ] 编写端到端集成测试
- [ ] 修复发现的问题
- [ ] 更新文档

### 第3周：多Agent支持工具

**Day 1-2: workflow_status.py**
- [ ] 实现 `get_workflow_status`
- [ ] 编写单元测试（4个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 3-4: stage_dependency_checker.py**
- [ ] 实现 `check_stage_ready`
- [ ] 定义阶段依赖关系
- [ ] 编写单元测试（5个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 5-6: 修改现有工具添加状态检查**
- [ ] 修改 `trd_generator.py`：添加PRD状态检查
- [ ] 修改 `task_decomposer.py`：添加TRD状态检查
- [ ] 修改 `code_generator.py`：添加任务状态检查
- [ ] 修改 `test_generator.py`：添加代码状态检查
- [ ] 更新相关测试用例

**Day 7: 集成到 MCP Server**
- [ ] 在 `mcp_server.py` 中注册新工具
- [ ] 编写集成测试
- [ ] 更新文档

### 第4周：完整工作流编排

**Day 1-3: workflow_orchestrator.py**
- [ ] 实现 `execute_full_workflow`（自动确认模式）
- [ ] 实现 `execute_full_workflow`（交互模式）
- [ ] 集成工作流状态查询和依赖检查
- [ ] 实现工作流状态管理
- [ ] 编写单元测试（6个测试用例）
- [ ] 测试覆盖率 >= 90%

**Day 4-5: 集成到 MCP Server**
- [ ] 在 `mcp_server.py` 中注册 `execute_full_workflow`
- [ ] 更新文档
- [ ] 编写端到端测试

**Day 6-7: 端到端测试和文档更新**
- [ ] 完整工作流端到端测试（单Agent模式）
- [ ] 多Agent并行测试
- [ ] 修复发现的问题
- [ ] 更新所有相关文档
- [ ] 代码审查和优化

## 测试计划

### 单元测试

每个新工具都需要：
- 成功场景测试
- 错误场景测试
- 边界条件测试
- 覆盖率 >= 90%

### 集成测试

1. **用户交互流程测试**
   - 询问4个问题 → 提交答案 → 创建工作区
   - PRD生成 → 确认 → 继续
   - PRD生成 → 修改 → 重新生成 → 确认

2. **任务执行流程测试**
   - 单个任务执行（Review通过）
   - 单个任务执行（Review失败重试）
   - 所有任务循环执行

3. **多Agent并行测试**
   - Agent A 生成PRD → Agent B 查询状态 → Agent B 生成TRD
   - Agent C 分解任务 → Agent D, E, F 并行处理不同任务
   - 验证状态依赖检查正常工作
   - 验证文件锁确保并发安全

4. **完整工作流测试**
   - 自动确认模式（端到端）
   - 交互模式（端到端）
   - PRD修改循环
   - TRD修改循环
   - 任务Review循环

### 端到端测试

1. **完整工作流自动确认模式**
   ```python
   result = execute_full_workflow(
       project_path="/path/to/project",
       requirement_name="用户认证功能",
       requirement_url="https://example.com/req.md",
       auto_confirm=True
   )
   assert result["success"] is True
   assert len(result["workflow_steps"]) == 11
   ```

2. **完整工作流交互模式**
   - 模拟用户交互
   - 验证工作流正确暂停和恢复

3. **多Agent并行工作流测试**
   ```python
   # Agent A: 生成PRD
   prd_result = generate_prd(workspace_id, requirement_url)
   
   # Agent B: 查询状态
   status = get_workflow_status(workspace_id)
   assert status["stages"]["prd"]["status"] == "completed"
   assert "trd" in status["next_available_stages"]
   
   # Agent B: 检查是否可以生成TRD
   check_result = check_stage_ready(workspace_id, "trd")
   assert check_result["ready"] is True
   
   # Agent B: 生成TRD
   trd_result = generate_trd(workspace_id, prd_result["prd_path"])
   
   # Agent C, D, E: 并行处理不同任务
   # ...
   ```

## 文档更新计划

### 需要更新的文档

1. **mcp-server/TOOLS.md**
   - 添加8个新工具的说明（6个编排工具 + 2个多Agent支持工具）
   - 添加使用示例
   - 添加多Agent协作示例

2. **mcp-server/CURSOR_INTEGRATION.md**
   - 添加工作流使用示例
   - 添加交互模式说明
   - 添加多Agent协作说明

3. **mcp-server/ARCHITECTURE.md**
   - 添加工作流编排说明
   - 添加多Agent并行支持说明
   - 更新架构图

4. **README.md**
   - 添加完整工作流说明
   - 添加多Agent并行支持说明
   - 更新使用示例

5. **WORKFLOW_GUIDE.md**（新建）
   - 完整工作流使用指南
   - 交互模式说明
   - 多Agent协作指南
   - 常见问题

6. **MULTI_AGENT_GUIDE.md**（新建）
   - 多Agent协作详细指南
   - 工作流状态查询使用
   - 状态依赖检查使用
   - 最佳实践

## 验收标准

### 功能验收

1. ✅ 所有8个新工具都已实现（6个编排工具 + 2个多Agent支持工具）
2. ✅ 所有工具都有单元测试，覆盖率 >= 90%
3. ✅ 完整工作流可以自动执行（`auto_confirm=true`）
4. ✅ 完整工作流支持交互模式（`auto_confirm=false`）
5. ✅ PRD/TRD修改循环正常工作
6. ✅ 任务Review循环正常工作
7. ✅ 工作流状态查询正常工作
8. ✅ 状态依赖检查正常工作
9. ✅ 多Agent并行处理不同任务正常工作
10. ✅ 多Agent顺序完成不同阶段正常工作
11. ✅ 所有集成测试通过
12. ✅ 端到端测试通过
13. ✅ 多Agent并行测试通过

### 代码质量验收

1. ✅ 所有代码遵循 Python 3.9+ 规范
2. ✅ 所有代码有类型提示
3. ✅ 所有代码有文档字符串
4. ✅ 代码通过 black、ruff、mypy 检查
5. ✅ 测试覆盖率 >= 90%

### 文档验收

1. ✅ 所有文档已更新
2. ✅ 使用示例清晰完整
3. ✅ 架构说明准确

## 风险与应对

### 风险1：交互模式实现复杂

**风险**：MCP Server 通过 stdio 通信，无法直接与用户交互

**应对**：
- 使用"交互请求 + 提交工具"模式
- Agent 处理交互，调用提交工具
- 工作流状态保存在工作区元数据中

### 风险2：工作流状态管理复杂

**风险**：工作流中断和恢复需要复杂的状态管理

**应对**：
- 使用 `workspace.json` 的 `workflow_state` 字段
- 每个步骤完成后更新状态
- 支持从任意步骤恢复

### 风险3：循环逻辑复杂

**风险**：PRD/TRD修改循环、Review循环逻辑复杂

**应对**：
- 使用最大重试次数限制
- 清晰的循环终止条件
- 完善的日志记录

## 后续优化

### 短期优化（第4周）

1. 工作流恢复机制
2. 工作流进度查询工具
3. 工作流取消工具

### 中期优化（第5-6周）

1. 工作流模板支持
2. 自定义工作流步骤
3. 工作流性能优化

### 长期优化（第7周+）

1. 工作流可视化
2. 工作流历史记录
3. 工作流分析报告

## 多Agent并行支持

### 新增功能

1. **工作流状态查询工具** (`workflow_status.py`)
   - 查询各阶段完成情况
   - 标识可以开始的阶段和被阻塞的阶段
   - 计算工作流进度百分比

2. **状态依赖检查工具** (`stage_dependency_checker.py`)
   - 检查阶段是否可以开始
   - 验证前置阶段依赖
   - 返回详细的依赖信息

3. **现有工具状态检查增强**
   - `trd_generator.py`：检查PRD状态
   - `task_decomposer.py`：检查TRD状态
   - `code_generator.py`：检查任务状态
   - `test_generator.py`：检查代码状态

### 多Agent协作流程

```
Agent A: 生成PRD
  ↓
Agent B: 查询工作流状态 → 发现PRD已完成 → 检查TRD是否可以开始 → 生成TRD
  ↓
Agent C: 查询工作流状态 → 发现TRD已完成 → 检查任务分解是否可以开始 → 分解任务
  ↓
Agent D, E, F: 并行处理不同任务（文件锁确保安全）
  ↓
Agent G: 查询工作流状态 → 发现所有任务已完成 → 生成测试
```

### 支持场景

1. ✅ **不同阶段由不同Agent顺序完成**
   - Agent A → PRD
   - Agent B → TRD
   - Agent C → 任务分解
   - Agent D, E, F → 并行处理任务

2. ✅ **不同任务由不同Agent并行处理**
   - 文件锁确保并发安全
   - 状态查询确保协调

3. ✅ **状态依赖检查防止错误执行**
   - 前置阶段未完成时，无法开始下一阶段
   - 清晰的错误提示

## 总结

本工作计划涵盖了从用户交互到完整工作流编排的所有功能实现，**预计4周完成**。每个阶段都有明确的目标、实现细节、测试计划和验收标准。**新增了多Agent并行支持功能**，使系统能够支持多个Agent协作完成整个开发流程。按照此计划执行，可以确保实现完整、可靠、支持多Agent并行的工作流编排工具。
