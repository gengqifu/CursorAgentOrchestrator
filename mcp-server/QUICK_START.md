# 快速开始指南

## 5 分钟快速集成

### 步骤 1：安装依赖

```bash
cd mcp-server
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 步骤 2：配置 Cursor

#### macOS

```bash
# 创建配置目录（如果不存在）
mkdir -p ~/Library/Application\ Support/Cursor/User/globalStorage

# 复制示例配置
cp mcp.json.example ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json

# 编辑配置文件，更新路径
nano ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json
```

#### Linux

```bash
# 创建配置目录（如果不存在）
mkdir -p ~/.config/Cursor/User/globalStorage

# 复制示例配置
cp mcp.json.example ~/.config/Cursor/User/globalStorage/mcp.json

# 编辑配置文件，更新路径
nano ~/.config/Cursor/User/globalStorage/mcp.json
```

#### Windows

```powershell
# 创建配置目录（如果不存在）
New-Item -ItemType Directory -Force -Path "$env:APPDATA\Cursor\User\globalStorage"

# 复制示例配置
Copy-Item mcp.json.example "$env:APPDATA\Cursor\User\globalStorage\mcp.json"

# 编辑配置文件，更新路径
notepad "$env:APPDATA\Cursor\User\globalStorage\mcp.json"
```

### 步骤 3：更新配置文件

编辑 `mcp.json`，将以下路径替换为实际路径：

```json
{
  "mcpServers": {
    "agent-orchestrator": {
      "command": "/absolute/path/to/mcp-server/start_mcp_server.sh",
      "args": []
    }
  }
}
```

**获取绝对路径**：

```bash
# macOS/Linux
pwd  # 在 mcp-server 目录下运行

# Windows PowerShell
(Get-Location).Path
```

### 步骤 4：验证配置

运行检查脚本：

```bash
./check_integration.sh
```

### 步骤 5：重启 Cursor

关闭并重新打开 Cursor IDE。

### 步骤 6：测试集成

在 Cursor 中：

1. 打开命令面板：`Cmd+Shift+P` (macOS) 或 `Ctrl+Shift+P` (Windows/Linux)
2. 输入 "MCP" 查看可用工具
3. 应该看到 Agent Orchestrator 相关工具

## 验证清单

- [ ] Python 3.9+ 已安装
- [ ] 虚拟环境已创建并激活
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] 启动脚本存在且可执行
- [ ] Cursor 配置文件已创建
- [ ] 配置文件中的路径已更新为绝对路径
- [ ] Cursor 已重启
- [ ] 工具在 Cursor 中可见

## 常见问题

### Q: 如何找到 Cursor 配置目录？

**macOS**: `~/Library/Application Support/Cursor/User/globalStorage`
**Linux**: `~/.config/Cursor/User/globalStorage`
**Windows**: `%APPDATA%\Cursor\User\globalStorage`

### Q: 如何获取绝对路径？

在 `mcp-server` 目录下运行：

```bash
# macOS/Linux
pwd

# Windows PowerShell
(Get-Location).Path
```

### Q: 启动脚本权限错误？

```bash
chmod +x start_mcp_server.sh
```

### Q: 工具不可见？

1. 检查 Cursor 日志（View → Output → MCP）
2. 确认配置文件路径正确
3. 确认启动脚本可执行
4. 重启 Cursor

## 下一步

- 阅读 [CURSOR_INTEGRATION.md](CURSOR_INTEGRATION.md) 了解详细配置
- 查看 [TOOLS.md](TOOLS.md) 了解可用工具
- 运行 `./check_integration.sh` 检查配置
