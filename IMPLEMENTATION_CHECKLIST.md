# Agent Orchestrator 详细执行检查清单

## 文档说明

本文档提供详细的执行检查清单，确保按照 `COMPLETE_WORK_PLAN.md` 中的计划逐步实现所有功能。

**使用方式**：
- 每个步骤完成后，勾选对应的 `[ ]` 复选框
- 遇到问题时，在 `备注` 栏记录
- 每个阶段结束时，进行阶段总结

---

## 前置准备工作

### 1. 环境准备

- [x] Python 3.9+ 已安装并验证（Python 3.14.0）
- [x] 虚拟环境已创建并激活（mcp-server/venv 存在）
- [ ] 所有依赖已安装（`pip install -r requirements.txt`）- 需要激活虚拟环境后验证
- [x] 项目结构已确认（core/, managers/, tools/, utils/ 目录结构正确）
- [x] Git 仓库已初始化

### 2. 状态字段定义

在开始实现前，先确认并更新状态字段定义：

- [x] 查看 `workspace_manager.py` 中的状态字段（已查看，第94-99行）
- [x] 确认需要添加的状态：
  - `prd_status`: `pending` | `in_progress` | `completed` | `failed` | `needs_regeneration`
  - `trd_status`: `pending` | `in_progress` | `completed` | `failed` | `needs_regeneration`
  - `tasks_status`: `pending` | `completed`
  - `code_status`: `pending` | `in_progress` | `completed`
  - `test_status`: `pending` | `completed`
- [x] 更新 `workspace_manager.py` 的状态管理方法（如需要）- 当前实现已满足，`update_workspace_status` 方法支持动态更新所有状态值
- [ ] 更新相关测试用例（待后续实现新功能时补充测试）

**备注**：当前状态字段定义已满足需求。`create_workspace` 方法初始化状态为 "pending"，`update_workspace_status` 方法支持动态更新为任意状态值（in_progress, completed, failed, needs_regeneration 等）。无需修改现有代码。

---

## 阶段1：用户交互工具（第1周）

### Day 1-2: orchestrator_questions.py

#### 1.1 创建文件结构

- [x] 创建文件：`mcp-server/src/tools/orchestrator_questions.py`
- [x] 添加文件头注释和模块文档字符串
- [x] 导入必要的模块：
  ```python
  from pathlib import Path
  from src.core.logger import setup_logger
  from src.core.exceptions import ValidationError
  from src.managers.workspace_manager import WorkspaceManager
  ```

#### 1.2 实现 ask_orchestrator_questions 函数

- [x] 实现函数签名和文档字符串
- [x] 实现返回交互请求的逻辑
- [x] 确保返回格式符合文档要求：
  ```python
  {
      "success": True,
      "interaction_required": True,
      "interaction_type": "questions",
      "questions": [...]
  }
  ```
- [x] 添加日志记录

**测试检查点**：
- [x] 返回的字典包含所有必需字段（success, interaction_required, interaction_type, questions）
- [x] questions 列表包含4个问题（project_path, requirement_name, requirement_url, workspace_path）
- [x] 每个问题包含 id, question, type, required, placeholder

#### 1.3 实现 submit_orchestrator_answers 函数

- [x] 实现函数签名和文档字符串
- [x] 实现参数验证：
  - [x] 检查必填字段（project_path, requirement_name, requirement_url）
  - [x] 验证路径有效性（检查路径存在且为目录）
- [x] 调用 `WorkspaceManager.create_workspace` 创建工作区
- [x] 返回包含 `workspace_id` 的字典
- [x] 添加错误处理和日志记录

**测试检查点**：
- [x] 缺少必填字段时抛出 ValidationError（已实现字段验证）
- [x] 无效路径时抛出 ValidationError（已实现路径验证）
- [x] 成功创建时返回 workspace_id（已实现返回格式）

#### 1.4 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_orchestrator_questions.py`
- [ ] 编写测试用例：
  - [ ] `test_ask_orchestrator_questions` - 测试询问问题
  - [ ] `test_submit_orchestrator_answers_success` - 测试提交答案成功
  - [ ] `test_submit_orchestrator_answers_missing_required` - 测试缺少必填项
  - [ ] `test_submit_orchestrator_answers_invalid_path` - 测试无效路径
