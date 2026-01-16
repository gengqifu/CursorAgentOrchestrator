# MCP Server 和 Skills 验证指南

> 本文档提供详细的步骤来验证 Agent Orchestrator MCP Server 和 Skills 在 Cursor IDE 中是否正确配置和运行。

> **快速参考**：如果不知道如何在 Cursor 中使用 MCP 工具，请先查看 [如何使用工具](HOW_TO_USE_TOOLS.md)。

## 📋 验证清单

在开始验证之前，请确保已完成以下配置：

- [ ] Python 3.9+ 已安装
- [ ] MCP Server 已安装（虚拟环境、依赖）
- [ ] Cursor IDE 配置文件 `mcp.json` 已创建
- [ ] Cursor IDE 已重启

## 🔍 验证方法

### 方法 1：运行集成检查脚本（推荐）

这是最快速和全面的验证方法：

```bash
cd mcp-server
./check_integration.sh
```

**如果 "mcp logs" 下没有内容，运行诊断脚本**：

```bash
cd mcp-server
./diagnose_mcp.sh
```

诊断脚本会检查：
- 启动脚本是否存在和可执行
- 虚拟环境和依赖
- Cursor 配置文件格式和路径
- 启动脚本是否能正常执行

**预期输出**：

```
🔍 检查 Cursor 集成配置...

1. 检查 Python 版本...
✓ Python 3.9.x

2. 检查虚拟环境...
✓ 虚拟环境存在
✓ 虚拟环境可激活

3. 检查依赖...
✓ mcp 库已安装

4. 检查启动脚本...
✓ 启动脚本存在
✓ 启动脚本可执行

5. 检查 Cursor 配置目录...
✓ Cursor 配置目录存在: /Users/username/Library/Application Support/Cursor/User/globalStorage
✓ mcp.json 配置文件存在
✓ agent-orchestrator 配置已存在

6. 检查路径配置...
✓ 启动脚本路径有效: /path/to/mcp-server/start_mcp_server.sh

✅ 检查完成！
```

如果所有检查项都显示 ✓，说明基础配置正确。

### 方法 2：检查 Cursor 日志

1. **打开 Cursor IDE**

2. **打开输出面板**
   - macOS: `View` → `Output` 或 `Cmd+Shift+U`
   - Windows/Linux: `View` → `Output` 或 `Ctrl+Shift+U`

3. **选择 MCP 日志通道**
   - 在输出面板的下拉菜单中选择 **"mcp logs"**

4. **查看连接日志**
   - 应该看到类似以下内容：
     ```
     [MCP] Starting agent-orchestrator server...
     [MCP] agent-orchestrator connected successfully
     [MCP] Registered 25 tools from agent-orchestrator
     ```

**如果看到错误信息**：
- `Failed to start agent-orchestrator`: 检查启动脚本路径和权限
- `Connection timeout`: 检查 Python 环境和依赖
- `Module not found`: 检查虚拟环境和依赖安装

