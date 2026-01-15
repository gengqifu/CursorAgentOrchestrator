"""总编排器询问工具 - TDD 第二步：实现 ask_orchestrator_questions 函数。

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


def ask_orchestrator_questions() -> dict:
    """询问4个问题。
    
    返回交互请求，包含4个问题：
    1. 项目路径（必填）
    2. 需求名称（必填）
    3. 需求URL（必填）
    4. 工作区路径（可选）
    
    Returns:
        包含交互请求的字典，格式：
        {
            "success": True,
            "interaction_required": True,
            "interaction_type": "questions",
            "questions": [
                {
                    "id": "project_path",
                    "question": "请输入项目路径（项目根目录）",
                    "type": "text",
                    "required": True,
                    "placeholder": "/path/to/project"
                },
                ...
            ]
        }
    """
    logger.info("询问总编排器4个问题")
    
    questions = [
        {
            "id": "project_path",
            "question": "请输入项目路径（项目根目录）",
            "type": "text",
            "required": True,
            "placeholder": "/path/to/project"
        },
        {
            "id": "requirement_name",
            "question": "请输入需求名称",
            "type": "text",
            "required": True,
            "placeholder": "用户认证功能"
        },
        {
            "id": "requirement_url",
            "question": "请输入需求URL或文件路径",
            "type": "text",
            "required": True,
            "placeholder": "https://example.com/req.md 或 /path/to/requirement.md"
        },
        {
            "id": "workspace_path",
            "question": "请输入工作区路径（可选，默认使用项目路径下的 .agent-orchestrator）",
            "type": "text",
            "required": False,
            "placeholder": "/path/to/.agent-orchestrator（可选）"
        }
    ]
    
    result = {
        "success": True,
        "interaction_required": True,
        "interaction_type": "questions",
        "questions": questions
    }
    
    logger.info(f"返回 {len(questions)} 个问题")
    return result