- [ ] 运行测试：`pytest mcp-server/tests/tools/test_orchestrator_questions.py -v`
- [ ] 确保所有测试通过
- [ ] 检查测试覆盖率：`pytest --cov=src/tools/orchestrator_questions --cov-report=term-missing`
- [ ] 确保覆盖率 >= 90%

**备注**：_________________________________

#### 1.5 集成到 MCP Server

- [ ] 在 `mcp_server.py` 中导入：
  ```python
  from src.tools.orchestrator_questions import (
      ask_orchestrator_questions,
      submit_orchestrator_answers
  )
  ```
- [ ] 在 `list_tools()` 函数中添加工具定义：
  - [ ] `ask_orchestrator_questions` 工具
  - [ ] `submit_orchestrator_answers` 工具
- [ ] 在 `call_tool()` 函数中添加处理逻辑：
  - [ ] 处理 `ask_orchestrator_questions` 调用
  - [ ] 处理 `submit_orchestrator_answers` 调用
- [ ] 添加错误处理

**测试检查点**：
- [ ] `list_tools()` 返回包含新工具
- [ ] `call_tool("ask_orchestrator_questions", {})` 正常工作
- [ ] `call_tool("submit_orchestrator_answers", {...})` 正常工作

#### 1.6 编写集成测试

- [ ] 创建或更新测试文件：`mcp-server/tests/test_mcp_server.py`
- [ ] 添加集成测试：
  - [ ] `test_ask_orchestrator_questions_via_mcp` - 通过 MCP 调用
  - [ ] `test_submit_orchestrator_answers_via_mcp` - 通过 MCP 调用
- [ ] 运行集成测试：`pytest mcp-server/tests/test_mcp_server.py::test_ask_orchestrator_questions_via_mcp -v`
- [ ] 确保所有集成测试通过

#### 1.7 代码质量检查

- [ ] 运行代码格式化：`black mcp-server/src/tools/orchestrator_questions.py`
- [ ] 运行代码检查：`ruff check mcp-server/src/tools/orchestrator_questions.py`
- [ ] 运行类型检查：`mypy mcp-server/src/tools/orchestrator_questions.py`
- [ ] 修复所有问题

#### 1.8 提交代码

- [ ] Git 添加文件：`git add mcp-server/src/tools/orchestrator_questions.py`
- [ ] Git 添加测试：`git add mcp-server/tests/tools/test_orchestrator_questions.py`
- [ ] Git 提交：`git commit -m "feat: 实现 orchestrator_questions 工具"`

**备注**：_________________________________

---

### Day 3-4: prd_confirmation.py

#### 2.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/prd_confirmation.py`
- [ ] 添加文件头注释和模块文档字符串
- [ ] 导入必要的模块

#### 2.2 实现 check_prd_confirmation 函数

- [ ] 实现函数签名和文档字符串
- [ ] 检查 PRD 文件是否存在
- [ ] 返回交互请求（包含 PRD 内容预览）
- [ ] 添加错误处理（WorkspaceNotFoundError）
- [ ] 添加日志记录

**测试检查点**：
- [ ] PRD 存在时返回确认请求
- [ ] PRD 不存在时返回错误

#### 2.3 实现 confirm_prd 函数

- [ ] 实现函数签名和文档字符串
- [ ] 更新工作区状态：`prd_status = "completed"`
- [ ] 调用 `workspace_manager.update_workspace_status`
- [ ] 返回确认结果
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] 成功确认时更新状态
- [ ] 工作区不存在时抛出 WorkspaceNotFoundError

#### 2.4 实现 modify_prd 函数

- [ ] 实现函数签名和文档字符串
- [ ] 更新工作区状态：`prd_status = "needs_regeneration"`
- [ ] 调用 `workspace_manager.update_workspace_status`
- [ ] 返回修改标记结果
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] 成功标记修改时更新状态
- [ ] 工作区不存在时抛出 WorkspaceNotFoundError