**如果 "mcp logs" 下没有任何内容**：
- 说明 MCP Server 可能没有成功启动或连接
- 请参考 [问题 6：mcp logs 下没有内容](#问题-6mcp-logs-下没有内容) 进行排查

### 方法 3：测试工具调用（实际验证，推荐）

**重要说明**：MCP 工具不会出现在命令面板中。它们通过 `@agent-orchestrator` 语法在 Cursor 聊天界面中调用。

这是最直接的验证方法，通过实际调用工具来验证功能。

#### 3.1 测试基础工具：创建工作区

在 Cursor 的聊天界面中，输入：

```
@agent-orchestrator create_workspace
```

**预期结果**：
- 工具被识别并执行
- 返回工作区 ID（如 `req-xxx`）
- 没有错误信息

#### 3.2 测试 SKILL 工具：生成 PRD

```
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req
```

**预期结果**：
- 工具被识别并执行
- 返回 PRD 生成结果
- 在工作区目录下创建 `PRD.md` 文件

#### 3.3 测试完整工作流工具

```
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=测试需求 \
  requirement_url=https://example.com/req \
  auto_confirm=true
```

**预期结果**：
- 工具被识别并执行
- 返回工作流执行结果
- 完成所有 8 个步骤（PRD → TRD → 任务分解 → 代码生成 → 测试生成 → 覆盖率分析）

### 方法 5：检查工作区文件

验证工具是否正常工作，可以检查生成的文件：

1. **检查工作区目录**
   ```bash
   # 在项目根目录下
   ls -la .agent-orchestrator/requirements/
   ```

2. **查看工作区元数据**
   ```bash
   # 查看工作区列表
   cat .agent-orchestrator/requirements/*/workspace.json
   ```

3. **检查生成的文件**
   - `PRD.md` - 产品需求文档
   - `TRD.md` - 技术设计文档
   - `tasks.json` - 任务列表
   - `code/` - 生成的代码文件
   - `tests/` - 生成的测试文件
   - `coverage/` - 覆盖率报告

## 🎯 完整验证流程

按照以下步骤进行完整验证：

### 步骤 1：基础配置验证

```bash
cd mcp-server
./check_integration.sh
```

确保所有检查项都通过。

### 步骤 2：Cursor 日志验证

1. 打开 Cursor IDE
2. 查看输出面板的 **"mcp logs"** 通道
3. 确认看到连接成功的日志

### 步骤 3：工具可用性验证

**重要**：MCP 工具不会出现在命令面板中，需要通过聊天界面调用。

1. **在 Cursor 聊天界面中测试**：
   ```
   @agent-orchestrator create_workspace
   ```
   或者直接描述需求：
   ```
   请帮我创建一个新的工作区
   ```

2. **预期行为**：
   - Cursor 识别并调用 MCP 工具
   - 返回工具执行结果
   - 如果工具不存在或未连接，会显示错误信息

3. **如果工具无法调用**：
   - 检查 "mcp logs" 是否有连接日志
   - 确认 `mcp.json` 配置正确
   - 完全重启 Cursor IDE

### 步骤 4：功能验证

在 Cursor 聊天界面中测试：

```bash
# 1. 创建工作区
@agent-orchestrator create_workspace

# 2. 生成 PRD（需要先创建工作区）
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req

# 3. 查询工作区信息
@agent-orchestrator get_workspace workspace_id=req-xxx
```

### 步骤 5：完整工作流验证

测试完整工作流工具：

```bash
@agent-orchestrator execute_full_workflow \
  project_path=$(pwd) \
  requirement_name=验证测试 \
  requirement_url=https://example.com/req \
  auto_confirm=true
```

## ❌ 常见问题排查

### 问题 1：集成检查脚本失败

**症状**：`check_integration.sh` 显示 ✗ 或 ⚠

**解决方案**：
1. 检查 Python 版本：`python3 --version` 应该 >= 3.9
2. 创建虚拟环境：`python3 -m venv venv`
3. 安装依赖：`source venv/bin/activate && pip install -r requirements.txt`
4. 检查启动脚本权限：`chmod +x start_mcp_server.sh`

### 问题 2：Cursor 日志显示连接失败

**症状**：输出面板显示 `Failed to start agent-orchestrator`

**解决方案**：
1. 检查 `mcp.json` 中的路径是否为绝对路径
2. 确认启动脚本路径正确
3. 检查启动脚本是否有执行权限
4. 查看详细错误信息，根据错误提示修复

### 问题 3：工具在命令面板中不可见

**症状**：在命令面板中搜索不到 Agent Orchestrator 工具

**重要说明**：这是**正常现象**！MCP 工具不会出现在命令面板中。

**正确的使用方式**：
1. 在 Cursor 聊天界面（Composer 或 Chat）中使用 `@agent-orchestrator` 语法
2. 或者直接描述需求，Cursor 会自动调用相应的 MCP 工具

**如果 `@agent-orchestrator` 无法识别**：
1. 确认 `mcp.json` 配置正确
2. 重启 Cursor IDE（完全关闭后重新打开）
3. 检查 "mcp logs" 是否有连接日志
4. 查看 Cursor 开发者工具（Console）是否有错误信息
5. 确认 MCP Server 在日志中显示已连接

**验证工具是否可用**：
在聊天界面中尝试：
```
@agent-orchestrator create_workspace
```
如果 Cursor 无法识别或显示错误，说明 MCP Server 未成功连接。

### 问题 4：工具调用失败

**症状**：调用工具时返回错误

**解决方案**：
1. 检查工具参数是否正确
2. 查看 Cursor 日志中的详细错误信息
3. 确认工作区 ID 是否存在
4. 检查环境变量（如 `AGENT_ORCHESTRATOR_ROOT`）是否正确设置

### 问题 5：文件未生成

**症状**：工具执行成功，但文件未生成

**解决方案**：
1. 检查 `AGENT_ORCHESTRATOR_ROOT` 环境变量
2. 确认工作区目录有写入权限
3. 查看工作区元数据文件（`workspace.json`）确认状态
4. 检查日志中的文件路径信息

### 问题 6：mcp logs 下没有内容

**症状**：在 Cursor 输出面板的 "mcp logs" 通道下看不到任何日志

**可能原因**：
1. MCP Server 没有成功启动
2. Cursor 没有成功连接到 MCP Server
3. 配置文件路径或格式错误
4. 启动脚本执行失败

**排查步骤**：

#### 步骤 1：检查配置文件

确认 `mcp.json` 配置文件存在且格式正确：

```bash
# macOS
cat ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json

# Linux
cat ~/.config/Cursor/User/globalStorage/mcp.json

# Windows
type %APPDATA%\Cursor\User\globalStorage\mcp.json
```

**检查要点**：
- 配置文件是否存在
- JSON 格式是否正确（可以使用 `python3 -m json.tool` 验证）
- `command` 路径是否为**绝对路径**
- 路径是否指向正确的启动脚本

#### 步骤 2：手动测试启动脚本

在终端中手动运行启动脚本，检查是否有错误：

```bash
cd mcp-server

# 测试启动脚本
./start_mcp_server.sh
```

**预期行为**：
- 脚本应该启动并等待输入（因为 MCP Server 使用 stdio 通信）
- 不应该立即退出
- 不应该显示错误信息

**如果出现错误**：
- 检查 Python 版本：`python3 --version` 应该 >= 3.9
- 检查虚拟环境：`ls -la venv/bin/activate`
- 检查依赖：`source venv/bin/activate && pip list | grep mcp`
- 检查启动脚本权限：`chmod +x start_mcp_server.sh`

#### 步骤 3：检查启动脚本路径

确认 `mcp.json` 中的路径是绝对路径且正确：

```bash
# 获取启动脚本的绝对路径
cd mcp-server
pwd  # 记录这个路径

# 检查启动脚本是否存在
ls -la start_mcp_server.sh

# 检查启动脚本是否可执行
test -x start_mcp_server.sh && echo "可执行" || echo "不可执行"
```

**更新 `mcp.json`**：
```json
{
  "mcpServers": {
    "agent-orchestrator": {
      "command": "/绝对路径/to/mcp-server/start_mcp_server.sh",
      "args": []
    }
  }
}
```

#### 步骤 4：检查 Cursor 是否识别配置

1. **完全重启 Cursor IDE**（完全关闭后重新打开）
2. **等待几秒钟**，让 Cursor 加载 MCP Server
3. **再次查看 "mcp logs"** 通道

#### 步骤 5：检查其他日志通道

如果 "mcp logs" 没有内容，检查其他可能的日志位置：

1. **"mcp file system"** 通道（如果配置了文件系统工具）
2. **Cursor 开发者工具**：
   - macOS: `Cmd+Shift+P` → "Developer: Toggle Developer Tools"
   - Windows/Linux: `Ctrl+Shift+P` → "Developer: Toggle Developer Tools"
   - 在 Console 中查看是否有 MCP 相关错误

#### 步骤 6：验证 MCP Server 是否能正常启动

使用 Python 直接测试 MCP Server：

```bash
cd mcp-server
source venv/bin/activate  # 如果使用虚拟环境
PYTHONPATH=. python3 src/main.py
```

**预期输出**：
```
MCP Server 启动中... (Python 3.x)
提示：使用 Ctrl+C 关闭 Server
MCP Server 已启动，等待连接...
可用工具：
  基础设施工具：create_workspace, get_workspace, ...
  SKILL 工具：generate_prd, generate_trd, ...
```

如果看到这些输出，说明 MCP Server 本身可以正常启动。

**按 `Ctrl+C` 退出测试**

#### 步骤 7：检查环境变量

确认 `mcp.json` 中是否配置了必要的环境变量：

```json
{
  "mcpServers": {
    "agent-orchestrator": {
      "command": "/path/to/mcp-server/start_mcp_server.sh",
      "args": [],
      "env": {
        "AGENT_ORCHESTRATOR_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

#### 步骤 8：查看 Cursor 开发者工具

如果以上步骤都正常，但 "mcp logs" 仍然没有内容：

1. 打开 Cursor 开发者工具（`Cmd+Shift+P` / `Ctrl+Shift+P` → "Developer: Toggle Developer Tools"）
2. 查看 Console 标签页
3. 搜索 "MCP" 或 "agent-orchestrator"
4. 查看是否有错误信息

**常见错误**：
- `spawn EACCES`: 启动脚本没有执行权限
- `spawn ENOENT`: 启动脚本路径不存在
- `Command failed`: 启动脚本执行失败

**解决方案**：
- 修复权限：`chmod +x start_mcp_server.sh`
- 修复路径：使用绝对路径
- 检查启动脚本：手动运行测试

## ✅ 验证成功标准

如果满足以下所有条件，说明 MCP Server 和 Skills 已成功配置：

- [x] 集成检查脚本所有项显示 ✓
- [x] Cursor 日志显示 MCP Server 连接成功
- [x] 命令面板中可以找到 Agent Orchestrator 工具
- [x] 可以成功调用基础工具（如 `create_workspace`）
- [x] 可以成功调用 SKILL 工具（如 `generate_prd`）
- [x] 可以成功执行完整工作流（`execute_full_workflow`）
- [x] 工作区文件正确生成（PRD.md, TRD.md, tasks.json 等）

## 📚 相关文档

- [Cursor 集成方案](CURSOR_INTEGRATION.md) - 完整的集成配置文档
- [快速开始指南](QUICK_START.md) - 5 分钟快速集成
- [工具文档](TOOLS.md) - 所有工具的详细说明
- [完整工作流使用指南](../WORKFLOW_GUIDE.md) - 完整工作流使用说明

## 🆘 获取帮助

如果验证过程中遇到问题：

1. 查看 [故障排查](CURSOR_INTEGRATION.md#故障排查) 部分
2. 检查 Cursor 日志中的详细错误信息
3. 运行集成检查脚本获取诊断信息
4. 查看项目 Issues 或提交新 Issue

---

**验证完成后，您就可以开始使用 Agent Orchestrator 进行智能开发流程编排了！** 🎉
