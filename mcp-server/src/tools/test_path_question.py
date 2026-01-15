"""测试路径询问工具 - TDD 第二步：实现 ask_test_path 函数。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现测试路径询问功能：
1. 询问测试路径（生成默认路径建议）
2. 提交测试路径并保存到工作区元数据
"""
from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError, WorkspaceNotFoundError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def ask_test_path(workspace_id: str) -> dict:
    """询问测试路径。

    获取工作区信息，生成默认路径建议（`{project_path}/tests/mock`），
    并返回交互请求。

    Args:
        workspace_id: 工作区ID

    Returns:
        包含交互请求的字典，格式：
        {
            "success": True,
            "interaction_required": True,
            "interaction_type": "question",
            "question": {
                "id": "test_path",
                "question": "请输入测试输出目录路径",
                "type": "text",
                "required": True,
                "default": "{project_path}/tests/mock",
                "placeholder": "/path/to/project/tests/mock"
            }
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
        ValidationError: 当工作区信息无效时
    """
    logger.info(f"询问测试路径: workspace_id={workspace_id}")

    try:
        # 获取工作区信息
        config = Config()
        workspace_manager = WorkspaceManager(config=config)
        workspace = workspace_manager.get_workspace(workspace_id)

        # 获取项目路径
        project_path = workspace.get("project_path")
        if not project_path:
            raise ValidationError(f"工作区 {workspace_id} 缺少 project_path 字段")

        # 生成默认路径建议：{project_path}/tests/mock
        default_path = str(Path(project_path) / "tests" / "mock")

        # 构建问题
        question = {
            "id": "test_path",
            "question": "请输入测试输出目录路径",
            "type": "text",
            "required": True,
            "default": default_path,
            "placeholder": default_path,
        }

        result = {
            "success": True,
            "interaction_required": True,
            "interaction_type": "question",
            "question": question,
        }

        logger.info(f"返回测试路径问题，默认路径: {default_path}")
        return result

    except WorkspaceNotFoundError as e:
        logger.error(f"工作区不存在: {workspace_id}")
        raise
    except ValidationError as e:
        logger.error(f"工作区信息无效: {workspace_id}, {e}")
        raise
    except Exception as e:
        logger.error(f"询问测试路径时发生错误: {workspace_id}, {e}")
        raise ValidationError(f"询问测试路径失败: {e}") from e
