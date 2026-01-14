#!/usr/bin/env python3
"""Cursor Agent Orchestrator MCP Server 入口。

Python 版本要求：>= 3.9

运行方式：
    python3 -m src.main
    或
    cd mcp-server && PYTHONPATH=. python3 src/main.py

关闭方式：
    1. 客户端断开连接时自动关闭（推荐）
    2. Ctrl+C (SIGINT) - 优雅关闭
    3. kill <PID> (SIGTERM) - 优雅关闭
"""
import sys
import signal
import atexit
from pathlib import Path

# 检查 Python 版本
if sys.version_info < (3, 9):
    print("错误：需要 Python 3.9 或更高版本", file=sys.stderr)
    print(f"当前版本：{sys.version}", file=sys.stderr)
    sys.exit(1)

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.logger import setup_logger

logger = setup_logger(__name__)

# 全局关闭标志
_shutdown_requested = False
_cleanup_called = False


def safe_log_info(message: str) -> None:
    """安全地记录日志信息，避免在关闭时写入已关闭的文件流。
    
    Args:
        message: 日志消息
    """
    try:
        # 检查日志处理器是否仍然可用
        if logger.handlers:
            for handler in logger.handlers:
                if hasattr(handler, 'stream') and handler.stream and not handler.stream.closed:
                    logger.info(message)
                    return
        # 如果日志不可用，使用 print 输出到 stderr
        print(f"[INFO] {message}", file=sys.stderr)
    except (ValueError, AttributeError, OSError):
        # 如果日志系统已关闭，使用 print
        try:
            print(f"[INFO] {message}", file=sys.stderr)
        except OSError:
            # stderr 也可能已关闭，忽略
            pass


def cleanup_resources() -> None:
    """清理资源。"""
    global _cleanup_called
    
    # 避免重复清理
    if _cleanup_called:
        return
    
    _cleanup_called = True
    
    safe_log_info("清理资源...")
    
    # TODO: 添加资源清理逻辑
    # - 关闭文件句柄
    # - 释放文件锁
    # - 保存工作区状态
    
    safe_log_info("资源清理完成")


def signal_handler(signum: int, frame) -> None:
    """信号处理器，用于优雅关闭。
    
    Args:
        signum: 信号编号
        frame: 当前堆栈帧
    """
    global _shutdown_requested
    
    signal_name = signal.Signals(signum).name
    safe_log_info(f"收到信号 {signal_name} ({signum})，准备关闭...")
    
    _shutdown_requested = True
    cleanup_resources()
    
    safe_log_info("MCP Server 已关闭")
    sys.exit(0)


def setup_signal_handlers() -> None:
    """设置信号处理器。"""
    # SIGINT: Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # SIGTERM: kill 命令默认信号
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 注册退出时的清理函数
    atexit.register(cleanup_resources)


if __name__ == "__main__":
    # 设置信号处理器
    setup_signal_handlers()
    
    logger.info(f"MCP Server 启动中... (Python {sys.version_info.major}.{sys.version_info.minor})")
    logger.info("提示：使用 Ctrl+C 关闭 Server")
    
    try:
        # 导入并运行 MCP Server
        import asyncio
        from src.mcp_server import run_server
        
        logger.info("MCP Server 已启动，等待连接...")
        logger.info("可用工具：")
        logger.info("  基础设施工具：create_workspace, get_workspace, update_workspace_status, get_tasks, update_task_status")
        logger.info("  SKILL 工具：generate_prd, generate_trd, decompose_tasks, generate_code, review_code, generate_tests, review_tests, analyze_coverage")
        
        # 运行 MCP Server（使用 stdio 通信）
        asyncio.run(run_server())
        
    except KeyboardInterrupt:
        safe_log_info("收到键盘中断信号")
    except Exception as e:
        try:
            logger.error(f"Server 运行错误: {e}", exc_info=True)
        except (ValueError, AttributeError, OSError):
            print(f"[ERROR] Server 运行错误: {e}", file=sys.stderr)
    finally:
        cleanup_resources()
        safe_log_info("MCP Server 已关闭")
