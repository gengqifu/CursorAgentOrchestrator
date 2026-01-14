#!/bin/bash
# 快速安装脚本

set -e

echo "🚀 开始安装 Cursor Agent Orchestrator MCP Server..."

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python3 --version

# 创建虚拟环境
echo "📦 创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境并安装依赖
echo "📥 安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ 安装完成！"
echo ""
echo "📝 下一步："
echo "   1. 激活虚拟环境: source venv/bin/activate"
echo "   2. 运行测试: PYTHONPATH=. python3 -m pytest"
echo "   3. 运行主程序: PYTHONPATH=. python3 src/main.py"
