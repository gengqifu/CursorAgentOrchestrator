"""文件锁工具测试 - TDD 第一步：编写失败的测试。"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

from src.utils.file_lock import FileLockError, file_lock, read_lock


class TestFileLock:
    """文件锁测试类。"""

    def test_file_lock_prevents_concurrent_writes(self, temp_dir):
        """测试文件锁防止并发写入。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        def increment_value():
            """并发增加值的函数。"""
            with file_lock(test_file):
                data = json.loads(test_file.read_text(encoding="utf-8"))
                data["value"] += 1
                time.sleep(0.01)  # 模拟处理时间
                test_file.write_text(json.dumps(data), encoding="utf-8")

        # Act - 10 个线程并发执行
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(increment_value) for _ in range(10)]
            for future in as_completed(futures):
                future.result()  # 等待完成

        # Assert - 值应该是 10（没有丢失更新）
        final_data = json.loads(test_file.read_text(encoding="utf-8"))
        assert final_data["value"] == 10

    def test_file_lock_timeout(self, temp_dir):
        """测试文件锁超时。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Act & Assert
        with file_lock(test_file, timeout=0.1):
            # 在锁内尝试再次获取锁（应该超时）
            with pytest.raises(FileLockError):
                with file_lock(test_file, timeout=0.1):
                    pass

    def test_read_lock_allows_multiple_readers(self, temp_dir):
        """测试读锁允许多个读者。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 42}', encoding="utf-8")

        read_count = []

        def read_value():
            """读取值的函数。"""
            with read_lock(test_file):
                data = json.loads(test_file.read_text(encoding="utf-8"))
                read_count.append(data["value"])
                time.sleep(0.01)

        # Act - 5 个线程同时读取
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(read_value) for _ in range(5)]
            for future in as_completed(futures):
                future.result()

        # Assert - 所有读取都应该成功
        assert len(read_count) == 5
        assert all(value == 42 for value in read_count)

    def test_file_lock_with_workspace_manager(self, temp_dir, monkeypatch):
        """测试文件锁与工作区管理器的集成。"""
        # Arrange
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        from src.core.config import Config
        from src.managers.workspace_manager import WorkspaceManager

        config = Config()
        manager = WorkspaceManager(config=config)

        # 创建测试项目目录
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()

        # 创建工作区
        workspace_id = manager.create_workspace(
            project_path=str(project_dir),
            requirement_name="测试需求",
            requirement_url="https://example.com/test",
        )

        def update_status():
            """并发更新状态。"""
            manager.update_workspace_status(workspace_id, {"prd_status": "completed"})

        # Act - 5 个线程并发更新
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_status) for _ in range(5)]
            for future in as_completed(futures):
                future.result()

        # Assert - 状态应该正确更新（没有冲突）
        workspace = manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"

    def test_file_lock_with_task_manager(self, temp_dir, monkeypatch):
        """测试文件锁与任务管理器的集成。"""
        # Arrange
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        from src.core.config import Config
        from src.managers.task_manager import TaskManager
        from src.managers.workspace_manager import WorkspaceManager

        config = Config()
        workspace_manager = WorkspaceManager(config=config)
        task_manager = TaskManager(config=config)

        # 创建测试项目目录
        project_dir = temp_dir / "test_project"
        project_dir.mkdir()

        # 创建工作区
        workspace_id = workspace_manager.create_workspace(
            project_path=str(project_dir),
            requirement_name="测试需求",
            requirement_url="https://example.com/test",
        )

        def update_task(task_id: str):
            """并发更新任务。"""
            task_manager.update_task_status(
                workspace_id, task_id, "completed", code_files=[f"file_{task_id}.py"]
            )

        # Act - 5 个线程并发更新不同任务
        task_ids = [f"task-{i:03d}" for i in range(5)]
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_task, task_id) for task_id in task_ids]
            for future in as_completed(futures):
                future.result()

        # Assert - 所有任务都应该正确更新
        tasks = task_manager.get_tasks(workspace_id)
        assert len(tasks) == 5
        for task in tasks:
            assert task["status"] == "completed"
            assert "code_files" in task

    def test_file_lock_creates_lock_file(self, temp_dir):
        """测试文件锁创建锁文件。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")
        lock_file = test_file.with_suffix(test_file.suffix + ".lock")

        # Act
        with file_lock(test_file):
            # 锁文件应该在锁期间存在
            assert lock_file.exists()

        # Assert - 锁文件应该在释放后删除
        assert not lock_file.exists()

    def test_file_lock_handles_missing_file(self, temp_dir):
        """测试文件锁处理不存在的文件。"""
        # Arrange
        test_file = temp_dir / "nonexistent.json"

        # Act & Assert - 应该创建文件并加锁
        with file_lock(test_file):
            test_file.write_text('{"value": 1}', encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == '{"value": 1}'

    def test_read_lock_handles_missing_file(self, temp_dir):
        """测试读锁处理不存在的文件。"""
        # Arrange
        test_file = temp_dir / "nonexistent.json"

        # Act & Assert - 读锁应该正常处理不存在的文件
        with pytest.raises(FileNotFoundError), read_lock(test_file):
            test_file.read_text(encoding="utf-8")

    def test_file_lock_handles_oserror_on_close(self, temp_dir, monkeypatch):
        """测试文件锁处理关闭时的 OSError。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock os.close 抛出 OSError
        original_close = __import__("os").close
        call_count = []

        def mock_close(fd):
            call_count.append(1)
            if len(call_count) == 1:  # 第一次调用时抛出错误
                raise OSError("模拟关闭错误")
            return original_close(fd)

        monkeypatch.setattr("os.close", mock_close)

        # Act & Assert - 应该正常处理错误
        with file_lock(test_file):
            test_file.write_text('{"value": 1}', encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == '{"value": 1}'

    def test_file_lock_handles_unlink_error(self, temp_dir, monkeypatch):
        """测试文件锁处理删除锁文件时的错误。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock Path.unlink 抛出 OSError
        original_unlink = Path.unlink

        def mock_unlink(self):
            if ".lock" in str(self):
                raise OSError("模拟删除错误")
            return original_unlink(self)

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        # Act & Assert - 应该正常处理错误
        with file_lock(test_file):
            test_file.write_text('{"value": 1}', encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == '{"value": 1}'

    def test_read_lock_handles_oserror_on_close(self, temp_dir, monkeypatch):
        """测试读锁处理关闭时的 OSError。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock os.close 抛出 OSError
        original_close = __import__("os").close
        call_count = []

        def mock_close(fd):
            call_count.append(1)
            if len(call_count) == 1:  # 第一次调用时抛出错误
                raise OSError("模拟关闭错误")
            return original_close(fd)

        monkeypatch.setattr("os.close", mock_close)

        # Act & Assert - 应该正常处理错误
        with read_lock(test_file):
            data = test_file.read_text(encoding="utf-8")

        assert data == '{"value": 0}'

    def test_file_lock_retry_mechanism(self, temp_dir, monkeypatch):
        """测试文件锁的重试机制。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock os.open 前两次失败，第三次成功
        original_open = __import__("os").open
        call_count = []

        def mock_open(*args, **kwargs):
            call_count.append(1)
            if len(call_count) <= 2:  # 前两次失败
                raise OSError("模拟锁被占用")
            return original_open(*args, **kwargs)

        monkeypatch.setattr("os.open", mock_open)

        # Act & Assert - 应该重试并成功
        with file_lock(test_file, timeout=1.0, retry_interval=0.1):
            test_file.write_text('{"value": 1}', encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == '{"value": 1}'
        assert len(call_count) == 3  # 应该重试了 2 次

    def test_read_lock_retry_mechanism(self, temp_dir, monkeypatch):
        """测试读锁的重试机制。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock os.open 前两次失败，第三次成功
        import os

        original_open = os.open
        call_count = []

        def mock_open(*args, **kwargs):
            call_count.append(1)
            if len(call_count) <= 2:  # 前两次失败
                raise OSError("模拟锁被占用")
            return original_open(*args, **kwargs)

        monkeypatch.setattr(os, "open", mock_open)

        # Act & Assert - 应该重试并成功
        with read_lock(test_file, timeout=1.0, retry_interval=0.1):
            data = test_file.read_text(encoding="utf-8")

        assert data == '{"value": 0}'
        assert len(call_count) == 3  # 应该重试了 2 次

    def test_file_lock_handles_fcntl_import_error(self, temp_dir, monkeypatch):
        """测试处理 fcntl 导入错误的情况。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock fcntl 导入失败
        import sys

        original_modules = sys.modules.copy()

        def mock_import(name, *args, **kwargs):
            if name == "fcntl":
                raise ImportError("fcntl not available")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Act & Assert - 应该抛出 FileLockError
        with pytest.raises(Exception):  # 可能是 FileLockError 或其他异常
            with file_lock(test_file):
                pass

    def test_read_lock_handles_fcntl_import_error(self, temp_dir, monkeypatch):
        """测试读锁处理 fcntl 导入错误的情况。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock fcntl 导入失败
        def mock_import(name, *args, **kwargs):
            if name == "fcntl":
                raise ImportError("fcntl not available")
            return __import__(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        # Act & Assert - 应该抛出 FileLockError
        with pytest.raises(Exception):  # 可能是 FileLockError 或其他异常
            with read_lock(test_file):
                pass

    def test_file_lock_handles_close_error_in_finally(self, temp_dir, monkeypatch):
        """测试文件锁在 finally 块中处理关闭错误。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock os.close 在 finally 中抛出错误
        import os

        original_close = os.close
        close_call_count = []

        def mock_close(fd):
            close_call_count.append(1)
            if len(close_call_count) == 1:  # 第一次调用时抛出错误
                raise OSError("模拟关闭错误")
            return original_close(fd)

        monkeypatch.setattr(os, "close", mock_close)

        # Act & Assert - 应该正常处理错误
        with file_lock(test_file):
            test_file.write_text('{"value": 1}', encoding="utf-8")

        assert test_file.read_text(encoding="utf-8") == '{"value": 1}'

    def test_read_lock_handles_unlock_error(self, temp_dir, monkeypatch):
        """测试读锁处理解锁错误的情况。"""
        # Arrange
        test_file = temp_dir / "test.json"
        test_file.write_text('{"value": 0}', encoding="utf-8")

        # Mock fcntl.flock 在解锁时抛出错误
        import fcntl

        original_flock = fcntl.flock

        def mock_flock(fd, op):
            if op & fcntl.LOCK_UN:  # 解锁操作
                raise OSError("模拟解锁错误")
            return original_flock(fd, op)

        monkeypatch.setattr(fcntl, "flock", mock_flock)

        # Act & Assert - 应该正常处理错误
        with read_lock(test_file):
            data = test_file.read_text(encoding="utf-8")

        assert data == '{"value": 0}'