#### 2.5 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_prd_confirmation.py`
- [ ] 编写测试用例：
  - [ ] `test_check_prd_confirmation_prd_exists` - PRD 存在时的确认请求
  - [ ] `test_check_prd_confirmation_prd_not_exists` - PRD 不存在时的错误
  - [ ] `test_confirm_prd_success` - 确认 PRD 成功
  - [ ] `test_modify_prd_success` - 修改 PRD 成功
  - [ ] `test_prd_modify_loop` - PRD 修改循环
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

**备注**：_________________________________

#### 2.6 集成到 MCP Server

- [ ] 在 `mcp_server.py` 中导入函数
- [ ] 在 `list_tools()` 中添加工具定义（3个工具）
- [ ] 在 `call_tool()` 中添加处理逻辑（3个工具）
- [ ] 添加错误处理

#### 2.7 编写集成测试

- [ ] 添加集成测试用例
- [ ] 运行集成测试并确保通过

#### 2.8 代码质量检查

- [ ] 运行 black, ruff, mypy
- [ ] 修复所有问题

#### 2.9 提交代码

- [ ] Git 提交：`git commit -m "feat: 实现 prd_confirmation 工具"`

**备注**：_________________________________

---

### Day 5: trd_confirmation.py

#### 3.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/trd_confirmation.py`
- [ ] 参考 `prd_confirmation.py` 的实现模式
- [ ] 实现针对 TRD 的确认和修改功能

#### 3.2 实现函数

- [ ] `check_trd_confirmation(workspace_id)` - 检查是否需要确认 TRD
- [ ] `confirm_trd(workspace_id)` - 确认 TRD
- [ ] `modify_trd(workspace_id)` - 标记需要修改 TRD

#### 3.3 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_trd_confirmation.py`
- [ ] 编写5个测试用例（参考 prd_confirmation）
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

#### 3.4 集成到 MCP Server

- [ ] 导入、注册、处理逻辑
- [ ] 编写集成测试

#### 3.5 代码质量检查和提交

- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 实现 trd_confirmation 工具"`

**备注**：_________________________________

---

### Day 6-7: test_path_question.py

#### 4.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/test_path_question.py`
- [ ] 导入必要的模块

#### 4.2 实现 ask_test_path 函数

- [ ] 获取工作区信息
- [ ] 生成默认路径建议（`{project_path}/tests/mock`）
- [ ] 返回交互请求
- [ ] 添加错误处理和日志记录

#### 4.3 实现 submit_test_path 函数

- [ ] 验证路径有效性
- [ ] 保存到工作区元数据
- [ ] 返回提交结果
- [ ] 添加错误处理和日志记录

#### 4.4 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_test_path_question.py`
- [ ] 编写3个测试用例
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

#### 4.5 集成到 MCP Server

- [ ] 导入、注册、处理逻辑
- [ ] 编写集成测试

#### 4.6 代码质量检查和提交

- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 实现 test_path_question 工具"`

**备注**：_________________________________

---

### 第1周总结

#### 5.1 集成测试

- [ ] 运行所有第1周工具的集成测试：
  ```bash
  pytest mcp-server/tests/test_mcp_server.py -v -k "orchestrator_questions|prd_confirmation|trd_confirmation|test_path"
  ```
- [ ] 确保所有测试通过

#### 5.2 端到端测试

- [ ] 创建端到端测试场景：
  - [ ] 询问4个问题 → 提交答案 → 创建工作区
  - [ ] 生成 PRD → 确认 PRD → 继续
  - [ ] 生成 PRD → 修改 PRD → 重新生成 → 确认
- [ ] 运行端到端测试并确保通过

#### 5.3 文档更新

- [ ] 更新 `mcp-server/TOOLS.md`：添加4个新工具的说明
- [ ] 更新 `README.md`：添加新工具的使用示例
- [ ] 更新 `mcp-server/ARCHITECTURE.md`：更新架构图

#### 5.4 代码审查

- [ ] 检查所有代码符合 Python 3.9+ 规范
- [ ] 检查所有代码有类型提示
- [ ] 检查所有代码有文档字符串
- [ ] 检查测试覆盖率 >= 90%

