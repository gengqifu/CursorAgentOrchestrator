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
        # TODO: 实现 MCP Server 主逻辑
        # 当通过 stdio 运行时，如果 stdin 关闭，循环会自动退出
        logger.info("MCP Server 已启动，等待连接...")
        
        # 模拟主循环（实际实现时会使用 MCP Server 的事件循环）
        # 当 stdin 关闭时，readline() 会抛出异常或返回空
        while not _shutdown_requested:
            try:
                # 尝试读取 stdin（阻塞或非阻塞取决于配置）
                # 当 stdin 关闭时，readline() 会返回空字符串
                if sys.stdin.isatty():
                    # 交互式终端模式 - 等待用户输入或 Ctrl+C
                    import select
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        line = sys.stdin.readline()
                        if not line:  # EOF
                            safe_log_info("检测到 stdin 关闭，准备退出...")
                            break
                else:
                    # 非交互式模式（通过管道运行）- 等待数据或 EOF
                    line = sys.stdin.readline()
                    if not line:  # EOF - stdin 已关闭
                        safe_log_info("检测到 stdin 关闭，准备退出...")
                        break
            except (EOFError, KeyboardInterrupt):
                safe_log_info("检测到输入流关闭或中断")
                break
            except Exception as e:
                # 其他错误（如 select 在 Windows 上不支持）
                try:
                    logger.debug(f"读取 stdin 时出错: {e}")
                except (ValueError, AttributeError, OSError):
                    pass
                # 短暂休眠后继续
                import time
                time.sleep(0.1)
        
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
