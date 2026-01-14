# 多 Agent 并行支持分析

## 问题

对于一个需求，从PRD生成到测试完成，是否支持各阶段任务在分别在独立agent完成？

## 当前实现分析

### 1. 工作流阶段

```
1. PRD生成 (prd-generator)
2. TRD生成 (trd-generator)
3. 任务分解 (task-decomposer)
4. 代码生成 (code-generator) - 多个任务
5. 代码审查 (code-reviewer) - 多个任务
6. 测试生成 (test-generator)
7. 测试审查 (test-reviewer)
8. 覆盖率分析 (coverage-analyzer)
```

### 2. 状态管理

工作区状态字段：
```json
{
  "status": {
    "prd_status": "pending" | "completed",
    "trd_status": "pending" | "completed",
    "tasks_status": "pending" | "completed",
    "code_status": "pending" | "in_progress" | "completed",
    "test_status": "pending" | "completed"
  }
}
```

### 3. 依赖关系

#### 阶段依赖

| 阶段 | 前置条件 | 检查方式 |
|------|---------|---------|
| PRD生成 | 工作区存在 | ✅ 检查 workspace.json |
| TRD生成 | PRD文件存在 | ✅ 检查 PRD.md 文件 |
| 任务分解 | TRD文件存在 | ✅ 检查 TRD.md 文件 |
| 代码生成 | 任务存在 | ✅ 检查 tasks.json |
| 代码审查 | 代码文件存在 | ✅ 检查任务中的 code_files |
| 测试生成 | 任务完成 | ✅ 检查任务状态 |
| 测试审查 | 测试文件存在 | ✅ 检查测试文件 |
| 覆盖率分析 | 测试存在 | ⚠️ 未明确检查 |

#### 状态依赖（当前未强制）

| 阶段 | 应该检查的前置状态 | 当前实现 |
|------|------------------|---------|
| TRD生成 | `prd_status == "completed"` | ❌ 只检查文件存在 |
| 任务分解 | `trd_status == "completed"` | ❌ 只检查文件存在 |
| 代码生成 | `tasks_status == "completed"` | ❌ 只检查任务存在 |
| 测试生成 | `code_status == "completed"` | ⚠️ 检查任务状态，但不检查 code_status |

## 多 Agent 并行支持情况

### ✅ 完全支持的场景

#### 1. 不同阶段由不同 Agent 完成（顺序执行）

```
Agent A (Cursor Terminal 1):
  1. 创建工作区
  2. 生成PRD
  3. 更新 prd_status: "completed"

Agent B (Cursor Terminal 2):
  1. 读取工作区（读锁，安全）
  2. 检查 PRD.md 存在
  3. 生成TRD
  4. 更新 trd_status: "completed"

Agent C (Cursor Terminal 3):
  1. 读取工作区（读锁，安全）
  2. 检查 TRD.md 存在
  3. 分解任务
  4. 更新 tasks_status: "completed"
```

**支持情况**：✅ **完全支持**
- 文件锁确保并发安全
- 每个阶段检查文件存在，不强制检查状态
- 不同Agent可以顺序完成不同阶段

#### 2. 不同任务由不同 Agent 并行完成

```
Agent D (Cursor Terminal 4):
  - 处理 task-001（代码生成 + Review）

Agent E (Cursor Terminal 5):
  - 处理 task-002（代码生成 + Review）

Agent F (Cursor Terminal 6):
  - 处理 task-003（代码生成 + Review）
```

**支持情况**：✅ **完全支持**
- 文件锁确保 tasks.json 的原子更新
- 不同任务可以并行处理
- 每个Agent更新自己的任务状态

### ⚠️ 部分支持的场景

#### 1. 同一阶段由多个 Agent 并行完成

```
Agent A 和 Agent B 同时生成PRD：
  - 都会更新 workspace.json
  - 文件锁会序列化执行
  - 后执行的会覆盖先执行的
```

**支持情况**：⚠️ **部分支持（会序列化）**
- 文件锁确保不会数据损坏
- 但后执行的会覆盖先执行的
- 需要协调机制避免冲突

#### 2. 前置阶段未完成时开始下一阶段

```
Agent A 正在生成PRD（prd_status: "pending"）
Agent B 尝试生成TRD：
  - 如果PRD文件已生成 → ✅ 可以执行
  - 如果PRD文件未生成 → ❌ 会失败
```

**支持情况**：⚠️ **部分支持（有风险）**
- 当前实现只检查文件存在，不检查状态
- 如果文件正在生成中，可能会读取到不完整文件
- 需要状态检查机制

### ❌ 不支持的场景

#### 1. 没有状态依赖检查

当前实现**不强制**检查前置阶段的状态：

```python
# trd_generator.py - 当前实现
def generate_trd(workspace_id: str, prd_path: str) -> dict:
    # 只检查文件存在
    prd_file = Path(prd_path)
    if not prd_file.exists():
        raise ValidationError(f"PRD 文件不存在: {prd_path}")
    
    # ❌ 没有检查 prd_status == "completed"
    # ❌ 没有检查 PRD 是否正在生成中
```

**问题**：
- 如果PRD正在生成中，TRD生成可能会读取到不完整的PRD
- 没有明确的状态依赖，Agent无法知道何时可以开始下一阶段

#### 2. 没有工作流状态查询工具

当前没有工具可以查询：
- 当前工作流进度
- 哪些阶段已完成
- 哪些阶段可以进行
- 哪些阶段需要等待

## 多 Agent 协作流程示例