#### 5.5 最终提交

- [ ] Git 提交：`git commit -m "feat: 完成阶段1 - 用户交互工具"`

**备注**：_________________________________

---

## 阶段2：任务执行工具（第2周）

### Day 1-3: task_executor.py

#### 6.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/task_executor.py`
- [ ] 导入必要的模块（包括 `code_generator`, `code_reviewer`）

#### 6.2 实现 execute_task 函数

- [ ] 实现函数签名和文档字符串
- [ ] 实现 Review 循环逻辑：
  - [ ] 生成代码（调用 `generate_code`）
  - [ ] Review 代码（调用 `review_code`）
  - [ ] 判断是否通过
  - [ ] 如果未通过，重试（最多 `max_review_retries` 次）
- [ ] 返回执行结果
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] Review 通过时返回成功
- [ ] Review 未通过时重试
- [ ] 达到最大重试次数时返回失败

#### 6.3 实现 execute_all_tasks 函数

- [ ] 实现函数签名和文档字符串
- [ ] 获取任务列表（pending 状态）
- [ ] 循环执行每个任务（调用 `execute_task`）
- [ ] 统计完成和失败的任务数
- [ ] 返回执行结果统计
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] 所有任务执行成功
- [ ] 部分任务失败
- [ ] 空任务列表

#### 6.4 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_task_executor.py`
- [ ] 编写5个测试用例：
  - [ ] `test_execute_task_success` - 任务执行成功
  - [ ] `test_execute_task_review_failed_retry` - Review 失败重试
  - [ ] `test_execute_task_max_retries` - 达到最大重试次数
  - [ ] `test_execute_all_tasks_success` - 执行所有任务成功
  - [ ] `test_execute_all_tasks_partial_failure` - 部分任务失败
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

**备注**：_________________________________

#### 6.5 集成到 MCP Server

- [ ] 导入、注册、处理逻辑
- [ ] 编写集成测试

#### 6.6 代码质量检查和提交

- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 实现 task_executor 工具"`

---

### Day 4-5: 集成到 MCP Server

#### 7.1 统一集成

- [ ] 检查所有第2周工具已集成到 `mcp_server.py`
- [ ] 更新 `list_tools()` 函数
- [ ] 更新 `call_tool()` 函数
- [ ] 确保错误处理一致

#### 7.2 编写集成测试

- [ ] 创建集成测试场景：
  - [ ] 单个任务执行（Review 通过）
  - [ ] 单个任务执行（Review 失败重试）
  - [ ] 所有任务循环执行
- [ ] 运行集成测试并确保通过

#### 7.3 提交代码

- [ ] Git 提交：`git commit -m "feat: 集成阶段2工具到 MCP Server"`

---

### Day 6-7: 集成测试和文档

#### 8.1 端到端集成测试

- [ ] 创建端到端测试场景：
  - [ ] 完整任务执行流程（代码生成 → Review → 通过）
  - [ ] 任务 Review 循环（失败 → 重试 → 通过）
  - [ ] 所有任务循环执行
- [ ] 运行端到端测试并确保通过

#### 8.2 修复问题

- [ ] 记录发现的问题
- [ ] 修复所有问题
- [ ] 重新运行测试确保通过

#### 8.3 文档更新

- [ ] 更新 `mcp-server/TOOLS.md`
- [ ] 更新 `README.md`
- [ ] 更新 `mcp-server/ARCHITECTURE.md`

#### 8.4 阶段总结

- [ ] 运行所有阶段2的测试
- [ ] 代码审查
- [ ] Git 提交：`git commit -m "feat: 完成阶段2 - 任务执行工具"`

**备注**：_________________________________

---

## 阶段3：多Agent支持工具（第3周）

### Day 1-2: workflow_status.py

#### 9.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/workflow_status.py`
- [ ] 导入必要的模块

#### 9.2 实现 get_workflow_status 函数

