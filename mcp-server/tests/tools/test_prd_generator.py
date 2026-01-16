"""PRD 生成工具测试 - TDD 第一步：编写失败的测试。"""

from pathlib import Path

import pytest

from src.core.exceptions import ValidationError
from src.tools.prd_generator import generate_prd
from tests.conftest import create_test_workspace


class TestPRDGenerator:
    """PRD 生成工具测试类。"""

    def test_generate_prd_with_valid_url(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用有效 URL 生成 PRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求",
            requirement_url="https://example.com/requirement",
        )
        requirement_url = "https://example.com/requirement"

        # Act
        result = generate_prd(workspace_id, requirement_url)

        # Assert
        assert result["success"] is True
        assert "prd_path" in result
        assert Path(result["prd_path"]).exists()

    def test_generate_prd_with_file_path(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用文件路径生成 PRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )
        requirement_file = temp_dir / "requirement.md"
        requirement_file.write_text("# 需求文档\n\n这是测试需求")

        # Act
        result = generate_prd(workspace_id, str(requirement_file))

        # Assert
        assert result["success"] is True
        assert "prd_path" in result

    def test_generate_prd_with_invalid_url(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用无效 URL 应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )
        requirement_url = ""

        # Act & Assert
        with pytest.raises(ValidationError):
            generate_prd(workspace_id, requirement_url)

    def test_generate_prd_creates_prd_file(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成 PRD 文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )
        requirement_url = "https://example.com/req"

        # Act
        result = generate_prd(workspace_id, requirement_url)

        # Assert
        prd_path = Path(result["prd_path"])
        assert prd_path.exists()
        assert prd_path.suffix == ".md"
        assert "PRD" in prd_path.name or "prd" in prd_path.name.lower()
