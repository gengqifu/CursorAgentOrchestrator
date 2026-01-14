"""MCP Server 实现 - 中央编排服务。

根据 PDF 文档架构：
Kiro CLI → MCP Server (中央编排服务) → 8个子SKILL模块 → 项目代码仓库

本模块实现 MCP Server，暴露 8 个 SKILL 工具和基础设施工具。
"""
import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from src.core.logger import setup_logger
from src.core.exceptions import (
    ValidationError,
    WorkspaceNotFoundError,
    TaskNotFoundError,
    AgentOrchestratorError
)
from src.managers.workspace_manager import WorkspaceManager
from src.managers.task_manager import TaskManager

# 导入 8 个 SKILL 工具
from src.tools.prd_generator import generate_prd
from src.tools.trd_generator import generate_trd
from src.tools.task_decomposer import decompose_tasks
from src.tools.code_generator import generate_code
from src.tools.code_reviewer import review_code
from src.tools.test_generator import generate_tests
from src.tools.test_reviewer import review_tests
from src.tools.coverage_analyzer import analyze_coverage

logger = setup_logger(__name__)

# 创建 MCP Server 实例
server = Server("agent-orchestrator")

# 初始化管理器
workspace_manager = WorkspaceManager()
task_manager = TaskManager()


def _handle_error(error: Exception) -> list[TextContent]:
    """统一错误处理。
    
    Args:
        error: 异常对象
    
    Returns:
        错误响应内容
    """
    error_type = error.__class__.__name__
    error_msg = str(error)
    
    logger.error(f"工具执行错误 [{error_type}]: {error_msg}", exc_info=True)
    
    return [
        TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": error_msg,
                "error_type": error_type
            }, ensure_ascii=False)
        )
    ]


