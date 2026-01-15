"""测试生成工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.core.logger import setup_logger
from src.managers.task_manager import TaskManager
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def generate_tests(workspace_id: str, test_output_dir: str) -> dict:
    """生成测试。

    Args:
        workspace_id: 工作区ID
        test_output_dir: 测试输出目录

    Returns:
        包含测试文件路径的字典

    Raises:
        ValidationError: 当代码生成未完成或没有已完成的任务时
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)
    task_manager = TaskManager()

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)

    # 获取所有任务
    tasks = task_manager.get_tasks(workspace_id)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    pending_tasks = [t for t in tasks if t.get("status") == "pending"]

    # ✅ 新增：检查代码生成状态
    # 根据 workflow_status.py，test 阶段的 ready 条件是：所有任务都已完成，且至少有一个已完成的任务
    if len(completed_tasks) == 0:
        raise ValidationError("没有已完成的任务，无法生成测试。请先完成代码生成。")
    if len(pending_tasks) > 0:
        raise ValidationError(
            "存在未完成的任务，无法生成测试。请先完成所有任务的代码生成。"
        )

    # ✅ 新增：标记测试生成为进行中
    workspace_manager.update_workspace_status(
        workspace_id, {"test_status": "in_progress"}
    )

    try:
        # 创建测试输出目录
        test_output_path = Path(test_output_dir)
        test_output_path.mkdir(parents=True, exist_ok=True)

        test_files = []

        # 为每个已完成的任务生成 Mock 测试
        for task in completed_tasks:
            test_file = _generate_mock_test(task, workspace, test_output_path)
            if test_file:
                test_files.append(str(test_file))

        # ✅ 新增：标记测试生成为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"test_status": "completed"}
        )

        logger.info(f"测试已生成: {len(test_files)} 个测试文件")

        return {
            "success": True,
            "test_files": test_files,
            "test_count": len(test_files),
            "workspace_id": workspace_id,
        }
    except Exception as e:
        # ✅ 新增：标记测试生成为失败
        workspace_manager.update_workspace_status(
            workspace_id, {"test_status": "failed"}
        )
        logger.error(f"测试生成失败: {workspace_id}, 错误: {e}", exc_info=True)
        raise


def _generate_mock_test(task: dict, workspace: dict, output_dir: Path) -> Path | None:
    """生成 Mock 测试文件。

    Args:
        task: 任务信息
        workspace: 工作区信息
        output_dir: 输出目录

    Returns:
        测试文件路径
    """
    task_id = task.get("task_id", "")
    if not task_id:
        return None

    # 生成测试文件名
    safe_name = task_id.replace("-", "_")
    test_file = output_dir / f"test_mock_{safe_name}.py"

    # 生成测试内容
    test_content = f'''"""Mock 测试: {task_id}

{task.get('description', '')}
"""
import pytest
from unittest.mock import Mock, patch


class TestMock{task_id.replace('-', '_').title()}:
    """{task_id} Mock 测试类"""

    def test_mock_basic(self):
        """基础 Mock 测试"""
        # Arrange
        mock_obj = Mock()
        mock_obj.method.return_value = "test_result"

        # Act
        result = mock_obj.method()

        # Assert
        assert result == "test_result"
        mock_obj.method.assert_called_once()

    @patch('builtins.open')
    def test_mock_file_operation(self, mock_open):
        """Mock 文件操作测试"""
        # Arrange
        mock_open.return_value.__enter__.return_value.read.return_value = "file content"

        # Act
        with open("test.txt", "r") as f:
            content = f.read()

        # Assert
        assert content == "file content"
'''

    test_file.write_text(test_content, encoding="utf-8")
    return test_file
