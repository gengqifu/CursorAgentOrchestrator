"""总编排器询问工具 - TDD 第一步：创建文件结构。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现总编排器询问4个问题的功能：
1. 询问4个问题（项目路径、需求名称、需求URL、工作区路径）
2. 提交答案并创建工作区
"""
from pathlib import Path

from src.core.logger import setup_logger
from src.core.exceptions import ValidationError
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)
