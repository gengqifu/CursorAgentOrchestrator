"""工作流状态查询工具 - TDD 第二步：实现 get_workflow_status 函数。

Python 3.9+ 兼容：使用内置类型 dict, list 而非 typing.Dict, typing.List

本模块实现工作流状态查询功能：
1. 获取工作流状态（各阶段状态、进度、可开始的阶段、被阻塞的阶段）
"""

from src.core.exceptions import WorkspaceNotFoundError
from src.core.logger import setup_logger
from src.managers.task_manager import TaskManager
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def get_workflow_status(workspace_id: str) -> dict:
    """获取工作流状态。

    获取工作区的工作流状态，包括各阶段的状态、进度、可开始的阶段和被阻塞的阶段。

    Args:
        workspace_id: 工作区ID

    Returns:
        包含工作流状态的字典，格式：
        {
            "success": True,
            "workspace_id": "req-xxx",
            "stages": {
                "prd": {
                    "status": "pending" | "in_progress" | "completed" | "failed" | "needs_regeneration",
                    "file": "/path/to/PRD.md",
                    "ready": True/False
                },
                "trd": {...},
                "tasks": {...},
                "code": {...},
                "test": {...},
                "coverage": {...}
            },
            "next_available_stages": ["prd", "trd", ...],
            "blocked_stages": ["tasks", "code", ...],
            "workflow_progress": {
                "completed_stages": 2,
                "total_stages": 6,
                "progress_percentage": 33.33
            }
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
    """
    logger.info(f"获取工作流状态: {workspace_id}")

    workspace_manager = WorkspaceManager()
    task_manager = TaskManager()

    try:
        # 获取工作区信息
        workspace = workspace_manager.get_workspace(workspace_id)
        status = workspace.get("status", {})
        files = workspace.get("files", {})

        # 获取任务信息
        tasks = task_manager.get_tasks(workspace_id)
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        pending_tasks = [t for t in tasks if t.get("status") == "pending"]

        # 构建阶段状态字典
        stages = {
            "prd": {
                "status": status.get("prd_status", "pending"),
                "file": files.get("prd_path"),
                "ready": True,  # PRD没有前置依赖
            },
            "trd": {
                "status": status.get("trd_status", "pending"),
                "file": files.get("trd_path"),
                "ready": status.get("prd_status") == "completed",
            },
            "tasks": {
                "status": status.get("tasks_status", "pending"),
                "file": files.get("tasks_json_path"),
                "task_count": len(tasks),
                "ready": status.get("trd_status") == "completed",
            },
            "code": {
                "status": status.get("code_status", "pending"),
                "completed_tasks": len(completed_tasks),
                "pending_tasks": len(pending_tasks),
                "total_tasks": len(tasks),
                "ready": status.get("tasks_status") == "completed",
            },
            "test": {
                "status": status.get("test_status", "pending"),
                "ready": len(pending_tasks) == 0 and len(completed_tasks) > 0,
            },
            "coverage": {
                "status": status.get("coverage_status", "pending"),
                "ready": status.get("test_status") == "completed",
            },
        }

        # 计算可以开始的阶段（ready=True 且状态为 pending 或 needs_regeneration）
        next_available_stages = [
            stage_name
            for stage_name, stage_info in stages.items()
            if stage_info["ready"]
            and stage_info["status"] in ["pending", "needs_regeneration"]
        ]

        # 计算被阻塞的阶段（ready=False 且状态为 pending）
        blocked_stages = [
            stage_name
            for stage_name, stage_info in stages.items()
            if not stage_info["ready"] and stage_info["status"] == "pending"
        ]

        # 计算工作流进度百分比
        completed_stages_count = len(
            [s for s in stages.values() if s["status"] == "completed"]
        )
        total_stages = len(stages)
        progress_percentage = (
            round(completed_stages_count / total_stages * 100, 2)
            if total_stages > 0
            else 0.0
        )

        result = {
            "success": True,
            "workspace_id": workspace_id,
            "stages": stages,
            "next_available_stages": next_available_stages,
            "blocked_stages": blocked_stages,
            "workflow_progress": {
                "completed_stages": completed_stages_count,
                "total_stages": total_stages,
                "progress_percentage": progress_percentage,
            },
        }

        logger.info(
            f"工作流状态查询成功: {workspace_id}, "
            f"进度: {progress_percentage}%, "
            f"可开始阶段: {next_available_stages}, "
            f"被阻塞阶段: {blocked_stages}"
        )

        return result

    except WorkspaceNotFoundError:
        logger.error(f"工作区不存在: {workspace_id}")
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {workspace_id}, 错误: {e}")
        raise
