"""任务管理器 - TDD 第二步：最小实现。

Python 3.9+ 兼容：使用内置类型 dict, list 而非 typing.Dict, typing.List
"""

import json
from pathlib import Path
from typing import Optional

from src.core.config import Config
from src.core.exceptions import TaskNotFoundError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager
from src.utils.file_lock import file_lock, read_lock

logger = setup_logger(__name__)


class TaskManager:
    """任务管理器。"""

    def __init__(self, config: Optional[Config] = None) -> None:
        """初始化任务管理器。

        Args:
            config: 配置管理器，如果为 None 则创建默认配置
        """
        self.config = config or Config()
        self.workspace_manager = WorkspaceManager(config=self.config)

    def get_tasks_file(self, workspace_id: str) -> Path:
        """获取任务文件路径。

        Args:
            workspace_id: 工作区ID

        Returns:
            任务文件路径
        """
        workspace = self.workspace_manager.get_workspace(workspace_id)
        tasks_path = workspace.get("files", {}).get("tasks_json_path")

        if tasks_path:
            return Path(tasks_path)

        # 默认路径
        workspace_dir = self.config.get_workspace_path(workspace_id)
        return workspace_dir / "tasks.json"

    def get_tasks(self, workspace_id: str) -> list[dict]:
        """获取所有任务。

        使用读锁，允许多个进程同时读取任务列表。

        Args:
            workspace_id: 工作区ID

        Returns:
            任务列表
        """
        tasks_file = self.get_tasks_file(workspace_id)

        if not tasks_file.exists():
            return []

        # 使用读锁，允许多个进程同时读取
        with read_lock(tasks_file), open(tasks_file, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("tasks", [])

    def get_task(self, workspace_id: str, task_id: str) -> dict:
        """获取单个任务。

        Args:
            workspace_id: 工作区ID
            task_id: 任务ID

        Returns:
            任务信息字典

        Raises:
            TaskNotFoundError: 当任务不存在时
        """
        tasks = self.get_tasks(workspace_id)

        for task in tasks:
            if task.get("task_id") == task_id:
                return task

        raise TaskNotFoundError(f"任务不存在: {task_id}")

    def update_task_status(
        self, workspace_id: str, task_id: str, status: str, **updates
    ) -> None:
        """更新任务状态。

        使用文件锁确保并发安全。支持多个 Cursor 终端同时更新不同任务，
        但同一任务的并发更新会被序列化。

        Args:
            workspace_id: 工作区ID
            task_id: 任务ID
            status: 新状态
            **updates: 其他要更新的字段

        Raises:
            FileLockError: 当无法在超时时间内获取锁时（其他进程正在修改）
        """
        tasks_file = self.get_tasks_file(workspace_id)

        # 使用文件锁保护读取-修改-写入操作
        with file_lock(tasks_file):
            # 读取现有任务（重新读取最新数据）
            if tasks_file.exists():
                with open(tasks_file, encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"workspace_id": workspace_id, "tasks": []}

            # 更新任务
            task_found = False
            for task in data.get("tasks", []):
                if task.get("task_id") == task_id:
                    task["status"] = status
                    task.update(updates)
                    task_found = True
                    break

            if not task_found:
                # 如果任务不存在，创建新任务
                new_task = {"task_id": task_id, "status": status, **updates}
                data.setdefault("tasks", []).append(new_task)

            # 保存
            tasks_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"更新任务状态: {workspace_id}/{task_id} -> {status}")
