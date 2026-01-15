"""总编排器询问工具 - TDD 第三步：实现 submit_orchestrator_answers 函数。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现总编排器询问4个问题的功能：
1. 询问4个问题（项目路径、需求名称、需求URL、工作区路径）
2. 提交答案并创建工作区
"""

from pathlib import Path

from src.core.exceptions import ValidationError
from src.core.logger import setup_logger
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
            "placeholder": "/path/to/project",
        },
        {
            "id": "requirement_name",
            "question": "请输入需求名称",
            "type": "text",
            "required": True,
            "placeholder": "用户认证功能",
        },
        {
            "id": "requirement_url",
            "question": "请输入需求URL或文件路径",
            "type": "text",
            "required": True,
            "placeholder": "https://example.com/req.md 或 /path/to/requirement.md",
        },
        {
            "id": "workspace_path",
            "question": "请输入工作区路径（可选，默认使用项目路径下的 .agent-orchestrator）",
            "type": "text",
            "required": False,
            "placeholder": "/path/to/.agent-orchestrator（可选）",
        },
    ]

    result = {
        "success": True,
        "interaction_required": True,
        "interaction_type": "questions",
        "questions": questions,
    }

    logger.info(f"返回 {len(questions)} 个问题")
    return result


def submit_orchestrator_answers(answers: dict) -> dict:
    """提交答案并创建工作区。

    验证答案并创建工作区。必填字段：
    - project_path: 项目路径（必填）
    - requirement_name: 需求名称（必填）
    - requirement_url: 需求URL（必填）
    - workspace_path: 工作区路径（可选）

    Args:
        answers: 包含4个问题答案的字典，格式：
            {
                "project_path": "/path/to/project",
                "requirement_name": "用户认证功能",
                "requirement_url": "https://example.com/req.md",
                "workspace_path": "/path/to/.agent-orchestrator"  # 可选
            }

    Returns:
        包含 workspace_id 的字典，格式：
        {
            "success": True,
            "workspace_id": "req-20240115-123456-用户认证功能"
        }

    Raises:
        ValidationError: 当必填字段缺失或路径无效时
    """
    logger.info("提交总编排器答案并创建工作区")

    # 验证必填字段
    required_fields = ["project_path", "requirement_name", "requirement_url"]
    for field in required_fields:
        if (
            field not in answers
            or not answers[field]
            or not str(answers[field]).strip()
        ):
            raise ValidationError(f"必填字段缺失或为空: {field}")

    # 提取参数
    project_path = str(answers["project_path"]).strip()
    requirement_name = str(answers["requirement_name"]).strip()
    requirement_url = str(answers["requirement_url"]).strip()

    # 验证项目路径（WorkspaceManager.create_workspace 会进一步验证）
    project_path_obj = Path(project_path)
    if not project_path_obj.exists():
        raise ValidationError(f"项目路径不存在: {project_path}")
    if not project_path_obj.is_dir():
        raise ValidationError(f"项目路径不是目录: {project_path}")

    # 创建工作区
    try:
        workspace_manager = WorkspaceManager()
        workspace_id = workspace_manager.create_workspace(
            project_path=project_path,
            requirement_name=requirement_name,
            requirement_url=requirement_url,
        )

        logger.info(f"成功创建工作区: {workspace_id}")

        return {"success": True, "workspace_id": workspace_id}
    except ValidationError:
        # 重新抛出 ValidationError（可能是路径验证失败）
        raise
    except Exception as e:
        logger.error(f"创建工作区失败: {e}", exc_info=True)
        raise ValidationError(f"创建工作区失败: {str(e)}") from e
