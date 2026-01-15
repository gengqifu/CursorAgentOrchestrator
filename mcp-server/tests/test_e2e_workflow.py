"""端到端工作流测试。

Python 3.9+ 兼容

阶段1（第1周）用户交互工具测试场景：
1. 询问4个问题 → 提交答案 → 创建工作区
2. 生成 PRD → 确认 PRD → 继续
3. 生成 PRD → 修改 PRD → 重新生成 → 确认

阶段2（第2周）任务执行工具测试场景：
1. 完整任务执行流程（代码生成 → Review → 通过）
2. 任务 Review 循环（失败 → 重试 → 通过）
3. 所有任务循环执行
"""

import json
from unittest.mock import patch

import pytest
from mcp.types import TextContent

from src.mcp_server import call_tool
from tests.conftest import create_test_workspace


class TestE2EWorkflow:
    """端到端工作流测试类。"""

    @pytest.mark.asyncio
    async def test_e2e_ask_questions_submit_answers_create_workspace(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """端到端测试：询问4个问题 → 提交答案 → 创建工作区。

        验证完整的工作流：
        1. 询问4个问题
        2. 提交答案
        3. 创建工作区
        """
        # Step 1: 询问4个问题
        result = await call_tool("ask_orchestrator_questions", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        assert data["interaction_type"] == "questions"
        assert len(data["questions"]) == 4

        # Step 2: 提交答案
        answers = {
            "project_path": str(sample_project_dir),
            "requirement_name": "端到端测试需求",
            "requirement_url": "https://example.com/e2e-test.md",
        }

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("submit_orchestrator_answers", answers)

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data
        workspace_id = data["workspace_id"]
        assert workspace_id.startswith("req-")

        # Step 3: 验证工作区已创建
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["workspace_id"] == workspace_id
        assert workspace["requirement_name"] == "端到端测试需求"
        assert workspace["requirement_url"] == "https://example.com/e2e-test.md"
        assert workspace["project_path"] == str(sample_project_dir)

    @pytest.mark.asyncio
    async def test_e2e_generate_prd_confirm_prd_continue(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """端到端测试：生成 PRD → 确认 PRD → 继续。

        验证完整的工作流：
        1. 创建工作区
        2. 生成 PRD
        3. 检查 PRD 确认
        4. 确认 PRD
        5. 验证状态已更新
        """
        # Step 1: 创建工作区
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="PRD确认测试需求"
        )

        # Step 2: 生成 PRD
        req_file = temp_dir / "requirement.md"
        req_file.write_text("# 需求文档\n\n这是测试需求。", encoding="utf-8")

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "generate_prd",
                {"workspace_id": workspace_id, "requirement_url": str(req_file)},
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "prd_path" in data

        # Step 3: 检查 PRD 确认
        result = await call_tool(
            "check_prd_confirmation", {"workspace_id": workspace_id}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        assert data["interaction_type"] == "prd_confirmation"
        assert "prd_path" in data
        assert "prd_preview" in data

        # Step 4: 确认 PRD
        result = await call_tool("confirm_prd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

        # Step 5: 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"

    @pytest.mark.asyncio
    async def test_e2e_generate_prd_modify_regenerate_confirm(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """端到端测试：生成 PRD → 修改 PRD → 重新生成 → 确认。

        验证完整的工作流：
        1. 创建工作区
        2. 生成 PRD
        3. 检查 PRD 确认
        4. 修改 PRD（标记需要重新生成）
        5. 验证状态为 needs_regeneration
        6. 重新生成 PRD
        7. 确认 PRD
        8. 验证状态为 completed
        """
        # Step 1: 创建工作区
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="PRD修改循环测试需求",
        )

        # Step 2: 生成 PRD
        req_file = temp_dir / "requirement.md"
        req_file.write_text("# 需求文档\n\n这是测试需求。", encoding="utf-8")

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "generate_prd",
                {"workspace_id": workspace_id, "requirement_url": str(req_file)},
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "prd_path" in data

        # Step 3: 检查 PRD 确认
        result = await call_tool(
            "check_prd_confirmation", {"workspace_id": workspace_id}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True

        # Step 4: 修改 PRD（标记需要重新生成）
        result = await call_tool("modify_prd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

        # Step 5: 验证状态为 needs_regeneration
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "needs_regeneration"

        # Step 6: 重新生成 PRD
        req_file.write_text(
            "# 需求文档（更新版）\n\n这是更新后的测试需求。", encoding="utf-8"
        )

        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "generate_prd",
                {"workspace_id": workspace_id, "requirement_url": str(req_file)},
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

        # Step 7: 确认 PRD
        result = await call_tool("confirm_prd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

        # Step 8: 验证状态为 completed
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"


class TestE2ETaskExecution:
    """端到端任务执行测试类 - 第2周任务执行工具。"""

    @pytest.mark.asyncio
    async def test_e2e_execute_task_code_generation_review_passed(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """端到端测试：完整任务执行流程（代码生成 → Review → 通过）。

        验证完整的工作流：
        1. 创建工作区
        2. 创建任务
        3. 执行任务（代码生成 → Review → 通过）
        4. 验证任务执行成功
        5. 验证代码文件已生成
        """
        # Step 1: 创建工作区
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="任务执行测试需求",
        )

        # Step 2: 创建任务
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-e2e-001"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="端到端测试任务 - Review 通过",
        )

        # Step 3: 执行任务（Mock generate_code 和 review_code）
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
            patch("src.mcp_server.workspace_manager", workspace_manager),
        ):
            # generate_code 返回成功
            mock_generate.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "code_files": ["/path/to/generated_file.py"],
            }

            # review_code 返回通过
            mock_review.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "passed": True,
                "review_report": "代码审查通过，质量良好。",
            }

            # 调用 execute_task 通过 MCP
            result = await call_tool(
                "execute_task",
                {
                    "workspace_id": workspace_id,
                    "task_id": task_id,
                },
            )

        # Step 4: 验证任务执行成功
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["task_id"] == task_id
        assert data["workspace_id"] == workspace_id
        assert data["passed"] is True
        assert data["retry_count"] == 0
        assert "code_files" in data
        assert len(data["code_files"]) > 0

        # Step 5: 验证 generate_code 和 review_code 被调用
        assert mock_generate.call_count == 1
        assert mock_review.call_count == 1

    @pytest.mark.asyncio
    async def test_e2e_execute_task_review_loop_failed_retry_passed(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """端到端测试：任务 Review 循环（失败 → 重试 → 通过）。

        验证完整的工作流：
        1. 创建工作区
        2. 创建任务
        3. 执行任务（第一次 Review 失败）
        4. 重试（第二次 Review 通过）
        5. 验证任务执行成功，retry_count=1
        """
        # Step 1: 创建工作区
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="任务Review循环测试需求",
        )

        # Step 2: 创建任务
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-e2e-002"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="端到端测试任务 - Review 循环",
        )

        # Step 3-4: 执行任务（Mock generate_code 和 review_code，模拟 Review 循环）
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
            patch("src.mcp_server.workspace_manager", workspace_manager),
        ):
            # generate_code 返回成功（每次调用都成功）
            mock_generate.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "code_files": ["/path/to/generated_file.py"],
            }

            # review_code 第一次返回失败，第二次返回通过
            mock_review.side_effect = [
                {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,  # 第一次失败
                    "review_report": "代码需要改进：缺少错误处理。",
                },
                {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": True,  # 第二次通过
                    "review_report": "代码审查通过，已添加错误处理。",
                },
            ]

            # 调用 execute_task 通过 MCP
            result = await call_tool(
                "execute_task",
                {
                    "workspace_id": workspace_id,
                    "task_id": task_id,
                    "max_review_retries": 3,
                },
            )

        # Step 5: 验证任务执行成功
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["task_id"] == task_id
        assert data["workspace_id"] == workspace_id
        assert data["passed"] is True
        assert data["retry_count"] == 1  # 重试了1次
        assert "code_files" in data

        # 验证 generate_code 被调用2次（第一次生成 + 重试时重新生成）
        # 验证 review_code 被调用2次（第一次失败 + 第二次通过）
        assert mock_generate.call_count == 2
        assert mock_review.call_count == 2

    @pytest.mark.asyncio
    async def test_e2e_execute_all_tasks_loop(
        self, temp_dir, sample_project_dir, workspace_manager
    ):
        """端到端测试：所有任务循环执行。

        验证完整的工作流：
        1. 创建工作区
        2. 创建多个 pending 任务
        3. 执行所有任务
        4. 验证所有任务都执行成功
        5. 验证统计信息正确
        """
        # Step 1: 创建工作区
        workspace_id = create_test_workspace(
            workspace_manager,
            sample_project_dir,
            requirement_name="所有任务循环执行测试需求",
        )

        # Step 2: 创建多个 pending 任务
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_ids = []
        for i in range(1, 4):
            task_id = f"task-e2e-all-{i:03d}"
            task_ids.append(task_id)
            task_manager.update_task_status(
                workspace_id,
                task_id,
                "pending",
                description=f"端到端测试任务 {i}",
            )

        # Step 3: 执行所有任务（Mock generate_code 和 review_code）
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
            patch("src.mcp_server.workspace_manager", workspace_manager),
        ):
            # generate_code 返回成功（为每个任务返回）
            def generate_side_effect(workspace_id: str, task_id: str):
                return {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "code_files": [f"/path/to/generated_file_{task_id}.py"],
                }

            mock_generate.side_effect = generate_side_effect

            # review_code 返回通过（为每个任务返回）
            def review_side_effect(workspace_id: str, task_id: str):
                return {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": True,
                    "review_report": f"任务 {task_id} 审查通过。",
                }

            mock_review.side_effect = review_side_effect

            # 调用 execute_all_tasks 通过 MCP
            result = await call_tool(
                "execute_all_tasks",
                {
                    "workspace_id": workspace_id,
                },
            )

        # Step 4: 验证所有任务都执行成功
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["workspace_id"] == workspace_id
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 3
        assert data["failed_tasks"] == 0
        assert len(data["task_results"]) == 3

        # 验证每个任务都成功
        for i, task_result in enumerate(data["task_results"]):
            assert task_result["success"] is True
            assert task_result["task_id"] == task_ids[i]
            assert task_result["passed"] is True
            assert task_result["retry_count"] == 0

        # Step 5: 验证 generate_code 和 review_code 被调用了3次（每个任务1次）
        assert mock_generate.call_count == 3
        assert mock_review.call_count == 3
