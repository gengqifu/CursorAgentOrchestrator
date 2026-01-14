# 新增功能与现有 Skill 的关系分析

## 问题

新增的工作流编排功能（如PRD确认和修改循环）与现有的8个SKILL工具之间是什么关系？这些功能是否应该从属于某个skill？是否会重复触发某个skill？

## 当前架构

### 8个核心SKILL工具

1. `prd-generator` - PRD生成
2. `trd-generator` - TRD生成
3. `task-decomposer` - 任务分解
4. `code-generator` - 代码生成
5. `code-reviewer` - 代码审查
6. `test-generator` - 测试生成
7. `test-reviewer` - 测试审查
8. `coverage-analyzer` - 覆盖率分析

### 新增的工作流编排工具

1. `orchestrator_questions` - 询问4个问题
2. `prd_confirmation` - PRD确认和修改循环
3. `trd_confirmation` - TRD确认和修改循环
4. `test_path_question` - 询问测试路径
5. `task_executor` - 任务执行（带Review循环）
6. `workflow_orchestrator` - 完整工作流编排

## 关系分析

### 1. PRD确认和修改循环 vs prd-generator

**问题**：`prd_confirmation` 与 `prd-generator` 是什么关系？

**分析**：

```
prd-generator (SKILL)
├── 职责：生成PRD文档
├── 输入：workspace_id, requirement_url
└── 输出：prd_path

prd_confirmation (编排工具)
├── 职责：工作流编排逻辑
├── 功能：
│   ├── 检查PRD是否需要确认
│   ├── 确认PRD（标记为已确认）
│   └── 标记需要修改PRD（触发重新生成）
└── 关系：会调用 prd-generator（如果需要修改）
```

**结论**：
- `prd-generator` 是**业务逻辑层**：负责PRD生成的核心逻辑
- `prd_confirmation` 是**编排层**：负责工作流编排，包括确认和修改循环
- **关系**：`prd_confirmation` 会**调用** `prd-generator`，但**不属于** `prd-generator`

**流程**：
```
用户 → prd_confirmation.check_prd_confirmation()
  ↓
返回交互请求（需要确认PRD）
  ↓
用户选择"修改" → prd_confirmation.modify_prd()
  ↓
工作流编排器 → prd-generator.generate_prd()  // 重新生成
  ↓
循环回到 prd_confirmation.check_prd_confirmation()
```

### 2. 任务执行循环 vs code-generator 和 code-reviewer

**问题**：`task_executor` 与 `code-generator`、`code-reviewer` 是什么关系？

**分析**：

```
code-generator (SKILL)
├── 职责：生成代码
└── 输出：code_files

code-reviewer (SKILL)
├── 职责：审查代码
└── 输出：passed, review_report

task_executor (编排工具)
├── 职责：任务执行编排
├── 功能：
│   ├── 调用 code-generator
│   ├── 调用 code-reviewer
│   ├── 判断Review是否通过
│   └── 如果未通过，循环回到 code-generator
└── 关系：会调用 code-generator 和 code-reviewer
```

**结论**：
- `code-generator` 和 `code-reviewer` 是**业务逻辑层**
- `task_executor` 是**编排层**：负责任务执行的编排逻辑
- **关系**：`task_executor` 会**调用** `code-generator` 和 `code-reviewer`，但**不属于**它们

### 3. 完整工作流编排 vs 所有SKILL工具

**问题**：`workflow_orchestrator` 与所有SKILL工具的关系？

**分析**：

```
workflow_orchestrator (高级编排工具)
├── 职责：完整工作流编排
├── 功能：
│   ├── 协调所有步骤
│   ├── 调用各个SKILL工具
│   ├── 调用编排工具（确认、循环等）
│   └── 管理工作流状态
└── 关系：会调用所有SKILL工具和编排工具
```

**结论**：
- `workflow_orchestrator` 是**最高层编排**：协调所有工具
- 所有SKILL工具是**业务逻辑层**：提供核心功能
- 编排工具（确认、循环等）是**中间层编排**：处理特定步骤的编排

## 架构层次

### 三层架构

```
┌─────────────────────────────────────────┐
│  工作流编排层 (Workflow Orchestration)   │
│  - workflow_orchestrator               │
│  - prd_confirmation                    │
│  - trd_confirmation                    │
│  - task_executor                       │
│  - orchestrator_questions              │
│  - test_path_question                  │
└──────────────────┬──────────────────────┘
                   │ 调用
┌──────────────────▼──────────────────────┐
│  SKILL工具层 (Business Logic)           │
│  - prd-generator                        │
│  - trd-generator                        │
│  - task-decomposer                      │
│  - code-generator                       │
│  - code-reviewer                        │
│  - test-generator                       │
│  - test-reviewer                        │
│  - coverage-analyzer                    │
└──────────────────┬──────────────────────┘
                   │ 使用
┌──────────────────▼──────────────────────┐
│  基础设施层 (Infrastructure)            │
│  - WorkspaceManager                     │
│  - TaskManager                         │
│  - Config                              │
│  - Logger                              │
└─────────────────────────────────────────┘
```

## 设计原则

### 1. 职责分离原则

