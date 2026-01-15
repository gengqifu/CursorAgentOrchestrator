# 多Agent协作指南

本指南介绍如何使用多个Agent协作完成开发流程。

## 概述

Agent Orchestrator 支持多个独立的Agent协作完成从PRD生成到测试完成的整个开发流程。通过工作流状态查询、阶段依赖检查和文件锁机制，确保多Agent协作的安全性和协调性。

## 核心机制

### 1. 工作流状态查询

`get_workflow_status` 工具提供完整的工作流状态信息：

- **各阶段状态**：每个阶段（PRD、TRD、任务分解、代码生成、测试生成、覆盖率分析）的当前状态
- **可开始的阶段**：基于依赖关系，识别可以开始的阶段
- **被阻塞的阶段**：前置依赖未完成，无法开始的阶段
- **工作流进度**：已完成阶段数和进度百分比

### 2. 阶段依赖检查

`check_stage_ready` 工具检查指定阶段是否可以开始：

- **前置阶段验证**：检查所有前置阶段是否已完成
- **文件依赖验证**：检查必需的文件是否存在
- **详细状态信息**：提供已完成、待完成、进行中的前置阶段列表

### 3. 文件锁机制

文件锁确保并发访问的安全性：

- **原子更新**：工作区元数据的更新是原子的
- **并发安全**：多个Agent同时更新不同状态字段时，不会导致数据损坏
- **状态一致性**：确保所有Agent看到一致的工作区状态

## 阶段依赖关系

```
PRD (无前置依赖)
  ↓
TRD (依赖 PRD 完成)
  ↓
任务分解 (依赖 TRD 完成)
  ↓
代码生成 (依赖 任务分解 完成)
  ↓
测试生成 (依赖 所有任务完成)
  ↓
覆盖率分析 (依赖 测试生成 完成)
```

## 使用场景

### 场景1：不同阶段由不同Agent顺序完成

**适用场景**：不同Agent负责不同的开发阶段

**工作流程**：

```bash
# Agent A: 生成 PRD
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req
@agent-orchestrator confirm_prd workspace_id=req-xxx

# Agent B: 查询工作流状态
@agent-orchestrator get_workflow_status workspace_id=req-xxx
# 返回: next_available_stages: ["trd"], blocked_stages: ["tasks", "code", "test", "coverage"]

# Agent B: 检查 TRD 是否可以开始
@agent-orchestrator check_stage_ready workspace_id=req-xxx stage=trd
# 返回: ready: true, reason: "前置阶段已完成，可以开始"

# Agent B: 生成 TRD
@agent-orchestrator generate_trd workspace_id=req-xxx
@agent-orchestrator confirm_trd workspace_id=req-xxx

# Agent C: 查询工作流状态
@agent-orchestrator get_workflow_status workspace_id=req-xxx
# 返回: next_available_stages: ["tasks"], blocked_stages: ["code", "test", "coverage"]

# Agent C: 分解任务
@agent-orchestrator decompose_tasks workspace_id=req-xxx
```

**优势**：
- 不同Agent可以专注于自己擅长的阶段
- 通过状态查询实现协调
- 依赖检查防止错误执行

### 场景2：不同任务由不同Agent并行处理

**适用场景**：任务分解后，多个Agent并行处理不同任务

**工作流程**：

```bash
# Agent C: 分解任务（创建3个任务）
@agent-orchestrator decompose_tasks workspace_id=req-xxx

# Agent D, E, F: 并行处理不同任务
# Agent D
@agent-orchestrator generate_code workspace_id=req-xxx task_id=task-001

# Agent E
@agent-orchestrator generate_code workspace_id=req-xxx task_id=task-002

# Agent F
@agent-orchestrator generate_code workspace_id=req-xxx task_id=task-003
```

**优势**：
- 提高开发效率，多个任务并行处理
- 文件锁确保并发安全
- 每个Agent独立处理自己的任务

### 场景3：状态依赖检查防止错误执行

**适用场景**：确保前置阶段完成后再执行下一阶段

**工作流程**：

```bash
# Agent A: 生成 PRD（但未确认）
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req

# Agent B: 尝试生成 TRD（应该失败）
@agent-orchestrator generate_trd workspace_id=req-xxx
# 返回: success: false, error: "PRD尚未完成，无法生成TRD。请先完成PRD生成。"

# Agent A: 确认 PRD
@agent-orchestrator confirm_prd workspace_id=req-xxx

# Agent B: 再次尝试生成 TRD（应该成功）
@agent-orchestrator generate_trd workspace_id=req-xxx
# 返回: success: true, trd_path: "..."
```

