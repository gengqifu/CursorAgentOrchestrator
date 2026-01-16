"""文件锁工具 - 支持多进程并发安全。

Python 3.9+ 兼容
"""

import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from src.core.logger import setup_logger

logger = setup_logger(__name__)


class FileLockError(Exception):
    """文件锁相关错误。"""

    pass


@contextmanager
def file_lock(file_path: Path, timeout: float = 30.0, retry_interval: float = 0.1):
    """文件锁上下文管理器。

    支持跨平台文件锁：
    - Unix/Linux/macOS: 使用 fcntl
    - Windows: 使用 msvcrt

    Args:
        file_path: 要锁定的文件路径
        timeout: 获取锁的超时时间（秒）
        retry_interval: 重试间隔（秒）

    Yields:
        None

    Raises:
        FileLockError: 当无法在超时时间内获取锁时

    Example:
        ```python
        from src.utils.file_lock import file_lock

        with file_lock(Path("workspace.json")):
            # 安全地读写文件
            workspace = json.load(...)
            workspace["status"] = "completed"
            json.dump(workspace, ...)
        ```
    """
    lock_file = file_path.with_suffix(file_path.suffix + ".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = None
    start_time = time.time()

    try:
        # 尝试获取锁
        while True:
            try:
                if sys.platform == "win32":
                    # Windows 使用 msvcrt
                    try:
                        import msvcrt
                    except ImportError:
                        raise FileLockError("Windows 平台需要 msvcrt 模块") from None
                    lock_fd = os.open(
                        str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR
                    )
                    # Windows 文件锁是进程级别的，这里使用独占创建模式
                    # 如果文件已存在，os.O_EXCL 会失败
                    break
                else:
                    # Unix/Linux/macOS 使用 fcntl
                    try:
                        import fcntl
                    except ImportError:
                        raise FileLockError("Unix 平台需要 fcntl 模块") from None
                    lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 非阻塞排他锁
                    break
            except OSError as e:
                # 锁被占用，检查超时
                if time.time() - start_time >= timeout:
                    raise FileLockError(
                        f"无法在 {timeout} 秒内获取文件锁: {file_path}. "
                        f"可能被其他进程占用。"
                    ) from e

                # 等待后重试
                time.sleep(retry_interval)
                if lock_fd is not None:
                    try:
                        os.close(lock_fd)
                    except OSError:
                        pass
                    lock_fd = None

        logger.debug(f"获取文件锁: {file_path}")

        # 执行受保护的操作
        yield

    finally:
        # 释放锁
        if lock_fd is not None:
            try:
                if sys.platform != "win32":
                    try:
                        import fcntl

                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    except ImportError:
                        pass  # 如果 fcntl 不可用，跳过解锁
                os.close(lock_fd)
            except OSError as e:
                logger.warning(f"释放文件锁时出错: {e}")

        # 删除锁文件（如果存在）
        try:
            if lock_file.exists():
                lock_file.unlink()
        except OSError as e:
            logger.warning(f"删除锁文件时出错: {e}")

        logger.debug(f"释放文件锁: {file_path}")


@contextmanager
def read_lock(file_path: Path, timeout: float = 30.0, retry_interval: float = 0.1):
    """读锁上下文管理器（共享锁）。

    允许多个进程同时读取，但阻止写入。

    Args:
        file_path: 要锁定的文件路径
        timeout: 获取锁的超时时间（秒）
        retry_interval: 重试间隔（秒）

    Yields:
        None

    Raises:
        FileLockError: 当无法在超时时间内获取锁时

    Note:
        Windows 平台不支持共享锁，会降级为排他锁。
    """
    lock_file = file_path.with_suffix(file_path.suffix + ".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = None
    start_time = time.time()

    try:
        while True:
            try:
                if sys.platform == "win32":
                    # Windows 不支持共享锁，使用排他锁
                    try:
                        import msvcrt
                    except ImportError:
                        raise FileLockError("Windows 平台需要 msvcrt 模块") from None
                    lock_fd = os.open(
                        str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR
                    )
                    break
                else:
                    # Unix/Linux/macOS 使用 fcntl 共享锁
                    try:
                        import fcntl
                    except ImportError:
                        raise FileLockError("Unix 平台需要 fcntl 模块") from None
                    lock_fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)
                    fcntl.flock(lock_fd, fcntl.LOCK_SH | fcntl.LOCK_NB)  # 非阻塞共享锁
                    break
            except OSError as e:
                if time.time() - start_time >= timeout:
                    raise FileLockError(
                        f"无法在 {timeout} 秒内获取读锁: {file_path}"
                    ) from e

                time.sleep(retry_interval)
                if lock_fd is not None:
                    try:
                        os.close(lock_fd)
                    except OSError:
                        pass
                    lock_fd = None

        logger.debug(f"获取读锁: {file_path}")
        yield

    finally:
        if lock_fd is not None:
            try:
                if sys.platform != "win32":
                    try:
                        import fcntl

                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    except ImportError:
                        pass  # 如果 fcntl 不可用，跳过解锁
                os.close(lock_fd)
            except OSError as e:
                logger.warning(f"释放读锁时出错: {e}")

        logger.debug(f"释放读锁: {file_path}")
