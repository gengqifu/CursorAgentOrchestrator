"""代码审查工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.managers.task_manager import TaskManager
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def review_code(workspace_id: str, task_id: str) -> dict:
    """审查代码。

    Args:
        workspace_id: 工作区ID
        task_id: 任务ID

    Returns:
        包含审查结果的字典
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)
    task_manager = TaskManager()

    # 获取任务信息
    task = task_manager.get_task(workspace_id, task_id)
    code_files = task.get("code_files", [])

    # TODO: 调用 Gemini API 进行代码审查
    # 目前先实现基础审查逻辑

    review_report = _review_code_files(code_files, task)

    # 判断是否通过（简化逻辑）
    passed = _evaluate_review(review_report)

    # 更新任务状态
    if passed:
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "reviewed",
            review_passed=True,
            review_report=review_report,
        )
    else:
        task_manager.update_task_status(
            workspace_id,
            task_id,
            "needs_fix",
            review_passed=False,
            review_report=review_report,
        )

    logger.info(f"代码审查完成: {task_id}, 通过: {passed}")

    return {
        "success": True,
        "task_id": task_id,
        "passed": passed,
        "review_report": review_report,
        "workspace_id": workspace_id,
    }


def _review_code_files(code_files: list[str], task: dict) -> str:
    """审查代码文件。

    Args:
        code_files: 代码文件路径列表
        task: 任务信息

    Returns:
        审查报告
    """
    if not code_files:
        return "警告：没有找到代码文件"

    report_lines = [f"# 代码审查报告: {task.get('task_id', 'unknown')}"]
    report_lines.append(f"\n任务描述: {task.get('description', 'N/A')}")
    report_lines.append(f"\n审查文件数: {len(code_files)}")

    # 检查文件是否存在
    existing_files = []
    for file_path in code_files:
        path = Path(file_path)
        if path.exists():
            existing_files.append(file_path)
            # 读取文件内容进行基础检查
            try:
                content = path.read_text(encoding="utf-8")
                # 基础检查
                if len(content) < 10:
                    report_lines.append(f"\n⚠️ {file_path}: 文件内容过短")
                elif "TODO" in content:
                    report_lines.append(f"\n⚠️ {file_path}: 包含 TODO 注释")
                else:
                    report_lines.append(f"\n✅ {file_path}: 基础检查通过")
            except Exception as e:
                report_lines.append(f"\n❌ {file_path}: 读取失败 - {e}")
        else:
            report_lines.append(f"\n❌ {file_path}: 文件不存在")

    if not existing_files:
        report_lines.append("\n\n结论: 没有可审查的文件")
    else:
        report_lines.append(f"\n\n结论: 审查了 {len(existing_files)} 个文件")

    return "\n".join(report_lines)


def _evaluate_review(review_report: str) -> bool:
    """评估审查结果。

    Args:
        review_report: 审查报告

    Returns:
        是否通过
    """
    # 简化逻辑：如果没有严重错误，则认为通过
    if "❌" in review_report or "文件不存在" in review_report:
        return False
    return True
