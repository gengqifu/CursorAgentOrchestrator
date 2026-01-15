"""任务分解工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

import json
from datetime import datetime
from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def decompose_tasks(workspace_id: str, trd_path: str | None = None) -> dict:
    """分解任务。

    Args:
        workspace_id: 工作区ID
        trd_path: TRD 文档路径（可选，默认从工作区获取）

    Returns:
        包含 tasks.json 路径的字典

    Raises:
        ValidationError: 当 TRD 状态未完成、TRD 路径无效或 TRD 文件不存在时
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    status = workspace.get("status", {})
    files = workspace.get("files", {})

    # ✅ 新增：检查TRD状态
    if status.get("trd_status") != "completed":
        raise ValidationError("TRD尚未完成，无法分解任务。请先完成TRD生成。")

    # 如果没有提供 trd_path，从工作区获取
    if not trd_path:
        trd_path = files.get("trd_path")
        if not trd_path:
            raise ValidationError("工作区中没有 TRD 文档，请先生成 TRD")

    # ✅ 新增：检查TRD文件存在
    trd_file = Path(trd_path)
    if not trd_file.exists():
        raise ValidationError(f"TRD 文件不存在: {trd_path}")

    # ✅ 新增：标记任务分解为进行中
    workspace_manager.update_workspace_status(
        workspace_id, {"tasks_status": "in_progress"}
    )

    workspace_dir = config.get_workspace_path(workspace_id)

    try:
        # 读取 TRD 内容
        trd_content = trd_file.read_text(encoding="utf-8")

        # 分解任务
        tasks = _decompose_tasks_from_trd(trd_content, workspace)

        # 保存 tasks.json
        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "created_at": datetime.now().isoformat(),
            "tasks": tasks,
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # ✅ 新增：标记任务分解为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "completed"}
        )

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["tasks_json_path"] = str(tasks_file)
        meta_file = workspace_dir / "workspace.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        logger.info(f"任务已分解: {len(tasks)} 个任务")

        return {
            "success": True,
            "tasks_json_path": str(tasks_file),
            "task_count": len(tasks),
            "workspace_id": workspace_id,
        }
    except Exception as e:
        # ✅ 新增：标记任务分解为失败
        workspace_manager.update_workspace_status(
            workspace_id, {"tasks_status": "failed"}
        )
        logger.error(f"任务分解失败: {workspace_id}, 错误: {e}", exc_info=True)
        raise


def _decompose_tasks_from_trd(trd_content: str, workspace: dict) -> list[dict]:
    """从 TRD 内容分解任务。

    Args:
        trd_content: TRD 文档内容
        workspace: 工作区信息

    Returns:
        任务列表
    """
    tasks = []

    # 简化的任务分解逻辑
    # TODO: 使用 AI 进行智能任务分解

    # 根据 TRD 内容提取关键功能点
    lines = trd_content.split("\n")
    task_index = 1

    for i, line in enumerate(lines):
        # 检测功能点（以 ## 或 ### 开头）
        if line.strip().startswith("##") and "功能" in line or "实现" in line:
            # 提取后续内容作为任务描述
            description_lines = []
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip().startswith("##"):
                    break
                if lines[j].strip():
                    description_lines.append(lines[j].strip())

            if description_lines:
                task_description = " ".join(description_lines[:3])  # 取前3行
                if len(task_description) > 10:  # 确保描述有意义
                    task = {
                        "task_id": f"task-{task_index:03d}",
                        "description": task_description,
                        "status": "pending",
                        "created_at": datetime.now().isoformat(),
                    }
                    tasks.append(task)
                    task_index += 1

    # 如果没有提取到任务，创建默认任务
    if not tasks:
        requirement_name = workspace.get("requirement_name", "未知需求")
        tasks.append(
            {
                "task_id": "task-001",
                "description": f"实现 {requirement_name} 的核心功能",
                "status": "pending",
                "created_at": datetime.now().isoformat(),
            }
        )

    return tasks
