# 文档更新总结

## 已更新的文档

### 1. 项目主文档

#### README.md
- ✅ 更新项目结构，说明 `skills/` 目录包含 `SKILL.md` 和 `scripts/` 入口脚本
- ✅ 添加架构说明：Agent 直接调用 skill，MCP Server 只提供基础设施工具

### 2. MCP Server 文档

#### mcp-server/ARCHITECTURE.md
- ✅ 更新系统架构图，说明 Agent 直接调用 skill 脚本
- ✅ 更新工具调用流程，分为：
  - Agent 调用 Skill 流程（新架构）
  - MCP Server 工具调用（基础设施）

#### mcp-server/CURSOR_INTEGRATION.md
- ✅ 更新可用工具列表，区分：
  - MCP Server 工具（基础设施）：create_workspace, get_workspace 等
  - Skills（Agent 直接调用）：8 个核心 skills
- ✅ 更新工作流程示例，说明 Agent 如何执行 skill 脚本

#### mcp-server/TOOLS.md
- ✅ 添加调用方式说明，说明 Agent 应该直接执行 skill 脚本
- ✅ 添加示例命令

### 3. Skills 文档

#### AGENTS.md
- ✅ 更新 8 个 skills 的 description：
  - prd-generator
  - trd-generator
  - task-decomposer
  - code-generator
  - code-reviewer
  - test-generator
  - test-reviewer
  - coverage-analyzer

#### skills/*/SKILL.md（所有 8 个 skills）
- ✅ 更新"目录与代码位置"部分，说明：
  - Skill 入口脚本位置：`skills/{skill-name}/scripts/{script_name}.py`
  - 核心实现位置：`mcp-server/src/tools/{tool_name}.py`
- ✅ 更新"标准调用流程"部分，说明：
  - Agent 如何调用脚本（命令行示例）
  - 返回结果格式（JSON）
  - 错误处理

## 文档更新要点

### 关键变化

1. **架构说明**：
   - Agent 直接调用 skill 脚本，不通过 MCP Server
   - MCP Server 只提供基础设施工具

2. **调用方式**：
   - 从 Python 导入改为命令行执行
   - 示例：`python3 skills/prd-generator/scripts/prd_generator.py <args>`

3. **返回格式**：
   - 统一为 JSON 格式输出
   - 便于 Agent 解析

4. **Skill 结构**：
   - 每个 skill 包含：SKILL.md + scripts/入口脚本
   - 核心实现在 mcp-server/src/tools/

## 文档一致性

所有文档现在都反映了新的架构（方案 3）：
- ✅ README.md
- ✅ mcp-server/ARCHITECTURE.md
- ✅ mcp-server/CURSOR_INTEGRATION.md
- ✅ mcp-server/TOOLS.md
- ✅ AGENTS.md
- ✅ skills/*/SKILL.md（所有 8 个）

## 待完成

- [ ] 调整 MCP Server 实现（移除直接调用工具的逻辑）
- [ ] 更新测试用例以适应新架构
