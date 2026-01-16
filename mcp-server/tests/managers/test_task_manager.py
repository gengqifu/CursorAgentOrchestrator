"""任务管理器测试 - TDD 第一步：编写失败的测试。"""

import json

import pytest

from src.core.config import Config
from src.core.exceptions import TaskNotFoundError
from src.managers.task_manager import TaskManager
from src.managers.workspace_manager import WorkspaceManager
from tests.conftest import create_test_workspace


class TestTaskManager:
    """任务管理器测试类。"""

    @pytest.fixture
    def config(self, temp_dir, monkeypatch):
        """创建测试用配置。"""
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        return Config()

    @pytest.fixture
    def workspace_manager(self, config):
        """创建工作区管理器实例。"""
        return WorkspaceManager(config=config)

    @pytest.fixture
    def manager(self, config):
        """创建任务管理器实例。"""
        return TaskManager(config=config)

    def test_get_tasks_returns_empty_list_when_no_tasks(
        self, manager, workspace_manager, sample_project_dir
    ):
        """测试没有任务时返回空列表。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # Act
        tasks = manager.get_tasks(workspace_id)

        # Assert
        assert isinstance(tasks, list)
        assert len(tasks) == 0

    def test_get_tasks_returns_tasks_from_file(
        self, manager, workspace_manager, sample_project_dir
    ):
        """测试从文件读取任务。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {"task_id": "task-001", "description": "任务1", "status": "pending"},
                {"task_id": "task-002", "description": "任务2", "status": "completed"},
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        tasks = manager.get_tasks(workspace_id)

        # Assert
        assert len(tasks) == 2
        assert tasks[0]["task_id"] == "task-001"
        assert tasks[1]["task_id"] == "task-002"

    def test_get_task_returns_specific_task(
        self, manager, workspace_manager, sample_project_dir
    ):
        """测试获取特定任务。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {"task_id": "task-001", "description": "任务1", "status": "pending"}
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        task = manager.get_task(workspace_id, "task-001")

        # Assert
        assert task["task_id"] == "task-001"
        assert task["description"] == "任务1"

    def test_get_task_raises_error_when_not_found(
        self, manager, workspace_manager, sample_project_dir
    ):
        """测试获取不存在任务时抛出异常。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {"workspace_id": workspace_id, "tasks": []}
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act & Assert
        with pytest.raises(TaskNotFoundError):
            manager.get_task(workspace_id, "non-existent-task")

    def test_update_task_status_updates_task(
        self, manager, workspace_manager, sample_project_dir
    ):
        """测试更新任务状态。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {"task_id": "task-001", "description": "任务1", "status": "pending"}
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        manager.update_task_status(
            workspace_id, "task-001", "completed", code_files=["file.py"]
        )

        # Assert
        updated_task = manager.get_task(workspace_id, "task-001")
        assert updated_task["status"] == "completed"
        assert updated_task["code_files"] == ["file.py"]
