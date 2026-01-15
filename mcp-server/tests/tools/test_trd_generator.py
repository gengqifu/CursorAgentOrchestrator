"""TRD 生成工具测试 - TDD 第一步：编写失败的测试。"""

from pathlib import Path

import pytest

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.tools.trd_generator import generate_trd
from tests.conftest import create_test_workspace


class TestTRDGenerator:
    """TRD 生成工具测试类。"""

    def test_generate_trd_with_valid_prd(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用有效 PRD 生成 TRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建测试 PRD 文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求\n\n这是测试PRD内容")

        # ✅ 新增：更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Act
        result = generate_trd(workspace_id, str(prd_file))

        # Assert
        assert result["success"] is True
        assert "trd_path" in result
        assert Path(result["trd_path"]).exists()

    def test_generate_trd_with_invalid_prd_path(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用无效 PRD 路径应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )
        prd_path = "/nonexistent/prd.md"

        # Act & Assert
        with pytest.raises(ValidationError):
            generate_trd(workspace_id, prd_path)

    def test_generate_trd_creates_trd_file(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成 TRD 文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # ✅ 新增：更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Act
        result = generate_trd(workspace_id, str(prd_file))

        # Assert
        trd_path = Path(result["trd_path"])
        assert trd_path.exists()
        assert trd_path.suffix == ".md"
        assert "TRD" in trd_path.name or "trd" in trd_path.name.lower()

    def test_generate_trd_with_python_project(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试为 Python 项目生成 TRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建 Python 文件
        python_file = sample_project_dir / "main.py"
        python_file.write_text("def main(): pass")
        requirements_file = sample_project_dir / "requirements.txt"
        requirements_file.write_text("pytest==7.0.0")

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # ✅ 新增：更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Act
        result = generate_trd(workspace_id, str(prd_file))

        # Assert
        assert result["success"] is True
        trd_path = Path(result["trd_path"])
        trd_content = trd_path.read_text(encoding="utf-8")
        assert (
            "python" in trd_content.lower() or "python-standard" in trd_content.lower()
        )

    def test_generate_trd_analyzes_directory_structure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试分析目录结构。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建多个目录
        (sample_project_dir / "src").mkdir()
        (sample_project_dir / "tests").mkdir()
        (sample_project_dir / "docs").mkdir()
        # 创建隐藏目录（应该被忽略）
        (sample_project_dir / ".git").mkdir()

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # ✅ 新增：更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Act
        result = generate_trd(workspace_id, str(prd_file))

        # Assert
        assert result["success"] is True
        trd_path = Path(result["trd_path"])
        trd_content = trd_path.read_text(encoding="utf-8")
        # 应该包含目录结构信息
        assert "src" in trd_content or "tests" in trd_content or "docs" in trd_content

    def test_generate_trd_with_prd_not_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试PRD未完成时生成TRD应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # PRD状态保持为 pending（默认状态）

        # Act & Assert
        with pytest.raises(ValidationError, match="PRD尚未完成"):
            generate_trd(workspace_id, str(prd_file))

    def test_generate_trd_with_prd_path_from_workspace(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试从工作区获取PRD路径生成TRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # 更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # 更新工作区文件路径
        import json

        from src.utils.file_lock import file_lock

        meta_file = workspace_dir / "workspace.json"
        with file_lock(meta_file):
            with open(meta_file, encoding="utf-8") as f:
                workspace = json.load(f)
            workspace["files"]["prd_path"] = str(prd_file)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Act - 不提供 prd_path，应该从工作区获取
        result = generate_trd(workspace_id)

        # Assert
        assert result["success"] is True
        assert "trd_path" in result
        assert Path(result["trd_path"]).exists()

    def test_generate_trd_marks_status_in_progress(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成TRD时标记状态为进行中。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # 更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Act
        result = generate_trd(workspace_id, str(prd_file))

        # Assert
        assert result["success"] is True
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "completed"

    def test_generate_trd_marks_status_failed_on_error(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成TRD失败时标记状态为失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")

        # 更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Mock 文件写入失败
        from unittest.mock import patch

        with patch("pathlib.Path.write_text", side_effect=OSError("写入失败")):
            # Act & Assert
            with pytest.raises(IOError):
                generate_trd(workspace_id, str(prd_file))

            # 验证状态被标记为失败
            workspace = workspace_manager.get_workspace(workspace_id)
            assert workspace["status"]["trd_status"] == "failed"
