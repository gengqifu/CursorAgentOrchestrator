"""任务分解工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""
import json
from pathlib import Path
from datetime import datetime

from src.core.config import Config
from src.core.logger import setup_logger
from src.core.exceptions import ValidationError
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def decompose_tasks(workspace_id: str, trd_path: str) -> dict:
    """分解任务。
    
    Args:
        workspace_id: 工作区ID
        trd_path: TRD 文档路径
    
    Returns:
        包含 tasks.json 路径的字典
    
    Raises:
        ValidationError: 当 TRD 路径无效时
    """
    # 验证 TRD 文件存在
    trd_file = Path(trd_path)
    if not trd_file.exists():
        raise ValidationError(f"TRD 文件不存在: {trd_path}")
    
    config = Config()
    workspace_manager = WorkspaceManager(config=config)
    
    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    workspace_dir = config.get_workspace_path(workspace_id)
    
    # 读取 TRD 内容
    trd_content = trd_file.read_text(encoding='utf-8')
    
    # 分解任务
    tasks = _decompose_tasks_from_trd(trd_content, workspace)
    
    # 保存 tasks.json
    tasks_file = workspace_dir / "tasks.json"
    tasks_data = {
        "workspace_id": workspace_id,
        "created_at": datetime.now().isoformat(),
        "tasks": tasks
    }
    with open(tasks_file, 'w', encoding='utf-8') as f:
        json.dump(tasks_data, f, ensure_ascii=False, indent=2)
    
    # 更新工作区状态
    workspace_manager.update_workspace_status(
        workspace_id,
        {"tasks_status": "completed"}
    )
    
    # 更新工作区文件路径
    workspace["files"]["tasks_json_path"] = str(tasks_file)
    meta_file = workspace_dir / "workspace.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(workspace, f, ensure_ascii=False, indent=2)
    
    logger.info(f"任务已分解: {len(tasks)} 个任务")
    
    return {
        "success": True,
        "tasks_json_path": str(tasks_file),
        "task_count": len(tasks),
        "workspace_id": workspace_id
    }


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
    lines = trd_content.split('\n')
    task_index = 1
    
    for i, line in enumerate(lines):
        # 检测功能点（以 ## 或 ### 开头）
        if line.strip().startswith('##') and '功能' in line or '实现' in line:
            # 提取后续内容作为任务描述
            description_lines = []
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip().startswith('##'):
                    break
                if lines[j].strip():
                    description_lines.append(lines[j].strip())
            
            if description_lines:
                task_description = ' '.join(description_lines[:3])  # 取前3行
                if len(task_description) > 10:  # 确保描述有意义
                    task = {
                        "task_id": f"task-{task_index:03d}",
                        "description": task_description,
                        "status": "pending",
                        "created_at": datetime.now().isoformat()
                    }
                    tasks.append(task)
                    task_index += 1
    
    # 如果没有提取到任务，创建默认任务
    if not tasks:
        requirement_name = workspace.get("requirement_name", "未知需求")
        tasks.append({
            "task_id": "task-001",
            "description": f"实现 {requirement_name} 的核心功能",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        })
    
    return tasks
