#!/bin/bash
# MCP Server 连接问题诊断脚本
# 用于排查 "mcp logs" 下没有内容的问题

set -e

echo "🔍 MCP Server 连接问题诊断"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查 1: 启动脚本是否存在
echo "1. 检查启动脚本..."
if [ -f "$SCRIPT_DIR/start_mcp_server.sh" ]; then
    echo -e "${GREEN}✓${NC} 启动脚本存在: $SCRIPT_DIR/start_mcp_server.sh"
    
    if [ -x "$SCRIPT_DIR/start_mcp_server.sh" ]; then
        echo -e "${GREEN}✓${NC} 启动脚本可执行"
    else
        echo -e "${RED}✗${NC} 启动脚本不可执行"
        echo "   修复: chmod +x $SCRIPT_DIR/start_mcp_server.sh"
    fi
else
    echo -e "${RED}✗${NC} 启动脚本不存在: $SCRIPT_DIR/start_mcp_server.sh"
    exit 1
fi

# 检查 2: 虚拟环境
echo ""
echo "2. 检查虚拟环境..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}✓${NC} 虚拟环境存在"
    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        echo -e "${GREEN}✓${NC} 虚拟环境可激活"
    fi
else
    echo -e "${YELLOW}⚠${NC} 虚拟环境不存在"
    echo "   建议: python3 -m venv venv"
fi

# 检查 3: 依赖
echo ""
echo "3. 检查依赖..."
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
    if python3 -c "import mcp" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} mcp 库已安装"
    else
        echo -e "${RED}✗${NC} mcp 库未安装"
        echo "   修复: pip install -r requirements.txt"
    fi
    deactivate
else
    echo -e "${YELLOW}⚠${NC} 跳过依赖检查（虚拟环境不存在）"
fi

# 检查 4: Cursor 配置文件
echo ""
echo "4. 检查 Cursor 配置文件..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    CURSOR_CONFIG="$HOME/Library/Application Support/Cursor/User/globalStorage"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CURSOR_CONFIG="$HOME/.config/Cursor/User/globalStorage"
else
    CURSOR_CONFIG="$APPDATA/Cursor/User/globalStorage"
fi

if [ -d "$CURSOR_CONFIG" ]; then
    echo -e "${GREEN}✓${NC} Cursor 配置目录存在"
    
    if [ -f "$CURSOR_CONFIG/mcp.json" ]; then
        echo -e "${GREEN}✓${NC} mcp.json 配置文件存在"
        
        # 检查 JSON 格式
        if python3 -m json.tool "$CURSOR_CONFIG/mcp.json" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} JSON 格式正确"
        else
            echo -e "${RED}✗${NC} JSON 格式错误"
            echo "   修复: 检查 JSON 语法"
        fi
        
        # 检查 agent-orchestrator 配置
        if grep -q "agent-orchestrator" "$CURSOR_CONFIG/mcp.json" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} agent-orchestrator 配置存在"
            
            # 提取 command 路径
            COMMAND_PATH=$(grep -A 5 "agent-orchestrator" "$CURSOR_CONFIG/mcp.json" | grep "command" | head -1 | sed 's/.*"command": *"\([^"]*\)".*/\1/')
            
            if [ -n "$COMMAND_PATH" ]; then
                echo -e "${BLUE}ℹ${NC} 配置的启动脚本路径: $COMMAND_PATH"
                
                # 检查路径是否为绝对路径
                if [[ "$COMMAND_PATH" == /* ]] || [[ "$COMMAND_PATH" == ~* ]]; then
                    echo -e "${GREEN}✓${NC} 路径是绝对路径"
                else
                    echo -e "${RED}✗${NC} 路径不是绝对路径（必须是绝对路径）"
                    echo "   当前路径: $COMMAND_PATH"
                    echo "   应该使用: $SCRIPT_DIR/start_mcp_server.sh"
                fi
                
                # 检查路径是否存在
                if [ -f "$COMMAND_PATH" ] || [ -x "$COMMAND_PATH" ]; then
                    echo -e "${GREEN}✓${NC} 启动脚本路径有效"
                else
                    echo -e "${RED}✗${NC} 启动脚本路径无效或不存在"
                    echo "   配置的路径: $COMMAND_PATH"
                    echo "   正确的路径应该是: $SCRIPT_DIR/start_mcp_server.sh"
                fi
            else
                echo -e "${YELLOW}⚠${NC} 未找到 command 配置"
            fi
        else
            echo -e "${YELLOW}⚠${NC} mcp.json 中未找到 agent-orchestrator 配置"
        fi
    else
        echo -e "${RED}✗${NC} mcp.json 配置文件不存在"
        echo "   应该创建: $CURSOR_CONFIG/mcp.json"
        echo "   参考示例: $SCRIPT_DIR/mcp.json.example"
    fi
else
    echo -e "${YELLOW}⚠${NC} Cursor 配置目录不存在: $CURSOR_CONFIG"
fi

# 检查 5: 测试启动脚本
echo ""
echo "5. 测试启动脚本（5秒超时）..."
if [ -f "$SCRIPT_DIR/start_mcp_server.sh" ] && [ -x "$SCRIPT_DIR/start_mcp_server.sh" ]; then
    # 使用 timeout 命令测试启动脚本（如果可用）
    if command -v timeout > /dev/null 2>&1; then
        if timeout 5 "$SCRIPT_DIR/start_mcp_server.sh" > /tmp/mcp_test.log 2>&1; then
            echo -e "${GREEN}✓${NC} 启动脚本可以执行（5秒内未退出）"
        else
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 124 ]; then
                echo -e "${GREEN}✓${NC} 启动脚本可以执行（超时是正常的，说明 Server 在运行）"
            else
                echo -e "${RED}✗${NC} 启动脚本执行失败（退出码: $EXIT_CODE）"
                echo "   错误日志:"
                cat /tmp/mcp_test.log | head -20
                echo ""
                echo "   完整日志: cat /tmp/mcp_test.log"
            fi
        fi
    else
        echo -e "${YELLOW}⚠${NC} 跳过测试（timeout 命令不可用）"
        echo "   手动测试: $SCRIPT_DIR/start_mcp_server.sh"
        echo "   （应该启动并等待输入，按 Ctrl+C 退出）"
    fi
else
    echo -e "${RED}✗${NC} 启动脚本不存在或不可执行"
fi

# 检查 6: Python 环境
echo ""
echo "6. 检查 Python 环境..."
if python3 --version | grep -E "Python 3\.([9]|[1-9][0-9])" > /dev/null; then
    echo -e "${GREEN}✓${NC} $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python 版本不符合要求（需要 3.9+）"
    python3 --version
fi

# 总结
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 诊断总结"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "如果所有检查项都显示 ✓，但 Cursor 中仍然没有日志："
echo ""
echo "1. 完全重启 Cursor IDE（完全关闭后重新打开）"
echo "2. 等待几秒钟让 Cursor 加载 MCP Server"
echo "3. 查看 Cursor 开发者工具（Cmd+Shift+P → Developer: Toggle Developer Tools）"
echo "4. 在 Console 中搜索 'MCP' 或 'agent-orchestrator' 查看错误"
echo ""
echo "如果看到错误，请参考: mcp-server/VERIFICATION_GUIDE.md"
echo ""
