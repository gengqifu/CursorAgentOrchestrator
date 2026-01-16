# Cursor 集成方案

本文档说明如何将 Agent Orchestrator MCP Server 集成到 Cursor IDE 中。

## 架构概览

```
┌─────────────────┐
│   Cursor IDE    │
│                 │
│  ┌───────────┐ │
│  │ MCP Client │ │
│  └─────┬──────┘ │
└────────┼────────┘
         │ stdio
         │
┌────────▼────────────────────────┐
│  Agent Orchestrator MCP Server   │
│  ┌────────────────────────────┐  │
│  │ 8 Core SKILL Tools         │  │
│  │ - PRD Generator            │  │
│  │ - TRD Generator            │  │
│  │ - Task Decomposer          │  │
│  │ - Code Generator           │  │
│  │ - Code Reviewer            │  │
│  │ - Test Generator           │  │
│  │ - Test Reviewer            │  │
│  │ - Coverage Analyzer        │  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │ Managers                   │  │
│  │ - Workspace Manager        │  │
│  │ - Task Manager             │  │
│  └────────────────────────────┘  │
└───────────────────────────────────┘
```

## 前置要求

1. **Python 3.9+**
   ```bash
   python3 --version  # 应该 >= 3.9
   ```

2. **Cursor IDE** 已安装并运行

3. **MCP Server 已安装**
   ```bash
   cd mcp-server
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 配置步骤

### 步骤 1：定位 Cursor 配置目录

Cursor 的 MCP 配置文件位置：

- **macOS**: `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`
- **Linux**: `~/.config/Cursor/User/globalStorage/mcp.json`
- **Windows**: `%APPDATA%\Cursor\User\globalStorage\mcp.json`

### 步骤 2：创建或编辑 MCP 配置文件

创建配置文件 `mcp.json`（如果不存在）：

```json
{
  "mcpServers": {
    "agent-orchestrator": {
      "command": "python3",
      "args": [
        "/absolute/path/to/mcp-server/src/main.py"
      ],
      "env": {
        "AGENT_ORCHESTRATOR_ROOT": "/path/to/your/project",
        "GEMINI_API_KEY": "your-gemini-api-key",
        "CLAUDE_API_KEY": "your-claude-api-key"
      }
    }
  }
}
```

**重要**：将 `/absolute/path/to/mcp-server/src/main.py` 替换为实际的绝对路径。

### 步骤 3：使用启动脚本（推荐）

为了更好的兼容性和环境管理，建议使用启动脚本：

**macOS/Linux** (`mcp-server/start_mcp_server.sh`):

```bash
#!/bin/bash
# Agent Orchestrator MCP Server 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 设置环境变量
export AGENT_ORCHESTRATOR_ROOT="${AGENT_ORCHESTRATOR_ROOT:-$(pwd)/..}"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 运行 MCP Server
exec python3 src/main.py
```

**Windows** (`mcp-server/start_mcp_server.bat`):

```batch
@echo off
REM Agent Orchestrator MCP Server 启动脚本

cd /d "%~dp0"

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 设置环境变量
if not defined AGENT_ORCHESTRATOR_ROOT (
    set AGENT_ORCHESTRATOR_ROOT=%~dp0..
)
set PYTHONPATH=%~dp0;%PYTHONPATH%

REM 运行 MCP Server
python src\main.py
```

然后更新 `mcp.json` 使用启动脚本：

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

### 步骤 4：配置环境变量（可选）

在 `mcp.json` 的 `env` 字段中配置：

- `AGENT_ORCHESTRATOR_ROOT`: Agent Orchestrator 工作区根目录（默认：当前工作目录）
- `GEMINI_API_KEY`: Gemini API 密钥（用于代码审查）
- `CLAUDE_API_KEY`: Claude API 密钥（用于代码生成）
- `MAX_RETRY_ATTEMPTS`: 最大重试次数（默认：3）
- `MAX_REVIEW_CYCLES`: 最大审查循环次数（默认：5）

### 步骤 5：重启 Cursor

配置完成后，重启 Cursor IDE 以加载 MCP Server。

## 验证集成

### 方法 1：检查 Cursor 日志

1. 打开 Cursor
2. 查看输出面板（View → Output）
3. 选择 "MCP" 通道
4. 应该看到 Agent Orchestrator 的连接日志

### 方法 2：使用 Cursor 命令面板

1. 按 `Cmd+Shift+P` (macOS) 或 `Ctrl+Shift+P` (Windows/Linux)
2. 输入 "MCP" 查看可用的 MCP 命令
3. 应该看到 Agent Orchestrator 相关的工具

### 方法 3：测试工具调用

在 Cursor 中，尝试使用 Agent Orchestrator 的工具：

```
@agent-orchestrator generate_prd
```

## 可用工具列表

### MCP Server 工具（基础设施）

集成成功后，以下 MCP 工具将在 Cursor 中可用：

1. **create_workspace** - 创建工作区
2. **get_workspace** - 获取工作区信息
3. **update_workspace_status** - 更新工作区状态
4. **get_tasks** - 获取任务列表
5. **update_task_status** - 更新任务状态

### 8 个 SKILL 工具（符合 PDF 架构）

以下 8 个核心 SKILL 工具通过 MCP Server 暴露，符合 PDF 文档架构：

1. **generate_prd** - 生成 PRD 文档（SKILL: prd-generator）
2. **generate_trd** - 生成 TRD 文档（SKILL: trd-generator）
3. **decompose_tasks** - 分解任务（SKILL: task-decomposer）
4. **generate_code** - 生成代码（SKILL: code-generator）
5. **review_code** - 审查代码（SKILL: code-reviewer）
6. **generate_tests** - 生成测试（SKILL: test-generator）
7. **review_tests** - 审查测试（SKILL: test-reviewer）
8. **analyze_coverage** - 分析覆盖率（SKILL: coverage-analyzer）

**架构说明**（符合 PDF 文档）：
- 所有工具都通过 **MCP Server** 暴露
- MCP Server 作为中央编排服务，直接调用 8 个子 SKILL 模块
- 调用流程：Cursor CLI → MCP Server → 8个子SKILL模块 → 项目代码仓库

## 工作流程示例

### 方式1：使用完整工作流编排工具（推荐）

**自动确认模式**（一次性完成所有步骤）：

```bash
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/req \
  auto_confirm=true
