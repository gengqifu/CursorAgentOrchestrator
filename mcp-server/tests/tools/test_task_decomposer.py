"""任务分解工具测试 - TDD 第一步：编写失败的测试。"""
import pytest
import json
from pathlib import Path
from src.tools.task_decomposer import decompose_tasks
from src.core.exceptions import ValidationError
from src.core.config import Config
from tests.conftest import create_test_workspace


class TestTaskDecomposer:
    """任务分解工具测试类。"""
    
    def test_decompose_tasks_with_valid_trd(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试使用有效 TRD 分解任务。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        
        # 创建测试 TRD 文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD: 测试需求\n\n## 实现方案\n\n### 功能1\n### 功能2")
        
        # Act
        result = decompose_tasks(workspace_id, str(trd_file))
        
        # Assert
        assert result["success"] is True
        assert "tasks_json_path" in result
        tasks_file = Path(result["tasks_json_path"])
        assert tasks_file.exists()
        
        # 验证 tasks.json 内容
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        assert "tasks" in tasks_data
        assert isinstance(tasks_data["tasks"], list)
        assert len(tasks_data["tasks"]) > 0
    
    def test_decompose_tasks_with_invalid_trd_path(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试使用无效 TRD 路径应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        trd_path = "/nonexistent/trd.md"
        
        # Act & Assert
        with pytest.raises(ValidationError):
            decompose_tasks(workspace_id, trd_path)
    
    def test_decompose_tasks_creates_valid_tasks_json(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试生成有效的 tasks.json 文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD\n\n## 实现方案\n\n需要实现功能A和功能B")
        
        # Act
        result = decompose_tasks(workspace_id, str(trd_file))
        
        # Assert
        tasks_file = Path(result["tasks_json_path"])
        with open(tasks_file, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
        
        # 验证任务结构
        for task in tasks_data["tasks"]:
            assert "task_id" in task
            assert "description" in task
            assert "status" in task
            assert task["status"] == "pending"
