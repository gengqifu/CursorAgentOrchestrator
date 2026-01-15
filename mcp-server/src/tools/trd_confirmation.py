"""TRD 确认工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现 TRD 确认和修改功能：
1. 检查 TRD 文件是否存在并返回确认请求
2. 确认 TRD（更新状态为 completed）
3. 标记需要修改 TRD（更新状态为 needs_regeneration）
"""

from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def check_trd_confirmation(workspace_id: str) -> dict:
    """检查 TRD 文件是否存在并返回确认请求。

    Args:
        workspace_id: 工作区ID

    Returns:
        包含交互请求的字典，格式：
        {
            "success": True,
            "interaction_required": True,
            "interaction_type": "trd_confirmation",
            "trd_path": "/path/to/TRD.md",
            "trd_preview": "TRD 内容预览（前500字符）"
        }
        或错误响应：
        {
            "success": False,
            "error": "错误信息"
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
    """
    logger.info(f"检查 TRD 确认请求: {workspace_id}")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    workspace_dir = config.get_workspace_path(workspace_id)

    # 检查 TRD 文件路径
    trd_path = workspace.get("files", {}).get("trd_path")
    trd_path = workspace_dir / "TRD.md" if not trd_path else Path(trd_path)

    # 检查文件是否存在
    if not trd_path.exists():
        logger.warning(f"TRD 文件不存在: {trd_path}")
        return {"success": False, "error": f"TRD 文件不存在: {trd_path}"}

    # 读取 TRD 内容预览（前500字符）
    try:
        trd_content = trd_path.read_text(encoding="utf-8")
        trd_preview = trd_content[:500] + ("..." if len(trd_content) > 500 else "")
    except Exception as e:
        logger.error(f"读取 TRD 文件失败: {e}", exc_info=True)
        trd_preview = "无法读取 TRD 内容"

    return {
        "success": True,
        "interaction_required": True,
        "interaction_type": "trd_confirmation",
        "trd_path": str(trd_path),
        "trd_preview": trd_preview,
    }


def confirm_trd(workspace_id: str) -> dict:
    """确认 TRD。

    更新工作区状态：`trd_status = "completed"`

    Args:
        workspace_id: 工作区ID

    Returns:
        包含确认结果的字典，格式：
        {
            "success": True,
            "workspace_id": "req-xxx"
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
    """
    logger.info(f"确认 TRD: {workspace_id}")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息（验证工作区存在）
    workspace_manager.get_workspace(workspace_id)

    # 更新工作区状态
    workspace_manager.update_workspace_status(workspace_id, {"trd_status": "completed"})

    logger.info(f"TRD 已确认: {workspace_id}")

    return {"success": True, "workspace_id": workspace_id}


def modify_trd(workspace_id: str) -> dict:
    """标记需要修改 TRD。

    更新工作区状态：`trd_status = "needs_regeneration"`

    Args:
        workspace_id: 工作区ID

    Returns:
        包含修改标记结果的字典，格式：
        {
            "success": True,
            "workspace_id": "req-xxx"
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
    """
    logger.info(f"标记需要修改 TRD: {workspace_id}")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息（验证工作区存在）
    workspace_manager.get_workspace(workspace_id)

    # 更新工作区状态
    workspace_manager.update_workspace_status(
        workspace_id, {"trd_status": "needs_regeneration"}
    )

    logger.info(f"TRD 已标记为需要修改: {workspace_id}")

    return {"success": True, "workspace_id": workspace_id}
