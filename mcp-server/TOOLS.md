# MCP Server 工具说明

> **注意**：所有工具通过 **MCP Server** 暴露，符合 PDF 文档架构。
> 核心实现在 `mcp-server/src/tools/` 中，通过 `mcp-server/src/mcp_server.py` 统一管理。

## 调用方式

所有工具通过 MCP Server 暴露，在 Cursor IDE 中通过 MCP 协议调用：

### 在 Cursor IDE 中使用

```bash
# 工作流编排工具
@agent-orchestrator ask_orchestrator_questions
@agent-orchestrator submit_orchestrator_answers project_path=/path/to/project requirement_name=用户认证功能 requirement_url=https://example.com/req

# PRD 确认工具
@agent-orchestrator check_prd_confirmation workspace_id=req-xxx
@agent-orchestrator confirm_prd workspace_id=req-xxx
@agent-orchestrator modify_prd workspace_id=req-xxx

# TRD 确认工具
@agent-orchestrator check_trd_confirmation workspace_id=req-xxx
@agent-orchestrator confirm_trd workspace_id=req-xxx
@agent-orchestrator modify_trd workspace_id=req-xxx

# 测试路径询问工具
@agent-orchestrator ask_test_path workspace_id=req-xxx
@agent-orchestrator submit_test_path workspace_id=req-xxx test_path=/path/to/tests/mock

# SKILL 工具
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req
@agent-orchestrator generate_trd workspace_id=req-xxx
@agent-orchestrator decompose_tasks workspace_id=req-xxx
```

### MCP 工具名称

所有工具通过以下 MCP 工具名称调用：

**工作流编排工具**：
- `ask_orchestrator_questions` - 询问4个问题
- `submit_orchestrator_answers` - 提交答案并创建工作区
- `check_prd_confirmation` - 检查 PRD 确认
- `confirm_prd` - 确认 PRD
- `modify_prd` - 修改 PRD
- `check_trd_confirmation` - 检查 TRD 确认
- `confirm_trd` - 确认 TRD
- `modify_trd` - 修改 TRD
- `ask_test_path` - 询问测试路径
- `submit_test_path` - 提交测试路径

**8 个核心 SKILL 工具**：
- `generate_prd` - PRD 生成
- `generate_trd` - TRD 生成
- `decompose_tasks` - 任务分解
- `generate_code` - 代码生成
- `review_code` - 代码审查
- `generate_tests` - 测试生成
- `review_tests` - 测试审查
- `analyze_coverage` - 覆盖率分析

详细调用说明请参考各 skill 的 `SKILL.md` 文档和 [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md)。

## 工具列表

## 工作流编排工具

### 1. 总编排器询问工具 (`orchestrator_questions`)

**功能**: 询问4个问题并创建工作区

**工具**:
- `ask_orchestrator_questions` - 询问4个问题（项目路径、需求名称、需求URL、工作区路径）
- `submit_orchestrator_answers` - 提交答案并创建工作区

**输入** (`submit_orchestrator_answers`):
- `project_path`: 项目路径（必填）
- `requirement_name`: 需求名称（必填）
- `requirement_url`: 需求URL或文件路径（必填）
- `workspace_path`: 工作区路径（可选）

**输出** (`submit_orchestrator_answers`):
- `workspace_id`: 工作区ID
- `success`: 是否成功

**测试文件**: `tests/tools/test_orchestrator_questions.py`

### 2. PRD 确认工具 (`prd_confirmation`)

**功能**: PRD 确认和修改循环

**工具**:
- `check_prd_confirmation` - 检查 PRD 文件是否存在并返回确认请求
- `confirm_prd` - 确认 PRD（更新状态为 completed）
- `modify_prd` - 标记需要修改 PRD（更新状态为 needs_regeneration）

**输入**:
- `workspace_id`: 工作区ID（所有工具都需要）

**输出** (`check_prd_confirmation`):
- `interaction_required`: 是否需要交互
- `interaction_type`: 交互类型（"prd_confirmation"）
- `prd_path`: PRD 文件路径
- `prd_preview`: PRD 预览内容

**输出** (`confirm_prd` / `modify_prd`):
- `success`: 是否成功
- `workspace_id`: 工作区ID

**测试文件**: `tests/tools/test_prd_confirmation.py`

### 3. TRD 确认工具 (`trd_confirmation`)

**功能**: TRD 确认和修改循环

**工具**:
- `check_trd_confirmation` - 检查 TRD 文件是否存在并返回确认请求
- `confirm_trd` - 确认 TRD（更新状态为 completed）
- `modify_trd` - 标记需要修改 TRD（更新状态为 needs_regeneration）

**输入**:
- `workspace_id`: 工作区ID（所有工具都需要）

**输出** (`check_trd_confirmation`):
- `interaction_required`: 是否需要交互
- `interaction_type`: 交互类型（"trd_confirmation"）
- `trd_path`: TRD 文件路径
- `trd_preview`: TRD 预览内容

**输出** (`confirm_trd` / `modify_trd`):
- `success`: 是否成功
- `workspace_id`: 工作区ID

**测试文件**: `tests/tools/test_trd_confirmation.py`

### 4. 测试路径询问工具 (`test_path_question`)

**功能**: 询问测试路径并保存到工作区元数据

**工具**:
- `ask_test_path` - 询问测试路径（生成默认路径建议）
- `submit_test_path` - 提交测试路径并保存到工作区元数据

**输入** (`ask_test_path`):
- `workspace_id`: 工作区ID

**输入** (`submit_test_path`):
- `workspace_id`: 工作区ID
- `test_path`: 测试输出目录路径