### 理想的多 Agent 协作流程

```
时间线：

T1: Agent A 创建并开始生成PRD
    - workspace.json: prd_status: "pending"

T2: Agent A 完成PRD生成
    - workspace.json: prd_status: "completed"
    - PRD.md 文件已保存

T3: Agent B 查询工作流状态
    - 发现 prd_status: "completed"
    - 开始生成TRD

T4: Agent B 完成TRD生成
    - workspace.json: trd_status: "completed"
    - TRD.md 文件已保存

T5: Agent C 查询工作流状态
    - 发现 trd_status: "completed"
    - 开始分解任务

T6: Agent C 完成任务分解
    - workspace.json: tasks_status: "completed"
    - tasks.json 文件已保存

T7-T9: Agent D, E, F 并行处理不同任务
    - Agent D: task-001
    - Agent E: task-002
    - Agent F: task-003
    - 文件锁确保 tasks.json 的原子更新

T10: Agent G 查询工作流状态
     - 发现所有任务已完成
     - 开始生成测试
```

### 当前实现的问题

1. **缺少状态查询工具**
   - Agent无法查询当前工作流进度
   - Agent无法知道何时可以开始下一阶段

2. **缺少状态依赖检查**
   - 不强制检查前置阶段状态
   - 可能在前置阶段未完成时开始下一阶段

3. **缺少工作流协调机制**
   - 没有"等待前置步骤完成"的机制
   - 没有"通知下一阶段可以开始"的机制

## 支持情况总结

### ✅ 当前已支持

1. **文件锁机制**：确保并发安全
2. **不同任务并行**：支持多个Agent并行处理不同任务
3. **顺序阶段执行**：支持不同Agent顺序完成不同阶段（如果手动协调）

### ⚠️ 部分支持

1. **同一阶段并行**：会序列化，后执行的会覆盖先执行的
2. **状态检查**：只检查文件存在，不强制检查状态

### ❌ 不支持

1. **工作流状态查询**：没有工具查询当前进度
2. **状态依赖检查**：不强制检查前置阶段状态
3. **工作流协调**：没有自动协调机制

## 改进建议

### 1. 添加工作流状态查询工具

```python
def get_workflow_status(workspace_id: str) -> dict:
    """获取工作流状态。
    
    Returns:
        {
            "workspace_id": "req-xxx",
            "stages": {
                "prd": {"status": "completed", "file": "PRD.md"},
                "trd": {"status": "completed", "file": "TRD.md"},
                "tasks": {"status": "completed", "count": 5},
                "code": {"status": "in_progress", "completed": 2, "total": 5},
                "test": {"status": "pending"}
            },
            "next_available_stages": ["code", "test"],  # 可以开始的阶段
            "blocked_stages": []  # 被阻塞的阶段
        }
    """
```

### 2. 添加状态依赖检查

```python
def check_stage_ready(workspace_id: str, stage: str) -> dict:
    """检查阶段是否可以开始。
    
    Args:
        workspace_id: 工作区ID
        stage: 阶段名称（"trd", "tasks", "code", "test"）
    
    Returns:
        {
            "ready": True/False,
            "reason": "前置阶段已完成" / "前置阶段未完成",
            "required_stages": ["prd"],  # 需要的前置阶段
            "completed_stages": ["prd"]  # 已完成的前置阶段
        }
    """
```

### 3. 添加阶段状态更新工具

```python
def mark_stage_in_progress(workspace_id: str, stage: str) -> dict:
    """标记阶段为进行中。
    
    防止多个Agent同时开始同一阶段。
    """
    
def mark_stage_completed(workspace_id: str, stage: str) -> dict:
    """标记阶段为已完成。
    
    通知其他Agent可以开始下一阶段。
    """
```

### 4. 在工具中添加状态检查

```python
# trd_generator.py
def generate_trd(workspace_id: str, prd_path: str) -> dict:
    # 检查PRD状态
    workspace = workspace_manager.get_workspace(workspace_id)
    if workspace["status"]["prd_status"] != "completed":
        raise ValidationError("PRD尚未完成，无法生成TRD")
    
    # 检查PRD文件存在
    prd_file = Path(prd_path)
    if not prd_file.exists():
        raise ValidationError(f"PRD 文件不存在: {prd_path}")
    
    # 标记TRD为进行中
    workspace_manager.update_workspace_status(
        workspace_id,
        {"trd_status": "in_progress"}
    )
    
    # ... 生成TRD ...
    
    # 标记TRD为已完成
    workspace_manager.update_workspace_status(
        workspace_id,
        {"trd_status": "completed"}
    )
```

## 结论

### 当前支持情况

**✅ 支持**：
- 不同Agent顺序完成不同阶段（如果手动协调）
- 不同Agent并行处理不同任务
- 文件锁确保并发安全

**⚠️ 部分支持**：
- 同一阶段并行（会序列化）
- 状态检查（只检查文件，不检查状态）

**❌ 不支持**：
- 工作流状态查询
- 状态依赖检查
- 工作流协调机制

### 建议

要实现完整的多Agent并行支持，需要：

1. **添加工作流状态查询工具**（优先级：高）
2. **添加状态依赖检查**（优先级：高）
3. **在工具中添加状态检查**（优先级：中）
4. **添加阶段状态更新工具**（优先级：中）

这样，多个Agent就可以：
- 查询当前工作流进度
- 知道何时可以开始下一阶段
- 避免在前置阶段未完成时开始下一阶段
- 协调工作流执行
