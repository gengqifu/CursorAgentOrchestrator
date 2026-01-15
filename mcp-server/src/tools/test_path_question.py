"""测试路径询问工具 - TDD 第三步：实现 submit_test_path 函数。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现测试路径询问功能：
1. 询问测试路径（生成默认路径建议）
2. 提交测试路径并保存到工作区元数据
"""
import json
import os
from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError, WorkspaceNotFoundError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager
from src.utils.file_lock import file_lock

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


def submit_test_path(workspace_id: str, test_path: str) -> dict:
    """提交测试路径并保存到工作区元数据。

    验证路径有效性，并将测试路径保存到工作区元数据的 `files.test_path` 字段。

    Args:
        workspace_id: 工作区ID
        test_path: 测试输出目录路径

    Returns:
        包含提交结果的字典，格式：
        {
            "success": True,
            "workspace_id": "req-20240115-123456-用户认证功能",
            "test_path": "/path/to/project/tests/mock"
        }

    Raises:
        WorkspaceNotFoundError: 当工作区不存在时
        ValidationError: 当路径无效时
    """
    logger.info(f"提交测试路径: workspace_id={workspace_id}, test_path={test_path}")

    try:
        # 获取工作区信息
        config = Config()
        workspace_manager = WorkspaceManager(config=config)
        workspace = workspace_manager.get_workspace(workspace_id)

        # 验证路径有效性
        if not test_path or not str(test_path).strip():
            raise ValidationError("测试路径不能为空")

        test_path_str = str(test_path).strip()
        test_path_obj = Path(test_path_str)

        # 验证路径格式（必须是绝对路径或相对路径）
        # 如果是相对路径，转换为相对于项目路径的绝对路径
        if not test_path_obj.is_absolute():
            project_path = workspace.get("project_path")
            if not project_path:
                raise ValidationError(f"工作区 {workspace_id} 缺少 project_path 字段")
            test_path_obj = Path(project_path) / test_path_obj
            test_path_str = str(test_path_obj)

        # 验证父目录是否存在（如果不存在，尝试创建）
        parent_dir = test_path_obj.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建父目录: {parent_dir}")
            except Exception as e:
                raise ValidationError(f"无法创建父目录 {parent_dir}: {e}") from e

        # 验证父目录是否可写
        if not os.access(parent_dir, os.W_OK):
            raise ValidationError(f"父目录不可写: {parent_dir}")

        # 如果测试路径已存在，验证是否为目录或可创建目录
        if test_path_obj.exists():
            if not test_path_obj.is_dir():
                raise ValidationError(f"测试路径已存在但不是目录: {test_path_str}")
        else:
            # 尝试创建目录以验证权限
            try:
                test_path_obj.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建测试目录: {test_path_obj}")
            except Exception as e:
                raise ValidationError(f"无法创建测试目录 {test_path_str}: {e}") from e

        # 保存到工作区元数据（使用文件锁）
        workspace_dir = config.get_workspace_path(workspace_id)
        meta_file = workspace_dir / "workspace.json"

        with file_lock(meta_file):
            # 重新读取最新数据（避免使用过期的缓存）
            if not meta_file.exists():
                raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")

            with open(meta_file, 'r', encoding='utf-8') as f:
                workspace_data = json.load(f)

            # 确保 files 字段存在
            if "files" not in workspace_data:
                workspace_data["files"] = {}

            # 更新 test_path
            workspace_data["files"]["test_path"] = test_path_str

            # 保存
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_data, f, ensure_ascii=False, indent=2)

        logger.info(f"成功保存测试路径: {workspace_id}, {test_path_str}")

        return {
            "success": True,
            "workspace_id": workspace_id,
            "test_path": test_path_str,
        }

    except WorkspaceNotFoundError as e:
        logger.error(f"工作区不存在: {workspace_id}")
        raise
    except ValidationError as e:
        logger.error(f"测试路径无效: {workspace_id}, {test_path}, {e}")
        raise
    except Exception as e:
        logger.error(f"提交测试路径时发生错误: {workspace_id}, {test_path}, {e}")
        raise ValidationError(f"提交测试路径失败: {e}") from e
