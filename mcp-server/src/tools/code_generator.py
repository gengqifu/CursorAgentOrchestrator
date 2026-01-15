"""代码生成工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.core.logger import setup_logger
from src.managers.task_manager import TaskManager
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def generate_code(workspace_id: str, task_id: str) -> dict:
    """生成代码。

    Args:
        workspace_id: 工作区ID
        task_id: 任务ID

    Returns:
        包含生成的文件路径的字典

    Raises:
        ValidationError: 当任务分解未完成或任务状态不是pending时
        TaskNotFoundError: 当任务不存在时
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)
    task_manager = TaskManager()

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    status = workspace.get("status", {})

    # ✅ 新增：检查任务分解状态
    if status.get("tasks_status") != "completed":
        raise ValidationError("任务分解尚未完成，无法生成代码。请先完成任务分解。")

    # 获取任务信息
    task = task_manager.get_task(workspace_id, task_id)

    # ✅ 新增：检查任务状态
    task_status = task.get("status", "pending")
    if task_status != "pending":
        raise ValidationError(
            f"任务状态为 {task_status}，无法生成代码。只能为 pending 状态的任务生成代码。"
        )

    # ✅ 新增：标记代码生成为进行中
    workspace_manager.update_workspace_status(
        workspace_id, {"code_status": "in_progress"}
    )

    project_path = Path(workspace["project_path"])

    try:
        # TODO: 调用 Cursor AI 生成代码
        # 目前先创建占位文件

        # 生成代码文件路径
        code_files = []

        # 根据任务描述生成文件名
        safe_name = task_id.replace("-", "_")
        code_file = project_path / f"{safe_name}.py"

        # 生成代码内容
        code_content = _generate_code_content(task, workspace)
        code_file.write_text(code_content, encoding="utf-8")
        code_files.append(str(code_file))

        # 生成测试文件
        test_file = project_path / "tests" / f"test_{safe_name}.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_content = _generate_test_content(task, workspace)
        test_file.write_text(test_content, encoding="utf-8")
        code_files.append(str(test_file))

        # 更新任务状态
        task_manager.update_task_status(
            workspace_id, task_id, "completed", code_files=code_files
        )

        # ✅ 新增：标记代码生成为已完成（当所有任务完成时）
        # 检查是否所有任务都已完成
        all_tasks = task_manager.get_tasks(workspace_id)
        all_completed = all(task.get("status") == "completed" for task in all_tasks)
        if all_completed:
            workspace_manager.update_workspace_status(
                workspace_id, {"code_status": "completed"}
            )

        logger.info(f"代码已生成: {task_id}, 文件数: {len(code_files)}")

        return {
            "success": True,
            "task_id": task_id,
            "code_files": code_files,
            "workspace_id": workspace_id,
        }
    except Exception as e:
        # ✅ 新增：标记代码生成为失败
        workspace_manager.update_workspace_status(
            workspace_id, {"code_status": "failed"}
        )
        logger.error(
            f"代码生成失败: {workspace_id}/{task_id}, 错误: {e}", exc_info=True
        )
        raise


def _generate_code_content(task: dict, workspace: dict) -> str:
    """生成代码内容。

    Args:
        task: 任务信息
        workspace: 工作区信息

    Returns:
        代码内容
    """
    task_description = task.get("description", "")
    task_id = task.get("task_id", "")

    code_template = f'''"""实现任务: {task_id}

{task_description}
"""
from typing import Optional


def {task_id.replace('-', '_')}() -> Optional[dict]:
    """实现 {task_description}

    Returns:
        执行结果字典
    """
    # TODO: 实现具体功能
    return {{"status": "success", "task_id": "{task_id}"}}


if __name__ == "__main__":
    result = {task_id.replace('-', '_')}()
    print(result)
'''
    return code_template


def _generate_test_content(task: dict, workspace: dict) -> str:
    """生成测试代码内容。

    Args:
        task: 任务信息
        workspace: 工作区信息

    Returns:
        测试代码内容
    """
    task_id = task.get("task_id", "")
    function_name = task_id.replace("-", "_")

    test_template = f'''"""测试任务: {task_id}"""
import pytest
from {task_id.replace('-', '_')} import {function_name}


class Test{task_id.replace('-', '_').title()}:
    """{task_id} 测试类"""

    def test_{function_name}_success(self):
        """测试 {function_name} 成功执行"""
        # Arrange & Act
        result = {function_name}()

        # Assert
        assert result is not None
        assert result["status"] == "success"
        assert result["task_id"] == "{task_id}"
'''
    return test_template
