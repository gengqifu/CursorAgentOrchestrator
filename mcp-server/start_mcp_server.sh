#!/bin/bash
# Agent Orchestrator MCP Server 启动脚本
# 用于 Cursor IDE 集成

set -e

# 获取脚本所在目录（绝对路径）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 Python 版本
if ! python3 --version | grep -E "Python 3\.([9]|[1-9][0-9])" > /dev/null; then
    echo "错误：需要 Python 3.9 或更高版本" >&2
    python3 --version >&2
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 设置环境变量
export AGENT_ORCHESTRATOR_ROOT="${AGENT_ORCHESTRATOR_ROOT:-$(dirname "$SCRIPT_DIR")}"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 运行 MCP Server
exec python3 src/main.py
