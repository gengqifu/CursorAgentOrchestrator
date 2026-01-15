"""阶段依赖检查工具测试 - TDD 第三步：编写单元测试。"""

import json

import pytest

from src.core.config import Config
from src.core.exceptions import ValidationError, WorkspaceNotFoundError
from src.tools.stage_dependency_checker import check_stage_ready
from src.utils.file_lock import file_lock
from tests.conftest import create_test_workspace


class TestStageDependencyChecker:
    """阶段依赖检查工具测试类。"""

    def test_check_stage_ready_prd(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试PRD阶段（无依赖）。

        验证PRD阶段（无前置依赖）：
        - ready=True（无前置依赖）
        - required_stages 为空
        - completed_stages 为空
        - file_ready=True（PRD阶段不需要文件依赖）
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # Act
        result = check_stage_ready(workspace_id, "prd")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "prd"
        assert result["ready"] is True
        assert result["reason"] == "前置阶段已完成，可以开始"
        assert result["required_stages"] == []
        assert result["completed_stages"] == []
        assert result["pending_stages"] == []
        assert result["in_progress_stages"] == []
        assert result["file_ready"] is True

    def test_check_stage_ready_trd_with_prd_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试TRD阶段（PRD已完成）。

        验证当PRD已完成时，TRD阶段可以开始：
        - ready=True（PRD已完成且文件存在）
        - required_stages 包含 prd
        - completed_stages 包含 prd
        - file_ready=True（PRD文件存在）
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

        # 创建PRD文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_file = workspace_dir / "PRD.md"
        prd_file.write_text("# PRD: 测试需求\n\n这是测试PRD内容")

        # 更新文件路径（直接写入 workspace.json）
        meta_file = workspace_dir / "workspace.json"
        with file_lock(meta_file):
            with open(meta_file, encoding="utf-8") as f:
                workspace = json.load(f)
            workspace["files"]["prd_path"] = str(prd_file)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Act
        result = check_stage_ready(workspace_id, "trd")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "trd"
        assert result["ready"] is True
        assert result["reason"] == "前置阶段已完成，可以开始"
        assert result["required_stages"] == ["prd"]
        assert result["completed_stages"] == ["prd"]
        assert result["pending_stages"] == []
        assert result["in_progress_stages"] == []
        assert result["file_ready"] is True

    def test_check_stage_ready_trd_with_prd_pending(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试TRD阶段（PRD未完成）。

        验证当PRD未完成时，TRD阶段不能开始：
        - ready=False（PRD未完成）
        - required_stages 包含 prd
        - pending_stages 包含 prd
        - reason 说明前置阶段未完成
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # PRD状态保持为 pending（默认状态）

        # Act
        result = check_stage_ready(workspace_id, "trd")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "trd"
        assert result["ready"] is False
        assert "前置阶段未完成" in result["reason"]
        assert "prd" in result["reason"]
        assert result["required_stages"] == ["prd"]
        assert result["completed_stages"] == []
        assert result["pending_stages"] == ["prd"]
        assert result["in_progress_stages"] == []

    def test_check_stage_ready_code_with_tasks_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试代码阶段（任务已完成）。

        验证当任务分解已完成时，代码阶段可以开始：
        - ready=True（tasks状态为completed且文件存在）
        - required_stages 包含 tasks
        - completed_stages 包含 tasks
        - file_ready=True（tasks.json文件存在）
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新tasks状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # 创建tasks.json文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "pending",
                }
            ],
        }
        tasks_file.write_text(json.dumps(tasks_data, ensure_ascii=False, indent=2))

        # 更新文件路径（直接写入 workspace.json）
        meta_file = workspace_dir / "workspace.json"
        with file_lock(meta_file):
            with open(meta_file, encoding="utf-8") as f:
                workspace = json.load(f)
            workspace["files"]["tasks_json_path"] = str(tasks_file)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Act
        result = check_stage_ready(workspace_id, "code")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "code"
        assert result["ready"] is True
        assert result["reason"] == "前置阶段已完成，可以开始"
        assert result["required_stages"] == ["tasks"]
        assert result["completed_stages"] == ["tasks"]
        assert result["pending_stages"] == []
        assert result["in_progress_stages"] == []
        assert result["file_ready"] is True

    def test_check_stage_ready_invalid_stage(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试无效阶段。

        验证当阶段名称无效时，抛出 ValidationError。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="未知阶段"):
            check_stage_ready(workspace_id, "invalid_stage")

    def test_check_stage_ready_trd_with_prd_completed_but_file_missing(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试TRD阶段（PRD已完成但文件不存在）。

        验证当PRD状态为completed但文件不存在时：
        - ready=False（文件不存在）
        - file_ready=False
        - reason 说明依赖文件不存在
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新PRD状态为已完成，但不创建文件
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )

        # Act
        result = check_stage_ready(workspace_id, "trd")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "trd"
        assert result["ready"] is False
        assert result["reason"] == "依赖文件不存在"
        assert result["required_stages"] == ["prd"]
        assert result["completed_stages"] == ["prd"]
        assert result["file_ready"] is False

    def test_check_stage_ready_trd_with_prd_in_progress(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试TRD阶段（PRD进行中）。

        验证当PRD状态为in_progress时，TRD阶段不能开始：
        - ready=False（PRD进行中）
        - in_progress_stages 包含 prd
        - reason 说明前置阶段未完成
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新PRD状态为进行中
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "in_progress"}
        )

        # Act
        result = check_stage_ready(workspace_id, "trd")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "trd"
        assert result["ready"] is False
        assert "前置阶段未完成" in result["reason"]
        assert "prd" in result["reason"]
        assert result["required_stages"] == ["prd"]
        assert result["completed_stages"] == []
        assert result["pending_stages"] == []
        assert result["in_progress_stages"] == ["prd"]

    def test_check_stage_ready_workspace_not_found(
        self, temp_dir, monkeypatch, workspace_manager
    ):
        """测试工作区不存在的情况。

        验证当工作区不存在时，抛出 WorkspaceNotFoundError。
        """
        # Arrange
        non_existent_workspace_id = "non-existent-workspace"

        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError):
            check_stage_ready(non_existent_workspace_id, "prd")

    def test_check_stage_ready_tasks_with_trd_completed_but_file_missing(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试tasks阶段（TRD已完成但文件不存在）。

        验证当TRD状态为completed但文件不存在时：
        - ready=False（文件不存在）
        - file_ready=False
        - reason 说明依赖文件不存在
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # 更新TRD状态为已完成，但不创建文件
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Act
        result = check_stage_ready(workspace_id, "tasks")

        # Assert
        assert result["success"] is True
        assert result["stage"] == "tasks"
        assert result["ready"] is False
        assert result["reason"] == "依赖文件不存在"
        assert result["required_stages"] == ["trd"]
        assert result["completed_stages"] == ["trd"]
        assert result["file_ready"] is False

    def test_check_stage_ready_general_exception(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试通用异常处理。

        验证当发生非预期的异常时，函数能够正确处理并重新抛出异常。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
            requirement_name="测试需求",
        )

        # Mock WorkspaceManager.get_workspace 抛出通用异常
        from unittest.mock import patch

        with patch(
            "src.tools.stage_dependency_checker.WorkspaceManager"
        ) as mock_manager_class:
            mock_manager = mock_manager_class.return_value
            mock_manager.get_workspace.side_effect = Exception("模拟异常")

            # Act & Assert
            with pytest.raises(Exception, match="模拟异常"):
                check_stage_ready(workspace_id, "prd")
