"""代码生成工具测试 - TDD 第一步：编写失败的测试。"""

import json

import pytest

from src.core.config import Config
from src.core.exceptions import TaskNotFoundError, ValidationError
from src.tools.code_generator import generate_code
from tests.conftest import create_test_workspace


class TestCodeGenerator:
    """代码生成工具测试类。"""

    def test_generate_code_with_valid_task(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用有效任务生成代码。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="用户认证功能"
        )

        # 创建 tasks.json
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现用户认证功能",
                    "status": "pending",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # ✅ 新增：更新任务分解状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # Act
        result = generate_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert "code_files" in result
        assert isinstance(result["code_files"], list)

    def test_generate_code_with_invalid_task_id(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用无效任务ID应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {"workspace_id": workspace_id, "tasks": []}
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # ✅ 新增：更新任务分解状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # Act & Assert
        with pytest.raises(TaskNotFoundError):
            generate_code(workspace_id, "non-existent-task")

    def test_generate_code_with_tasks_not_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务分解未完成时生成代码应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能",
                    "status": "pending",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # tasks_status 保持为 pending（默认状态）

        # Act & Assert
        with pytest.raises(ValidationError, match="任务分解尚未完成"):
            generate_code(workspace_id, "task-001")

    def test_generate_code_with_task_not_pending(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务状态不是pending时生成代码应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能",
                    "status": "completed",  # 已完成的任务
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # 更新任务分解状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="任务状态为"):
            generate_code(workspace_id, "task-001")

    def test_generate_code_marks_status_in_progress(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成代码时标记状态为进行中。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能",
                    "status": "pending",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # 更新任务分解状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # Act
        result = generate_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        workspace = workspace_manager.get_workspace(workspace_id)
        # 由于所有任务都已完成，code_status 应该为 completed
        assert workspace["status"]["code_status"] == "completed"

    def test_generate_code_marks_status_failed_on_error(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成代码失败时标记状态为失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能",
                    "status": "pending",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # 更新任务分解状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # Mock Path.write_text 失败
        from unittest.mock import patch

        with patch("pathlib.Path.write_text", side_effect=OSError("写入失败")):
            # Act & Assert
            with pytest.raises(OSError):
                generate_code(workspace_id, "task-001")

            # 验证状态被标记为失败
            workspace = workspace_manager.get_workspace(workspace_id)
            assert workspace["status"]["code_status"] == "failed"
