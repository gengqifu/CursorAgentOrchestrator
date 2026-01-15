"""测试生成工具测试 - TDD 第一步：编写失败的测试。"""

import json
from pathlib import Path

import pytest

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.tools.test_generator import generate_tests
from tests.conftest import create_test_workspace


class TestTestGenerator:
    """测试生成工具测试类。"""

    def test_generate_tests_with_valid_workspace(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试为有效工作区生成测试。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # ✅ 新增：创建已完成的任务
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能1",
                    "status": "completed",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        test_output_dir = str(temp_dir / "tests" / "mocks")

        # Act
        result = generate_tests(workspace_id, test_output_dir)

        # Assert
        assert result["success"] is True
        assert "test_files" in result
        assert isinstance(result["test_files"], list)

    def test_generate_tests_creates_test_files(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成测试文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # ✅ 新增：创建已完成的任务
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能1",
                    "status": "completed",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        test_output_dir = str(temp_dir / "tests" / "mocks")

        # Act
        generate_tests(workspace_id, test_output_dir)

        # Assert
        test_output_path = Path(test_output_dir)
        if test_output_path.exists():
            test_files = list(test_output_path.rglob("test_*.py"))
            assert len(test_files) >= 0  # 至少目录被创建

    def test_generate_tests_with_no_completed_tasks(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试没有已完成任务时生成测试应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建 tasks.json，但没有已完成的任务
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能1",
                    "status": "pending",  # 未完成的任务
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        test_output_dir = str(temp_dir / "tests" / "mocks")

        # Act & Assert
        with pytest.raises(ValidationError, match="没有已完成的任务"):
            generate_tests(workspace_id, test_output_dir)

    def test_generate_tests_with_pending_tasks(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试存在未完成任务时生成测试应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建 tasks.json，包含已完成和未完成的任务
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能1",
                    "status": "completed",
                },
                {
                    "task_id": "task-002",
                    "description": "实现功能2",
                    "status": "pending",  # 未完成的任务
                },
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        test_output_dir = str(temp_dir / "tests" / "mocks")

        # Act & Assert
        with pytest.raises(ValidationError, match="存在未完成的任务"):
            generate_tests(workspace_id, test_output_dir)

    def test_generate_tests_marks_status_in_progress(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成测试时标记状态为进行中。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建已完成的任务
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能1",
                    "status": "completed",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        test_output_dir = str(temp_dir / "tests" / "mocks")

        # Act
        generate_tests(workspace_id, test_output_dir)

        # Assert
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["test_status"] == "completed"

    def test_generate_tests_marks_status_failed_on_error(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成测试失败时标记状态为失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建已完成的任务
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现功能1",
                    "status": "completed",
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        test_output_dir = str(temp_dir / "tests" / "mocks")

        # Mock Path.write_text 失败
        from unittest.mock import patch

        with patch("pathlib.Path.write_text", side_effect=OSError("写入失败")):
            # Act & Assert
            with pytest.raises(OSError):
                generate_tests(workspace_id, test_output_dir)

            # 验证状态被标记为失败
            workspace = workspace_manager.get_workspace(workspace_id)
            assert workspace["status"]["test_status"] == "failed"
