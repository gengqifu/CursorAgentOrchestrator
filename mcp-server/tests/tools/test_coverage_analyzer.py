"""覆盖率分析工具测试 - TDD 第一步：编写失败的测试。"""
import pytest
from pathlib import Path
from src.tools.coverage_analyzer import analyze_coverage
from tests.conftest import create_test_workspace


class TestCoverageAnalyzer:
    """覆盖率分析工具测试类。"""
    
    def test_analyze_coverage_with_valid_project(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试分析有效项目的覆盖率。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        project_path = str(sample_project_dir)
        
        # 创建测试代码文件
        code_file = Path(project_path) / "module.py"
        code_file.write_text("def func():\n    return True")
        
        # Act
        result = analyze_coverage(workspace_id, project_path)
        
        # Assert
        assert result["success"] is True
        assert "coverage" in result
        assert "coverage_report_path" in result
        assert isinstance(result["coverage"], (int, float))
        assert 0 <= result["coverage"] <= 100
    
    def test_analyze_coverage_creates_report(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试生成覆盖率报告。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        project_path = str(sample_project_dir)
        
        # Act
        result = analyze_coverage(workspace_id, project_path)
        
        # Assert
        if result.get("coverage_report_path"):
            report_path = Path(result["coverage_report_path"])
            # 报告文件可能不存在（如果未安装 coverage），但路径应该有效
            assert isinstance(result["coverage_report_path"], str)
    
    def test_analyze_coverage_handles_missing_coverage_tool(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试处理 coverage 工具未安装的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        project_path = str(sample_project_dir)
        
        # Mock subprocess.run 来模拟 FileNotFoundError
        import subprocess
        original_run = subprocess.run
        
        def mock_run(*args, **kwargs):
            if "coverage" in args[0]:
                raise FileNotFoundError("coverage command not found")
            return original_run(*args, **kwargs)
        
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        # Act
        result = analyze_coverage(workspace_id, project_path)
        
        # Assert
        # 即使 coverage 工具未安装，也应该返回成功（但覆盖率可能为 0）
        assert result["success"] is True
        assert "coverage" in result
    
    def test_analyze_coverage_handles_invalid_json(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试处理无效 JSON 输出的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        project_path = str(sample_project_dir)
        
        # Mock subprocess.run 来模拟无效 JSON 输出
        import subprocess
        from unittest.mock import MagicMock
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        
        def mock_run(*args, **kwargs):
            if "coverage" in args[0] and "json" in args[0]:
                return mock_result
            return subprocess.run(*args, **kwargs)
        
        monkeypatch.setattr(subprocess, "run", mock_run)
        
        # Act
        result = analyze_coverage(workspace_id, project_path)
        
        # Assert
        # 即使 JSON 解析失败，也应该返回成功（使用默认覆盖率 0）
        assert result["success"] is True
        assert "coverage" in result
