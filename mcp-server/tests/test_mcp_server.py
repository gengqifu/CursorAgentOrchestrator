"""MCP Server 测试 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.types import TextContent

from src.core.exceptions import (
    ValidationError,
)
from src.mcp_server import _handle_error, call_tool, list_tools


class TestMCPServer:
    """MCP Server 测试类。"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """测试 list_tools 返回所有工具。"""
        tools = await list_tools()

        assert (
            len(tools) == 25
        )  # 5 个基础设施工具 + 2 个工作流编排工具 + 3 个 PRD 确认工具 + 3 个 TRD 确认工具 + 2 个测试路径询问工具 + 2 个任务执行工具 + 8 个 SKILL 工具

        # 检查基础设施工具
        tool_names = [tool.name for tool in tools]
        assert "create_workspace" in tool_names
        assert "get_workspace" in tool_names
        assert "update_workspace_status" in tool_names
        assert "get_tasks" in tool_names
        assert "update_task_status" in tool_names

        # 检查工作流编排工具
        assert "ask_orchestrator_questions" in tool_names
        assert "submit_orchestrator_answers" in tool_names

        # 检查 PRD 确认工具
        assert "check_prd_confirmation" in tool_names
        assert "confirm_prd" in tool_names
        assert "modify_prd" in tool_names

        # 检查 TRD 确认工具
        assert "check_trd_confirmation" in tool_names
        assert "confirm_trd" in tool_names
        assert "modify_trd" in tool_names

        # 检查测试路径询问工具
        assert "ask_test_path" in tool_names
        assert "submit_test_path" in tool_names

        # 检查任务执行工具
        assert "execute_task" in tool_names
        assert "execute_all_tasks" in tool_names

        # 检查 SKILL 工具
        assert "generate_prd" in tool_names
        assert "generate_trd" in tool_names
        assert "decompose_tasks" in tool_names
        assert "generate_code" in tool_names
        assert "review_code" in tool_names
        assert "generate_tests" in tool_names
        assert "review_tests" in tool_names
        assert "analyze_coverage" in tool_names

    def test_handle_error_returns_error_response(self):
        """测试 _handle_error 返回错误响应。"""
        error = ValidationError("测试错误")
        result = _handle_error(error)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        error_data = json.loads(result[0].text)
        assert error_data["success"] is False
        assert error_data["error"] == "测试错误"
        assert error_data["error_type"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_call_tool_create_workspace(self, temp_dir, sample_project_dir):
        """测试 create_workspace 工具。"""
        result = await call_tool(
            "create_workspace",
            {
                "project_path": str(sample_project_dir),
                "requirement_name": "测试需求",
                "requirement_url": "https://example.com/req",
            },
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data

    @pytest.mark.asyncio
    async def test_call_tool_get_workspace(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 get_workspace 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("get_workspace", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace" in data
        assert data["workspace"]["workspace_id"] == workspace_id

    @pytest.mark.asyncio
    async def test_call_tool_get_workspace_not_found(self):
        """测试 get_workspace 工具 - 工作区不存在。"""
        result = await call_tool(
            "get_workspace", {"workspace_id": "non-existent-workspace"}
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert data["error_type"] == "WorkspaceNotFoundError"

    @pytest.mark.asyncio
    async def test_call_tool_update_workspace_status(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 update_workspace_status 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "update_workspace_status",
                {
                    "workspace_id": workspace_id,
                    "status_updates": {"prd_status": "completed"},
                },
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_call_tool_get_tasks(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 get_tasks 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 task_manager
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager(config=workspace_manager.config)

        with patch("src.mcp_server.task_manager", task_manager):
            result = await call_tool("get_tasks", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    @pytest.mark.asyncio
    async def test_call_tool_update_task_status(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 update_task_status 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 task_manager
        from src.managers.task_manager import TaskManager

        task_manager = TaskManager(config=workspace_manager.config)

        with patch("src.mcp_server.task_manager", task_manager):
            result = await call_tool(
                "update_task_status",
                {
                    "workspace_id": workspace_id,
                    "task_id": "task-001",
                    "status": "completed",
                },
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_call_tool_generate_prd(
        self,
        create_test_workspace_fixture,
        temp_dir,
        workspace_manager,
        sample_project_dir,
    ):
        """测试 generate_prd 工具。"""
        workspace_id = create_test_workspace_fixture
        req_file = temp_dir / "requirement.md"
        req_file.write_text("# 测试需求", encoding="utf-8")

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

    @pytest.mark.asyncio
    async def test_call_tool_generate_trd(
        self,
        create_test_workspace_fixture,
        temp_dir,
        workspace_manager,
        sample_project_dir,
    ):
        """测试 generate_trd 工具。"""
        workspace_id = create_test_workspace_fixture

        # 先创建 PRD
        prd_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id)) / "PRD.md"
        )
        prd_file.write_text("# PRD", encoding="utf-8")
        workspace_manager.update_workspace_status(
            workspace_id, {"prd_status": "completed"}
        )
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["prd_path"] = str(prd_file)
        meta_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id))
            / "workspace.json"
        )
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("generate_trd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "trd_path" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_trd_without_prd(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 generate_trd 工具 - 没有 PRD。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("generate_trd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "PRD" in data["error"] or "prd" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_call_tool_decompose_tasks(
        self,
        create_test_workspace_fixture,
        temp_dir,
        workspace_manager,
        sample_project_dir,
    ):
        """测试 decompose_tasks 工具。"""
        workspace_id = create_test_workspace_fixture

        # 先创建 TRD
        trd_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id)) / "TRD.md"
        )
        trd_file.write_text("# TRD\n## 任务1\n## 任务2", encoding="utf-8")
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["trd_path"] = str(trd_file)
        meta_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id))
            / "workspace.json"
        )
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("decompose_tasks", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "tasks_json_path" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_code(
        self,
        create_test_workspace_fixture,
        temp_dir,
        workspace_manager,
        sample_project_dir,
    ):
        """测试 generate_code 工具。"""
        workspace_id = create_test_workspace_fixture

        # 先创建 tasks.json
        tasks_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id))
            / "tasks.json"
        )
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {"task_id": "task-001", "description": "测试任务", "status": "pending"}
            ],
        }
        import json

        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "generate_code", {"workspace_id": workspace_id, "task_id": "task-001"}
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_call_tool_review_code(
        self,
        create_test_workspace_fixture,
        temp_dir,
        workspace_manager,
        sample_project_dir,
    ):
        """测试 review_code 工具。"""
        workspace_id = create_test_workspace_fixture

        # 先创建 tasks.json 和代码文件
        tasks_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id))
            / "tasks.json"
        )
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(temp_dir / "test.py")],
                }
            ],
        }
        import json

        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # 创建代码文件
        code_file = temp_dir / "test.py"
        code_file.write_text("def test(): pass", encoding="utf-8")

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "review_code", {"workspace_id": workspace_id, "task_id": "task-001"}
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_tests(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 generate_tests 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("generate_tests", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "test_files" in data

    @pytest.mark.asyncio
    async def test_call_tool_review_tests(
        self,
        create_test_workspace_fixture,
        temp_dir,
        workspace_manager,
        sample_project_dir,
    ):
        """测试 review_tests 工具。"""
        workspace_id = create_test_workspace_fixture

        # 创建测试文件
        test_file = temp_dir / "test_example.py"
        test_file.write_text("def test_example(): pass", encoding="utf-8")

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "review_tests",
                {"workspace_id": workspace_id, "test_files": [str(test_file)]},
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "passed" in data

    @pytest.mark.asyncio
    async def test_call_tool_analyze_coverage(
        self, create_test_workspace_fixture, sample_project_dir, workspace_manager
    ):
        """测试 analyze_coverage 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "analyze_coverage",
                {"workspace_id": workspace_id, "project_path": str(sample_project_dir)},
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "coverage" in data

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """测试未知工具。"""
        result = await call_tool("unknown_tool", {})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "未知工具" in data["error"] or "unknown" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_call_tool_with_none_arguments(self):
        """测试 call_tool 使用 None 参数。"""
        result = await call_tool("get_tasks", None)

        assert len(result) == 1
        data = json.loads(result[0].text)
        # 应该处理 None 参数，可能返回错误或空列表
        assert "success" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_prd_with_validation_error(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 generate_prd 工具 - 验证错误。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "generate_prd",
                {
                    "workspace_id": workspace_id,
                    "requirement_url": "",  # 空 URL 应该触发验证错误
                },
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert data["error_type"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_call_tool_decompose_tasks_without_trd(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 decompose_tasks 工具 - 没有 TRD。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("decompose_tasks", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "TRD" in data["error"] or "trd" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_call_tool_analyze_coverage_without_project_path(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试 analyze_coverage 工具 - 没有 project_path。"""
        workspace_id = create_test_workspace_fixture

        # 移除工作区中的 project_path
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["project_path"] = ""
        meta_file = (
            Path(workspace_manager.config.get_workspace_path(workspace_id))
            / "workspace.json"
        )
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("analyze_coverage", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "项目路径" in data["error"] or "project_path" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_call_tool_handles_general_exception(self, monkeypatch):
        """测试 call_tool 处理一般异常。"""
        # Mock generate_prd 抛出一般异常
        from src.tools import prd_generator

        def mock_generate_prd(*args, **kwargs):
            raise RuntimeError("模拟运行时错误")

        monkeypatch.setattr(prd_generator, "generate_prd", mock_generate_prd)

        result = await call_tool(
            "generate_prd",
            {"workspace_id": "test-workspace", "requirement_url": "/path/to/req.md"},
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_ask_orchestrator_questions_via_mcp(self):
        """测试通过 MCP 调用 ask_orchestrator_questions 工具。"""
        result = await call_tool("ask_orchestrator_questions", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        assert data["interaction_type"] == "questions"
        assert "questions" in data
        assert len(data["questions"]) == 4

        # 验证问题结构
        question_ids = [q["id"] for q in data["questions"]]
        assert "project_path" in question_ids
        assert "requirement_name" in question_ids
        assert "requirement_url" in question_ids
        assert "workspace_path" in question_ids

    @pytest.mark.asyncio
    async def test_submit_orchestrator_answers_via_mcp(
        self, temp_dir, sample_project_dir
    ):
        """测试通过 MCP 调用 submit_orchestrator_answers 工具。"""
        answers = {
            "project_path": str(sample_project_dir),
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/requirement.md",
        }

        result = await call_tool("submit_orchestrator_answers", answers)

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data
        assert data["workspace_id"].startswith("req-")

    @pytest.mark.asyncio
    async def test_submit_orchestrator_answers_via_mcp_missing_required(self):
        """测试通过 MCP 调用 submit_orchestrator_answers - 缺少必填字段。"""
        result = await call_tool(
            "submit_orchestrator_answers",
            {
                "project_path": "/tmp",
                # 缺少 requirement_name 和 requirement_url
            },
        )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "error" in data
        assert "必填字段缺失或为空" in data["error"]

    @pytest.mark.asyncio
    async def test_check_prd_confirmation_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 check_prd_confirmation 工具。"""
        workspace_id = create_test_workspace_fixture

        # 创建 PRD 文件
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        prd_path = workspace_dir / "PRD.md"
        prd_path.write_text("# PRD 文档\n\n这是测试 PRD 内容。", encoding="utf-8")

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["prd_path"] = str(prd_path)
        meta_file = workspace_dir / "workspace.json"
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
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

    @pytest.mark.asyncio
    async def test_confirm_prd_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 confirm_prd 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("confirm_prd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"

    @pytest.mark.asyncio
    async def test_modify_prd_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 modify_prd 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("modify_prd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "needs_regeneration"

    @pytest.mark.asyncio
    async def test_check_trd_confirmation_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 check_trd_confirmation 工具。"""
        workspace_id = create_test_workspace_fixture

        # 创建 TRD 文件
        from src.core.config import Config

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_path = workspace_dir / "TRD.md"
        trd_path.write_text("# TRD 文档\n\n这是测试 TRD 内容。", encoding="utf-8")

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["trd_path"] = str(trd_path)
        meta_file = workspace_dir / "workspace.json"
        import json

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "check_trd_confirmation", {"workspace_id": workspace_id}
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        assert data["interaction_type"] == "trd_confirmation"
        assert "trd_path" in data
        assert "trd_preview" in data

    @pytest.mark.asyncio
    async def test_confirm_trd_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 confirm_trd 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("confirm_trd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "completed"

    @pytest.mark.asyncio
    async def test_modify_trd_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 modify_trd 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("modify_trd", {"workspace_id": workspace_id})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data

        # 验证状态已更新
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["trd_status"] == "needs_regeneration"

    @pytest.mark.asyncio
    async def test_ask_test_path_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 ask_test_path 工具。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool("ask_test_path", {"workspace_id": workspace_id})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        assert data["interaction_type"] == "question"
        assert "question" in data
        assert data["question"]["id"] == "test_path"
        assert "default" in data["question"]
        assert str(sample_project_dir) in data["question"]["default"]

    @pytest.mark.asyncio
    async def test_submit_test_path_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 submit_test_path 工具。"""
        workspace_id = create_test_workspace_fixture
        test_path = str(sample_project_dir / "tests" / "mock")

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "submit_test_path",
                {"workspace_id": workspace_id, "test_path": test_path},
            )

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["workspace_id"] == workspace_id
        assert data["test_path"] == test_path

        # 验证已保存到工作区元数据
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["files"]["test_path"] == test_path

    @pytest.mark.asyncio
    async def test_submit_test_path_via_mcp_missing_required(
        self, create_test_workspace_fixture, workspace_manager
    ):
        """测试通过 MCP 调用 submit_test_path - 缺少必填字段。"""
        workspace_id = create_test_workspace_fixture

        # Mock mcp_server 模块中的 workspace_manager
        with patch("src.mcp_server.workspace_manager", workspace_manager):
            result = await call_tool(
                "submit_test_path",
                {
                    "workspace_id": workspace_id
                    # 缺少 test_path
                },
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_execute_task_via_mcp(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """测试通过 MCP 调用 execute_task 工具。"""
        workspace_id = create_test_workspace_fixture

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-001"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock execute_task 函数
        with patch("src.mcp_server.execute_task") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "passed": True,
                "retry_count": 0,
                "review_report": "审查通过",
                "code_files": ["/path/to/file.py"],
            }

            result = await call_tool(
                "execute_task",
                {
                    "workspace_id": workspace_id,
                    "task_id": task_id,
                },
            )

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["task_id"] == task_id
        assert data["workspace_id"] == workspace_id
        assert data["passed"] is True

    @pytest.mark.asyncio
    async def test_execute_task_via_mcp_with_retries(
        self, create_test_workspace_fixture, workspace_manager
    ):
        """测试通过 MCP 调用 execute_task 工具 - 带重试次数参数。"""
        workspace_id = create_test_workspace_fixture

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-002"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="测试任务",
        )

        # Mock execute_task 函数
        with patch("src.mcp_server.execute_task") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "passed": True,
                "retry_count": 1,
                "review_report": "审查通过",
                "code_files": ["/path/to/file.py"],
            }

            result = await call_tool(
                "execute_task",
                {
                    "workspace_id": workspace_id,
                    "task_id": task_id,
                    "max_review_retries": 5,
                },
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["retry_count"] == 1
        # 验证传递了 max_review_retries 参数
        assert mock_execute.call_args[1]["max_review_retries"] == 5

    @pytest.mark.asyncio
    async def test_execute_all_tasks_via_mcp(
        self, create_test_workspace_fixture, workspace_manager
    ):
        """测试通过 MCP 调用 execute_all_tasks 工具。"""
        workspace_id = create_test_workspace_fixture

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 创建2个 pending 任务
        for i in range(1, 3):
            task_id = f"task-{i:03d}"
            task_manager.update_task_status(
                workspace_id,
                task_id,
                "pending",
                description=f"测试任务 {i}",
            )

        # Mock execute_all_tasks 函数
        with patch("src.mcp_server.execute_all_tasks") as mock_execute_all:
            mock_execute_all.return_value = {
                "success": True,
                "workspace_id": workspace_id,
                "total_tasks": 2,
                "completed_tasks": 2,
                "failed_tasks": 0,
                "task_results": [
                    {
                        "success": True,
                        "task_id": "task-001",
                        "passed": True,
                        "retry_count": 0,
                    },
                    {
                        "success": True,
                        "task_id": "task-002",
                        "passed": True,
                        "retry_count": 0,
                    },
                ],
            }

            result = await call_tool(
                "execute_all_tasks",
                {
                    "workspace_id": workspace_id,
                },
            )

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["workspace_id"] == workspace_id
        assert data["total_tasks"] == 2
        assert data["completed_tasks"] == 2
        assert data["failed_tasks"] == 0
        assert len(data["task_results"]) == 2

    @pytest.mark.asyncio
    async def test_execute_all_tasks_via_mcp_with_retries(
        self, create_test_workspace_fixture, workspace_manager
    ):
        """测试通过 MCP 调用 execute_all_tasks 工具 - 带重试次数参数。"""
        workspace_id = create_test_workspace_fixture

        # Mock execute_all_tasks 函数
        with patch("src.mcp_server.execute_all_tasks") as mock_execute_all:
            mock_execute_all.return_value = {
                "success": True,
                "workspace_id": workspace_id,
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "task_results": [],
            }

            result = await call_tool(
                "execute_all_tasks",
                {
                    "workspace_id": workspace_id,
                    "max_review_retries": 5,
                },
            )

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        # 验证传递了 max_review_retries 参数
        assert mock_execute_all.call_args[1]["max_review_retries"] == 5

    @pytest.mark.asyncio
    async def test_integration_execute_task_review_passed(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """集成测试：单个任务执行（Review 通过）。

        测试完整流程：
        1. 创建任务
        2. 调用 execute_task 通过 MCP
        3. 验证 generate_code 被调用
        4. 验证 review_code 被调用并返回 passed=True
        5. 验证任务执行成功
        """
        workspace_id = create_test_workspace_fixture

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-integration-001"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="集成测试任务 - Review 通过",
        )

        # Mock generate_code 和 review_code，模拟 Review 通过的场景
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
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

        # 验证结果
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["task_id"] == task_id
        assert data["workspace_id"] == workspace_id
        assert data["passed"] is True
        assert data["retry_count"] == 0

        # 验证 generate_code 和 review_code 被调用
        assert mock_generate.call_count == 1
        assert mock_review.call_count == 1

    @pytest.mark.asyncio
    async def test_integration_execute_task_review_failed_retry(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """集成测试：单个任务执行（Review 失败重试）。

        测试完整流程：
        1. 创建任务
        2. 调用 execute_task 通过 MCP
        3. 验证 generate_code 被调用
        4. 验证 review_code 第一次返回 passed=False
        5. 验证 review_code 第二次返回 passed=True（重试成功）
        6. 验证任务执行成功，retry_count=1
        """
        workspace_id = create_test_workspace_fixture

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        task_id = "task-integration-002"
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "pending",
            description="集成测试任务 - Review 失败重试",
        )

        # Mock generate_code 和 review_code，模拟 Review 失败后重试成功的场景
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
        ):
            # generate_code 返回成功
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
                    "passed": False,
                    "review_report": "代码需要改进：缺少错误处理。",
                },
                {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": True,
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

        # 验证结果
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["task_id"] == task_id
        assert data["workspace_id"] == workspace_id
        assert data["passed"] is True
        assert data["retry_count"] == 1  # 重试了1次

        # 验证 generate_code 被调用1次，review_code 被调用2次（1次失败 + 1次成功）
        assert mock_generate.call_count == 2  # 第一次生成 + 重试时重新生成
        assert mock_review.call_count == 2  # 第一次审查失败 + 第二次审查通过

    @pytest.mark.asyncio
    async def test_integration_execute_all_tasks_loop(
        self, create_test_workspace_fixture, workspace_manager, sample_project_dir
    ):
        """集成测试：所有任务循环执行。

        测试完整流程：
        1. 创建多个 pending 任务
        2. 调用 execute_all_tasks 通过 MCP
        3. 验证每个任务都被执行
        4. 验证所有任务执行成功
        5. 验证统计信息正确
        """
        workspace_id = create_test_workspace_fixture

        from src.managers.task_manager import TaskManager

        task_manager = TaskManager()
        # 创建3个 pending 任务
        task_ids = []
        for i in range(1, 4):
            task_id = f"task-integration-all-{i:03d}"
            task_ids.append(task_id)
            task_manager.update_task_status(
                workspace_id,
                task_id,
                "pending",
                description=f"集成测试任务 {i}",
            )

        # Mock generate_code 和 review_code，模拟所有任务都成功
        with (
            patch("src.tools.task_executor.generate_code") as mock_generate,
            patch("src.tools.task_executor.review_code") as mock_review,
        ):
            # generate_code 返回成功
            def generate_side_effect(workspace_id: str, task_id: str):
                return {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "code_files": [f"/path/to/generated_file_{task_id}.py"],
                }

            mock_generate.side_effect = generate_side_effect

            # review_code 返回通过
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

        # 验证结果
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

        # 验证 generate_code 和 review_code 被调用了3次（每个任务1次）
        assert mock_generate.call_count == 3
        assert mock_review.call_count == 3
