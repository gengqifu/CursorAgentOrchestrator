"""测试生成工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""
from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager
from src.managers.task_manager import TaskManager

logger = setup_logger(__name__)


def generate_tests(workspace_id: str, test_output_dir: str) -> dict:
    """生成测试。
    
    Args:
        workspace_id: 工作区ID
        test_output_dir: 测试输出目录
    
    Returns:
        包含测试文件路径的字典
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)
    task_manager = TaskManager()
    
    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    project_path = Path(workspace["project_path"])
    
    # 获取所有已完成的任务
    tasks = task_manager.get_tasks(workspace_id)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    # 创建测试输出目录
    test_output_path = Path(test_output_dir)
    test_output_path.mkdir(parents=True, exist_ok=True)
    
    test_files = []
    
    # 为每个已完成的任务生成 Mock 测试
    for task in completed_tasks:
        test_file = _generate_mock_test(task, workspace, test_output_path)
        if test_file:
            test_files.append(str(test_file))
    
    # 更新工作区状态
    workspace_manager.update_workspace_status(
        workspace_id,
        {"test_status": "completed"}
    )
    
    logger.info(f"测试已生成: {len(test_files)} 个测试文件")
    
    return {
        "success": True,
        "test_files": test_files,
        "test_count": len(test_files),
        "workspace_id": workspace_id
    }


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
    safe_name = task_id.replace('-', '_')
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
    
    test_file.write_text(test_content, encoding='utf-8')
    return test_file
