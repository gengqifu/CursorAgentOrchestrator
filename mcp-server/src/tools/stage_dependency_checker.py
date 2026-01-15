"""阶段依赖检查工具 - TDD 第二步：实现 check_stage_ready 函数。

Python 3.9+ 兼容：使用内置类型 dict, list 而非 typing.Dict, typing.List

本模块实现阶段依赖检查功能：
1. 检查阶段是否可以开始
2. 验证前置阶段依赖
3. 返回详细的依赖信息
"""

from pathlib import Path

from src.core.exceptions import ValidationError, WorkspaceNotFoundError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)

# 阶段依赖定义
STAGE_DEPENDENCIES = {
    "prd": [],  # PRD没有前置依赖
    "trd": ["prd"],
    "tasks": ["trd"],
    "code": ["tasks"],
    "test": ["code"],
    "coverage": ["test"],
}


def check_stage_ready(workspace_id: str, stage: str) -> dict:
    """检查阶段是否可以开始。

    检查指定阶段是否可以开始，验证前置阶段依赖和文件依赖。

    Args:
        workspace_id: 工作区ID
        stage: 阶段名称（"prd", "trd", "tasks", "code", "test", "coverage"）

    Returns:
        包含检查结果的字典，格式：
        {
            "success": True,
            "stage": "trd",
            "ready": True/False,
            "reason": "前置阶段已完成，可以开始" | "前置阶段未完成: prd" | "依赖文件不存在",
            "required_stages": ["prd"],
            "completed_stages": ["prd"],
            "pending_stages": [],
            "in_progress_stages": [],
            "file_ready": True/False
        }

    Raises:
        ValidationError: 当阶段名称无效时
        WorkspaceNotFoundError: 当工作区不存在时
    """
    logger.info(f"检查阶段是否可以开始: {workspace_id}/{stage}")

    # 验证阶段名称
    if stage not in STAGE_DEPENDENCIES:
        error_msg = f"未知阶段: {stage}"
        logger.error(error_msg)
        raise ValidationError(error_msg)

    workspace_manager = WorkspaceManager()

    try:
        # 获取工作区信息
        workspace = workspace_manager.get_workspace(workspace_id)
        status = workspace.get("status", {})
        files = workspace.get("files", {})

        # 获取前置阶段
        required_stages = STAGE_DEPENDENCIES[stage]

        # 检查前置阶段状态
        completed_stages = []
        pending_stages = []
        in_progress_stages = []

        for req_stage in required_stages:
            req_status = status.get(f"{req_stage}_status", "pending")
            if req_status == "completed":
                completed_stages.append(req_stage)
            elif req_status == "in_progress":
                in_progress_stages.append(req_stage)
            else:
                pending_stages.append(req_stage)

        # 判断是否可以开始（所有前置阶段必须 completed，且没有 in_progress）
        ready = (
            len(pending_stages) == 0
            and len(in_progress_stages) == 0
            and len(completed_stages) == len(required_stages)
        )

        # 检查文件是否存在（对于有文件依赖的阶段）
        file_ready = True
        if stage == "trd":
            prd_path = files.get("prd_path")
            file_ready = prd_path is not None and Path(prd_path).exists()
        elif stage == "tasks":
            trd_path = files.get("trd_path")
            file_ready = trd_path is not None and Path(trd_path).exists()
        elif stage == "code":
            tasks_json_path = files.get("tasks_json_path")
            file_ready = tasks_json_path is not None and Path(tasks_json_path).exists()

        # 生成原因说明
        if ready and file_ready:
            reason = "前置阶段已完成，可以开始"
        elif not ready:
            blocking_stages = pending_stages + in_progress_stages
            reason = f"前置阶段未完成: {', '.join(blocking_stages)}"
        else:
            reason = "依赖文件不存在"

        result = {
            "success": True,
            "stage": stage,
            "ready": ready and file_ready,
            "reason": reason,
            "required_stages": required_stages,
            "completed_stages": completed_stages,
            "pending_stages": pending_stages,
            "in_progress_stages": in_progress_stages,
            "file_ready": file_ready,
        }

        logger.info(
            f"阶段检查完成: {workspace_id}/{stage}, "
            f"ready={ready and file_ready}, reason={reason}"
        )

        return result

    except WorkspaceNotFoundError:
        logger.error(f"工作区不存在: {workspace_id}")
        raise
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            f"检查阶段依赖失败: {workspace_id}/{stage}, 错误: {e}", exc_info=True
        )
        raise
