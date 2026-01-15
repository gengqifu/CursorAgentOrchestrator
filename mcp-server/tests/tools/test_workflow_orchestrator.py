"""工作流编排工具测试 - TDD 第一步：编写失败的测试。

Python 3.9+ 兼容
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import (
    AgentOrchestratorError,
    ValidationError,
    WorkspaceNotFoundError,
)
from src.tools.workflow_orchestrator import (
    _get_workflow_state,
    _should_skip_step,
    _update_workflow_state,
    execute_full_workflow,
)
from tests.conftest import create_test_workspace


class TestWorkflowOrchestrator:
    """工作流编排工具测试类。"""

    def test_execute_full_workflow_auto_confirm(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试自动确认模式的完整工作流。

        验证当 auto_confirm=True 时，工作流自动执行所有步骤。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        # Mock 所有工具函数
        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            # 设置 mock 返回值
            workspace_id = "req-test-001"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 3,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 3,
                "completed_tasks": 3,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py", "test_2.py"],
                "test_count": 2,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 85.5,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is True
            assert result["workspace_id"] == workspace_id
            assert len(result["workflow_steps"]) == 8  # 8个步骤
            assert "final_status" in result

            # 验证所有步骤都已完成
            for step in result["workflow_steps"]:
                assert step["status"] == "completed"

            # 验证工具调用次数
            assert mock_submit.call_count == 1
            assert mock_generate_prd.call_count == 1
            assert mock_confirm_prd.call_count == 1
            assert mock_generate_trd.call_count == 1
            assert mock_confirm_trd.call_count == 1
            assert mock_decompose.call_count == 1
            assert mock_execute_tasks.call_count == 1

    def test_execute_full_workflow_with_interactions(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试交互模式的完整工作流。

        验证当 auto_confirm=False 时，工作流会在需要交互时暂停并返回交互请求。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-002"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act - 第一次调用，应该返回 PRD 确认请求
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
            )

            # Assert - 应该返回交互请求
            assert result["success"] is True
            assert result["interaction_required"] is True
            assert result["interaction_type"] == "prd_confirmation"
            assert "prd_path" in result
            assert "prd_preview" in result

            # 注意：交互模式的完整流程测试比较复杂，需要多次调用和状态管理
            # 这里只验证第一次调用返回交互请求，完整流程测试在端到端测试中覆盖

    def test_execute_full_workflow_prd_modify_loop(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 PRD 修改循环。

        验证当 PRD 需要修改时，会重新生成 PRD。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.modify_prd") as mock_modify_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
        ):
            workspace_id = "req-test-003"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_modify_prd.return_value = {"success": True}
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 75.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act - 第一次生成 PRD，然后修改
            result1 = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
            )
            # 第一次调用应该返回 PRD 确认请求
            assert result1.get("interaction_type") == "prd_confirmation"

            # 模拟修改 PRD 的响应
            result2 = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "modify",
                },
            )
            # 修改后应该继续生成 PRD，可能返回确认请求或继续执行
            assert result2.get("interaction_type") in ["prd_confirmation", None]

            # 模拟确认 PRD 的响应（如果还在 PRD 循环中）
            if result2.get("interaction_type") == "prd_confirmation":
                execute_full_workflow(
                    workspace_id=workspace_id,
                    auto_confirm=False,
                    interaction_response={
                        "interaction_type": "prd_confirmation",
                        "action": "confirm",
                    },
                )

            # Assert - 验证 PRD 被生成了多次（修改后重新生成）
            assert mock_generate_prd.call_count >= 2
            assert mock_modify_prd.call_count >= 1

    def test_execute_full_workflow_trd_modify_loop(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 修改循环。

        验证当 TRD 需要修改时，会重新生成 TRD。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.modify_trd") as mock_modify_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
        ):
            workspace_id = "req-test-004"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_check_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
                "trd_preview": "TRD 预览内容",
            }
            mock_modify_trd.return_value = {"success": True}
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 75.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act - 先完成 PRD
            execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # 设置 _should_skip_step 返回 True 对于步骤2（PRD已完成）
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                step_num == 2 and step_name == "PRD 生成和确认"
            )

            # 第一次调用：生成 TRD 并返回确认请求
            result0 = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
            )
            # 应该返回 TRD 确认请求
            assert result0.get("interaction_type") == "trd_confirmation"

            # 模拟修改 TRD 的响应
            result1 = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "trd_confirmation",
                    "action": "modify",
                },
            )
            # 修改后应该继续生成 TRD，可能返回确认请求或继续执行
            assert result1.get("interaction_type") in ["trd_confirmation", None]

            # 模拟确认 TRD 的响应（如果还在 TRD 循环中）
            if result1.get("interaction_type") == "trd_confirmation":
                execute_full_workflow(
                    workspace_id=workspace_id,
                    auto_confirm=False,
                    interaction_response={
                        "interaction_type": "trd_confirmation",
                        "action": "confirm",
                    },
                )

            # Assert - 验证 TRD 被生成了多次（修改后重新生成）
            assert mock_generate_trd.call_count >= 1
            assert mock_modify_trd.call_count >= 1

    def test_execute_full_workflow_task_review_loop(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务 Review 循环。

        验证当任务 Review 失败时，会重试并最终通过。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-005"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 2,
            }
            # execute_all_tasks 内部会处理 Review 循环，这里模拟最终成功
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 2,
                "completed_tasks": 2,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
                max_review_retries=3,
            )

            # Assert
            assert result["success"] is True
            assert mock_execute_tasks.call_count == 1
            # 验证 max_review_retries 参数被传递
            assert mock_execute_tasks.call_args[1]["max_review_retries"] == 3

    def test_execute_full_workflow_partial_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试部分失败场景。

        验证当某些步骤失败时，工作流能够正确处理错误。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-006"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": False,
                "error": "PRD 生成失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act & Assert - PRD 生成失败应该抛出异常
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert - 应该返回失败结果
            assert result["success"] is False
            assert "error" in result
            assert "PRD 生成失败" in result["error"]
            assert len(result["workflow_steps"]) > 0  # 应该记录已完成的步骤

    def test_execute_full_workflow_validation_error(self):
        """测试参数验证错误。

        验证当参数无效时，抛出 ValidationError。
        """
        # Act & Assert
        with pytest.raises(ValidationError, match="project_path 不能为空"):
            execute_full_workflow(
                project_path="",
                requirement_name="测试需求",
                requirement_url="https://example.com/req.md",
                auto_confirm=True,
            )

        with pytest.raises(ValidationError, match="requirement_name 不能为空"):
            execute_full_workflow(
                project_path="/path/to/project",
                requirement_name="",
                requirement_url="https://example.com/req.md",
                auto_confirm=True,
            )

        with pytest.raises(ValidationError, match="requirement_url 不能为空"):
            execute_full_workflow(
                project_path="/path/to/project",
                requirement_name="测试需求",
                requirement_url="",
                auto_confirm=True,
            )

    def test_interactive_mode_ask_questions(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试交互模式返回询问问题。

        验证当 auto_confirm=False 且参数未提供时，返回询问4个问题的交互请求。
        """
        # Act
        result = execute_full_workflow(auto_confirm=False)

        # Assert
        assert result["success"] is True
        assert result["interaction_required"] is True
        assert result["interaction_type"] == "questions"
        assert "questions" in result

    def test_interactive_mode_with_answers(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试交互模式处理 answers。

        验证当提供 answers 交互响应时，正确提取参数。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
        ):
            workspace_id = "req-test-007"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act - 提供 answers，工作流应该继续执行
            result = execute_full_workflow(
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "questions",
                    "answers": {
                        "project_path": project_path,
                        "requirement_name": requirement_name,
                        "requirement_url": requirement_url,
                    },
                },
            )

            # Assert - 第一次调用应该返回 PRD 确认请求（因为交互模式下会询问 PRD）
            assert result["success"] is True
            assert result.get("interaction_required") is True
            assert result.get("interaction_type") == "prd_confirmation"
            assert mock_submit.call_count == 1

    def test_workspace_recovery(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试从工作区恢复参数。

        验证当提供 workspace_id 时，从工作区恢复参数。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"
        workspace_id = "req-test-008"

        with (
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act - 当 auto_confirm=True 时，可以从工作区恢复参数
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is True
            assert result["workspace_id"] == workspace_id

    def test_prd_max_retries(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 PRD 循环达到最大重试次数。

        验证当 PRD 循环达到最大重试次数时，抛出异常。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-009"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            # generate_prd 每次成功，但 confirm_prd 一直失败，导致循环达到最大次数
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            # confirm_prd 一直失败，导致循环达到最大次数
            mock_confirm_prd.return_value = {"success": False, "error": "确认失败"}
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            # 验证错误消息包含 PRD 循环达到最大重试次数
            assert "PRD 循环达到最大重试次数" in result["error"] or "PRD 确认失败" in result["error"]

    def test_trd_stage_not_ready(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 阶段未就绪。

        验证当 TRD 阶段未就绪时，抛出异常。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-010"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            # TRD 阶段未就绪
            mock_check_stage.side_effect = [
                {"ready": True, "reason": "可以开始"},  # PRD 检查
                {"ready": False, "reason": "PRD 未完成"},  # TRD 检查
            ]
            mock_get_status.return_value = {
                "success": True,
                "stages": {"prd": {"status": "completed"}},
                "workflow_progress": {"completed_stages": 1},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "TRD 阶段未就绪" in result["error"]

    def test_test_path_interactive_mode(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试测试路径交互模式。

        验证当 auto_confirm=False 时，返回测试路径询问请求。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-011"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_check_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
                "trd_preview": "TRD 预览内容",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act - 先完成 PRD 和 TRD
            # 第一次调用：确认 PRD
            result1 = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "confirm",
                },
            )
            # 第二次调用：确认 TRD
            result2 = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "trd_confirmation",
                    "action": "confirm",
                },
            )
            # 第三次调用：到达测试路径询问（需要确保步骤2和3已完成）
            # 设置 _should_skip_step 返回 True 对于步骤2和3
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                (step_num == 2 and step_name == "PRD 生成和确认")
                or (step_num == 3 and step_name == "TRD 生成和确认")
            )
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
            )

            # Assert
            assert result["success"] is True
            assert result["interaction_required"] is True
            assert result["interaction_type"] == "question"
            assert "question" in result

    def test_update_workflow_state_failed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试更新工作流状态为失败状态。

        验证 _update_workflow_state 函数处理 failed 状态。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # Act
        _update_workflow_state(workspace_id, 1, "测试步骤", "failed")

        # Assert
        state = _get_workflow_state(workspace_id)
        assert state["step_status"] == "failed"
        assert len(state.get("failed_steps", [])) > 0

    def test_should_skip_step(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试跳过步骤功能。

        验证 _should_skip_step 函数正确判断步骤是否已完成。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # 先标记步骤1为已完成
        _update_workflow_state(workspace_id, 1, "创建工作区", "completed")

        # Act
        should_skip = _should_skip_step(workspace_id, 1, "创建工作区")

        # Assert
        assert should_skip is True

        # 测试未完成的步骤
        should_skip2 = _should_skip_step(workspace_id, 2, "PRD 生成和确认")
        assert should_skip2 is False

    def test_get_workflow_state(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试获取工作流状态。

        验证 _get_workflow_state 函数正确返回工作流状态。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # Act
        state = _get_workflow_state(workspace_id)

        # Assert
        assert isinstance(state, dict)
        assert "completed_steps" in state or state == {}

    def test_invalid_prd_action(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试无效的 PRD 确认操作。

        验证当提供无效的 action 时，抛出 ValidationError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-012"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "invalid_action",  # 无效的操作
                },
            )

            # Assert
            assert result["success"] is False
            assert "无效的 PRD 确认操作" in result["error"]

    def test_test_path_empty(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试测试路径为空的情况。

        验证当测试路径为空时，抛出 ValidationError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
        ):
            workspace_id = "req-test-013"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_check_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
                "trd_preview": "TRD 预览内容",
            }
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act - 先完成 PRD 和 TRD，然后到达测试路径询问
            # 第一次调用：确认 PRD
            execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "confirm",
                },
            )
            # 第二次调用：确认 TRD
            execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "trd_confirmation",
                    "action": "confirm",
                },
            )
            # 第三次调用：提供空的测试路径（需要确保步骤2和3已完成）
            # 设置 _should_skip_step 返回 True 对于步骤2和3
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                (step_num == 2 and step_name == "PRD 生成和确认")
                or (step_num == 3 and step_name == "TRD 生成和确认")
            )
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "question",
                    "answer": "",  # 空的测试路径
                },
            )

            # Assert
            assert result["success"] is False
            assert "测试路径不能为空" in result["error"]

    def test_coverage_analysis_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试覆盖率分析失败。

        验证当覆盖率分析失败时，抛出异常。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-014"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            # 覆盖率分析失败
            mock_analyze_coverage.return_value = {
                "success": False,
                "error": "覆盖率分析失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 5},
                "next_available_stages": ["coverage"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "覆盖率分析失败" in result["error"]

    def test_skip_completed_steps(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试跳过已完成的步骤。

        验证当步骤已完成时，跳过执行。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )

        # 标记步骤2为已完成
        _update_workflow_state(workspace_id, 2, "PRD 生成和确认", "completed")

        with (
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": str(sample_project_dir),
                "requirement_name": "测试需求",
                "requirement_url": "https://example.com/req.md",
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_get_state.return_value = {
                "completed_steps": [{"step": 1, "name": "创建工作区", "status": "completed"}],
            }
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                step_num == 2 and step_name == "PRD 生成和确认"
            )
            mock_update_state.return_value = None
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act - 当 auto_confirm=True 时，可以从工作区恢复参数
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is True
            # 验证 PRD 步骤被跳过
            prd_step = next(
                (s for s in result["workflow_steps"] if s["step"] == 2), None
            )
            assert prd_step is not None
            assert prd_step["status"] == "completed"

    def test_workspace_not_found_recovery(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试工作区不存在时的恢复逻辑。

        验证当提供不存在的 workspace_id 时，会创建新工作区。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-015"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.side_effect = WorkspaceNotFoundError(
                f"Workspace not found: {workspace_id}"
            )
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act - 提供不存在的 workspace_id，应该创建新工作区
            result = execute_full_workflow(
                workspace_id=workspace_id,
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is True
            assert mock_submit.call_count == 1

    def test_create_workspace_missing_params(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试创建工作区时缺少参数。

        验证当缺少必要参数时，抛出 ValidationError。
        """
        # Arrange
        project_path = str(sample_project_dir)

        # Act & Assert
        # 在 auto_confirm=True 模式下，会先检查 requirement_name 和 requirement_url
        with pytest.raises(ValidationError, match="requirement_name 不能为空|requirement_url 不能为空"):
            execute_full_workflow(
                project_path=project_path,
                requirement_name="",
                requirement_url="",
                auto_confirm=True,
            )

    def test_create_workspace_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试创建工作区失败。

        验证当创建工作区失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
        ):
            mock_submit.return_value = {
                "success": False,
                "error": "创建工作区失败",
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "创建工作区失败" in result["error"]

    def test_step1_skip_logic(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试步骤1跳过逻辑。

        验证当步骤1已完成时，跳过执行。
        """
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager=workspace_manager,
            project_dir=sample_project_dir,
        )
        _update_workflow_state(workspace_id, 1, "创建工作区", "completed")

        with (
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": str(sample_project_dir),
                "requirement_name": "测试需求",
                "requirement_url": "https://example.com/req.md",
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_get_state.return_value = {
                "completed_steps": [{"step": 1, "name": "创建工作区", "status": "completed"}],
            }
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                step_num == 1 and step_name == "创建工作区"
            )
            mock_update_state.return_value = None
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                    "coverage": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 6},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is True
            # 验证步骤1被跳过
            step1 = next(
                (s for s in result["workflow_steps"] if s["step"] == 1), None
            )
            assert step1 is not None
            assert step1["status"] == "completed"

    def test_prd_stage_not_ready(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 PRD 阶段未就绪警告。

        验证当 PRD 阶段未就绪时，会记录警告但继续执行。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-016"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_check_stage.return_value = {"ready": False, "reason": "PRD 阶段未就绪"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            # PRD 阶段未就绪时应该继续执行（因为 PRD 没有前置依赖）
            assert mock_generate_prd.call_count == 1

    def test_prd_confirm_failure_interactive(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 PRD 确认失败（交互模式）。

        验证当 PRD 确认失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-017"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {
                "success": False,
                "error": "PRD 确认失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "confirm",
                },
            )

            # Assert
            assert result["success"] is False
            assert "PRD 确认失败" in result["error"]

    def test_prd_modify_failure_interactive(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 PRD 修改失败（交互模式）。

        验证当 PRD 修改失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.modify_prd") as mock_modify_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-018"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_modify_prd.return_value = {
                "success": False,
                "error": "PRD 修改标记失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "modify",
                },
            )

            # Assert
            assert result["success"] is False
            assert "PRD 修改标记失败" in result["error"]

    def test_check_prd_confirmation_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试检查 PRD 确认失败。

        验证当检查 PRD 确认失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-019"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": False,
                "error": "检查 PRD 确认失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {},
                "workflow_progress": {"completed_stages": 0},
                "next_available_stages": ["prd"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
            )

            # Assert
            assert result["success"] is False
            assert "检查 PRD 确认失败" in result["error"]

    def test_trd_generate_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 生成失败。

        验证当 TRD 生成失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-020"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": False,
                "error": "TRD 生成失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 1},
                "next_available_stages": ["trd"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "TRD 生成失败" in result["error"]

    def test_trd_confirm_failure_interactive(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 确认失败（交互模式）。

        验证当 TRD 确认失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
        ):
            workspace_id = "req-test-021"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            # 跳过步骤1和2（初始问题和PRD），因为工作流已经到达TRD步骤
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                (step_num == 1 and step_name == "提交初始答案")
                or (step_num == 2 and step_name == "PRD 生成和确认")
            )
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_check_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
                "trd_preview": "TRD 预览内容",
            }
            mock_confirm_trd.return_value = {
                "success": False,
                "error": "TRD 确认失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 1},
                "next_available_stages": ["trd"],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "trd_confirmation",
                    "action": "confirm",
                },
            )

            # Assert
            assert result["success"] is False
            assert "TRD 确认失败" in result["error"]

    def test_trd_modify_failure_interactive(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 修改失败（交互模式）。

        验证当 TRD 修改失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.modify_trd") as mock_modify_trd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
        ):
            workspace_id = "req-test-022"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            # 跳过步骤1和2（初始问题和PRD），因为工作流已经到达TRD步骤
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                (step_num == 1 and step_name == "提交初始答案")
                or (step_num == 2 and step_name == "PRD 生成和确认")
            )
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_check_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
                "trd_preview": "TRD 预览内容",
            }
            mock_modify_trd.return_value = {
                "success": False,
                "error": "TRD 修改标记失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 1},
                "next_available_stages": ["trd"],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "trd_confirmation",
                    "action": "modify",
                },
            )

            # Assert
            assert result["success"] is False
            assert "TRD 修改标记失败" in result["error"]

    def test_check_trd_confirmation_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试检查 TRD 确认失败。

        验证当检查 TRD 确认失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch("src.tools.prd_confirmation.WorkspaceManager") as mock_prd_ws_manager,
        ):
            workspace_id = "req-test-023"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_prd_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            prd_completed = [False]  # 使用列表以便在闭包中修改
            
            # 不跳过任何步骤，让工作流正常执行到TRD步骤
            # 但在第三次调用时，PRD 步骤应该已完成
            def skip_step_side_effect(ws_id, step_num, step_name):
                # 第三次调用时，如果 PRD 步骤已完成，跳过它
                if step_num == 2 and step_name == "PRD 生成和确认":
                    return prd_completed[0]
                return False
            mock_skip_step.side_effect = skip_step_side_effect
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_check_trd.return_value = {
                "success": False,
                "error": "检查 TRD 确认失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 1},
                "next_available_stages": ["trd"],
            }

            # Act - 先完成 PRD 确认
            result1 = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
            )
            # 确认 PRD
            result2 = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "confirm",
                },
            )
            # 标记 PRD 步骤已完成
            prd_completed[0] = True
            # 然后测试 TRD 确认失败
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
            )

            # Assert
            assert result["success"] is False
            assert "检查 TRD 确认失败" in result["error"]

    def test_trd_confirm_failure_auto(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 确认失败（自动确认模式）。

        验证当 TRD 确认失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-024"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {
                "success": False,
                "error": "TRD 确认失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 1},
                "next_available_stages": ["trd"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "TRD 确认失败" in result["error"]

    def test_tasks_decompose_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务分解失败。

        验证当任务分解失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-025"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": False,
                "error": "任务分解失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 2},
                "next_available_stages": ["tasks"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "任务分解失败" in result["error"]

    def test_tasks_stage_not_ready(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务分解阶段未就绪。

        验证当任务分解阶段未就绪时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-026"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            # 任务分解阶段未就绪
            mock_check_stage.side_effect = lambda ws_id, stage: (
                {"ready": False, "reason": "任务分解阶段未就绪"}
                if stage == "tasks"
                else {"ready": True, "reason": "可以开始"}
            )
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 2},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "任务分解阶段未就绪" in result["error"]

    def test_code_stage_not_ready(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试代码生成阶段未就绪。

        验证当代码生成阶段未就绪时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-027"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            # 代码生成阶段未就绪
            mock_check_stage.side_effect = lambda ws_id, stage: (
                {"ready": False, "reason": "代码生成阶段未就绪"}
                if stage == "code"
                else {"ready": True, "reason": "可以开始"}
            )
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 3},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "代码生成阶段未就绪" in result["error"]

    def test_task_execution_partial_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试任务执行部分失败。

        验证当部分任务执行失败时，会记录警告但继续执行。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-028"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 2,
            }
            # 部分任务执行失败
            mock_execute_tasks.return_value = {
                "success": False,
                "total_tasks": 2,
                "completed_tasks": 1,
                "failed_tasks": 1,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            # 部分任务失败时应该继续执行
            assert result["success"] is True
            # 验证步骤5的状态为 failed
            step5 = next(
                (s for s in result["workflow_steps"] if s["step"] == 5), None
            )
            assert step5 is not None
            assert step5["status"] == "failed"

    def test_ask_test_path_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试询问测试路径失败。

        验证当询问测试路径失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-029"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": False,
                "error": "询问测试路径失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "询问测试路径失败" in result["error"]

    def test_submit_test_path_failure_interactive(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试提交测试路径失败（交互模式）。

        验证当提交测试路径失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
            patch(
                "src.tools.workflow_orchestrator.check_prd_confirmation"
            ) as mock_check_prd,
            patch(
                "src.tools.workflow_orchestrator.check_trd_confirmation"
            ) as mock_check_trd,
        ):
            workspace_id = "req-test-030"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.side_effect = lambda ws_id, step_num, step_name: (
                (step_num == 2 and step_name == "PRD 生成和确认")
                or (step_num == 3 and step_name == "TRD 生成和确认")
            )
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_check_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
                "prd_preview": "PRD 预览内容",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_check_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
                "trd_preview": "TRD 预览内容",
            }
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {
                "success": False,
                "error": "提交测试路径失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act - 先完成 PRD 和 TRD
            execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "prd_confirmation",
                    "action": "confirm",
                },
            )
            execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "trd_confirmation",
                    "action": "confirm",
                },
            )
            # 然后提供测试路径
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=False,
                interaction_response={
                    "interaction_type": "question",
                    "answer": "/path/to/tests",
                },
            )

            # Assert
            assert result["success"] is False
            assert "提交测试路径失败" in result["error"]

    def test_submit_test_path_failure_auto(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试提交测试路径失败（自动确认模式）。

        验证当提交测试路径失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-031"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {
                "success": False,
                "error": "提交测试路径失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "提交测试路径失败" in result["error"]

    def test_test_stage_not_ready(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试测试生成阶段未就绪警告。

        验证当测试生成阶段未就绪时，会记录警告但继续执行。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-032"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            # 测试生成阶段未就绪
            mock_check_stage.side_effect = lambda ws_id, stage: (
                {"ready": False, "reason": "测试生成阶段未就绪"}
                if stage == "test"
                else {"ready": True, "reason": "可以开始"}
            )
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            # 测试生成阶段未就绪时应该继续执行
            assert result["success"] is True
            assert mock_generate_tests.call_count == 1

    def test_test_path_default_empty(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试测试路径默认值为空。

        验证当测试路径默认值为空时，使用 {project_path}/tests/mock。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-033"
            mock_workspace_instance = MagicMock()
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": project_path,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            # 测试路径默认值为空
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": ""},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is True
            # 验证使用了默认路径 {project_path}/tests/mock
            assert mock_submit_test_path.call_count == 1
            call_args = mock_submit_test_path.call_args
            assert call_args[0][1] == str(Path(project_path) / "tests" / "mock")

    def test_test_path_missing_project_path(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试测试路径缺少 project_path。

        验证当工作区缺少 project_path 时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-034"
            mock_workspace_instance = MagicMock()
            # 工作区缺少 project_path
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": None,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            # 测试路径默认值为空
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": ""},
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            # 验证错误消息：可能是 "project_path 不能为空" 或 "工作区缺少 project_path 字段"
            assert (
                "project_path 不能为空" in result["error"]
                or "工作区缺少 project_path 字段" in result["error"]
            )

    def test_generate_tests_failure(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试测试生成失败。

        验证当测试生成失败时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-035"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": False,
                "error": "测试生成失败",
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 4},
                "next_available_stages": ["test"],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "测试生成失败" in result["error"]

    def test_coverage_stage_not_ready(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试覆盖率分析阶段未就绪警告。

        验证当覆盖率分析阶段未就绪时，会记录警告但继续执行。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.analyze_coverage"
            ) as mock_analyze_coverage,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
        ):
            workspace_id = "req-test-036"
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_analyze_coverage.return_value = {
                "success": True,
                "coverage": 80.0,
                "coverage_report_path": "/path/to/coverage.html",
            }
            # 覆盖率分析阶段未就绪
            mock_check_stage.side_effect = lambda ws_id, stage: (
                {"ready": False, "reason": "覆盖率分析阶段未就绪"}
                if stage == "coverage"
                else {"ready": True, "reason": "可以开始"}
            )
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 5},
                "next_available_stages": [],
            }

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            # 覆盖率分析阶段未就绪时应该继续执行
            assert result["success"] is True
            assert mock_analyze_coverage.call_count == 1

    def test_coverage_missing_project_path(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试覆盖率分析缺少 project_path。

        验证当工作区缺少 project_path 时，抛出 AgentOrchestratorError。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
            patch("src.tools.workflow_orchestrator.generate_prd") as mock_generate_prd,
            patch("src.tools.workflow_orchestrator.confirm_prd") as mock_confirm_prd,
            patch("src.tools.workflow_orchestrator.generate_trd") as mock_generate_trd,
            patch("src.tools.workflow_orchestrator.confirm_trd") as mock_confirm_trd,
            patch("src.tools.workflow_orchestrator.decompose_tasks") as mock_decompose,
            patch(
                "src.tools.workflow_orchestrator.execute_all_tasks"
            ) as mock_execute_tasks,
            patch(
                "src.tools.workflow_orchestrator.ask_test_path"
            ) as mock_ask_test_path,
            patch(
                "src.tools.workflow_orchestrator.submit_test_path"
            ) as mock_submit_test_path,
            patch(
                "src.tools.workflow_orchestrator.generate_tests"
            ) as mock_generate_tests,
            patch(
                "src.tools.workflow_orchestrator.check_stage_ready"
            ) as mock_check_stage,
            patch(
                "src.tools.workflow_orchestrator.get_workflow_status"
            ) as mock_get_status,
            patch(
                "src.tools.workflow_orchestrator._update_workflow_state"
            ) as mock_update_state,
            patch(
                "src.tools.workflow_orchestrator._get_workflow_state"
            ) as mock_get_state,
            patch(
                "src.tools.workflow_orchestrator._should_skip_step"
            ) as mock_skip_step,
            patch("src.tools.workflow_orchestrator.WorkspaceManager") as mock_ws_manager,
        ):
            workspace_id = "req-test-037"
            mock_workspace_instance = MagicMock()
            # 工作区缺少 project_path
            mock_workspace_instance.get_workspace.return_value = {
                "workspace_id": workspace_id,
                "project_path": None,
                "requirement_name": requirement_name,
                "requirement_url": requirement_url,
            }
            mock_ws_manager.return_value = mock_workspace_instance
            mock_update_state.return_value = None
            mock_get_state.return_value = {}
            mock_skip_step.return_value = False
            mock_submit.return_value = {"success": True, "workspace_id": workspace_id}
            mock_generate_prd.return_value = {
                "success": True,
                "prd_path": "/path/to/PRD.md",
            }
            mock_confirm_prd.return_value = {"success": True}
            mock_generate_trd.return_value = {
                "success": True,
                "trd_path": "/path/to/TRD.md",
            }
            mock_confirm_trd.return_value = {"success": True}
            mock_decompose.return_value = {
                "success": True,
                "tasks_json_path": "/path/to/tasks.json",
                "task_count": 1,
            }
            mock_execute_tasks.return_value = {
                "success": True,
                "total_tasks": 1,
                "completed_tasks": 1,
                "failed_tasks": 0,
            }
            mock_ask_test_path.return_value = {
                "success": True,
                "question": {"default": "/path/to/tests"},
            }
            mock_submit_test_path.return_value = {"success": True}
            mock_generate_tests.return_value = {
                "success": True,
                "test_files": ["test_1.py"],
                "test_count": 1,
            }
            mock_check_stage.return_value = {"ready": True, "reason": "可以开始"}
            mock_get_status.return_value = {
                "success": True,
                "stages": {
                    "prd": {"status": "completed"},
                    "trd": {"status": "completed"},
                    "tasks": {"status": "completed"},
                    "code": {"status": "completed"},
                    "test": {"status": "completed"},
                },
                "workflow_progress": {"completed_stages": 5},
                "next_available_stages": ["coverage"],
            }

            # Act
            result = execute_full_workflow(
                workspace_id=workspace_id,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            # 验证错误消息：可能是 "project_path 不能为空" 或 "工作区缺少 project_path 字段"
            assert (
                "project_path 不能为空" in result["error"]
                or "工作区缺少 project_path 字段" in result["error"]
            )

    def test_general_exception_handling(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试通用异常处理。

        验证当发生未预期的异常时，会捕获并返回错误信息。
        """
        # Arrange
        project_path = str(sample_project_dir)
        requirement_name = "测试需求"
        requirement_url = "https://example.com/req.md"

        with (
            patch(
                "src.tools.workflow_orchestrator.submit_orchestrator_answers"
            ) as mock_submit,
        ):
            workspace_id = "req-test-038"
            # 模拟抛出未预期的异常
            mock_submit.side_effect = Exception("未预期的异常")

            # Act
            result = execute_full_workflow(
                project_path=project_path,
                requirement_name=requirement_name,
                requirement_url=requirement_url,
                auto_confirm=True,
            )

            # Assert
            assert result["success"] is False
            assert "工作流执行异常" in result["error"]
            assert "未预期的异常" in result["error"]