- **SKILL工具**：专注于单一业务功能（生成、审查、分析）
- **编排工具**：专注于工作流编排（确认、循环、协调）
- **工作流编排器**：专注于整体流程协调

### 2. 调用关系

```
编排工具 → SKILL工具 → 基础设施
```

- 编排工具**调用**SKILL工具，但不**包含**SKILL工具
- SKILL工具保持独立，可以被多个编排工具调用

### 3. 不会重复触发

- 编排工具通过**调用**SKILL工具来实现功能
- 不会重复实现SKILL工具的逻辑
- 例如：`prd_confirmation.modify_prd()` 会调用 `prd-generator.generate_prd()`，而不是重新实现PRD生成逻辑

## 具体关系示例

### 示例1：PRD确认和修改循环

```python
# 编排工具：prd_confirmation.py
def modify_prd(workspace_id: str) -> dict:
    """标记需要修改PRD，触发重新生成。"""
    # 1. 更新工作区状态
    workspace_manager.update_workspace_status(
        workspace_id,
        {"prd_status": "needs_regeneration"}
    )
    
    # 2. 返回修改标记
    return {
        "success": True,
        "action": "modify",
        "next_step": "generate_prd"  # 提示工作流编排器调用 prd-generator
    }

# 工作流编排器：workflow_orchestrator.py
def execute_full_workflow(...):
    # ...
    while prd_retry < max_prd_retries:
        # 调用 SKILL 工具生成PRD
        prd_result = generate_prd(workspace_id, requirement_url)  # 调用 prd-generator
        
        # 调用编排工具检查确认
        confirm_result = check_prd_confirmation(workspace_id)  # 调用 prd_confirmation
        
        if confirm_result.get("action") == "modify":
            modify_prd(workspace_id)  # 调用 prd_confirmation
            prd_retry += 1
            continue  # 循环回到 generate_prd
        elif confirm_result.get("action") == "confirm":
            break  # 继续下一步
```

### 示例2：任务执行循环

```python
# 编排工具：task_executor.py
def execute_task(workspace_id: str, task_id: str, max_review_retries: int = 3) -> dict:
    """执行单个任务（带Review循环）。"""
    retry_count = 0
    
    while retry_count < max_review_retries:
        # 调用 SKILL 工具生成代码
        code_result = generate_code(workspace_id, task_id)  # 调用 code-generator
        
        # 调用 SKILL 工具审查代码
        review_result = review_code(workspace_id, task_id)  # 调用 code-reviewer
        
        # 编排逻辑：判断是否通过
        if review_result["passed"]:
            return {"success": True, "status": "completed"}
        
        retry_count += 1
    
    return {"success": True, "status": "needs_fix"}
```

## 结论

### 1. 新增功能不属于任何SKILL

- 这些功能是**工作流编排层**的工具
- 它们**调用**SKILL工具，但不**属于**SKILL工具
- SKILL工具保持独立和可复用

### 2. 不会重复触发，而是调用

- `prd_confirmation` 不会重新实现PRD生成逻辑
- 它会**调用** `prd-generator.generate_prd()` 来重新生成
- 同样，`task_executor` 会**调用** `code-generator` 和 `code-reviewer`

### 3. 清晰的层次结构

```
工作流编排层（新增）
    ↓ 调用
SKILL工具层（现有）
    ↓ 使用
基础设施层（现有）
```

### 4. 设计优势

- ✅ **职责清晰**：每个工具只负责自己的职责
- ✅ **可复用**：SKILL工具可以被多个编排工具调用
- ✅ **可测试**：每层都可以独立测试
- ✅ **可扩展**：可以添加新的编排工具而不影响SKILL工具

## 建议

### 1. 保持当前设计

当前的设计（编排工具调用SKILL工具）是正确的，应该保持。

### 2. 明确调用关系

在文档中明确说明：
- 编排工具**调用**SKILL工具
- SKILL工具是**被调用**的，不是**被包含**的

### 3. 避免重复实现

确保编排工具不重复实现SKILL工具的逻辑，而是通过调用实现。

### 4. 文档更新

在实现计划中明确：
- 每个编排工具会调用哪些SKILL工具
- 调用时机和条件
- 数据流转关系

## 更新后的实现计划

### orchestrator_questions.py
- **不调用任何SKILL工具**
- 独立功能：询问问题和创建工作区

### prd_confirmation.py
- **会触发调用** `prd-generator.generate_prd()`（当需要修改时）
- 不包含PRD生成逻辑

### trd_confirmation.py
- **会触发调用** `trd-generator.generate_trd()`（当需要修改时）
- 不包含TRD生成逻辑

### task_executor.py
- **会调用** `code-generator.generate_code()`
- **会调用** `code-reviewer.review_code()`
- 不包含代码生成和审查逻辑

### workflow_orchestrator.py
- **会调用**所有SKILL工具
- **会调用**所有编排工具
- 协调整个工作流

## 总结

新增的工作流编排功能**不属于任何SKILL**，它们是**独立的编排层工具**。它们会**调用**SKILL工具来实现功能，但不会**重复实现**SKILL工具的逻辑。这种设计符合职责分离原则，保持了架构的清晰性和可维护性。