- [ ] 实现函数签名和文档字符串
- [ ] 获取工作区信息
- [ ] 获取任务信息
- [ ] 构建阶段状态字典：
  - [ ] prd 阶段
  - [ ] trd 阶段
  - [ ] tasks 阶段
  - [ ] code 阶段
  - [ ] test 阶段
  - [ ] coverage 阶段
- [ ] 计算可以开始的阶段
- [ ] 计算被阻塞的阶段
- [ ] 计算工作流进度百分比
- [ ] 返回工作流状态字典
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] 初始状态
- [ ] PRD 完成后的状态
- [ ] 所有阶段完成
- [ ] 部分进度

#### 9.3 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_workflow_status.py`
- [ ] 编写4个测试用例
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

#### 9.4 集成到 MCP Server

- [ ] 导入、注册、处理逻辑
- [ ] 编写集成测试

#### 9.5 代码质量检查和提交

- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 实现 workflow_status 工具"`

**备注**：_________________________________

---

### Day 3-4: stage_dependency_checker.py

#### 10.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/stage_dependency_checker.py`
- [ ] 定义阶段依赖关系常量：
  ```python
  STAGE_DEPENDENCIES = {
      "prd": [],
      "trd": ["prd"],
      "tasks": ["trd"],
      "code": ["tasks"],
      "test": ["code"],
      "coverage": ["test"]
  }
  ```

#### 10.2 实现 check_stage_ready 函数

- [ ] 实现函数签名和文档字符串
- [ ] 验证阶段名称
- [ ] 获取前置阶段
- [ ] 检查前置阶段状态
- [ ] 检查文件是否存在（对于有文件依赖的阶段）
- [ ] 判断是否可以开始
- [ ] 返回检查结果
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] PRD 阶段（无依赖）
- [ ] TRD 阶段（PRD 已完成）
- [ ] TRD 阶段（PRD 未完成）
- [ ] 代码阶段（任务已完成）
- [ ] 无效阶段

#### 10.3 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_stage_dependency_checker.py`
- [ ] 编写5个测试用例
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

#### 10.4 集成到 MCP Server

- [ ] 导入、注册、处理逻辑
- [ ] 编写集成测试

#### 10.5 代码质量检查和提交

- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 实现 stage_dependency_checker 工具"`

**备注**：_________________________________

---

### Day 5-6: 修改现有工具添加状态检查

#### 11.1 修改 trd_generator.py

- [ ] 添加 PRD 状态检查：
  ```python
  if workspace["status"].get("prd_status") != "completed":
      raise ValidationError("PRD尚未完成，无法生成TRD。")
  ```
- [ ] 添加 PRD 文件存在检查
- [ ] 标记 TRD 为进行中（`trd_status = "in_progress"`）
- [ ] 生成成功后标记为已完成（`trd_status = "completed"`）
- [ ] 生成失败时标记为失败（`trd_status = "failed"`）
- [ ] 更新相关测试用例

#### 11.2 修改 task_decomposer.py

- [ ] 添加 TRD 状态检查
- [ ] 添加 TRD 文件存在检查
- [ ] 标记任务分解状态
- [ ] 更新相关测试用例

#### 11.3 修改 code_generator.py

- [ ] 添加任务状态检查
- [ ] 标记代码生成状态
- [ ] 更新相关测试用例

#### 11.4 修改 test_generator.py

- [ ] 添加代码状态检查
- [ ] 标记测试生成状态
- [ ] 更新相关测试用例

#### 11.5 测试和提交

- [ ] 运行所有相关测试并确保通过
- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 为现有工具添加状态检查"`

**备注**：_________________________________

---

### Day 7: 集成到 MCP Server

#### 12.1 统一集成

- [ ] 检查所有第3周工具已集成
- [ ] 更新 `list_tools()` 函数
- [ ] 更新 `call_tool()` 函数

#### 12.2 编写集成测试

- [ ] 创建多Agent并行测试场景：
  - [ ] Agent A 生成 PRD → Agent B 查询状态 → Agent B 生成 TRD
  - [ ] Agent C 分解任务 → Agent D, E, F 并行处理不同任务
  - [ ] 验证状态依赖检查正常工作
  - [ ] 验证文件锁确保并发安全
- [ ] 运行集成测试并确保通过

