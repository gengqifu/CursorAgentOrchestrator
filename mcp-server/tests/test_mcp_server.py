"""MCP Server 测试 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

from mcp.types import TextContent

from src.mcp_server import (
    server,
    list_tools,
    call_tool,
    _handle_error
)
from src.core.exceptions import (
    ValidationError,
    WorkspaceNotFoundError,
    TaskNotFoundError,
    AgentOrchestratorError
)


class TestMCPServer:
    """MCP Server 测试类。"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """测试 list_tools 返回所有工具。"""
        tools = await list_tools()
        
        assert len(tools) == 15  # 5 个基础设施工具 + 2 个工作流编排工具 + 8 个 SKILL 工具
        
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
                "requirement_url": "https://example.com/req"
            }
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace_id" in data

    @pytest.mark.asyncio
    async def test_call_tool_get_workspace(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 get_workspace 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "get_workspace",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "workspace" in data
        assert data["workspace"]["workspace_id"] == workspace_id

    @pytest.mark.asyncio
    async def test_call_tool_get_workspace_not_found(self):
        """测试 get_workspace 工具 - 工作区不存在。"""
        result = await call_tool(
            "get_workspace",
            {"workspace_id": "non-existent-workspace"}
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert data["error_type"] == "WorkspaceNotFoundError"

    @pytest.mark.asyncio
    async def test_call_tool_update_workspace_status(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 update_workspace_status 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "update_workspace_status",
                {
                    "workspace_id": workspace_id,
                    "status_updates": {"prd_status": "completed"}
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_call_tool_get_tasks(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 get_tasks 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 task_manager
        from src.managers.task_manager import TaskManager
        from src.core.config import Config
        task_manager = TaskManager(config=workspace_manager.config)
        
        with patch('src.mcp_server.task_manager', task_manager):
            result = await call_tool(
                "get_tasks",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    @pytest.mark.asyncio
    async def test_call_tool_update_task_status(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 update_task_status 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 task_manager
        from src.managers.task_manager import TaskManager
        task_manager = TaskManager(config=workspace_manager.config)
        
        with patch('src.mcp_server.task_manager', task_manager):
            result = await call_tool(
                "update_task_status",
                {
                    "workspace_id": workspace_id,
                    "task_id": "task-001",
                    "status": "completed"
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_call_tool_generate_prd(self, create_test_workspace_fixture, temp_dir, workspace_manager, sample_project_dir):
        """测试 generate_prd 工具。"""
        workspace_id = create_test_workspace_fixture
        req_file = temp_dir / "requirement.md"
        req_file.write_text("# 测试需求", encoding='utf-8')
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "generate_prd",
                {
                    "workspace_id": workspace_id,
                    "requirement_url": str(req_file)
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "prd_path" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_trd(self, create_test_workspace_fixture, temp_dir, workspace_manager, sample_project_dir):
        """测试 generate_trd 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # 先创建 PRD
        prd_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "PRD.md"
        prd_file.write_text("# PRD", encoding='utf-8')
        workspace_manager.update_workspace_status(
            workspace_id,
            {"prd_status": "completed"}
        )
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["prd_path"] = str(prd_file)
        meta_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "workspace.json"
        import json
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "generate_trd",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "trd_path" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_trd_without_prd(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 generate_trd 工具 - 没有 PRD。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "generate_trd",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "PRD" in data["error"] or "prd" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_call_tool_decompose_tasks(self, create_test_workspace_fixture, temp_dir, workspace_manager, sample_project_dir):
        """测试 decompose_tasks 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # 先创建 TRD
        trd_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "TRD.md"
        trd_file.write_text("# TRD\n## 任务1\n## 任务2", encoding='utf-8')
        workspace_manager.update_workspace_status(
            workspace_id,
            {"trd_status": "completed"}
        )
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["trd_path"] = str(trd_file)
        meta_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "workspace.json"
        import json
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "decompose_tasks",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "tasks_json_path" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_code(self, create_test_workspace_fixture, temp_dir, workspace_manager, sample_project_dir):
        """测试 generate_code 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # 先创建 tasks.json
        tasks_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "pending"
                }
            ]
        }
        import json
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "generate_code",
                {
                    "workspace_id": workspace_id,
                    "task_id": "task-001"
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_call_tool_review_code(self, create_test_workspace_fixture, temp_dir, workspace_manager, sample_project_dir):
        """测试 review_code 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # 先创建 tasks.json 和代码文件
        tasks_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(temp_dir / "test.py")]
                }
            ]
        }
        import json
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        
        # 创建代码文件
        code_file = temp_dir / "test.py"
        code_file.write_text("def test(): pass", encoding='utf-8')
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "review_code",
                {
                    "workspace_id": workspace_id,
                    "task_id": "task-001"
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_call_tool_generate_tests(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 generate_tests 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "generate_tests",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "test_files" in data

    @pytest.mark.asyncio
    async def test_call_tool_review_tests(self, create_test_workspace_fixture, temp_dir, workspace_manager, sample_project_dir):
        """测试 review_tests 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # 创建测试文件
        test_file = temp_dir / "test_example.py"
        test_file.write_text("def test_example(): pass", encoding='utf-8')
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "review_tests",
                {
                    "workspace_id": workspace_id,
                    "test_files": [str(test_file)]
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert "passed" in data

    @pytest.mark.asyncio
    async def test_call_tool_analyze_coverage(self, create_test_workspace_fixture, sample_project_dir, workspace_manager):
        """测试 analyze_coverage 工具。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "analyze_coverage",
                {
                    "workspace_id": workspace_id,
                    "project_path": str(sample_project_dir)
                }
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
    async def test_call_tool_generate_prd_with_validation_error(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 generate_prd 工具 - 验证错误。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "generate_prd",
                {
                    "workspace_id": workspace_id,
                    "requirement_url": ""  # 空 URL 应该触发验证错误
                }
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert data["error_type"] == "ValidationError"
    
    @pytest.mark.asyncio
    async def test_call_tool_decompose_tasks_without_trd(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 decompose_tasks 工具 - 没有 TRD。"""
        workspace_id = create_test_workspace_fixture
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "decompose_tasks",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "TRD" in data["error"] or "trd" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_call_tool_analyze_coverage_without_project_path(self, create_test_workspace_fixture, workspace_manager, sample_project_dir):
        """测试 analyze_coverage 工具 - 没有 project_path。"""
        workspace_id = create_test_workspace_fixture
        
        # 移除工作区中的 project_path
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["project_path"] = ""
        meta_file = Path(workspace_manager.config.get_workspace_path(workspace_id)) / "workspace.json"
        import json
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)
        
        # Mock mcp_server 模块中的 workspace_manager
        with patch('src.mcp_server.workspace_manager', workspace_manager):
            result = await call_tool(
                "analyze_coverage",
                {"workspace_id": workspace_id}
            )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "项目路径" in data["error"] or "project_path" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_call_tool_handles_general_exception(self, monkeypatch):
        """测试 call_tool 处理一般异常。"""
        # Mock generate_prd 抛出一般异常
        from src.tools import prd_generator
        original_generate_prd = prd_generator.generate_prd
        
        def mock_generate_prd(*args, **kwargs):
            raise RuntimeError("模拟运行时错误")
        
        monkeypatch.setattr(prd_generator, "generate_prd", mock_generate_prd)
        
        result = await call_tool(
            "generate_prd",
            {
                "workspace_id": "test-workspace",
                "requirement_url": "/path/to/req.md"
            }
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
    async def test_submit_orchestrator_answers_via_mcp(self, temp_dir, sample_project_dir):
        """测试通过 MCP 调用 submit_orchestrator_answers 工具。"""
        answers = {
            "project_path": str(sample_project_dir),
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/requirement.md"
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
            }
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is False
        assert "error" in data
        assert "必填字段缺失或为空" in data["error"]
