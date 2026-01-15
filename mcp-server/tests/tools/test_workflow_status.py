"""工作流状态查询工具测试 - TDD 第三步：编写单元测试。"""

from unittest.mock import patch

import pytest

from src.core.exceptions import WorkspaceNotFoundError
from src.tools.workflow_status import get_workflow_status
from tests.conftest import create_test_workspace


class TestWorkflowStatus:
    """工作流状态查询工具测试类。"""

    def test_get_workflow_status_initial(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试初始状态。

        验证新创建的工作区返回正确的初始状态：
        - 所有阶段状态为 pending
        - PRD 阶段 ready=True（无前置依赖）
        - 其他阶段 ready=False（有前置依赖）
        - next_available_stages 包含 prd
        - blocked_stages 包含其他阶段
        - 进度为 0%
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # Act
        result = get_workflow_status(workspace_id)

        # Assert
        assert result["success"] is True
        assert result["workspace_id"] == workspace_id
        assert "stages" in result
        assert "next_available_stages" in result
        assert "blocked_stages" in result
        assert "workflow_progress" in result

        # 验证各阶段状态
        stages = result["stages"]
        assert stages["prd"]["status"] == "pending"
        assert stages["prd"]["ready"] is True
        assert stages["trd"]["status"] == "pending"
        assert stages["trd"]["ready"] is False
        assert stages["tasks"]["status"] == "pending"
        assert stages["tasks"]["ready"] is False
        assert stages["code"]["status"] == "pending"
        assert stages["code"]["ready"] is False
        assert stages["test"]["status"] == "pending"
        assert stages["test"]["ready"] is False
        assert stages["coverage"]["status"] == "pending"
        assert stages["coverage"]["ready"] is False

        # 验证可开始和被阻塞的阶段
        assert "prd" in result["next_available_stages"]
        assert "trd" in result["blocked_stages"]
        assert "tasks" in result["blocked_stages"]
        assert "code" in result["blocked_stages"]

        # 验证进度
        progress = result["workflow_progress"]
        assert progress["completed_stages"] == 0
        assert progress["total_stages"] == 6
        assert progress["progress_percentage"] == 0.0

    def test_get_workflow_status_prd_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试PRD完成后的状态。

        验证PRD完成后：
        - PRD 状态为 completed
        - TRD 阶段 ready=True（PRD已完成）
        - tasks, code, test, coverage 阶段 ready=False
        - next_available_stages 包含 trd
        - 进度为 16.67%（1/6）
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新PRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # 创建PRD文件路径
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求\n\n这是测试PRD内容")

        # 更新文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["prd_path"] = str(prd_file)
        workspace_manager.update_workspace_status(workspace_id, {})

        # Act
        result = get_workflow_status(workspace_id)

        # Assert
        assert result["success"] is True
        stages = result["stages"]

        # 验证PRD状态
        assert stages["prd"]["status"] == "completed"
        assert stages["prd"]["ready"] is True

        # 验证TRD可以开始
        assert stages["trd"]["status"] == "pending"
        assert stages["trd"]["ready"] is True
        assert "trd" in result["next_available_stages"]

        # 验证其他阶段仍被阻塞
        assert stages["tasks"]["ready"] is False
        assert stages["code"]["ready"] is False
        assert stages["test"]["ready"] is False
        assert stages["coverage"]["ready"] is False

        # 验证进度
        progress = result["workflow_progress"]
        assert progress["completed_stages"] == 1
        assert progress["progress_percentage"] == pytest.approx(16.67, abs=0.01)

    def test_get_workflow_status_all_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试所有阶段完成。

        验证所有阶段完成后：
        - 所有阶段状态为 completed
        - 所有阶段 ready=True
        - next_available_stages 为空
        - blocked_stages 为空
        - 进度为 100%
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新所有阶段状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id,
            {
                "prd_status": "completed",
                "trd_status": "completed",
                "tasks_status": "completed",
                "code_status": "completed",
                "test_status": "completed",
                "coverage_status": "completed",
            },
        )

        # 创建任务并标记为已完成
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-001"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "completed",
            description="测试任务",
        )

        # Act
        result = get_workflow_status(workspace_id)

        # Assert
        assert result["success"] is True
        stages = result["stages"]

        # 验证所有阶段状态为 completed
        assert stages["prd"]["status"] == "completed"
        assert stages["trd"]["status"] == "completed"
        assert stages["tasks"]["status"] == "completed"
        assert stages["code"]["status"] == "completed"
        assert stages["test"]["status"] == "completed"
        assert stages["coverage"]["status"] == "completed"

        # 验证所有阶段 ready=True
        assert stages["prd"]["ready"] is True
        assert stages["trd"]["ready"] is True
        assert stages["tasks"]["ready"] is True
        assert stages["code"]["ready"] is True
        assert stages["test"]["ready"] is True
        assert stages["coverage"]["ready"] is True

        # 验证可开始和被阻塞的阶段为空
        assert len(result["next_available_stages"]) == 0
        assert len(result["blocked_stages"]) == 0

        # 验证进度
        progress = result["workflow_progress"]
        assert progress["completed_stages"] == 6
        assert progress["progress_percentage"] == 100.0

    def test_get_workflow_status_partial_progress(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试部分进度。

        验证部分阶段完成后的状态：
        - PRD 和 TRD 已完成
        - tasks 已完成
        - code 进行中（有部分任务完成）
        - test 和 coverage 待处理
        - 进度为 50%（3/6）
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新部分阶段状态
        workspace_manager.update_workspace_status(
            workspace_id,
            {
                "prd_status": "completed",
                "trd_status": "completed",
                "tasks_status": "completed",
                "code_status": "in_progress",
            },
        )

        # 创建部分完成的任务
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_manager.update_task_status(
            workspace_id,
            "task-001",
            "completed",
            description="已完成的任务",
        )
        task_manager.update_task_status(
            workspace_id,
            "task-002",
            "pending",
            description="待处理的任务",
        )

        # Act
        result = get_workflow_status(workspace_id)

        # Assert
        assert result["success"] is True
        stages = result["stages"]

        # 验证已完成阶段
        assert stages["prd"]["status"] == "completed"
        assert stages["trd"]["status"] == "completed"
        assert stages["tasks"]["status"] == "completed"

        # 验证进行中阶段
        assert stages["code"]["status"] == "in_progress"
        assert stages["code"]["completed_tasks"] == 1
        assert stages["code"]["pending_tasks"] == 1
        assert stages["code"]["total_tasks"] == 2

        # 验证待处理阶段
        assert stages["test"]["status"] == "pending"
        assert stages["coverage"]["status"] == "pending"

        # 验证 code 阶段 ready=True（tasks已完成）
        assert stages["code"]["ready"] is True

        # 验证 test 阶段 ready=False（有pending任务）
        assert stages["test"]["ready"] is False

        # 验证进度
        progress = result["workflow_progress"]
        assert progress["completed_stages"] == 3
        assert progress["progress_percentage"] == 50.0

    def test_get_workflow_status_workspace_not_found(
        self, temp_dir, monkeypatch, workspace_manager
    ):
        """测试工作区不存在的情况。

        验证当工作区不存在时，抛出 WorkspaceNotFoundError。
        """
        # Arrange
        non_existent_workspace_id = "non-existent-workspace"

        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            get_workflow_status(non_existent_workspace_id)

    def test_get_workflow_status_general_exception(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试通用异常处理。

        验证当发生通用异常时，异常会被正确记录并重新抛出。
        通过模拟 TaskManager.get_tasks 抛出异常来触发通用异常处理。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # Mock TaskManager.get_tasks 抛出异常
        with patch("src.tools.workflow_status.TaskManager") as mock_task_manager_class:
            mock_task_manager = mock_task_manager_class.return_value
            mock_task_manager.get_tasks.side_effect = Exception("模拟异常")

            # Act & Assert
            with pytest.raises(Exception, match="模拟异常"):
                get_workflow_status(workspace_id)
