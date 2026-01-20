# 如何在 Cursor 中使用 MCP 工具

## 📌 重要说明

**MCP 工具不会出现在命令面板中！**

在 Cursor IDE 中，MCP 工具通过以下方式使用：
1. 在聊天界面中使用 `@agent-orchestrator` 语法
2. 直接描述需求，让 Cursor 自动调用相应的工具

## 🎯 使用方法

### 方法 1：使用 @agent-orchestrator 语法（推荐）

在 Cursor 的聊天界面（Composer 或 Chat）中，使用以下语法：

```
@agent-orchestrator <工具名称> <参数>
```

**示例**：

```bash
# 创建工作区
@agent-orchestrator create_workspace \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=/path/to/requirement.md

# 或者：先让工具询问问题，再提交答案（更适合交互式使用）
@agent-orchestrator ask_orchestrator_questions
@agent-orchestrator submit_orchestrator_answers \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=/path/to/requirement.md

# 生成 PRD
@agent-orchestrator generate_prd workspace_id=req-001 requirement_url=https://example.com/req.md

# 执行完整工作流
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/req.md \
  auto_confirm=true
```

### 方法 2：直接描述需求（自然语言）

你也可以直接描述需求，Cursor 会自动识别并调用相应的 MCP 工具：

```
请帮我创建一个新的工作区

为工作区 req-001 生成 PRD，需求文档在 https://example.com/req.md

执行完整的工作流，项目路径是 /path/to/project，需求名称是用户认证功能
```

## ✅ 验证工具是否可用

### 步骤 1：检查 MCP Server 连接

1. 打开 Cursor 输出面板（`View` → `Output` 或 `Cmd+Shift+U`）
2. 选择 **"mcp logs"** 通道
3. 应该看到类似以下内容：
   ```
   [MCP] Starting agent-orchestrator server...
   [MCP] agent-orchestrator connected successfully
   [MCP] Registered 28 tools from agent-orchestrator
   ```

### 步骤 2：测试工具调用

在聊天界面中尝试：

```
@agent-orchestrator ask_orchestrator_questions
```

**预期结果**：
- Cursor 识别并调用工具
- 返回 4 个问题（`project_path` / `requirement_name` / `requirement_url` / 可选 `workspace_path`）
- 没有错误信息

然后提交答案创建工作区：

```bash
@agent-orchestrator submit_orchestrator_answers \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=/path/to/requirement.md
```

**预期结果**：返回 `workspace_id`（如 `req-xxx`）

**如果无法识别**：
- 检查 "mcp logs" 是否有连接日志
- 确认 `mcp.json` 配置正确
- 完全重启 Cursor IDE

## 🔍 常见问题

### Q: 为什么在命令面板中找不到 MCP 工具？

**A**: 这是正常现象。MCP 工具不会出现在命令面板中，它们通过聊天界面调用。

### Q: 如何使用 `@agent-orchestrator` 语法？

**A**: 
1. 打开 Cursor 聊天界面（Composer 或 Chat）
2. 输入 `@agent-orchestrator` 后跟工具名称
3. 添加必要的参数

### Q: Cursor 无法识别 `@agent-orchestrator`，怎么办？

**A**: 
1. 检查 "mcp logs" 是否有连接日志
2. 确认 `mcp.json` 配置正确（路径必须是绝对路径）
3. 完全重启 Cursor IDE
4. 运行诊断脚本：`./diagnose_mcp.sh`

### Q: 如何查看所有可用的工具？

**A**: 目前没有单独的 `list_tools` 工具（工具列表由 MCP Server 通过协议提供）。请查看文档：
- [TOOLS.md](TOOLS.md) - 完整的工具列表和说明
- [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md) - 集成指南

## 📚 相关文档

- [验证指南](VERIFICATION_GUIDE.md) - 详细的验证步骤和故障排查
- [工具说明](TOOLS.md) - 所有工具的详细说明
- [集成指南](CURSOR_INTEGRATION.md) - Cursor 集成配置
