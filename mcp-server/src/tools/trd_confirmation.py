"""TRD 确认工具 - TDD 第一步：创建文件结构。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现 TRD 确认和修改功能：
1. 检查 TRD 文件是否存在并返回确认请求
2. 确认 TRD（更新状态为 completed）
3. 标记需要修改 TRD（更新状态为 needs_regeneration）
"""

from pathlib import Path

from src.core.config import Config
from src.core.exceptions import WorkspaceNotFoundError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)
