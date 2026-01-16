"""测试路径询问工具测试 - TDD 第一步：编写失败的测试。"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import ValidationError, WorkspaceNotFoundError
from src.tools.test_path_question import ask_test_path, submit_test_path
from tests.conftest import create_test_workspace


class TestTestPathQuestion:
    """测试路径询问工具测试类。"""

    def test_ask_test_path_success(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试询问测试路径成功。

        验证返回的字典包含所有必需字段，question 包含正确的默认路径。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act
        result = ask_test_path(workspace_id)

        # Assert
        assert result["success"] is True
        assert result["interaction_required"] is True
        assert result["interaction_type"] == "question"
        assert "question" in result

        question = result["question"]
        assert question["id"] == "test_path"
        assert question["question"] == "请输入测试输出目录路径"
        assert question["type"] == "text"
        assert question["required"] is True
        assert "default" in question
        assert "placeholder" in question

        # 验证默认路径格式
        default_path = question["default"]
        assert str(sample_project_dir) in default_path
        assert "tests" in default_path
        assert "mock" in default_path

    def test_ask_test_path_workspace_not_found(self):
        """测试工作区不存在。

        验证当工作区不存在时抛出 WorkspaceNotFoundError。
        """
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            ask_test_path("nonexistent-workspace-id")

    def test_ask_test_path_missing_project_path(self, temp_dir, workspace_manager):
        """测试工作区缺少 project_path 字段。

        验证当工作区缺少 project_path 字段时抛出 ValidationError。
        """
        # Arrange - 创建一个缺少 project_path 的工作区
        workspace_id = "req-20240115-123456-测试需求"
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        workspace_meta = {
            "workspace_id": workspace_id,
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/req.md",
            "created_at": "2024-01-15T12:34:56",
            "status": {
                "prd_status": "pending",
                "trd_status": "pending",
                "tasks_status": "pending",
                "code_status": "pending",
                "test_status": "pending",
            },
            "files": {"prd_path": None, "trd_path": None, "tasks_json_path": None},
        }

        meta_file = workspace_dir / "workspace.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace_meta, f, ensure_ascii=False, indent=2)

        # Act & Assert
        with pytest.raises(ValidationError, match="缺少 project_path 字段"):
            ask_test_path(workspace_id)

    def test_submit_test_path_success(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试提交测试路径成功。

        验证成功提交时返回 test_path，并保存到工作区元数据。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_path = str(sample_project_dir / "tests" / "mock")

        # Act
        result = submit_test_path(workspace_id, test_path)

        # Assert
        assert result["success"] is True
        assert result["workspace_id"] == workspace_id
        assert result["test_path"] == test_path

        # 验证已保存到工作区元数据
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["files"]["test_path"] == test_path

        # 验证目录已创建
        assert Path(test_path).exists()
        assert Path(test_path).is_dir()

    def test_submit_test_path_relative_path(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试提交相对路径。

        验证相对路径会被转换为相对于项目路径的绝对路径。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        relative_path = "tests/mock"

        # Act
        result = submit_test_path(workspace_id, relative_path)

        # Assert
        expected_path = str(sample_project_dir / relative_path)
        assert result["test_path"] == expected_path

        # 验证已保存到工作区元数据
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["files"]["test_path"] == expected_path

    def test_submit_test_path_empty(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试提交空路径。

        验证空路径时抛出 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act & Assert
        with pytest.raises(ValidationError, match="测试路径不能为空"):
            submit_test_path(workspace_id, "")

        with pytest.raises(ValidationError, match="测试路径不能为空"):
            submit_test_path(workspace_id, "   ")

    def test_submit_test_path_workspace_not_found(self, temp_dir):
        """测试工作区不存在。

        验证当工作区不存在时抛出 WorkspaceNotFoundError。
        """
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            submit_test_path("nonexistent-workspace-id", "/tmp/tests/mock")

    def test_submit_test_path_existing_file(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试测试路径已存在但不是目录。

        验证当路径已存在但不是目录时抛出 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_file = sample_project_dir / "tests" / "mock"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")

        # Act & Assert
        with pytest.raises(ValidationError, match="测试路径已存在但不是目录"):
            submit_test_path(workspace_id, str(test_file))

    def test_submit_test_path_parent_not_writable(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试父目录不可写。

        验证当父目录不可写时抛出 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_path = "/root/tests/mock"  # 假设 /root 不可写（在大多数系统上）

        # Act & Assert
        # 注意：这个测试可能在某些系统上失败，因为 /root 可能不存在或可写
        # 实际行为是：当尝试创建父目录时失败，抛出"无法创建父目录"异常
        # 或者当父目录存在但不可写时，抛出"父目录不可写"异常
        with pytest.raises(ValidationError) as exc_info:
            submit_test_path(workspace_id, test_path)

        # 验证错误消息包含"无法创建父目录"或"父目录不可写"
        error_msg = str(exc_info.value)
        assert "无法创建父目录" in error_msg or "父目录不可写" in error_msg

    def test_submit_test_path_missing_project_path(self, temp_dir, workspace_manager):
        """测试工作区缺少 project_path 字段（在 submit_test_path 中）。

        验证当工作区缺少 project_path 字段时抛出 ValidationError。
        """
        # Arrange - 创建一个缺少 project_path 的工作区
        workspace_id = "req-20240115-123456-测试需求"
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        workspace_meta = {
            "workspace_id": workspace_id,
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/req.md",
            "created_at": "2024-01-15T12:34:56",
            "status": {
                "prd_status": "pending",
                "trd_status": "pending",
                "tasks_status": "pending",
                "code_status": "pending",
                "test_status": "pending",
            },
            "files": {"prd_path": None, "trd_path": None, "tasks_json_path": None},
        }

        meta_file = workspace_dir / "workspace.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace_meta, f, ensure_ascii=False, indent=2)

        # Act & Assert
        with pytest.raises(ValidationError, match="缺少 project_path 字段"):
            submit_test_path(workspace_id, "tests/mock")

    def test_submit_test_path_parent_not_writable_check(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试父目录存在但不可写。

        验证当父目录存在但不可写时抛出 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_dir = sample_project_dir / "tests" / "mock"
        test_dir.parent.mkdir(parents=True, exist_ok=True)

        # Mock os.access 返回 False（不可写）
        with patch("src.tools.test_path_question.os.access", return_value=False):
            with pytest.raises(ValidationError, match="父目录不可写"):
                submit_test_path(workspace_id, str(test_dir))

    def test_submit_test_path_create_directory_error(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试创建测试目录失败。

        验证当创建测试目录失败时抛出 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_path = sample_project_dir / "tests" / "mock"
        test_path.parent.mkdir(parents=True, exist_ok=True)

        # Mock test_path_obj.mkdir 抛出异常（只影响测试路径的创建）
        # 我们需要在函数内部 mock，因为需要先创建 Path 对象
        original_mkdir = Path.mkdir

        def mock_mkdir(self, *args, **kwargs):
            # 只对测试路径的 mkdir 调用抛出异常
            if str(self) == str(test_path):
                raise PermissionError("Permission denied")
            return original_mkdir(self, *args, **kwargs)

        with patch.object(Path, "mkdir", side_effect=mock_mkdir, autospec=True):
            with pytest.raises(ValidationError) as exc_info:
                submit_test_path(workspace_id, str(test_path))

            # 验证错误消息包含"无法创建测试目录"或"提交测试路径失败"
            error_msg = str(exc_info.value)
            assert "无法创建测试目录" in error_msg or "提交测试路径失败" in error_msg

    def test_submit_test_path_workspace_file_missing(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试工作区元数据文件不存在。

        验证当工作区元数据文件不存在时抛出 WorkspaceNotFoundError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # 删除 workspace.json
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        meta_file = workspace_dir / "workspace.json"
        meta_file.unlink()

        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            submit_test_path(workspace_id, str(sample_project_dir / "tests" / "mock"))

    def test_submit_test_path_missing_files_field(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试工作区元数据缺少 files 字段。

        验证当工作区元数据缺少 files 字段时，会自动创建。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # 删除 files 字段
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        meta_file = workspace_dir / "workspace.json"

        with open(meta_file, encoding="utf-8") as f:
            workspace_data = json.load(f)

        del workspace_data["files"]

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace_data, f, ensure_ascii=False, indent=2)

        test_path = str(sample_project_dir / "tests" / "mock")

        # Act
        result = submit_test_path(workspace_id, test_path)

        # Assert
        assert result["success"] is True

        # 验证 files 字段已创建
        workspace = workspace_manager.get_workspace(workspace_id)
        assert "files" in workspace
        assert workspace["files"]["test_path"] == test_path

    def test_ask_test_path_exception(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试 ask_test_path 发生异常。

        验证当 ask_test_path 发生非预期异常时，会被捕获并转换为 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Mock WorkspaceManager.get_workspace 抛出异常
        with patch(
            "src.tools.test_path_question.WorkspaceManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.get_workspace.side_effect = RuntimeError("Unexpected error")

            # Act & Assert
            with pytest.raises(ValidationError, match="询问测试路径失败"):
                ask_test_path(workspace_id)

    def test_submit_test_path_exception(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试 submit_test_path 发生异常。

        验证当 submit_test_path 发生非预期异常时，会被捕获并转换为 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_path = str(sample_project_dir / "tests" / "mock")

        # Mock json.dump 抛出异常
        with patch("json.dump", side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(ValidationError, match="提交测试路径失败"):
                submit_test_path(workspace_id, test_path)

    def test_submit_test_path_meta_file_not_exists_in_lock(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试在文件锁内检查 meta_file 不存在。

        验证当在文件锁内检查 meta_file 不存在时抛出 WorkspaceNotFoundError。
        这覆盖了第 175 行的检查。
        """
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)
        test_path = str(sample_project_dir / "tests" / "mock")

        # 在文件锁获取后删除 meta_file（模拟并发删除）
        from src.core.config import Config
        from src.utils.file_lock import file_lock

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        meta_file = workspace_dir / "workspace.json"

        # Mock file_lock 上下文管理器，在进入时删除文件
        original_file_lock = file_lock

        @patch("src.tools.test_path_question.file_lock")
        def test_with_mock_lock(mock_lock):
            def lock_context(meta_file_path):
                # 删除文件以触发第 175 行的检查
                if meta_file_path == meta_file:
                    meta_file.unlink()
                # 返回一个上下文管理器
                from contextlib import contextmanager

                @contextmanager
                def lock():
                    yield

                return lock()

            mock_lock.side_effect = lock_context

            # Act & Assert
            with pytest.raises(WorkspaceNotFoundError):
                submit_test_path(workspace_id, test_path)

        test_with_mock_lock()
