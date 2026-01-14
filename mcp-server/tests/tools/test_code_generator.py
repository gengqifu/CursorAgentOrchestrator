"""代码生成工具测试 - TDD 第一步：编写失败的测试。"""
import pytest
import json
from pathlib import Path
from src.tools.code_generator import generate_code
from src.core.exceptions import TaskNotFoundError
from tests.conftest import create_test_workspace


class TestCodeGenerator:
    """代码生成工具测试类。"""
    
    def test_generate_code_with_valid_task(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试使用有效任务生成代码。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="用户认证功能"
        )
        
        # 创建 tasks.json
        from src.core.config import Config
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现用户认证功能",
                    "status": "pending"
                }
            ]
        }
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        # Act
        result = generate_code(workspace_id, "task-001")
        
        # Assert
        assert result["success"] is True
        assert "code_files" in result
        assert isinstance(result["code_files"], list)
    
    def test_generate_code_with_invalid_task_id(self, temp_dir, monkeypatch, workspace_manager, sample_project_dir):
        """测试使用无效任务ID应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="测试需求"
        )
        
        from src.core.config import Config
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {"workspace_id": workspace_id, "tasks": []}
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        # Act & Assert
        with pytest.raises(TaskNotFoundError):
            generate_code(workspace_id, "non-existent-task")