```

**交互模式**（在关键步骤暂停，等待用户确认）：

```bash
# 第一次调用：开始工作流
@agent-orchestrator execute_full_workflow \
  project_path=/path/to/project \
  requirement_name=用户认证功能 \
  requirement_url=https://example.com/req \
  auto_confirm=false

# 返回 PRD 确认请求，用户确认后继续
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'

# 返回 TRD 确认请求，用户确认后继续
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"action": "confirm"}'

# 返回测试路径询问，用户提供路径后继续
@agent-orchestrator execute_full_workflow \
  workspace_id=req-xxx \
  auto_confirm=false \
  interaction_response='{"answer": "/path/to/tests"}'
```

详细使用说明请参考 [WORKFLOW_GUIDE.md](../WORKFLOW_GUIDE.md)。

### 方式2：分步骤调用（手动控制）

1. **创建需求工作区**（通过 MCP 工具）
   ```
   @agent-orchestrator create_workspace
   ```

2. **生成 PRD**（通过 MCP 工具）
   ```
   @agent-orchestrator generate_prd workspace_id="req-001" requirement_url="/path/to/req.md"
   ```

3. **生成 TRD**（通过 MCP 工具）
   ```
   @agent-orchestrator generate_trd workspace_id="req-001"
   ```

4. **分解任务**（通过 MCP 工具）
   ```
   @agent-orchestrator decompose_tasks workspace_id="req-001"
   ```

5. **生成代码**（通过 MCP 工具）
   ```
   @agent-orchestrator generate_code workspace_id="req-001" task_id="task-001"
   ```

6. **审查代码**（通过 MCP 工具）
   ```
   @agent-orchestrator review_code workspace_id="req-001" task_id="task-001"
   ```

7. **生成测试**
   ```
   @agent-orchestrator generate_tests workspace_id test_output_dir
   ```

8. **分析覆盖率**
   ```
   @agent-orchestrator analyze_coverage workspace_id project_path
   ```

### 多Agent协作示例

多个Agent可以协作完成开发流程，详细说明请参考 [MULTI_AGENT_GUIDE.md](MULTI_AGENT_GUIDE.md)。

**示例：Agent A 生成 PRD → Agent B 生成 TRD**

```bash
# Agent A: 生成 PRD
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req
@agent-orchestrator confirm_prd workspace_id=req-xxx

# Agent B: 查询工作流状态
@agent-orchestrator get_workflow_status workspace_id=req-xxx

# Agent B: 检查 TRD 是否可以开始
@agent-orchestrator check_stage_ready workspace_id=req-xxx stage=trd

# Agent B: 生成 TRD
@agent-orchestrator generate_trd workspace_id=req-xxx
```

## 故障排查

### 问题 1：MCP Server 无法启动

**症状**：Cursor 日志显示连接失败

**解决方案**：
1. 检查 Python 版本：`python3 --version` 应该 >= 3.9
2. 检查路径是否正确（使用绝对路径）
3. 检查虚拟环境是否激活
4. 检查依赖是否安装：`pip list | grep mcp`

### 问题 2：工具不可用

**症状**：在 Cursor 中看不到 Agent Orchestrator 工具

**解决方案**：
1. 确认 `mcp.json` 配置正确
2. 重启 Cursor
3. 检查 Cursor 日志中的错误信息

### 问题 3：权限错误

**症状**：启动脚本无法执行

**解决方案**：
```bash
chmod +x mcp-server/start_mcp_server.sh
```

### 问题 4：环境变量未生效

**症状**：工具运行时找不到配置

**解决方案**：
1. 在 `mcp.json` 的 `env` 字段中设置环境变量
2. 或在启动脚本中设置环境变量

## 高级配置

### 使用虚拟环境

如果使用虚拟环境，确保启动脚本正确激活：

```bash
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate
exec python3 src/main.py
```

### 自定义工作区根目录

在 `mcp.json` 中设置：

```json
{
  "mcpServers": {
    "agent-orchestrator": {
      "command": "...",
      "args": [...],
      "env": {
        "AGENT_ORCHESTRATOR_ROOT": "/custom/path/to/workspace"
      }
    }
  }
}
```

### 多项目配置

可以为不同项目配置不同的工作区：

```json
{
  "mcpServers": {
    "agent-orchestrator-project1": {
      "command": "...",
      "env": {
        "AGENT_ORCHESTRATOR_ROOT": "/path/to/project1"
      }
    },
    "agent-orchestrator-project2": {
      "command": "...",
      "env": {
        "AGENT_ORCHESTRATOR_ROOT": "/path/to/project2"
      }
    }
  }
}
```

## 参考资源

- [Cursor MCP 文档](https://docs.cursor.com)
- [Model Context Protocol 规范](https://modelcontextprotocol.io)
- [项目 README](../README.md)
- [工具文档](TOOLS.md)

## 支持

如遇问题，请：

1. 查看 [故障排查](#故障排查) 部分
2. 检查 Cursor 日志
3. 查看项目 Issues