**优势**：
- 防止前置阶段未完成时错误执行下一阶段
- 清晰的错误提示
- 确保工作流的正确顺序

## 最佳实践

### 1. 执行前检查状态

在执行任何阶段前，先查询工作流状态或检查阶段依赖：

```bash
# 方式1：查询完整工作流状态
@agent-orchestrator get_workflow_status workspace_id=req-xxx

# 方式2：检查特定阶段是否可以开始
@agent-orchestrator check_stage_ready workspace_id=req-xxx stage=trd
```

### 2. 使用状态查询进行协调

多Agent协作时，定期查询工作流状态，了解当前进度和可执行的阶段：

```bash
# 查询工作流状态
@agent-orchestrator get_workflow_status workspace_id=req-xxx

# 根据返回的 next_available_stages 决定下一步操作
# 如果 "trd" 在 next_available_stages 中，则可以开始生成 TRD
```

### 3. 处理被阻塞的阶段

如果阶段被阻塞，检查阻塞原因：

```bash
# 查询工作流状态
@agent-orchestrator get_workflow_status workspace_id=req-xxx
# 返回: blocked_stages: ["tasks", "code", "test", "coverage"]

# 检查被阻塞的阶段
@agent-orchestrator check_stage_ready workspace_id=req-xxx stage=tasks
# 返回: ready: false, reason: "前置阶段未完成: trd"
```

### 4. 并行处理任务时的注意事项

- 每个Agent处理不同的任务ID，避免冲突
- 文件锁会自动处理并发更新
- 定期查询任务状态，了解整体进度

## 工具参考

### get_workflow_status

**功能**：获取工作流状态

**输入**：
- `workspace_id`: 工作区ID

**输出示例**：
```json
{
  "success": true,
  "workspace_id": "req-xxx",
  "stages": {
    "prd": {
      "status": "completed",
      "file": "/path/to/PRD.md",
      "ready": true
    },
    "trd": {
      "status": "pending",
      "file": null,
      "ready": true
    },
    "tasks": {
      "status": "pending",
      "file": null,
      "task_count": 0,
      "ready": false
    }
  },
  "next_available_stages": ["trd"],
  "blocked_stages": ["tasks", "code", "test", "coverage"],
  "workflow_progress": {
    "completed_stages": 1,
    "total_stages": 6,
    "progress_percentage": 16.67
  }
}
```

### check_stage_ready

**功能**：检查阶段是否可以开始

**输入**：
- `workspace_id`: 工作区ID
- `stage`: 阶段名称（"prd", "trd", "tasks", "code", "test", "coverage"）

**输出示例**：
```json
{
  "success": true,
  "stage": "trd",
  "ready": true,
  "reason": "前置阶段已完成，可以开始",
  "required_stages": ["prd"],
  "completed_stages": ["prd"],
  "pending_stages": [],
  "in_progress_stages": [],
  "file_ready": true
}
```

## 测试

多Agent协作功能已通过完整的集成测试验证：

- `test_multi_agent_prd_to_trd_workflow` - PRD到TRD工作流测试
- `test_multi_agent_parallel_task_execution` - 并行任务执行测试
- `test_multi_agent_state_dependency_check` - 状态依赖检查测试
- `test_multi_agent_file_lock_concurrency` - 文件锁并发安全测试

运行测试：

```bash
cd mcp-server
source venv/bin/activate
python3 -m pytest tests/test_mcp_server.py -k "multi_agent" -v
```

## 常见问题

### Q: 多个Agent同时更新工作区状态会冲突吗？

A: 不会。文件锁机制确保并发更新的安全性。多个Agent可以同时更新不同的状态字段，系统会序列化这些更新，确保数据一致性。

### Q: 如何知道当前可以执行哪个阶段？

A: 使用 `get_workflow_status` 查询工作流状态，返回的 `next_available_stages` 列表包含所有可以开始的阶段。

### Q: 如果前置阶段未完成，会怎样？

A: 如果尝试执行一个前置阶段未完成的阶段，系统会返回错误，提示需要先完成前置阶段。例如，如果PRD未完成，尝试生成TRD会返回 "PRD尚未完成，无法生成TRD"。

### Q: 多个Agent可以并行处理同一个任务吗？

A: 不建议。虽然文件锁会确保数据安全，但多个Agent处理同一个任务可能导致重复工作。建议每个Agent处理不同的任务ID。

## 相关文档

- [TOOLS.md](TOOLS.md) - 完整工具列表和说明
- [README.md](README.md) - 项目概述和安装说明
- [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md) - Cursor IDE 集成指南