#### 12.3 文档更新

- [ ] 更新 `mcp-server/TOOLS.md`
- [ ] 更新 `README.md`
- [ ] 创建 `MULTI_AGENT_GUIDE.md`（多Agent协作指南）

#### 12.4 阶段总结

- [ ] 运行所有阶段3的测试
- [ ] 代码审查
- [ ] Git 提交：`git commit -m "feat: 完成阶段3 - 多Agent支持工具"`

**备注**：_________________________________

---

## 阶段4：完整工作流编排（第4周）

### Day 1-3: workflow_orchestrator.py

#### 13.1 创建文件结构

- [ ] 创建文件：`mcp-server/src/tools/workflow_orchestrator.py`
- [ ] 导入所有需要的工具函数

#### 13.2 实现 execute_full_workflow 函数（自动确认模式）

- [ ] 实现函数签名和文档字符串
- [ ] 参数验证（auto_confirm=True 时）
- [ ] 执行完整工作流：
  - [ ] 1. 提交答案并创建工作区
  - [ ] 2. PRD 循环（生成 → 确认）
  - [ ] 3. TRD 循环（生成 → 确认）
  - [ ] 4. 任务分解
  - [ ] 5. 任务循环执行
  - [ ] 6. 询问测试路径（使用默认路径）
  - [ ] 7. 生成测试
  - [ ] 8. 生成覆盖率报告
- [ ] 记录工作流步骤
- [ ] 返回工作流执行结果
- [ ] 添加错误处理和日志记录

**测试检查点**：
- [ ] 自动确认模式完整执行
- [ ] 所有步骤正确执行
- [ ] 错误处理正确

#### 13.3 实现 execute_full_workflow 函数（交互模式）

- [ ] 处理交互请求：
  - [ ] 询问4个问题
  - [ ] PRD 确认循环
  - [ ] TRD 确认循环
  - [ ] 询问测试路径
- [ ] 工作流状态管理
- [ ] 支持工作流中断和恢复
- [ ] 返回交互请求（当需要用户交互时）

**测试检查点**：
- [ ] 交互模式正确暂停和恢复
- [ ] 交互请求格式正确

#### 13.4 集成工作流状态查询和依赖检查

- [ ] 在关键步骤调用 `get_workflow_status`
- [ ] 在关键步骤调用 `check_stage_ready`
- [ ] 根据状态决定下一步操作

#### 13.5 实现工作流状态管理

- [ ] 使用 `workspace.json` 的 `workflow_state` 字段
- [ ] 每个步骤完成后更新状态
- [ ] 支持从任意步骤恢复

#### 13.6 编写单元测试（TDD）

- [ ] 创建测试文件：`mcp-server/tests/tools/test_workflow_orchestrator.py`
- [ ] 编写6个测试用例：
  - [ ] `test_execute_full_workflow_auto_confirm` - 自动确认模式
  - [ ] `test_execute_full_workflow_with_interactions` - 交互模式
  - [ ] `test_execute_full_workflow_prd_modify_loop` - PRD 修改循环
  - [ ] `test_execute_full_workflow_trd_modify_loop` - TRD 修改循环
  - [ ] `test_execute_full_workflow_task_review_loop` - 任务 Review 循环
  - [ ] `test_execute_full_workflow_partial_failure` - 部分失败场景
- [ ] 运行测试并确保通过
- [ ] 检查测试覆盖率 >= 90%

**备注**：_________________________________

#### 13.7 集成到 MCP Server

- [ ] 导入、注册、处理逻辑
- [ ] 编写集成测试

#### 13.8 代码质量检查和提交

- [ ] 代码质量检查
- [ ] Git 提交：`git commit -m "feat: 实现 workflow_orchestrator 工具"`

---

### Day 4-5: 集成到 MCP Server

#### 14.1 统一集成

- [ ] 检查所有第4周工具已集成
- [ ] 更新 `list_tools()` 函数
- [ ] 更新 `call_tool()` 函数

#### 14.2 编写端到端测试

