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
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   ├── logger.py        # 日志系统
│   │   └── exceptions.py    # 异常定义
│   ├── managers/            # 业务管理器
│   │   ├── __init__.py
│   │   ├── workspace_manager.py
│   │   └── task_manager.py
│   ├── tools/               # MCP 工具
│   │   ├── __init__.py
│   │   └── ...
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── file_lock.py
│       └── git_utils.py
└── tests/                   # 测试文件
    ├── __init__.py
    ├── conftest.py
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

# 运行测试并查看覆盖率
PYTHONPATH=. python3 -m pytest --cov=src --cov-report=html

# 运行特定测试文件
PYTHONPATH=. python3 -m pytest tests/managers/test_workspace_manager.py
```

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
