"""TRD 生成工具测试 - TDD 第一步：编写失败的测试。"""
import pytest
from pathlib import Path
from src.tools.trd_generator import generate_trd
from src.core.exceptions import ValidationError
from src.core.config import Config
from tests.conftest import create_test_workspace


class TestTRDGenerator:
    """TRD 生成工具测试类。"""
    
    def test_generate_trd_with_valid_prd(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试使用有效 PRD 生成 TRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        
        # 创建测试 PRD 文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求\n\n这是测试PRD内容")
        
        # Act
        result = generate_trd(workspace_id, str(prd_file))
        
        # Assert
        assert result["success"] is True
        assert "trd_path" in result
        assert Path(result["trd_path"]).exists()
    
    def test_generate_trd_with_invalid_prd_path(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试使用无效 PRD 路径应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        prd_path = "/nonexistent/prd.md"
        
        # Act & Assert
        with pytest.raises(ValidationError):
            generate_trd(workspace_id, prd_path)
    
    def test_generate_trd_creates_trd_file(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试生成 TRD 文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求")
        
        # Act
        result = generate_trd(workspace_id, str(prd_file))
        
        # Assert
        trd_path = Path(result["trd_path"])
        assert trd_path.exists()
        assert trd_path.suffix == ".md"
        assert "TRD" in trd_path.name or "trd" in trd_path.name.lower()
    
    def test_generate_trd_with_python_project(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试为 Python 项目生成 TRD。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
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
        
        # Act
        result = generate_trd(workspace_id, str(prd_file))
        
        # Assert
        assert result["success"] is True
        trd_path = Path(result["trd_path"])
        trd_content = trd_path.read_text(encoding='utf-8')
        assert "python" in trd_content.lower() or "python-standard" in trd_content.lower()
    
    def test_generate_trd_analyzes_directory_structure(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试分析目录结构。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
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
        
        # Act
        result = generate_trd(workspace_id, str(prd_file))
        
        # Assert
        assert result["success"] is True
        trd_path = Path(result["trd_path"])
        trd_content = trd_path.read_text(encoding='utf-8')
        # 应该包含目录结构信息
        assert "src" in trd_content or "tests" in trd_content or "docs" in trd_content