- [ ] 创建端到端测试场景：
  - [ ] 完整工作流自动确认模式
  - [ ] 完整工作流交互模式
  - [ ] PRD 修改循环
  - [ ] TRD 修改循环
  - [ ] 任务 Review 循环
- [ ] 运行端到端测试并确保通过

#### 14.3 文档更新

- [ ] 更新 `mcp-server/TOOLS.md`
- [ ] 更新 `README.md`
- [ ] 创建 `WORKFLOW_GUIDE.md`（完整工作流使用指南）

#### 14.4 提交代码

- [ ] Git 提交：`git commit -m "feat: 集成阶段4工具到 MCP Server"`

---

### Day 6-7: 端到端测试和文档更新

#### 15.1 完整工作流端到端测试（单Agent模式）

- [ ] 创建端到端测试场景
- [ ] 运行测试并确保通过
- [ ] 记录测试结果

#### 15.2 多Agent并行测试

- [ ] 创建多Agent并行测试场景
- [ ] 运行测试并确保通过
- [ ] 验证并发安全性

#### 15.3 修复问题

- [ ] 记录发现的问题
- [ ] 修复所有问题
- [ ] 重新运行测试确保通过

#### 15.4 更新所有相关文档

- [ ] 更新 `mcp-server/TOOLS.md`
- [ ] 更新 `mcp-server/CURSOR_INTEGRATION.md`
- [ ] 更新 `mcp-server/ARCHITECTURE.md`
- [ ] 更新 `README.md`
- [ ] 更新 `WORKFLOW_GUIDE.md`
- [ ] 更新 `MULTI_AGENT_GUIDE.md`

#### 15.5 代码审查和优化

- [ ] 代码审查
- [ ] 性能优化（如需要）
- [ ] 代码重构（如需要）

#### 15.6 最终提交

- [ ] Git 提交：`git commit -m "feat: 完成阶段4 - 完整工作流编排"`

**备注**：_________________________________

---

## 项目最终验收

### 16.1 功能验收

- [ ] 所有8个新工具都已实现
- [ ] 所有工具都有单元测试，覆盖率 >= 90%
- [ ] 完整工作流可以自动执行（`auto_confirm=true`）
- [ ] 完整工作流支持交互模式（`auto_confirm=false`）
- [ ] PRD/TRD 修改循环正常工作
- [ ] 任务 Review 循环正常工作
- [ ] 工作流状态查询正常工作
- [ ] 状态依赖检查正常工作
- [ ] 多Agent 并行处理不同任务正常工作
- [ ] 多Agent 顺序完成不同阶段正常工作
- [ ] 所有集成测试通过
- [ ] 端到端测试通过
- [ ] 多Agent 并行测试通过

### 16.2 代码质量验收

- [ ] 所有代码遵循 Python 3.9+ 规范
- [ ] 所有代码有类型提示
- [ ] 所有代码有文档字符串
- [ ] 代码通过 black、ruff、mypy 检查
- [ ] 测试覆盖率 >= 90%

### 16.3 文档验收

- [ ] 所有文档已更新
- [ ] 使用示例清晰完整
- [ ] 架构说明准确

### 16.4 最终测试

- [ ] 运行所有测试：`pytest mcp-server/tests/ -v --cov=src --cov-report=html`
- [ ] 检查测试覆盖率报告
- [ ] 确保覆盖率 >= 90%

### 16.5 最终提交

- [ ] Git 提交：`git commit -m "feat: 完成 Agent Orchestrator 完整工作流编排功能"`

---

## 常见问题记录

### 问题1：_________________________________

**解决方案**：_________________________________

### 问题2：_________________________________

**解决方案**：_________________________________

### 问题3：_________________________________

**解决方案**：_________________________________

---

## 执行总结

### 开始日期：_____________
### 预计完成日期：_____________
### 实际完成日期：_____________

### 完成情况统计

- 阶段1：用户交互工具 - [ ] 完成
- 阶段2：任务执行工具 - [ ] 完成
- 阶段3：多Agent支持工具 - [ ] 完成
- 阶段4：完整工作流编排 - [ ] 完成

### 最终测试覆盖率：_____%

### 备注

_________________________________
_________________________________
_________________________________
