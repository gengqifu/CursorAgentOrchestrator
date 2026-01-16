"""TRD 确认工具测试 - TDD 第一步：编写失败的测试。"""

from unittest.mock import patch

import pytest

from src.core.exceptions import WorkspaceNotFoundError
from src.tools.trd_confirmation import check_trd_confirmation, confirm_trd, modify_trd
from tests.conftest import create_test_workspace


class TestTRDConfirmation:
    """TRD 确认工具测试类。"""

    def test_check_trd_confirmation_trd_exists(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试 TRD 存在时的确认请求。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # 创建 TRD 文件
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_path = workspace_dir / "TRD.md"
        trd_path.write_text("# TRD 文档\n\n这是测试 TRD 内容。", encoding="utf-8")

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["trd_path"] = str(trd_path)
        meta_file = workspace_dir / "workspace.json"
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Act
        result = check_trd_confirmation(workspace_id)

        # Assert
        assert result["success"] is True
        assert result["interaction_required"] is True
        assert result["interaction_type"] == "trd_confirmation"
        assert "trd_path" in result
        assert "trd_preview" in result
        assert result["trd_path"] == str(trd_path)

    def test_check_trd_confirmation_trd_not_exists(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试 TRD 不存在时的错误。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act & Assert
        result = check_trd_confirmation(workspace_id)

        assert result["success"] is False
        assert "error" in result
        assert "TRD 文件不存在" in result["error"]

    def test_check_trd_confirmation_workspace_not_found(self):
        """测试工作区不存在时的错误。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            check_trd_confirmation("non-existent-workspace")

    def test_check_trd_confirmation_read_error(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试读取 TRD 文件失败时的处理。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_path = workspace_dir / "TRD.md"

        # 创建一个无法读取的文件（使用 mock 模拟读取失败）
        trd_path.write_text("test", encoding="utf-8")

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["trd_path"] = str(trd_path)
        meta_file = workspace_dir / "workspace.json"
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # 使用 mock 模拟读取文件时抛出异常
        with patch(
            "pathlib.Path.read_text", side_effect=PermissionError("Permission denied")
        ):
            # Act
            result = check_trd_confirmation(workspace_id)

            # Assert
            assert result["success"] is True
            assert result["interaction_required"] is True
            assert result["interaction_type"] == "trd_confirmation"
            assert result["trd_preview"] == "无法读取 TRD 内容"

    def test_confirm_trd_success(self, temp_dir, sample_project_dir, workspace_manager):
        """测试确认 TRD 成功。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act
        result = confirm_trd(workspace_id)

        # Assert
        assert result["success"] is True
        assert "workspace_id" in result

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "completed"

    def test_confirm_trd_workspace_not_found(self):
        """测试确认 TRD 时工作区不存在。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            confirm_trd("non-existent-workspace")

    def test_modify_trd_success(self, temp_dir, sample_project_dir, workspace_manager):
        """测试修改 TRD 成功。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act
        result = modify_trd(workspace_id)

        # Assert
        assert result["success"] is True
        assert "workspace_id" in result

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "needs_regeneration"

    def test_modify_trd_workspace_not_found(self):
        """测试修改 TRD 时工作区不存在。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            modify_trd("non-existent-workspace")

    def test_trd_modify_loop(self, temp_dir, sample_project_dir, workspace_manager):
        """测试 TRD 修改循环。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # 1. 确认 TRD
        confirm_result = confirm_trd(workspace_id)
        assert confirm_result["success"] is True

        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "completed"

        # 2. 标记需要修改
        modify_result = modify_trd(workspace_id)
        assert modify_result["success"] is True

        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "needs_regeneration"

        # 3. 再次确认
        confirm_result2 = confirm_trd(workspace_id)
        assert confirm_result2["success"] is True

        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "completed"