**输出** (`ask_test_path`):
- `interaction_required`: 是否需要交互
- `interaction_type`: 交互类型（"question"）
- `question`: 问题信息（包含默认路径建议）

**输出** (`submit_test_path`):
- `success`: 是否成功
- `workspace_id`: 工作区ID
- `test_path`: 保存的测试路径

**测试文件**: `tests/tools/test_test_path_question.py`

## 8 个核心 SKILL 工具

### 1. PRD 生成工具 (`prd_generator`)

**功能**: 根据需求URL生成标准化的PRD文档

**输入**:
- `workspace_id`: 工作区ID
- `requirement_url`: 需求文档URL或文件路径

**输出**:
- `prd_path`: PRD文档路径
- `success`: 是否成功

**测试文件**: `tests/tools/test_prd_generator.py`

### 2. TRD 生成工具 (`trd_generator`)

**功能**: 根据PRD文档生成详细的技术设计文档(TRD)

**输入**:
- `workspace_id`: 工作区ID
- `prd_path`: PRD文档路径

**输出**:
- `trd_path`: TRD文档路径
- `success`: 是否成功

**测试文件**: `tests/tools/test_trd_generator.py`

### 3. 任务分解工具 (`task_decomposer`)

**功能**: 将TRD文档分解为独立的开发任务

**输入**:
- `workspace_id`: 工作区ID
- `trd_path`: TRD文档路径

**输出**:
- `tasks_json_path`: tasks.json文件路径
- `task_count`: 任务数量
- `success`: 是否成功

**测试文件**: `tests/tools/test_task_decomposer.py`

### 4. 代码生成工具 (`code_generator`)

**功能**: 根据任务描述生成功能代码和测试

**输入**:
- `workspace_id`: 工作区ID
- `task_id`: 任务ID

**输出**:
- `code_files`: 生成的代码文件路径列表
- `task_id`: 任务ID
- `success`: 是否成功

**测试文件**: `tests/tools/test_code_generator.py`

### 5. 代码审查工具 (`code_reviewer`)

**功能**: 使用 Gemini 审查代码质量

**输入**:
- `workspace_id`: 工作区ID
- `task_id`: 任务ID

**输出**:
- `passed`: 是否通过审查
- `review_report`: 审查报告
- `success`: 是否成功

**测试文件**: `tests/tools/test_code_reviewer.py`

### 6. 测试生成工具 (`test_generator`)

**功能**: 生成Mock测试和集成测试

**输入**:
- `workspace_id`: 工作区ID
- `test_output_dir`: 测试输出目录

**输出**:
- `test_files`: 测试文件路径列表
- `test_count`: 测试文件数量
- `success`: 是否成功

**测试文件**: `tests/tools/test_test_generator.py`

### 7. 测试审查工具 (`test_reviewer`)

**功能**: 审查测试代码质量

**输入**:
- `workspace_id`: 工作区ID
- `test_files`: 测试文件路径列表

**输出**:
- `passed`: 是否通过审查
- `review_report`: 审查报告
- `success`: 是否成功

**测试文件**: `tests/tools/test_test_reviewer.py`

### 8. 覆盖率分析工具 (`coverage_analyzer`)

**功能**: 分析代码测试覆盖率并生成报告

**输入**:
- `workspace_id`: 工作区ID
- `project_path`: 项目路径

**输出**:
- `coverage`: 覆盖率百分比
- `coverage_report_path`: 覆盖率报告路径
- `success`: 是否成功

**测试文件**: `tests/tools/test_coverage_analyzer.py`

## 实现状态

✅ **所有 8 个工具已实现基础功能**
- 每个工具都有对应的测试文件
- 遵循 TDD 开发模式
- 使用 Python 3.9+ 类型提示
- 包含错误处理和日志记录

## 待完善功能

以下功能标记为 TODO，需要后续实现：

1. **PRD 生成**: 从 URL 读取需求文档（HTTP 请求）
2. **TRD 生成**: 使用 AI 进行智能代码库分析
3. **任务分解**: 使用 AI 进行智能任务分解
4. **代码生成**: 集成 Cursor AI API
5. **代码审查**: 集成 Gemini API
6. **测试生成**: 使用 AI 生成更完善的测试
7. **覆盖率分析**: 完善覆盖率统计逻辑

## 运行测试

```bash
cd mcp-server
source venv/bin/activate  # 如果使用虚拟环境
PYTHONPATH=. python3 -m pytest tests/tools/ -v
```

## 使用示例

### 通过 MCP Server 调用（推荐）

在 Cursor IDE 中，通过 MCP 协议调用：

```bash
# 1. 创建工作区
@agent-orchestrator create_workspace project_path=/path/to/project requirement_name=用户认证功能

# 2. 生成 PRD
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req

# 3. 生成 TRD
@agent-orchestrator generate_trd workspace_id=req-xxx prd_path=PRD.md

# 4. 分解任务
@agent-orchestrator decompose_tasks workspace_id=req-xxx trd_path=TRD.md
```

### 直接调用 Python 函数（开发/测试）

```python
from src.tools.prd_generator import generate_prd
from src.tools.trd_generator import generate_trd
from src.tools.task_decomposer import decompose_tasks

# 生成 PRD
prd_result = generate_prd("workspace-001", "https://example.com/req")
print(prd_result["prd_path"])

# 生成 TRD
trd_result = generate_trd("workspace-001", prd_result["prd_path"])
print(trd_result["trd_path"])

# 分解任务
tasks_result = decompose_tasks("workspace-001", trd_result["trd_path"])
print(f"生成了 {tasks_result['task_count']} 个任务")
```

> **注意**：直接调用 Python 函数主要用于开发和测试。生产环境应通过 MCP Server 调用。
