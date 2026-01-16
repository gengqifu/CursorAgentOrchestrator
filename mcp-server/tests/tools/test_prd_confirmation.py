"""PRD 确认工具测试 - TDD 第一步：编写失败的测试。"""

from unittest.mock import patch

import pytest

from src.core.exceptions import WorkspaceNotFoundError
from src.tools.prd_confirmation import check_prd_confirmation, confirm_prd, modify_prd
from tests.conftest import create_test_workspace


class TestPRDConfirmation:
    """PRD 确认工具测试类。"""

    def test_check_prd_confirmation_prd_exists(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试 PRD 存在时的确认请求。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # 创建 PRD 文件
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_path = workspace_dir / "PRD.md"
        prd_path.write_text("# PRD 文档\n\n这是测试 PRD 内容。", encoding="utf-8")

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["prd_path"] = str(prd_path)
        meta_file = workspace_dir / "workspace.json"
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Act
        result = check_prd_confirmation(workspace_id)

        # Assert
        assert result["success"] is True
        assert result["interaction_required"] is True
        assert result["interaction_type"] == "prd_confirmation"
        assert "prd_path" in result
        assert "prd_preview" in result
        assert result["prd_path"] == str(prd_path)

    def test_check_prd_confirmation_prd_not_exists(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试 PRD 不存在时的错误。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act & Assert
        result = check_prd_confirmation(workspace_id)

        assert result["success"] is False
        assert "error" in result
        assert "PRD 文件不存在" in result["error"]

    def test_check_prd_confirmation_workspace_not_found(self):
        """测试工作区不存在时的错误。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            check_prd_confirmation("non-existent-workspace")

    def test_check_prd_confirmation_read_error(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """测试读取 PRD 文件失败时的处理。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_path = workspace_dir / "PRD.md"

        # 创建一个无法读取的文件（使用 mock 模拟读取失败）
        prd_path.write_text("test", encoding="utf-8")

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["prd_path"] = str(prd_path)
        meta_file = workspace_dir / "workspace.json"
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # 使用 mock 模拟读取文件时抛出异常
        with patch(
            "pathlib.Path.read_text", side_effect=PermissionError("Permission denied")
        ):
            # Act
            result = check_prd_confirmation(workspace_id)

            # Assert
            assert result["success"] is True
            assert result["interaction_required"] is True
            assert result["interaction_type"] == "prd_confirmation"
            assert result["prd_preview"] == "无法读取 PRD 内容"

    def test_confirm_prd_success(self, temp_dir, sample_project_dir, workspace_manager):
        """测试确认 PRD 成功。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act
        result = confirm_prd(workspace_id)

        # Assert
        assert result["success"] is True
        assert "workspace_id" in result

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"

    def test_confirm_prd_workspace_not_found(self):
        """测试确认 PRD 时工作区不存在。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            confirm_prd("non-existent-workspace")

    def test_modify_prd_success(self, temp_dir, sample_project_dir, workspace_manager):
        """测试修改 PRD 成功。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # Act
        result = modify_prd(workspace_id)

        # Assert
        assert result["success"] is True
        assert "workspace_id" in result

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "needs_regeneration"

    def test_modify_prd_workspace_not_found(self):
        """测试修改 PRD 时工作区不存在。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            modify_prd("non-existent-workspace")

    def test_prd_modify_loop(self, temp_dir, sample_project_dir, workspace_manager):
        """测试 PRD 修改循环。"""
        # Arrange
        workspace_id = create_test_workspace(workspace_manager, sample_project_dir)

        # 1. 确认 PRD
        confirm_result = confirm_prd(workspace_id)
        assert confirm_result["success"] is True

        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"

        # 2. 标记需要修改
        modify_result = modify_prd(workspace_id)
        assert modify_result["success"] is True

        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "needs_regeneration"

        # 3. 再次确认
        confirm_result2 = confirm_prd(workspace_id)
        assert confirm_result2["success"] is True

        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"
