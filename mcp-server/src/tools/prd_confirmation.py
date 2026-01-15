"""PRD 确认工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现 PRD 确认和修改功能：
1. 检查 PRD 文件是否存在并返回确认请求
2. 确认 PRD（更新状态为 completed）
3. 标记需要修改 PRD（更新状态为 needs_regeneration）
"""

from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def check_prd_confirmation(workspace_id: str) -> dict:
    """检查 PRD 文件是否存在并返回确认请求。

    Args:
        workspace_id: 工作区ID

    Returns:
        包含交互请求的字典，格式：
        {
            "success": True,
            "interaction_required": True,
            "interaction_type": "prd_confirmation",
            "prd_path": "/path/to/PRD.md",
            "prd_preview": "PRD 内容预览（前500字符）"
        }
        或错误响应：
        {
            "success": False,
            "error": "错误信息"
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
    """
    logger.info(f"检查 PRD 确认请求: {workspace_id}")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    workspace_dir = config.get_workspace_path(workspace_id)

    # 检查 PRD 文件路径
    prd_path = workspace.get("files", {}).get("prd_path")
    prd_path = workspace_dir / "PRD.md" if not prd_path else Path(prd_path)

    # 检查文件是否存在
    if not prd_path.exists():
        logger.warning(f"PRD 文件不存在: {prd_path}")
        return {"success": False, "error": f"PRD 文件不存在: {prd_path}"}

    # 读取 PRD 内容预览（前500字符）
    try:
        prd_content = prd_path.read_text(encoding="utf-8")
        prd_preview = prd_content[:500] + ("..." if len(prd_content) > 500 else "")
    except Exception as e:
        logger.error(f"读取 PRD 文件失败: {e}", exc_info=True)
        prd_preview = "无法读取 PRD 内容"

    return {
        "success": True,
        "interaction_required": True,
        "interaction_type": "prd_confirmation",
        "prd_path": str(prd_path),
        "prd_preview": prd_preview,
    }


def confirm_prd(workspace_id: str) -> dict:
    """确认 PRD。

    更新工作区状态：`prd_status = "completed"`

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
    logger.info(f"确认 PRD: {workspace_id}")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息（验证工作区存在）
    workspace_manager.get_workspace(workspace_id)

    # 更新工作区状态
    workspace_manager.update_workspace_status(workspace_id, {"prd_status": "completed"})

    logger.info(f"PRD 已确认: {workspace_id}")

    return {"success": True, "workspace_id": workspace_id}


def modify_prd(workspace_id: str) -> dict:
    """标记需要修改 PRD。

    更新工作区状态：`prd_status = "needs_regeneration"`

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
    logger.info(f"标记需要修改 PRD: {workspace_id}")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息（验证工作区存在）
    workspace_manager.get_workspace(workspace_id)

    # 更新工作区状态
    workspace_manager.update_workspace_status(
        workspace_id, {"prd_status": "needs_regeneration"}
    )

    logger.info(f"PRD 已标记为需要修改: {workspace_id}")

    return {"success": True, "workspace_id": workspace_id}
