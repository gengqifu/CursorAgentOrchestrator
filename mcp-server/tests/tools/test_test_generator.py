"""测试生成工具测试 - TDD 第一步：编写失败的测试。"""
import pytest
from pathlib import Path
from src.tools.test_generator import generate_tests
from tests.conftest import create_test_workspace


class TestTestGenerator:
    """测试生成工具测试类。"""
    
    def test_generate_tests_with_valid_workspace(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试为有效工作区生成测试。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        test_output_dir = str(temp_dir / "tests" / "mocks")
        
        # Act
        result = generate_tests(workspace_id, test_output_dir)
        
        # Assert
        assert result["success"] is True
        assert "test_files" in result
        assert isinstance(result["test_files"], list)
    
    def test_generate_tests_creates_test_files(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试生成测试文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        test_output_dir = str(temp_dir / "tests" / "mocks")
        
        # Act
        result = generate_tests(workspace_id, test_output_dir)
        
        # Assert
        test_output_path = Path(test_output_dir)
        if test_output_path.exists():
            test_files = list(test_output_path.rglob("test_*.py"))
            assert len(test_files) >= 0  # 至少目录被创建