# ==================== 基础设施工具 ====================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具。"""
    return [
        # 基础设施工具
        Tool(
            name="create_workspace",
            description="创建工作区",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "项目路径"},
                    "requirement_name": {"type": "string", "description": "需求名称"},
                    "requirement_url": {"type": "string", "description": "需求URL或文件路径"}
                },
                "required": ["project_path", "requirement_name", "requirement_url"]
            }
        ),
        Tool(
            name="get_workspace",
            description="获取工作区信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"}
                },
                "required": ["workspace_id"]
            }
        ),
        Tool(
            name="update_workspace_status",
            description="更新工作区状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "status_updates": {"type": "object", "description": "状态更新字典"}
                },
                "required": ["workspace_id", "status_updates"]
            }
        ),
        Tool(
            name="get_tasks",
            description="获取任务列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"}
                },
                "required": ["workspace_id"]
            }
        ),
        Tool(
            name="update_task_status",
            description="更新任务状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "task_id": {"type": "string", "description": "任务ID"},
                    "status": {"type": "string", "description": "新状态"},
                    "updates": {"type": "object", "description": "其他更新字段"}
                },
                "required": ["workspace_id", "task_id", "status"]
            }
        ),
        # 8 个 SKILL 工具
        Tool(
            name="generate_prd",
            description="生成 PRD 文档（SKILL: prd-generator）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "requirement_url": {"type": "string", "description": "需求文档URL或文件路径"}
                },
                "required": ["workspace_id", "requirement_url"]
            }
        ),
        Tool(
            name="generate_trd",
            description="生成 TRD 文档（SKILL: trd-generator）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "prd_path": {"type": "string", "description": "PRD 文档路径（可选，默认从工作区获取）"}
                },
                "required": ["workspace_id"]
            }
        ),
        Tool(
            name="decompose_tasks",
            description="分解任务（SKILL: task-decomposer）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "trd_path": {"type": "string", "description": "TRD 文档路径（可选，默认从工作区获取）"}
                },
                "required": ["workspace_id"]
            }
        ),
        Tool(
            name="generate_code",
            description="生成代码（SKILL: code-generator）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "task_id": {"type": "string", "description": "任务ID"}
                },
                "required": ["workspace_id", "task_id"]
            }
        ),
        Tool(
            name="review_code",
            description="审查代码（SKILL: code-reviewer）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "task_id": {"type": "string", "description": "任务ID"}
                },
                "required": ["workspace_id", "task_id"]
            }
        ),
        Tool(
            name="generate_tests",
            description="生成测试（SKILL: test-generator）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "test_output_dir": {"type": "string", "description": "测试输出目录（可选）"}
                },
                "required": ["workspace_id"]
            }
        ),
        Tool(
            name="review_tests",
            description="审查测试（SKILL: test-reviewer）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "test_files": {"type": "array", "items": {"type": "string"}, "description": "测试文件路径列表"}
                },
                "required": ["workspace_id", "test_files"]
            }
        ),
        Tool(
            name="analyze_coverage",
            description="分析覆盖率（SKILL: coverage-analyzer）",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {"type": "string", "description": "工作区ID"},
                    "project_path": {"type": "string", "description": "项目路径（可选，默认从工作区获取）"}
                },
                "required": ["workspace_id"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """调用工具。
    
    Args:
        name: 工具名称
        arguments: 工具参数
    
    Returns:
        工具执行结果
    """
    if arguments is None:
        arguments = {}
    
    try:
        # 基础设施工具
        if name == "create_workspace":
            workspace_id = workspace_manager.create_workspace(
                project_path=arguments["project_path"],
                requirement_name=arguments["requirement_name"],
                requirement_url=arguments["requirement_url"]
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "workspace_id": workspace_id
                    }, ensure_ascii=False)
                )
            ]
        
        elif name == "get_workspace":
            workspace = workspace_manager.get_workspace(arguments["workspace_id"])
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "workspace": workspace
                    }, ensure_ascii=False)
                )
            ]
        
        elif name == "update_workspace_status":
            workspace_manager.update_workspace_status(
                arguments["workspace_id"],
                arguments["status_updates"]
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True
                    }, ensure_ascii=False)
                )
            ]
        
        elif name == "get_tasks":
            tasks = task_manager.get_tasks(arguments["workspace_id"])
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "tasks": tasks
                    }, ensure_ascii=False)
                )
            ]
        
        elif name == "update_task_status":
            task_manager.update_task_status(
                arguments["workspace_id"],
                arguments["task_id"],
                arguments["status"],
                **arguments.get("updates", {})
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True
                    }, ensure_ascii=False)
                )
            ]
        
        # 8 个 SKILL 工具
        elif name == "generate_prd":
            result = generate_prd(
                workspace_id=arguments["workspace_id"],
                requirement_url=arguments["requirement_url"]
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "generate_trd":
            # 如果没有提供 prd_path，从工作区获取
            prd_path = arguments.get("prd_path")
            if not prd_path:
                workspace = workspace_manager.get_workspace(arguments["workspace_id"])
                prd_path = workspace.get("files", {}).get("prd_path")
                if not prd_path:
                    raise ValidationError("工作区中没有 PRD 文档，请先生成 PRD")
            
            result = generate_trd(
                workspace_id=arguments["workspace_id"],
                prd_path=prd_path
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "decompose_tasks":
            # 如果没有提供 trd_path，从工作区获取
            trd_path = arguments.get("trd_path")
            if not trd_path:
                workspace = workspace_manager.get_workspace(arguments["workspace_id"])
                trd_path = workspace.get("files", {}).get("trd_path")
                if not trd_path:
                    raise ValidationError("工作区中没有 TRD 文档，请先生成 TRD")
            
            result = decompose_tasks(
                workspace_id=arguments["workspace_id"],
                trd_path=trd_path
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "generate_code":
            result = generate_code(
                workspace_id=arguments["workspace_id"],
                task_id=arguments["task_id"]
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "review_code":
            result = review_code(
                workspace_id=arguments["workspace_id"],
                task_id=arguments["task_id"]
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "generate_tests":
            test_output_dir = arguments.get("test_output_dir", "")
            result = generate_tests(
                workspace_id=arguments["workspace_id"],
                test_output_dir=test_output_dir
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "review_tests":
            result = review_tests(
                workspace_id=arguments["workspace_id"],
                test_files=arguments["test_files"]
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        elif name == "analyze_coverage":
            # 如果没有提供 project_path，从工作区获取
            project_path = arguments.get("project_path")
            if not project_path:
                workspace = workspace_manager.get_workspace(arguments["workspace_id"])
                project_path = workspace.get("project_path")
                if not project_path:
                    raise ValidationError("工作区中没有项目路径")
            
            result = analyze_coverage(
                workspace_id=arguments["workspace_id"],
                project_path=project_path
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False)
                )
            ]
        
        else:
            raise ValueError(f"未知工具: {name}")
    
    except (ValidationError, WorkspaceNotFoundError, TaskNotFoundError, AgentOrchestratorError) as e:
        return _handle_error(e)
    except Exception as e:
        logger.error(f"工具执行异常: {e}", exc_info=True)
        return _handle_error(e)


async def run_server():
    """运行 MCP Server。"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
