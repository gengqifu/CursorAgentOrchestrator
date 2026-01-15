"""端到端工作流测试 - 第1周用户交互工具。

Python 3.9+ 兼容

测试完整的工作流场景：
1. 询问4个问题 → 提交答案 → 创建工作区
2. 生成 PRD → 确认 PRD → 继续
3. 生成 PRD → 修改 PRD → 重新生成 → 确认
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

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
        with patch('src.mcp_server.workspace_manager', workspace_manager):
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
            workspace_manager, sample_project_dir,
            requirement_name="PRD确认测试需求"
        )
        
        # Step 2: 生成 PRD
        req_file = temp_dir / "requirement.md"
        req_file.write_text("# 需求文档\n\n这是测试需求。", encoding='utf-8')
        
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
        
        # Step 3: 检查 PRD 确认
        result = await call_tool(
            "check_prd_confirmation",
            {"workspace_id": workspace_id}
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        assert data["interaction_type"] == "prd_confirmation"
        assert "prd_path" in data
        assert "prd_preview" in data
        
        # Step 4: 确认 PRD
        result = await call_tool(
            "confirm_prd",
            {"workspace_id": workspace_id}
        )
        
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
            workspace_manager, sample_project_dir,
            requirement_name="PRD修改循环测试需求"
        )
        
        # Step 2: 生成 PRD
        req_file = temp_dir / "requirement.md"
        req_file.write_text("# 需求文档\n\n这是测试需求。", encoding='utf-8')
        
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
        
        # Step 3: 检查 PRD 确认
        result = await call_tool(
            "check_prd_confirmation",
            {"workspace_id": workspace_id}
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        assert data["interaction_required"] is True
        
        # Step 4: 修改 PRD（标记需要重新生成）
        result = await call_tool(
            "modify_prd",
            {"workspace_id": workspace_id}
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        
        # Step 5: 验证状态为 needs_regeneration
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "needs_regeneration"
        
        # Step 6: 重新生成 PRD
        req_file.write_text("# 需求文档（更新版）\n\n这是更新后的测试需求。", encoding='utf-8')
        
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
        
        # Step 7: 确认 PRD
        result = await call_tool(
            "confirm_prd",
            {"workspace_id": workspace_id}
        )
        
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert data["success"] is True
        
        # Step 8: 验证状态为 completed
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["prd_status"] == "completed"
