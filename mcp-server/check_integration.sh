#!/bin/bash
# Cursor 集成检查脚本
# 检查 Agent Orchestrator MCP Server 是否正确配置

set -e

echo "🔍 检查 Cursor 集成配置..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo "1. 检查 Python 版本..."
if python3 --version | grep -E "Python 3\.([9]|[1-9][0-9])" > /dev/null; then
    echo -e "${GREEN}✓${NC} $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python 版本不符合要求（需要 3.9+）"
    exit 1
fi

# 检查虚拟环境
echo ""
echo "2. 检查虚拟环境..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}✓${NC} 虚拟环境存在"
    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        echo -e "${GREEN}✓${NC} 虚拟环境可激活"
    fi
else
    echo -e "${YELLOW}⚠${NC} 虚拟环境不存在，建议运行: python3 -m venv venv"
fi

# 检查依赖
echo ""
echo "3. 检查依赖..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    if python3 -c "import mcp" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} mcp 库已安装"
    else
        echo -e "${RED}✗${NC} mcp 库未安装，运行: pip install -r requirements.txt"
    fi
    deactivate
else
    echo -e "${YELLOW}⚠${NC} 跳过依赖检查（虚拟环境不存在）"
fi

# 检查启动脚本
echo ""
echo "4. 检查启动脚本..."
if [ -f "$SCRIPT_DIR/start_mcp_server.sh" ]; then
    echo -e "${GREEN}✓${NC} 启动脚本存在"
    if [ -x "$SCRIPT_DIR/start_mcp_server.sh" ]; then
        echo -e "${GREEN}✓${NC} 启动脚本可执行"
    else
        echo -e "${YELLOW}⚠${NC} 启动脚本不可执行，运行: chmod +x start_mcp_server.sh"
    fi
else
    echo -e "${RED}✗${NC} 启动脚本不存在"
fi

# 检查 Cursor 配置目录
echo ""
echo "5. 检查 Cursor 配置目录..."
CURSOR_CONFIG_MACOS="$HOME/Library/Application Support/Cursor/User/globalStorage"
CURSOR_CONFIG_LINUX="$HOME/.config/Cursor/User/globalStorage"
CURSOR_CONFIG_WINDOWS="$APPDATA/Cursor/User/globalStorage"

if [[ "$OSTYPE" == "darwin"* ]]; then
    CURSOR_CONFIG="$CURSOR_CONFIG_MACOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURSOR_CONFIG="$CURSOR_CONFIG_LINUX"
else
    CURSOR_CONFIG="$CURSOR_CONFIG_WINDOWS"
fi

if [ -d "$CURSOR_CONFIG" ]; then
    echo -e "${GREEN}✓${NC} Cursor 配置目录存在: $CURSOR_CONFIG"
    
    if [ -f "$CURSOR_CONFIG/mcp.json" ]; then
        echo -e "${GREEN}✓${NC} mcp.json 配置文件存在"
        
        # 检查是否包含 agent-orchestrator 配置
        if grep -q "agent-orchestrator" "$CURSOR_CONFIG/mcp.json" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} agent-orchestrator 配置已存在"
        else
            echo -e "${YELLOW}⚠${NC} mcp.json 中未找到 agent-orchestrator 配置"
            echo "   请参考 mcp.json.example 添加配置"
        fi
    else
        echo -e "${YELLOW}⚠${NC} mcp.json 配置文件不存在"
        echo "   请创建配置文件: $CURSOR_CONFIG/mcp.json"
        echo "   参考示例: $SCRIPT_DIR/mcp.json.example"
    fi
else
    echo -e "${YELLOW}⚠${NC} Cursor 配置目录不存在: $CURSOR_CONFIG"
    echo "   可能 Cursor 尚未运行过，或路径不正确"
fi

# 检查路径配置
echo ""
echo "6. 检查路径配置..."
if [ -f "$CURSOR_CONFIG/mcp.json" ]; then
    # 提取 command 路径
    COMMAND_PATH=$(grep -A 5 "agent-orchestrator" "$CURSOR_CONFIG/mcp.json" | grep "command" | head -1 | sed 's/.*"command": *"\([^"]*\)".*/\1/')
    
    if [ -n "$COMMAND_PATH" ]; then
        if [ -f "$COMMAND_PATH" ] || [ -x "$COMMAND_PATH" ]; then
            echo -e "${GREEN}✓${NC} 启动脚本路径有效: $COMMAND_PATH"
        else
            echo -e "${RED}✗${NC} 启动脚本路径无效: $COMMAND_PATH"
            echo "   请更新 mcp.json 中的路径为: $SCRIPT_DIR/start_mcp_server.sh"
        fi
    fi
fi

echo ""
echo "✅ 检查完成！"
echo ""
echo "📝 下一步："
echo "   1. 如果虚拟环境不存在，运行: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
echo "   2. 如果 mcp.json 不存在，创建配置文件并参考 mcp.json.example"
echo "   3. 重启 Cursor IDE"
echo "   4. 在 Cursor 中测试工具调用"
