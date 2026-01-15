# Cursor Agent Orchestrator MCP Server

适配 Cursor 的智能开发流程编排服务。

## Python 版本要求

**本项目要求 Python 3.9 或更高版本**

```bash
# 检查 Python 版本
python3 --version  # 应该显示 Python 3.9.x 或更高

# 如果版本不符合，请升级 Python
```

## 项目结构

```
mcp-server/
├── src/
│   ├── __init__.py
│   ├── main.py              # MCP Server 入口
│   ├── mcp_server.py        # MCP Server 核心实现（中央编排服务）
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── logger.py        # 日志系统
│   │   └── exceptions.py    # 异常定义
│   ├── managers/            # 业务管理器
│   │   ├── workspace_manager.py  # 工作区管理
│   │   └── task_manager.py       # 任务管理
│   ├── tools/               # 8 个核心 SKILL 工具实现
│   │   ├── prd_generator.py
│   │   ├── trd_generator.py
│   │   ├── task_decomposer.py
│   │   ├── code_generator.py
│   │   ├── code_reviewer.py
│   │   ├── test_generator.py
│   │   ├── test_reviewer.py
│   │   └── coverage_analyzer.py
│   └── utils/               # 工具函数
│       └── file_lock.py     # 文件锁（并发安全）
└── tests/                   # 测试文件
    ├── conftest.py
    ├── test_main.py         # 主入口测试
    ├── test_mcp_server.py   # MCP Server 测试
    ├── core/
    ├── managers/
    ├── tools/
    └── utils/
```

## 安装

### 方式 1：使用虚拟环境（强烈推荐）

```bash
# 1. 确保使用 Python 3.9+
python3 --version

# 2. 创建虚拟环境
cd mcp-server
python3 -m venv venv

# 3. 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 验证安装
python3 -m pytest --version
```

### 方式 2：系统级安装（不推荐）

```bash
# 使用 --user 标志安装到用户目录
pip3 install --user -r requirements.txt
```

**注意**：如果遇到 "externally-managed-environment" 错误，请使用虚拟环境方式。

## 运行

### 确保虚拟环境已激活

```bash
# 如果使用虚拟环境，先激活
source venv/bin/activate  # macOS/Linux
```

### 运行主程序

```bash
# 方式 1：使用 PYTHONPATH
PYTHONPATH=. python3 src/main.py

# 方式 2：使用模块方式
PYTHONPATH=. python3 -m src.main
```

## 关闭 Server

### 自动关闭（推荐）

- **客户端断开时**：当 Cursor 关闭或断开连接时，Server 会自动检测并退出
- **无需手动操作**：Server 会随客户端生命周期自动管理

### 手动关闭

**如果直接运行 Server：**

```bash
# 方式 1：Ctrl+C（在运行 Server 的终端）
# 按 Ctrl+C

# 方式 2：使用 kill 命令
# 找到进程 ID
ps aux | grep "src/main.py"

# 优雅关闭
kill <PID>

# 强制关闭（不推荐）
kill -9 <PID>
```

**详细说明请参考：** [SHUTDOWN.md](SHUTDOWN.md)

## 开发

### 运行测试（TDD 流程）

```bash
# 确保虚拟环境已激活
source venv/bin/activate  # macOS/Linux

# 运行所有测试
PYTHONPATH=. python3 -m pytest

# 运行测试并查看覆盖率（当前覆盖率：95.57%）
PYTHONPATH=. python3 -m pytest --cov=src --cov-report=html

# 运行特定测试文件
PYTHONPATH=. python3 -m pytest tests/managers/test_workspace_manager.py
PYTHONPATH=. python3 -m pytest tests/test_mcp_server.py  # MCP Server 测试
```

**测试统计**：
- 测试用例总数：101 个
- 测试覆盖率：95.57%（超过 90% 要求）
- 所有测试通过：✅

### 代码格式化

```bash
# 格式化代码
python3 -m black src tests

# 检查代码
python3 -m ruff check src tests

# 类型检查
python3 -m mypy src
```

## TDD 开发流程

本项目严格遵循 TDD（测试驱动开发）：

1. **Red**: 先写失败的测试
2. **Green**: 写最小实现让测试通过
3. **Refactor**: 重构改进代码

## Python 3 兼容性

- ✅ 使用 Python 3.9+ 内置类型提示（`dict`, `list` 而非 `Dict`, `List`）
- ✅ 使用 `from __future__ import annotations` 支持延迟求值（可选）
- ✅ 所有代码在 Python 3.9+ 环境下测试通过

## 多Agent支持

本项目支持多个Agent协作完成开发流程，通过以下机制确保并发安全：

### 核心功能

1. **工作流状态查询** (`get_workflow_status`)
   - 查询当前工作流各阶段状态
   - 识别可以开始的阶段和被阻塞的阶段
   - 计算工作流进度百分比

2. **阶段依赖检查** (`check_stage_ready`)
   - 检查指定阶段是否可以开始
   - 验证前置阶段依赖和文件依赖
   - 提供详细的依赖状态信息

3. **文件锁机制** (`file_lock`)
   - 确保并发访问工作区元数据的安全性
   - 支持多Agent同时更新不同状态字段
   - 防止数据损坏或丢失

### 支持场景

1. **不同阶段由不同Agent顺序完成**
   - Agent A → PRD生成
   - Agent B → TRD生成（查询状态后开始）
   - Agent C → 任务分解
   - Agent D, E, F → 并行处理不同任务

2. **不同任务由不同Agent并行处理**
   - 文件锁确保并发安全
   - 状态查询确保协调
   - 每个Agent更新自己的任务状态

3. **状态依赖检查防止错误执行**
   - 前置阶段未完成时，无法开始下一阶段
   - 清晰的错误提示

### 使用示例

```bash
# Agent A: 生成 PRD
@agent-orchestrator generate_prd workspace_id=req-xxx requirement_url=https://example.com/req
@agent-orchestrator confirm_prd workspace_id=req-xxx

# Agent B: 查询状态，发现 PRD 已完成
@agent-orchestrator get_workflow_status workspace_id=req-xxx

# Agent B: 检查 TRD 是否可以开始
@agent-orchestrator check_stage_ready workspace_id=req-xxx stage=trd

# Agent B: 生成 TRD
@agent-orchestrator generate_trd workspace_id=req-xxx

# Agent C, D, E: 并行处理不同任务
@agent-orchestrator generate_code workspace_id=req-xxx task_id=task-001
@agent-orchestrator generate_code workspace_id=req-xxx task_id=task-002
@agent-orchestrator generate_code workspace_id=req-xxx task_id=task-003
```

详细使用指南请参考：[MULTI_AGENT_GUIDE.md](MULTI_AGENT_GUIDE.md)
