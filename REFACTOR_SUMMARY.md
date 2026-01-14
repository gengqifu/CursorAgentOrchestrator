# 架构重构总结（方案 3）

## ✅ 已完成的工作

### 1. 创建 Skill 入口脚本

已为所有 8 个 skills 创建入口脚本：

- ✅ `skills/prd-generator/scripts/prd_generator.py`
- ✅ `skills/trd-generator/scripts/trd_generator.py`
- ✅ `skills/task-decomposer/scripts/task_decomposer.py`
- ✅ `skills/code-generator/scripts/code_generator.py`
- ✅ `skills/code-reviewer/scripts/code_reviewer.py`
- ✅ `skills/test-generator/scripts/test_generator.py`
- ✅ `skills/test-reviewer/scripts/test_reviewer.py`
- ✅ `skills/coverage-analyzer/scripts/coverage_analyzer.py`

**脚本特点**：
- 薄包装：导入 `mcp-server/src/tools/` 中的核心实现
- 自动处理导入路径：自动添加 `mcp-server` 到 Python 路径
- 命令行接口：支持直接执行和测试
- JSON 输出：便于 Agent 解析结果

### 2. 更新 SKILL.md 文档

已更新 `skills/prd-generator/SKILL.md`：
- ✅ 说明脚本位置
- ✅ 说明如何调用脚本
- ✅ 说明返回结果格式

**待更新**：其他 7 个 skills 的 SKILL.md（参考 prd-generator 的格式）

---

## 📋 待完成的工作

### 1. 更新剩余 SKILL.md 文档

需要更新以下 skills 的 SKILL.md：
- [ ] `skills/trd-generator/SKILL.md`
- [ ] `skills/task-decomposer/SKILL.md`
- [ ] `skills/code-generator/SKILL.md`
- [ ] `skills/code-reviewer/SKILL.md`
- [ ] `skills/test-generator/SKILL.md`
- [ ] `skills/test-reviewer/SKILL.md`
- [ ] `skills/coverage-analyzer/SKILL.md`

**更新模板**：

在每个 SKILL.md 的 "目录与代码位置" 部分：

```markdown
### 1. 目录与代码位置

- **Skill 入口脚本**：`skills/{skill-name}/scripts/{script_name}.py`
- **核心实现**：`mcp-server/src/tools/{tool_name}.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/{script_name}.py`：入口脚本，由 Agent 调用
```

在 "标准调用流程" 部分：

```markdown
### 步骤 2：调用 Skill 脚本

**Agent 应该执行以下命令**：

```bash
python3 skills/{skill-name}/scripts/{script_name}.py \
    <参数1> \
    <参数2>
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    ...
}
```

失败时：
```json
{
    "success": false,
    "error": "错误信息",
    "error_type": "ErrorType"
}
```
```

### 2. 调整 MCP Server

需要修改 `mcp-server/src/main.py`：
- [ ] 移除直接调用 8 个工具的逻辑
- [ ] 只保留工作区管理工具：
  - `create_workspace`
  - `get_workspace`
  - `update_workspace_status`
  - `get_tasks`
  - `update_task_status`
- [ ] **不提供** `execute_skill` 工具（Agent 直接调用 skill）

### 3. 更新测试用例

- [ ] 测试 skill 脚本的导入和执行
- [ ] 保持对 `mcp-server/src/tools/` 的测试（核心实现）

---

## 🎯 架构确认

### 最终架构

```
用户 Prompt
    ↓
Agent (在 Cursor 中)
    ↓ 根据 prompt 选择 skill
Skill (SKILL.md + scripts/入口脚本)
    ↓ 调用
mcp-server/src/tools/*.py (核心实现)
    ↓ 使用
mcp-server/src/managers/*.py (WorkspaceManager, TaskManager)
    ↓ 使用
mcp-server/src/core/*.py (Config, Logger, Exceptions)
```

### MCP Server 职责

- ✅ **提供基础设施工具**：
  - 工作区管理（create_workspace, get_workspace 等）
  - 任务管理（get_tasks, update_task_status 等）
- ❌ **不直接调用工具**：工具由 Agent 通过 skill 调用
- ❌ **不提供 execute_skill**：Agent 直接执行 skill 脚本

---

## 📝 使用示例

### Agent 调用示例

**用户输入**：
```
为工作区 req-001 生成 PRD，需求文档在 /path/to/req.md
```

**Agent 处理**：
1. 识别意图：生成 PRD
2. 选择 skill：prd-generator
3. 读取 `skills/prd-generator/SKILL.md`
4. 执行脚本：
   ```bash
   python3 skills/prd-generator/scripts/prd_generator.py req-001 /path/to/req.md
   ```
5. 解析返回结果，反馈给用户

---

## ✅ 下一步

1. 更新剩余 7 个 skills 的 SKILL.md
2. 调整 MCP Server（移除直接调用工具的逻辑）
3. 更新测试用例
4. 提交代码
