"""测试路径询问工具 - TDD 第一步：创建文件结构。

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
