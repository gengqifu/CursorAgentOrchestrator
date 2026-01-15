"""任务执行工具 - TDD 第二步：实现 execute_task 函数。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict

本模块实现任务执行功能：
1. 执行单个任务（生成代码 → Review → 重试循环）
2. 执行所有待处理任务
"""

from src.core.exceptions import TaskNotFoundError
from src.core.logger import setup_logger
from src.managers.task_manager import TaskManager
from src.tools.code_generator import generate_code
from src.tools.code_reviewer import review_code

logger = setup_logger(__name__)

# 默认最大重试次数
DEFAULT_MAX_REVIEW_RETRIES = 3


def execute_task(
    workspace_id: str,
    task_id: str,
    max_review_retries: int = DEFAULT_MAX_REVIEW_RETRIES,
) -> dict:
    """执行单个任务（生成代码 → Review → 重试循环）。

    执行流程：
    1. 生成代码（调用 `generate_code`）
    2. Review 代码（调用 `review_code`）
    3. 如果 Review 通过，返回成功
    4. 如果 Review 未通过，重试（最多 `max_review_retries` 次）
    5. 达到最大重试次数时返回失败

    Args:
        workspace_id: 工作区ID
        task_id: 任务ID
        max_review_retries: 最大 Review 重试次数，默认为 3

    Returns:
        包含执行结果的字典，格式：
        {
            "success": True/False,
            "task_id": "task-xxx",
            "workspace_id": "req-xxx",
            "passed": True/False,  # Review 是否通过
            "retry_count": 0,  # 重试次数
            "review_report": "...",  # 最后一次 Review 报告
            "code_files": ["/path/to/file.py"],  # 生成的代码文件列表
            "error": "..."  # 如果失败，包含错误信息
        }

    Raises:
        TaskNotFoundError: 当任务不存在时
    """
    logger.info(
        f"开始执行任务: {workspace_id}/{task_id}, 最大重试次数: {max_review_retries}"
    )

    task_manager = TaskManager()

    # 验证任务存在
    try:
        task_manager.get_task(workspace_id, task_id)
    except TaskNotFoundError:
        logger.error(f"任务不存在: {workspace_id}/{task_id}")
        raise

    retry_count = 0
    last_review_report = ""
    last_code_files = []

    # Review 循环
    while retry_count <= max_review_retries:
        try:
            # 1. 生成代码
            logger.info(f"生成代码: {workspace_id}/{task_id}, 重试次数: {retry_count}")
            generate_result = generate_code(workspace_id, task_id)

            if not generate_result.get("success"):
                error_msg = f"代码生成失败: {generate_result.get('error', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,
                    "retry_count": retry_count,
                    "review_report": "",
                    "code_files": [],
                    "error": error_msg,
                }

            code_files = generate_result.get("code_files", [])
            last_code_files = code_files
            logger.info(f"代码生成成功: {task_id}, 文件数: {len(code_files)}")

            # 2. Review 代码
            logger.info(f"审查代码: {workspace_id}/{task_id}, 重试次数: {retry_count}")
            review_result = review_code(workspace_id, task_id)

            if not review_result.get("success"):
                error_msg = f"代码审查失败: {review_result.get('error', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,
                    "retry_count": retry_count,
                    "review_report": "",
                    "code_files": code_files,
                    "error": error_msg,
                }

            passed = review_result.get("passed", False)
            review_report = review_result.get("review_report", "")
            last_review_report = review_report

            # 3. 判断是否通过
            if passed:
                logger.info(
                    f"任务执行成功: {workspace_id}/{task_id}, 重试次数: {retry_count}"
                )
                return {
                    "success": True,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": True,
                    "retry_count": retry_count,
                    "review_report": review_report,
                    "code_files": code_files,
                }

            # 4. 未通过，检查是否需要重试
            retry_count += 1
            if retry_count > max_review_retries:
                logger.warning(
                    f"任务执行失败: {workspace_id}/{task_id}, "
                    f"达到最大重试次数: {max_review_retries}"
                )
                return {
                    "success": False,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,
                    "retry_count": retry_count - 1,  # 实际重试次数
                    "review_report": review_report,
                    "code_files": code_files,
                    "error": f"达到最大重试次数 ({max_review_retries})，Review 仍未通过",
                }

            logger.info(
                f"Review 未通过，准备重试: {workspace_id}/{task_id}, "
                f"当前重试次数: {retry_count}/{max_review_retries}"
            )

        except TaskNotFoundError:
            # 重新抛出 TaskNotFoundError
            raise
        except Exception as e:
            logger.error(
                f"任务执行异常: {workspace_id}/{task_id}, 错误: {e}", exc_info=True
            )
            return {
                "success": False,
                "task_id": task_id,
                "workspace_id": workspace_id,
                "passed": False,
                "retry_count": retry_count,
                "review_report": last_review_report,
                "code_files": last_code_files,
                "error": f"任务执行异常: {str(e)}",
            }

    # 理论上不会到达这里，但为了类型安全
    logger.error(f"任务执行失败: {workspace_id}/{task_id}, 未知错误")
    return {
        "success": False,
        "task_id": task_id,
        "workspace_id": workspace_id,
        "passed": False,
        "retry_count": retry_count,
        "review_report": last_review_report,
        "code_files": last_code_files,
        "error": "未知错误：循环异常退出",
    }


