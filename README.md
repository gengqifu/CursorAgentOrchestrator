# Cursor Agent Orchestrator

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-95.57%25-brightgreen.svg)](mcp-server/htmlcov/index.html)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

适配 Cursor IDE 的智能开发流程编排系统，通过 MCP (Model Context Protocol) 协议集成到 Cursor 中。

## 📋 目录

- [项目概述](#项目概述)
- [核心特性](#核心特性)
- [前置要求](#前置要求)
- [快速开始](#快速开始)
- [使用示例](#使用示例)
- [8 个核心 SKILL 工具](#8-个核心-skill-工具)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [开发](#开发)
- [文档](#文档)
- [常见问题](#常见问题)
- [贡献](#贡献)
- [许可证](#许可证)

## 项目概述

Agent Orchestrator 是一个智能开发流程编排系统，提供从需求分析到代码实现的完整自动化流程。通过 8 个核心 SKILL 工具，实现 PRD 生成、TRD 生成、任务分解、代码生成、代码审查、测试生成、测试审查和覆盖率分析等功能。

**当前版本**：v0.1.0（开发中）

⚠️ **注意**：本项目仍在积极开发中，API 可能会有变化。

## ✨ 核心特性

- 🚀 **8 个核心 SKILL 工具**：完整的开发流程自动化
- 🔄 **Multi-Agent 架构**：多智能体协作，提升代码质量
- 📦 **MCP 协议集成**：无缝集成到 Cursor IDE
- 🧪 **TDD 开发模式**：测试覆盖率 95.57%（超过 90% 要求）
- 🐍 **Python 3.9+ 兼容**：现代化 Python 代码
- 🔒 **零依赖设计**：最小化外部依赖
- 🛡️ **安全保护**：完善的输入验证和错误处理

## 📋 前置要求

在开始之前，请确保您的系统满足以下要求：

- **Python**: 3.9 或更高版本
- **Cursor IDE**: 最新版本（支持 MCP 协议）
- **操作系统**: macOS / Linux / Windows
- **内存**: 8GB+ RAM（推荐）
- **磁盘空间**: 至少 500MB 可用空间

### 检查 Python 版本

```bash
python3 --version  # 应该显示 Python 3.9.x 或更高
```

## 🚀 快速开始

### 1. 安装 MCP Server

```bash
# 克隆仓库（如果还没有）
git clone <repository-url>
cd CursorAgentOrchestrator

# 进入 mcp-server 目录
cd mcp-server

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 Cursor

详细配置步骤请参考：
- [快速开始指南](mcp-server/QUICK_START.md) - 5 分钟快速集成
- [Cursor 集成方案](mcp-server/CURSOR_INTEGRATION.md) - 完整集成文档

**快速配置**：

1. 复制示例配置文件到 Cursor 配置目录：
   ```bash
   # macOS
   cp mcp-server/mcp.json.example ~/Library/Application\ Support/Cursor/User/globalStorage/mcp.json
   
   # Linux
   cp mcp-server/mcp.json.example ~/.config/Cursor/User/globalStorage/mcp.json
   
   # Windows
   copy mcp-server\mcp.json.example %APPDATA%\Cursor\User\globalStorage\mcp.json
   ```

2. 编辑配置文件，更新启动脚本的绝对路径

3. 重启 Cursor IDE

### 3. 验证集成

运行集成检查脚本：

```bash
cd mcp-server
./check_integration.sh
```

**预期输出**：
```
🔍 检查 Cursor 集成配置...
✓ Python 3.9.x
✓ 虚拟环境存在
✓ mcp 库已安装
✓ 启动脚本存在
✓ Cursor 配置目录存在
✅ 检查完成！
```

## 💡 使用示例

### 在 Cursor 中创建工作区

在 Cursor 的命令面板中（`Cmd+Shift+P` / `Ctrl+Shift+P`），输入：

```
@agent-orchestrator create_workspace
```

### 生成 PRD 文档

```
@agent-orchestrator generate_prd workspace-001 https://example.com/requirement
```

### 生成代码

```
@agent-orchestrator generate_code workspace-001 task-001
```

### 审查代码

```
@agent-orchestrator review_code workspace-001 task-001
```

### 完整工作流程示例

```bash
# 1. 创建工作区
create_workspace(project_path="/path/to/project", requirement_name="用户认证功能")

# 2. 生成 PRD
generate_prd(workspace_id="workspace-001", requirement_url="https://example.com/req")

# 3. 生成 TRD
generate_trd(workspace_id="workspace-001", prd_path="PRD.md")

# 4. 分解任务
decompose_tasks(workspace_id="workspace-001", trd_path="TRD.md")

# 5. 生成代码
generate_code(workspace_id="workspace-001", task_id="task-001")

# 6. 审查代码
review_code(workspace_id="workspace-001", task_id="task-001")

# 7. 生成测试
generate_tests(workspace_id="workspace-001", test_output_dir="tests/")

# 8. 分析覆盖率
analyze_coverage(workspace_id="workspace-001", project_path="/path/to/project")
```

## 📁 项目结构

```
CursorAgentOrchestrator/
├── skills/                        # Skills 目录（自包含）
│   ├── prd-generator/
│   │   ├── SKILL.md              # Skill 指导文档
│   │   └── scripts/
│   │       └── prd_generator.py  # 入口脚本
│   ├── trd-generator/
│   ├── task-decomposer/
│   ├── code-generator/
│   ├── code-reviewer/
│   ├── test-generator/
│   ├── test-reviewer/
│   └── coverage-analyzer/
├── mcp-server/                    # MCP Server 实现
│   ├── src/                       # 源代码
│   │   ├── core/                 # 核心模块
│   │   │   ├── config.py        # 配置管理
│   │   │   ├── logger.py        # 日志系统
│   │   │   └── exceptions.py   # 异常定义
│   │   ├── managers/            # 业务管理器
│   │   │   ├── workspace_manager.py  # 工作区管理
│   │   │   └── task_manager.py       # 任务管理
│   │   ├── tools/               # 8 个核心工具实现（核心逻辑）
│   │   │   ├── prd_generator.py
│   │   │   ├── trd_generator.py
│   │   │   ├── task_decomposer.py
│   │   │   ├── code_generator.py
│   │   │   ├── code_reviewer.py
│   │   │   ├── test_generator.py
│   │   │   ├── test_reviewer.py
│   │   │   └── coverage_analyzer.py
│   │   ├── mcp_server.py        # MCP Server 核心实现
│   │   └── main.py              # MCP Server 入口
│   ├── tests/                    # 测试文件
│   │   ├── core/
│   │   ├── managers/
│   │   └── tools/
│   ├── CURSOR_INTEGRATION.md    # Cursor 集成文档
│   ├── QUICK_START.md           # 快速开始指南
│   ├── ARCHITECTURE.md          # 架构设计文档
│   ├── TOOLS.md                 # 工具文档
│   ├── start_mcp_server.sh      # 启动脚本 (macOS/Linux)
│   ├── start_mcp_server.bat     # 启动脚本 (Windows)
│   └── check_integration.sh     # 集成检查脚本
├── ARCHITECTURE_DISCUSSION.md    # 架构方案讨论
├── ARCHITECTURE_IMPLEMENTATION.md # 架构实施方案
├── REFACTOR_SUMMARY.md           # 重构总结
└── README.md                     # 项目说明
```

**架构说明**（符合 PDF 文档）：
- **Cursor CLI**：用户界面层（命令行或 Cursor IDE），对应 PDF 中的 "Kiro CLI"
- **MCP Server** (`mcp-server/`)：中央编排服务，通过 MCP 协议暴露所有工具（基础设施工具 + 8 个 SKILL 工具）
- **8个子SKILL模块** (`mcp-server/src/tools/`)：核心业务逻辑，通过 MCP Server 调用
- **调用流程**：Cursor CLI → MCP Server → 8个子SKILL模块 → 项目代码仓库

## 🛠️ 8 个核心 SKILL 工具

1. **PRD Generator** - 产品需求文档生成
   - 从需求 URL 或文件生成标准化的 PRD 文档
   - 支持多种需求文档格式

2. **TRD Generator** - 技术设计文档生成
   - 基于 PRD 生成详细的技术设计文档
   - 自动分析代码库结构

3. **Task Decomposer** - 任务分解
   - 将 TRD 分解为独立的开发任务
   - 生成结构化的任务列表

4. **Code Generator** - 代码生成
   - 根据任务描述生成功能代码
   - 自动生成对应的测试文件

5. **Code Reviewer** - 代码审查
   - 使用 AI 审查代码质量
   - 生成详细的审查报告

6. **Test Generator** - 测试生成
   - 为已完成任务生成 Mock 测试
   - 支持批量测试生成

7. **Test Reviewer** - 测试审查
   - 审查测试代码质量
   - 检查测试覆盖率和质量

8. **Coverage Analyzer** - 覆盖率分析
   - 分析代码测试覆盖率
   - 生成 HTML 覆盖率报告

详细文档：[TOOLS.md](mcp-server/TOOLS.md)

## 🔧 技术栈

- **语言**: Python 3.9+
- **协议**: MCP (Model Context Protocol)
- **测试框架**: pytest, pytest-cov
- **代码质量**: black, ruff, mypy
- **类型检查**: mypy
- **包管理**: pip, setuptools

## 🛠️ 开发

### 运行测试

```bash
cd mcp-server
source venv/bin/activate  # Windows: venv\Scripts\activate
PYTHONPATH=. python3 -m pytest
```

### 查看测试覆盖率

```bash
PYTHONPATH=. python3 -m pytest --cov=src --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```

### 代码格式化

```bash
# 格式化代码
python3 -m black src tests

# 检查代码风格
python3 -m ruff check src tests

# 类型检查
python3 -m mypy src
```

### 开发流程

本项目严格遵循 TDD（测试驱动开发）模式：

1. **Red**: 先写失败的测试
2. **Green**: 写最小实现让测试通过
3. **Refactor**: 重构改进代码

## 📚 文档

- [快速开始](mcp-server/QUICK_START.md) - 5 分钟快速集成指南
- [Cursor 集成方案](mcp-server/CURSOR_INTEGRATION.md) - 完整的集成配置文档
- [架构设计](mcp-server/ARCHITECTURE.md) - 系统架构和技术设计
- [工具文档](mcp-server/TOOLS.md) - 8 个核心 SKILL 工具的详细说明
- [安装指南](mcp-server/INSTALL.md) - 详细的安装和配置步骤
- [Python 3 兼容性](mcp-server/PYTHON3_COMPATIBILITY.md) - Python 3.9+ 兼容性说明

## ❓ 常见问题

### Q: 如何检查集成是否成功？

A: 运行集成检查脚本：
```bash
cd mcp-server
./check_integration.sh
```

### Q: MCP Server 无法启动怎么办？

A: 请检查：
1. Python 版本是否符合要求（3.9+）
2. 虚拟环境是否正确激活
3. 依赖是否完整安装
4. 启动脚本路径是否正确

详细故障排查请参考 [Cursor 集成方案 - 故障排查](mcp-server/CURSOR_INTEGRATION.md#故障排查)

### Q: 工具在 Cursor 中不可见？

A: 请确认：
1. `mcp.json` 配置文件已正确创建
2. 配置文件中的路径是绝对路径
3. 启动脚本具有执行权限
4. Cursor IDE 已重启

### Q: 如何更新配置？

A: 修改 `mcp.json` 配置文件后，需要重启 Cursor IDE 才能生效。

### Q: 支持哪些操作系统？

A: 支持 macOS、Linux 和 Windows。每个平台都有对应的启动脚本。

### Q: 测试覆盖率要求是多少？

A: 项目要求测试覆盖率 >= 90%，当前覆盖率为 95.57%（101 个测试用例全部通过）。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加新功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 [项目规则](.cursor/rules/project.md)
- 使用 Python 3.9+ 类型提示
- 遵循 TDD 开发模式
- 提交信息使用中文

### 报告问题

如发现问题，请通过 [GitHub Issues](https://github.com/your-repo/issues) 报告。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

```
MIT License

Copyright (c) 2026 gengqifu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Cursor IDE](https://cursor.sh/) - 提供优秀的 AI 编程环境
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 协议标准
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP Server 框架（计划集成）

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**

