"""任务执行工具测试 - TDD 第四步：编写单元测试。"""

from unittest.mock import patch

import pytest

from src.core.exceptions import TaskNotFoundError
from src.tools.task_executor import execute_all_tasks, execute_task
from tests.conftest import create_test_workspace


class TestTaskExecutor:
    """任务执行工具测试类。"""

    def test_execute_task_success(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务执行成功。

        验证当代码生成和 Review 都通过时，返回成功结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # 创建任务
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-001"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock generate_code 和 review_code
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
        ):
            mock_generate.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "code_files": ["/path/to/file.py"],
            }
            mock_review.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "passed": True,
                "review_report": "审查通过",
            }

            # Act
            result = execute_task(workspace_id, task_id)

            # Assert
            assert result["success"] is True
            assert result["passed"] is True
            assert result["task_id"] == task_id
            assert result["workspace_id"] == workspace_id
            assert result["retry_count"] == 0
            assert len(result["code_files"]) > 0
            assert "review_report" in result

            # 验证调用次数
            assert mock_generate.call_count == 1
            assert mock_review.call_count == 1

    def test_execute_task_review_failed_retry(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 Review 失败重试。

        验证当 Review 第一次失败，第二次通过时，会重试并成功。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-002"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock generate_code 和 review_code
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
        ):
            # 第一次 Review 失败，第二次通过
            mock_generate.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "code_files": ["/path/to/file.py"],
            }
            mock_review.side_effect = [
                {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,  # 第一次失败
                    "review_report": "需要修复",
                },
                {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": True,  # 第二次通过
                    "review_report": "审查通过",
                },
            ]

            # Act
            result = execute_task(workspace_id, task_id, max_review_retries=3)

            # Assert
            assert result["success"] is True
            assert result["passed"] is True
            assert result["retry_count"] == 1  # 重试了1次
            assert mock_generate.call_count == 2  # 生成了2次代码
            assert mock_review.call_count == 2  # Review 了2次

    def test_execute_task_max_retries(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试达到最大重试次数。

        验证当 Review 一直失败，达到最大重试次数时，返回失败。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-003"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock generate_code 和 review_code
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
        ):
            # 一直失败
            mock_generate.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "code_files": ["/path/to/file.py"],
            }
            mock_review.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "passed": False,  # 一直失败
                "review_report": "需要修复",
            }

            # Act
            max_retries = 2
            result = execute_task(workspace_id, task_id, max_review_retries=max_retries)

            # Assert
            assert result["success"] is False
            assert result["passed"] is False
            assert result["retry_count"] == max_retries
            assert "error" in result
            assert "达到最大重试次数" in result["error"]
            # 应该尝试 max_retries + 1 次（初始尝试 + 重试）
            assert mock_generate.call_count == max_retries + 1
            assert mock_review.call_count == max_retries + 1

    def test_execute_all_tasks_success(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试执行所有任务成功。

        验证当所有 pending 任务都执行成功时，返回成功统计。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 创建3个 pending 任务
        for i in range(1, 4):
            task_id = f"task-{i:03d}"
            task_manager.update_task_status(
                workspace_id,
                task_id,
                "pending",
                description=f"测试任务 {i}",
            )

        # Mock execute_task
        with patch("src.tools.task_executor.execute_task") as mock_execute:
            # 所有任务都成功
            mock_execute.side_effect = [
                {
                    "success": True,
                    "task_id": f"task-{i:03d}",
                    "workspace_id": workspace_id,
                    "passed": True,
                    "retry_count": 0,
                    "review_report": "审查通过",
                    "code_files": [f"/path/to/file{i}.py"],
                }
                for i in range(1, 4)
            ]

            # Act
            result = execute_all_tasks(workspace_id)

            # Assert
            assert result["success"] is True
            assert result["workspace_id"] == workspace_id
            assert result["total_tasks"] == 3
            assert result["completed_tasks"] == 3
            assert result["failed_tasks"] == 0
            assert len(result["task_results"]) == 3
            assert mock_execute.call_count == 3

    def test_execute_all_tasks_partial_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试部分任务失败。

        验证当部分任务失败时，返回正确的统计信息。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 创建3个 pending 任务
        for i in range(1, 4):
            task_id = f"task-{i:03d}"
            task_manager.update_task_status(
                workspace_id,
                task_id,
                "pending",
                description=f"测试任务 {i}",
            )

        # Mock execute_task
        with patch("src.tools.task_executor.execute_task") as mock_execute:
            # 第一个成功，第二个失败，第三个成功
            mock_execute.side_effect = [
                {
                    "success": True,
                    "task_id": "task-001",
                    "workspace_id": workspace_id,
                    "passed": True,
                    "retry_count": 0,
                    "review_report": "审查通过",
                    "code_files": ["/path/to/file1.py"],
                },
                {
                    "success": False,
                    "task_id": "task-002",
                    "workspace_id": workspace_id,
                    "passed": False,
                    "retry_count": 2,
                    "review_report": "需要修复",
                    "code_files": [],
                    "error": "达到最大重试次数",
                },
                {
                    "success": True,
                    "task_id": "task-003",
                    "workspace_id": workspace_id,
                    "passed": True,
                    "retry_count": 0,
                    "review_report": "审查通过",
                    "code_files": ["/path/to/file3.py"],
                },
            ]

            # Act
            result = execute_all_tasks(workspace_id)

            # Assert
            assert result["success"] is False  # 有失败任务，整体失败
            assert result["workspace_id"] == workspace_id
            assert result["total_tasks"] == 3
            assert result["completed_tasks"] == 2
            assert result["failed_tasks"] == 1
            assert len(result["task_results"]) == 3
            assert mock_execute.call_count == 3

    def test_execute_all_tasks_empty_list(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试空任务列表。

        验证当没有 pending 任务时，返回空结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # Act
        result = execute_all_tasks(workspace_id)

        # Assert
        assert result["success"] is True
        assert result["workspace_id"] == workspace_id
        assert result["total_tasks"] == 0
        assert result["completed_tasks"] == 0
        assert result["failed_tasks"] == 0
        assert result["task_results"] == []

    def test_execute_task_task_not_found(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务不存在。

        验证当任务不存在时，抛出 TaskNotFoundError。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # Act & Assert
        with pytest.raises(TaskNotFoundError):
            execute_task(workspace_id, "non-existent-task")

    def test_execute_task_generate_code_failed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试代码生成失败。

        验证当代码生成失败时，返回失败结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-004"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock generate_code 返回失败
        with patch("src.tools.task_executor.generate_code") as mock_generate:
            mock_generate.return_value = {
                "success": False,
                "error": "代码生成失败",
            }

            # Act
            result = execute_task(workspace_id, task_id)

            # Assert
            assert result["success"] is False
            assert result["passed"] is False
            assert "error" in result
            assert "代码生成失败" in result["error"]
            assert mock_generate.call_count == 1

    def test_execute_task_review_code_failed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试代码审查失败。

        验证当代码审查失败时，返回失败结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-005"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock generate_code 成功，review_code 失败
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
        ):
            mock_generate.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "code_files": ["/path/to/file.py"],
            }
            mock_review.return_value = {
                "success": False,
                "error": "代码审查失败",
            }

            # Act
            result = execute_task(workspace_id, task_id)

            # Assert
            assert result["success"] is False
            assert result["passed"] is False
            assert "error" in result
            assert "代码审查失败" in result["error"]
            assert mock_generate.call_count == 1
            assert mock_review.call_count == 1

    def test_execute_task_exception(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务执行异常。

        验证当执行过程中发生异常时，返回失败结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-006"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock generate_code 抛出异常
        with patch("src.tools.task_executor.generate_code") as mock_generate:
            mock_generate.side_effect = Exception("生成代码异常")

            # Act
            result = execute_task(workspace_id, task_id)

            # Assert
            assert result["success"] is False
            assert result["passed"] is False
            assert "error" in result
            assert "任务执行异常" in result["error"]

    def test_execute_all_tasks_task_not_found(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试执行所有任务时任务不存在。

        验证当某个任务不存在时，记录错误但继续执行其他任务。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 创建1个 pending 任务
        task_manager.update_task_status(
            workspace_id,
            "task-001",
            "pending",
            description="测试任务",
        )

        # Mock execute_task 抛出 TaskNotFoundError
        with patch("src.tools.task_executor.execute_task") as mock_execute:
            mock_execute.side_effect = TaskNotFoundError("任务不存在")

            # Act
            result = execute_all_tasks(workspace_id)

            # Assert
            assert result["success"] is False
            assert result["failed_tasks"] == 1
            assert len(result["task_results"]) == 1
            assert result["task_results"][0]["error"] is not None

    def test_execute_all_tasks_exception(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试执行所有任务时发生异常。

        验证当执行过程中发生异常时，返回失败结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 创建1个 pending 任务
        task_manager.update_task_status(
            workspace_id,
            "task-001",
            "pending",
            description="测试任务",
        )

        # Mock execute_task 抛出异常
        with patch("src.tools.task_executor.execute_task") as mock_execute:
            mock_execute.side_effect = Exception("执行异常")

            # Act
            result = execute_all_tasks(workspace_id)

            # Assert
            assert result["success"] is False
            assert result["failed_tasks"] == 1
            assert len(result["task_results"]) == 1
            assert "任务执行异常" in result["task_results"][0]["error"]

    def test_execute_all_tasks_get_tasks_exception(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试获取任务列表时发生异常。

        验证当获取任务列表失败时，返回失败结果。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # Mock TaskManager.get_tasks 抛出异常
        with patch("src.tools.task_executor.TaskManager") as mock_task_manager_class:
            mock_task_manager = mock_task_manager_class.return_value
            mock_task_manager.get_tasks.side_effect = Exception("获取任务列表异常")

            # Act
            result = execute_all_tasks(workspace_id)

            # Assert
            assert result["success"] is False
            assert "error" in result
            assert "执行所有任务异常" in result["error"]

    def test_execute_all_tasks_missing_task_id(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务缺少 task_id。

        验证当任务缺少 task_id 时，跳过该任务。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 直接写入一个缺少 task_id 的任务到 tasks.json
        tasks_file = task_manager.get_tasks_file(workspace_id)
        tasks_file.parent.mkdir(parents=True, exist_ok=True)
        import json

        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "workspace_id": workspace_id,
                    "tasks": [
                        {"status": "pending", "description": "缺少 task_id 的任务"},
                        {
                            "task_id": "task-001",
                            "status": "pending",
                            "description": "正常任务",
                        },
                    ],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        # Mock execute_task
        with patch("src.tools.task_executor.execute_task") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "task_id": "task-001",
                "workspace_id": workspace_id,
                "passed": True,
                "retry_count": 0,
                "review_report": "审查通过",
                "code_files": ["/path/to/file.py"],
            }

            # Act
            result = execute_all_tasks(workspace_id)

            # Assert
            assert result["success"] is True
            assert result["total_tasks"] == 2  # 总共2个 pending 任务
            assert result["completed_tasks"] == 1  # 只有1个有效任务被执行
            assert result["failed_tasks"] == 0
            assert mock_execute.call_count == 1  # 只执行了1个任务（另一个被跳过）