def execute_all_tasks(
    workspace_id: str,
    max_review_retries: int = DEFAULT_MAX_REVIEW_RETRIES,
) -> dict:
    """执行所有待处理任务。

    获取所有状态为 "pending" 的任务，循环执行每个任务（调用 `execute_task`），
    统计完成和失败的任务数，并返回执行结果统计。

    Args:
        workspace_id: 工作区ID
        max_review_retries: 每个任务的最大 Review 重试次数，默认为 3

    Returns:
        包含执行结果统计的字典，格式：
        {
            "success": True/False,
            "workspace_id": "req-xxx",
            "total_tasks": 5,  # 总任务数
            "completed_tasks": 3,  # 成功完成的任务数
            "failed_tasks": 2,  # 失败的任务数
            "task_results": [  # 每个任务的执行结果
                {
                    "task_id": "task-001",
                    "success": True,
                    "passed": True,
                    "retry_count": 0,
                    ...
                },
                ...
            ],
            "error": "..."  # 如果整体失败，包含错误信息
        }
    """
    logger.info(f"开始执行所有待处理任务: {workspace_id}")

    task_manager = TaskManager()

    try:
        # 获取所有任务
        all_tasks = task_manager.get_tasks(workspace_id)
        logger.info(f"获取到 {len(all_tasks)} 个任务")

        # 过滤出 pending 状态的任务
        pending_tasks = [task for task in all_tasks if task.get("status") == "pending"]
        logger.info(f"找到 {len(pending_tasks)} 个待处理任务")

        # 如果没有待处理任务，返回空结果
        if not pending_tasks:
            logger.info(f"没有待处理任务: {workspace_id}")
            return {
                "success": True,
                "workspace_id": workspace_id,
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "task_results": [],
            }

        # 循环执行每个任务
        task_results = []
        completed_count = 0
        failed_count = 0

        for task in pending_tasks:
            task_id = task.get("task_id")
            if not task_id:
                logger.warning(f"任务缺少 task_id，跳过: {task}")
                continue

            logger.info(f"执行任务: {workspace_id}/{task_id}")

            try:
                # 执行任务
                result = execute_task(
                    workspace_id, task_id, max_review_retries=max_review_retries
                )
                task_results.append(result)

                # 统计成功和失败
                if result.get("success") and result.get("passed"):
                    completed_count += 1
                    logger.info(f"任务执行成功: {workspace_id}/{task_id}")
                else:
                    failed_count += 1
                    logger.warning(
                        f"任务执行失败: {workspace_id}/{task_id}, "
                        f"错误: {result.get('error', '未知错误')}"
                    )

            except TaskNotFoundError as e:
                # 任务不存在，记录错误但继续执行其他任务
                failed_count += 1
                error_result = {
                    "success": False,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,
                    "retry_count": 0,
                    "review_report": "",
                    "code_files": [],
                    "error": f"任务不存在: {str(e)}",
                }
                task_results.append(error_result)
                logger.error(f"任务不存在: {workspace_id}/{task_id}")

            except Exception as e:
                # 其他异常，记录错误但继续执行其他任务
                failed_count += 1
                error_result = {
                    "success": False,
                    "task_id": task_id,
                    "workspace_id": workspace_id,
                    "passed": False,
                    "retry_count": 0,
                    "review_report": "",
                    "code_files": [],
                    "error": f"任务执行异常: {str(e)}",
                }
                task_results.append(error_result)
                logger.error(
                    f"任务执行异常: {workspace_id}/{task_id}, 错误: {e}",
                    exc_info=True,
                )

        # 返回执行结果统计
        total_tasks = len(pending_tasks)
        success = failed_count == 0  # 所有任务都成功才算成功

        logger.info(
            f"所有任务执行完成: {workspace_id}, "
            f"总计: {total_tasks}, 成功: {completed_count}, 失败: {failed_count}"
        )

        return {
            "success": success,
            "workspace_id": workspace_id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "task_results": task_results,
        }

    except Exception as e:
        logger.error(f"执行所有任务异常: {workspace_id}, 错误: {e}", exc_info=True)
        return {
            "success": False,
            "workspace_id": workspace_id,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "task_results": [],
            "error": f"执行所有任务异常: {str(e)}",
        }
