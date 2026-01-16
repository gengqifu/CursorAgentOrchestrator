"""测试审查工具测试 - TDD 第一步：编写失败的测试。"""

from src.tools.test_reviewer import review_tests


class TestTestReviewer:
    """测试审查工具测试类。"""

    def test_review_tests_with_valid_files(self, temp_dir, monkeypatch):
        """测试审查有效测试文件。"""
        # Arrange
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        workspace_id = "test-workspace-001"

        # 创建测试文件
        test_file = temp_dir / "test_example.py"
        test_file.write_text("import pytest\n\ndef test_example():\n    assert True")

        # Act
        result = review_tests(workspace_id, [str(test_file)])

        # Assert
        assert result["success"] is True
        assert "review_report" in result
        assert "passed" in result

    def test_review_tests_with_empty_list(self, temp_dir, monkeypatch):
        """测试审查空测试文件列表。"""
        # Arrange
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        workspace_id = "test-workspace-002"

        # Act
        result = review_tests(workspace_id, [])

        # Assert
        assert result["success"] is True
        assert "passed" in result
