"""工作流编排工具。

实现完整的工作流编排功能，支持自动确认模式和交互模式。

工作流程：
1. 提交答案并创建工作区
2. PRD 循环（生成 → 确认）
3. TRD 循环（生成 → 确认）
4. 任务分解
5. 任务循环执行
6. 询问测试路径（使用默认路径）
7. 生成测试
8. 生成覆盖率报告
"""

from datetime import datetime
from pathlib import Path
from typing import Union

from src.core.config import Config
from src.core.exceptions import (
    AgentOrchestratorError,
    ValidationError,
    WorkspaceNotFoundError,
)
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

# 工作流编排工具
from src.tools.coverage_analyzer import analyze_coverage
from src.tools.orchestrator_questions import (
    ask_orchestrator_questions,
    submit_orchestrator_answers,
)
from src.tools.prd_confirmation import (
    check_prd_confirmation,
    confirm_prd,
    modify_prd,
)
from src.tools.prd_generator import generate_prd
from src.tools.stage_dependency_checker import check_stage_ready
from src.tools.task_decomposer import decompose_tasks
from src.tools.task_executor import execute_all_tasks
from src.tools.test_generator import generate_tests
from src.tools.test_path_question import ask_test_path, submit_test_path
from src.tools.trd_confirmation import (
    check_trd_confirmation,
    confirm_trd,
    modify_trd,
)
from src.tools.trd_generator import generate_trd
from src.tools.workflow_status import get_workflow_status

logger = setup_logger(__name__)

# 默认最大Review重试次数
DEFAULT_MAX_REVIEW_RETRIES = 3


def _update_workflow_state(
    workspace_id: str,
    current_step: int,
    step_name: str,
    step_status: str = "in_progress",
) -> None:
    """更新工作流状态。

    Args:
        workspace_id: 工作区ID
        current_step: 当前步骤编号（1-8）
        step_name: 当前步骤名称
        step_status: 步骤状态（"in_progress", "completed", "failed"）
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取当前工作流状态
    workspace = workspace_manager.get_workspace(workspace_id)
    workflow_state = workspace.get("workflow_state", {})

    # 更新工作流状态
    completed_steps = workflow_state.get("completed_steps", [])
    if step_status == "completed":
        # 如果步骤完成，添加到已完成步骤列表
        step_info = {"step": current_step, "name": step_name, "status": step_status}
        if step_info not in completed_steps:
            completed_steps.append(step_info)
    elif step_status == "failed":
        # 如果步骤失败，记录失败信息
        failed_steps = workflow_state.get("failed_steps", [])
        failed_steps.append(
            {"step": current_step, "name": step_name, "status": step_status}
        )
        workflow_state["failed_steps"] = failed_steps

    # 更新工作流状态
    workflow_state.update(
        {
            "current_step": current_step,
            "step_name": step_name,
            "step_status": step_status,
            "completed_steps": completed_steps,
            "last_updated": datetime.now().isoformat(),
        }
    )

    # 保存到工作区元数据
    workspace_dir = config.get_workspace_path(workspace_id)
    meta_file = workspace_dir / "workspace.json"

    import json

    from src.utils.file_lock import file_lock

    with file_lock(meta_file):
        with open(meta_file, encoding="utf-8") as f:
            workspace_data = json.load(f)
        workspace_data["workflow_state"] = workflow_state
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace_data, f, ensure_ascii=False, indent=2)

    logger.info(
        f"更新工作流状态: {workspace_id}, 步骤{current_step} ({step_name}) -> {step_status}"
    )


def _get_workflow_state(workspace_id: str) -> dict:
    """获取工作流状态。

    Args:
        workspace_id: 工作区ID

    Returns:
        工作流状态字典，格式：
        {
            "current_step": 1,
            "step_name": "创建工作区",
            "step_status": "completed",
            "completed_steps": [...],
            "failed_steps": [...],
            "last_updated": "..."
        }
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)
    workspace = workspace_manager.get_workspace(workspace_id)
    return workspace.get("workflow_state", {})


def _should_skip_step(workspace_id: str, step_number: int, step_name: str) -> bool:
    """检查是否应该跳过步骤（如果已完成）。

    Args:
        workspace_id: 工作区ID
        step_number: 步骤编号
        step_name: 步骤名称

    Returns:
        如果步骤已完成，返回 True；否则返回 False
    """
    workflow_state = _get_workflow_state(workspace_id)
    completed_steps = workflow_state.get("completed_steps", [])
    for step_info in completed_steps:
        if (
            step_info.get("step") == step_number
            and step_info.get("status") == "completed"
        ):
            logger.info(f"步骤{step_number} ({step_name}) 已完成，跳过执行")
            return True
    return False


def execute_full_workflow(
    project_path: Union[str, None] = None,
    requirement_name: Union[str, None] = None,
    requirement_url: Union[str, None] = None,
    workspace_path: Union[str, None] = None,
    workspace_id: Union[str, None] = None,
    auto_confirm: bool = True,
    max_review_retries: int = DEFAULT_MAX_REVIEW_RETRIES,
    interaction_response: Union[dict, None] = None,
) -> dict:
    """执行完整工作流。

    自动执行从需求输入到代码完成的整个开发流程。

    工作流程：
    1. 提交答案并创建工作区
    2. PRD 循环（生成 → 确认）
    3. TRD 循环（生成 → 确认）
    4. 任务分解
    5. 任务循环执行
    6. 询问测试路径（使用默认路径）
    7. 生成测试
    8. 生成覆盖率报告

    Args:
        project_path: 项目路径（交互模式下可选）
        requirement_name: 需求名称（交互模式下可选）
        requirement_url: 需求URL或文件路径（交互模式下可选）
        workspace_path: 工作区路径（可选，默认使用项目路径下的 .agent-orchestrator）
        workspace_id: 工作区ID（用于恢复工作流，可选）
        auto_confirm: 是否自动确认（默认为 True）
            - True: 自动确认模式，PRD/TRD 生成后自动确认，测试路径使用默认值
            - False: 交互模式，需要用户确认和输入
        max_review_retries: 每个任务的最大 Review 重试次数（可选，默认为 3）
        interaction_response: 交互响应（用于恢复工作流，可选）
            - 当 interaction_type="questions" 时，包含 answers 字段
            - 当 interaction_type="prd_confirmation" 时，包含 action 字段（"confirm" 或 "modify"）
            - 当 interaction_type="trd_confirmation" 时，包含 action 字段（"confirm" 或 "modify"）
            - 当 interaction_type="question" 时，包含 answer 字段（test_path）

    Returns:
        包含工作流执行结果的字典，格式：
        {
            "success": True/False,
            "workspace_id": "req-xxx",
            "workflow_steps": [...],
            "final_status": {...},
            "interaction_required": True/False,  # 交互模式下，需要用户交互时返回 True
            "interaction_type": "...",  # 交互类型
            "error": "..."  # 如果失败，包含错误信息
        }

    Raises:
        ValidationError: 当参数无效时
        WorkspaceNotFoundError: 当工作区不存在时
        AgentOrchestratorError: 当工作流执行失败时
    """
    logger.info(
        f"开始执行完整工作流: project_path={project_path}, "
        f"requirement_name={requirement_name}, auto_confirm={auto_confirm}, "
        f"workspace_id={workspace_id}"
    )

    workflow_steps = []
    current_workspace_id = workspace_id or ""

    # 交互模式：如果参数未提供且没有交互响应，返回询问4个问题的交互请求
    if not auto_confirm:
        # 如果提供了 workspace_id，说明是恢复工作流，不应该返回初始问题
        if (
            not current_workspace_id
            and not interaction_response
            and (not project_path or not requirement_name or not requirement_url)
        ):
            logger.info("交互模式：参数未提供，返回询问4个问题")
            return ask_orchestrator_questions()

        # 处理交互响应：如果是 answers，提取参数
        if (
            interaction_response
            and interaction_response.get("interaction_type") == "questions"
        ):
            answers = interaction_response.get("answers", {})
            project_path = answers.get("project_path") or project_path
            requirement_name = answers.get("requirement_name") or requirement_name
            requirement_url = answers.get("requirement_url") or requirement_url
            workspace_path = answers.get("workspace_path") or workspace_path

    # 如果提供了 workspace_id，先尝试恢复工作流（在参数验证之前）
    if current_workspace_id:
        try:
            config = Config()
            workspace_manager = WorkspaceManager(config=config)
            workspace = workspace_manager.get_workspace(current_workspace_id)
            # 从工作区恢复参数
            if not project_path:
                project_path = workspace.get("project_path")
            if not requirement_name:
                requirement_name = workspace.get("requirement_name")
            if not requirement_url:
                requirement_url = workspace.get("requirement_url")
            workspace_id = current_workspace_id
            logger.info(f"从工作区恢复工作流: {workspace_id}")
        except WorkspaceNotFoundError:
            logger.warning(f"工作区不存在: {current_workspace_id}，将创建新工作区")
            workspace_id = ""

    # 参数验证（自动确认模式或交互模式但参数已提供）
    # 注意：如果提供了 workspace_id 且成功恢复，参数可能已从工作区恢复
    # 如果从工作区恢复后参数仍为空，允许继续执行，但在使用时再检查
    if auto_confirm:
        # 只有在没有 workspace_id 或恢复失败时才进行严格验证
        if not current_workspace_id:
            if not project_path or not str(project_path).strip():
                raise ValidationError("project_path 不能为空")
            if not requirement_name or not str(requirement_name).strip():
                raise ValidationError("requirement_name 不能为空")
            if not requirement_url or not str(requirement_url).strip():
                raise ValidationError("requirement_url 不能为空")

    try:
        # 步骤1: 提交答案并创建工作区（如果还没有工作区）
        if not workspace_id:
            logger.info("步骤1: 提交答案并创建工作区")
            if not project_path or not requirement_name or not requirement_url:
                raise ValidationError(
                    "创建工作区需要 project_path, requirement_name, requirement_url"
                )

            step1_result = submit_orchestrator_answers(
                {
                    "project_path": project_path,
                    "requirement_name": requirement_name,
                    "requirement_url": requirement_url,
                    "workspace_path": workspace_path,
                }
            )
            if not step1_result.get("success"):
                raise AgentOrchestratorError(
                    f"创建工作区失败: {step1_result.get('error', '未知错误')}"
                )
            workspace_id = step1_result["workspace_id"]
            workflow_steps.append(
                {
                    "step": 1,
                    "name": "创建工作区",
                    "status": "completed",
                    "result": step1_result,
                }
            )
            logger.info(f"步骤1完成: 工作区ID={workspace_id}")
            # 更新工作流状态
            _update_workflow_state(workspace_id, 1, "创建工作区", "completed")
        else:
            logger.info(f"使用现有工作区: {workspace_id}")
            # 检查步骤1是否已完成
            if _should_skip_step(workspace_id, 1, "创建工作区"):
                workflow_steps.append(
                    {
                        "step": 1,
                        "name": "创建工作区",
                        "status": "completed",
                        "result": {"workspace_id": workspace_id},
                    }
                )

        # 步骤2: PRD 循环（生成 → 确认）
        logger.info("步骤2: PRD 循环（生成 → 确认）")

        max_prd_loops = 3  # 最多重试3次

        # 检查是否应该跳过步骤2
        if _should_skip_step(workspace_id, 2, "PRD 生成和确认"):
            workflow_steps.append(
                {
                    "step": 2,
                    "name": "PRD 生成和确认",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤2已完成，跳过执行")
            # 跳过步骤2，直接进入步骤3
            prd_loop_count = max_prd_loops  # 设置循环计数为最大值，避免进入循环
        else:
            # 更新工作流状态：步骤2开始
            _update_workflow_state(workspace_id, 2, "PRD 生成和确认", "in_progress")
            prd_loop_count = 0

        # 检查 PRD 阶段是否就绪
        prd_ready_check = check_stage_ready(workspace_id, "prd")
        if not prd_ready_check.get("ready"):
            logger.warning(
                f"PRD 阶段未就绪: {prd_ready_check.get('reason')}，"
                f"但继续执行（PRD 没有前置依赖）"
            )

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        while prd_loop_count < max_prd_loops:
            prd_loop_count += 1
            logger.info(f"PRD 循环第 {prd_loop_count} 次")

            # 生成 PRD
            prd_result = generate_prd(workspace_id, requirement_url)
            if not prd_result.get("success"):
                raise AgentOrchestratorError(
                    f"PRD 生成失败: {prd_result.get('error', '未知错误')}"
                )

            # 交互模式：处理交互响应或返回确认请求
            if not auto_confirm:
                # 如果有交互响应，处理确认或修改
                if (
                    interaction_response
                    and interaction_response.get("interaction_type")
                    == "prd_confirmation"
                ):
                    action = interaction_response.get("action")
                    if action == "confirm":
                        confirm_result = confirm_prd(workspace_id)
                        if not confirm_result.get("success"):
                            raise AgentOrchestratorError(
                                f"PRD 确认失败: {confirm_result.get('error', '未知错误')}"
                            )
                        workflow_steps.append(
                            {
                                "step": 2,
                                "name": "PRD 生成和确认",
                                "status": "completed",
                                "result": {"prd_path": prd_result.get("prd_path")},
                            }
                        )
                        logger.info("步骤2完成: PRD 已生成并确认")
                        # 更新工作流状态
                        _update_workflow_state(
                            workspace_id, 2, "PRD 生成和确认", "completed"
                        )
                        break
                    elif action == "modify":
                        modify_result = modify_prd(workspace_id)
                        if not modify_result.get("success"):
                            raise AgentOrchestratorError(
                                f"PRD 修改标记失败: {modify_result.get('error', '未知错误')}"
                            )
                        logger.info("PRD 标记为需要修改，将重新生成")
                        continue  # 继续循环，重新生成
                    else:
                        raise ValidationError(f"无效的 PRD 确认操作: {action}")
                else:
                    # 没有交互响应，返回确认请求
                    prd_confirmation = check_prd_confirmation(workspace_id)
                    if not prd_confirmation.get("success"):
                        raise AgentOrchestratorError(
                            f"检查 PRD 确认失败: {prd_confirmation.get('error', '未知错误')}"
                        )
                    logger.info("交互模式：返回 PRD 确认请求")
                    return {
                        "success": True,
                        "workspace_id": workspace_id,
                        "workflow_steps": workflow_steps,
                        "interaction_required": True,
                        "interaction_type": "prd_confirmation",
                        "prd_path": prd_confirmation.get("prd_path"),
                        "prd_preview": prd_confirmation.get("prd_preview"),
                    }
            else:
                # 自动确认模式：直接确认 PRD
                confirm_result = confirm_prd(workspace_id)
                if not confirm_result.get("success"):
                    raise AgentOrchestratorError(
                        f"PRD 确认失败: {confirm_result.get('error', '未知错误')}"
                    )
                workflow_steps.append(
                    {
                        "step": 2,
                        "name": "PRD 生成和确认",
                        "status": "completed",
                        "result": {"prd_path": prd_result.get("prd_path")},
                    }
                )
                logger.info("步骤2完成: PRD 已生成并确认")
                # 更新工作流状态
                _update_workflow_state(workspace_id, 2, "PRD 生成和确认", "completed")
                # 查询工作流状态
                workflow_status = get_workflow_status(workspace_id)
                logger.info(
                    f"PRD 完成后工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
                    f"可开始阶段={workflow_status.get('next_available_stages', [])}"
                )
                break

        # 只有在步骤未被跳过且循环达到最大次数时才抛出错误
        if prd_loop_count >= max_prd_loops and not _should_skip_step(workspace_id, 2, "PRD 生成和确认"):
            # 更新工作流状态：步骤2失败
            _update_workflow_state(workspace_id, 2, "PRD 生成和确认", "failed")
            raise AgentOrchestratorError("PRD 循环达到最大重试次数")

        # 步骤3: TRD 循环（生成 → 确认）
        logger.info("步骤3: TRD 循环（生成 → 确认）")

        max_trd_loops = 3  # 最多重试3次

        # 检查是否应该跳过步骤3
        if _should_skip_step(workspace_id, 3, "TRD 生成和确认"):
            workflow_steps.append(
                {
                    "step": 3,
                    "name": "TRD 生成和确认",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤3已完成，跳过执行")
            # 跳过步骤3，直接进入步骤4
            trd_loop_count = max_trd_loops  # 设置循环计数为最大值，避免进入循环
        else:
            # 更新工作流状态：步骤3开始
            _update_workflow_state(workspace_id, 3, "TRD 生成和确认", "in_progress")
            trd_loop_count = 0

        # 检查 TRD 阶段是否就绪
        trd_ready_check = check_stage_ready(workspace_id, "trd")
        if not trd_ready_check.get("ready"):
            raise AgentOrchestratorError(
                f"TRD 阶段未就绪: {trd_ready_check.get('reason')}"
            )
        logger.info(f"TRD 阶段就绪检查通过: {trd_ready_check.get('reason')}")

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        while trd_loop_count < max_trd_loops:
            trd_loop_count += 1
            logger.info(f"TRD 循环第 {trd_loop_count} 次")

            # 生成 TRD
            trd_result = generate_trd(workspace_id)
            if not trd_result.get("success"):
                raise AgentOrchestratorError(
                    f"TRD 生成失败: {trd_result.get('error', '未知错误')}"
                )

            # 交互模式：处理交互响应或返回确认请求
            if not auto_confirm:
                # 如果有交互响应，处理确认或修改
                if (
                    interaction_response
                    and interaction_response.get("interaction_type")
                    == "trd_confirmation"
                ):
                    action = interaction_response.get("action")
                    if action == "confirm":
                        confirm_result = confirm_trd(workspace_id)
                        if not confirm_result.get("success"):
                            raise AgentOrchestratorError(
                                f"TRD 确认失败: {confirm_result.get('error', '未知错误')}"
                            )
                        workflow_steps.append(
                            {
                                "step": 3,
                                "name": "TRD 生成和确认",
                                "status": "completed",
                                "result": {"trd_path": trd_result.get("trd_path")},
                            }
                        )
                        logger.info("步骤3完成: TRD 已生成并确认")
                        # 更新工作流状态
                        _update_workflow_state(
                            workspace_id, 3, "TRD 生成和确认", "completed"
                        )
                        break
                    elif action == "modify":
                        modify_result = modify_trd(workspace_id)
                        if not modify_result.get("success"):
                            raise AgentOrchestratorError(
                                f"TRD 修改标记失败: {modify_result.get('error', '未知错误')}"
                            )
                        logger.info("TRD 标记为需要修改，将重新生成")
                        continue  # 继续循环，重新生成
                    else:
                        raise ValidationError(f"无效的 TRD 确认操作: {action}")
                else:
                    # 没有交互响应，返回确认请求
                    trd_confirmation = check_trd_confirmation(workspace_id)
                    if not trd_confirmation.get("success"):
                        raise AgentOrchestratorError(
                            f"检查 TRD 确认失败: {trd_confirmation.get('error', '未知错误')}"
                        )
                    logger.info("交互模式：返回 TRD 确认请求")
                    return {
                        "success": True,
                        "workspace_id": workspace_id,
                        "workflow_steps": workflow_steps,
                        "interaction_required": True,
                        "interaction_type": "trd_confirmation",
                        "trd_path": trd_confirmation.get("trd_path"),
                        "trd_preview": trd_confirmation.get("trd_preview"),
                    }
            else:
                # 自动确认模式：直接确认 TRD
                confirm_result = confirm_trd(workspace_id)
                if not confirm_result.get("success"):
                    raise AgentOrchestratorError(
                        f"TRD 确认失败: {confirm_result.get('error', '未知错误')}"
                    )
                workflow_steps.append(
                    {
                        "step": 3,
                        "name": "TRD 生成和确认",
                        "status": "completed",
                        "result": {"trd_path": trd_result.get("trd_path")},
                    }
                )
                logger.info("步骤3完成: TRD 已生成并确认")
                # 更新工作流状态
                _update_workflow_state(workspace_id, 3, "TRD 生成和确认", "completed")
                # 查询工作流状态
                workflow_status = get_workflow_status(workspace_id)
                logger.info(
                    f"TRD 完成后工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
                    f"可开始阶段={workflow_status.get('next_available_stages', [])}"
                )
                break

        # 只有在步骤未被跳过且循环达到最大次数时才抛出错误
        if trd_loop_count >= max_trd_loops and not _should_skip_step(workspace_id, 3, "TRD 生成和确认"):
            # 更新工作流状态：步骤3失败
            _update_workflow_state(workspace_id, 3, "TRD 生成和确认", "failed")
            raise AgentOrchestratorError("TRD 循环达到最大重试次数")

        # 步骤4: 任务分解
        logger.info("步骤4: 任务分解")

        # 检查是否应该跳过步骤4
        if _should_skip_step(workspace_id, 4, "任务分解"):
            workflow_steps.append(
                {
                    "step": 4,
                    "name": "任务分解",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤4已完成，跳过执行")
        else:
            # 更新工作流状态：步骤4开始
            _update_workflow_state(workspace_id, 4, "任务分解", "in_progress")

        # 检查任务分解阶段是否就绪
        tasks_ready_check = check_stage_ready(workspace_id, "tasks")
        if not tasks_ready_check.get("ready"):
            raise AgentOrchestratorError(
                f"任务分解阶段未就绪: {tasks_ready_check.get('reason')}"
            )
        logger.info(f"任务分解阶段就绪检查通过: {tasks_ready_check.get('reason')}")

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        decompose_result = decompose_tasks(workspace_id)
        if not decompose_result.get("success"):
            raise AgentOrchestratorError(
                f"任务分解失败: {decompose_result.get('error', '未知错误')}"
            )
        workflow_steps.append(
            {
                "step": 4,
                "name": "任务分解",
                "status": "completed",
                "result": {
                    "tasks_json_path": decompose_result.get("tasks_json_path"),
                    "task_count": decompose_result.get("task_count"),
                },
            }
        )
        logger.info(f"步骤4完成: 已分解 {decompose_result.get('task_count')} 个任务")
        # 更新工作流状态
        _update_workflow_state(workspace_id, 4, "任务分解", "completed")

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"任务分解完成后工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        # 步骤5: 任务循环执行
        logger.info("步骤5: 任务循环执行")

        # 检查是否应该跳过步骤5
        if _should_skip_step(workspace_id, 5, "任务执行"):
            workflow_steps.append(
                {
                    "step": 5,
                    "name": "任务执行",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤5已完成，跳过执行")
        else:
            # 更新工作流状态：步骤5开始
            _update_workflow_state(workspace_id, 5, "任务执行", "in_progress")

        # 检查代码生成阶段是否就绪
        code_ready_check = check_stage_ready(workspace_id, "code")
        if not code_ready_check.get("ready"):
            raise AgentOrchestratorError(
                f"代码生成阶段未就绪: {code_ready_check.get('reason')}"
            )
        logger.info(f"代码生成阶段就绪检查通过: {code_ready_check.get('reason')}")

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        execute_result = execute_all_tasks(
            workspace_id, max_review_retries=max_review_retries
        )
        workflow_steps.append(
            {
                "step": 5,
                "name": "任务执行",
                "status": "completed" if execute_result.get("success") else "failed",
                "result": {
                    "total_tasks": execute_result.get("total_tasks"),
                    "completed_tasks": execute_result.get("completed_tasks"),
                    "failed_tasks": execute_result.get("failed_tasks"),
                },
            }
        )
        if not execute_result.get("success"):
            logger.warning(
                f"部分任务执行失败: {execute_result.get('failed_tasks')} 个任务失败"
            )
        logger.info(
            f"步骤5完成: 总计 {execute_result.get('total_tasks')} 个任务, "
            f"成功 {execute_result.get('completed_tasks')} 个, "
            f"失败 {execute_result.get('failed_tasks')} 个"
        )
        # 更新工作流状态
        step5_status = "completed" if execute_result.get("success") else "failed"
        _update_workflow_state(workspace_id, 5, "任务执行", step5_status)

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"任务执行完成后工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        # 步骤6: 询问测试路径（使用默认路径）
        logger.info("步骤6: 询问测试路径（使用默认路径）")

        # 检查是否应该跳过步骤6
        if _should_skip_step(workspace_id, 6, "测试路径设置"):
            workflow_steps.append(
                {
                    "step": 6,
                    "name": "测试路径设置",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤6已完成，跳过执行")
            # 获取测试路径
            config = Config()
            workspace_manager = WorkspaceManager(config=config)
            workspace = workspace_manager.get_workspace(workspace_id)
            default_test_path = workspace.get("files", {}).get("test_path", "")
        else:
            # 更新工作流状态：步骤6开始
            _update_workflow_state(workspace_id, 6, "测试路径设置", "in_progress")

        # 检查测试生成阶段是否就绪
        test_ready_check = check_stage_ready(workspace_id, "test")
        if not test_ready_check.get("ready"):
            logger.warning(
                f"测试生成阶段未就绪: {test_ready_check.get('reason')}，"
                f"但继续执行（可能没有已完成的任务）"
            )
        else:
            logger.info(f"测试生成阶段就绪检查通过: {test_ready_check.get('reason')}")

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        test_path_result = ask_test_path(workspace_id)
        if not test_path_result.get("success"):
            raise AgentOrchestratorError(
                f"询问测试路径失败: {test_path_result.get('error', '未知错误')}"
            )

        # 交互模式：处理交互响应或返回询问请求
        if not auto_confirm:
            # 如果有交互响应，提取测试路径
            if (
                interaction_response
                and interaction_response.get("interaction_type") == "question"
            ):
                test_path = interaction_response.get("answer")
                if not test_path:
                    raise ValidationError("测试路径不能为空")
                submit_path_result = submit_test_path(workspace_id, test_path)
                if not submit_path_result.get("success"):
                    raise AgentOrchestratorError(
                        f"提交测试路径失败: {submit_path_result.get('error', '未知错误')}"
                    )
                workflow_steps.append(
                    {
                        "step": 6,
                        "name": "测试路径设置",
                        "status": "completed",
                        "result": {"test_path": test_path},
                    }
                )
                logger.info(f"步骤6完成: 测试路径={test_path}")
                # 更新工作流状态
                _update_workflow_state(workspace_id, 6, "测试路径设置", "completed")
                default_test_path = test_path
            else:
                # 没有交互响应，返回询问请求
                logger.info("交互模式：返回测试路径询问请求")
                return {
                    "success": True,
                    "workspace_id": workspace_id,
                    "workflow_steps": workflow_steps,
                    "interaction_required": True,
                    "interaction_type": "question",
                    "question": test_path_result.get("question"),
                }
        else:
            # 自动确认模式：使用默认路径
            default_test_path = test_path_result.get("question", {}).get("default", "")
            if not default_test_path:
                # 如果没有默认路径，使用 {project_path}/tests/mock
                config = Config()
                workspace_manager = WorkspaceManager(config=config)
                workspace = workspace_manager.get_workspace(workspace_id)
                project_path_str = workspace.get("project_path")
                if not project_path_str:
                    raise AgentOrchestratorError("工作区缺少 project_path 字段")
                project_path_obj = Path(str(project_path_str))
                default_test_path = str(project_path_obj / "tests" / "mock")

            submit_path_result = submit_test_path(workspace_id, default_test_path)
            if not submit_path_result.get("success"):
                raise AgentOrchestratorError(
                    f"提交测试路径失败: {submit_path_result.get('error', '未知错误')}"
                )
            workflow_steps.append(
                {
                    "step": 6,
                    "name": "测试路径设置",
                    "status": "completed",
                    "result": {"test_path": default_test_path},
                }
            )
            logger.info(f"步骤6完成: 测试路径={default_test_path}")
            # 更新工作流状态
            _update_workflow_state(workspace_id, 6, "测试路径设置", "completed")

        # 步骤7: 生成测试
        logger.info("步骤7: 生成测试")

        # 检查是否应该跳过步骤7
        if _should_skip_step(workspace_id, 7, "生成测试"):
            workflow_steps.append(
                {
                    "step": 7,
                    "name": "生成测试",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤7已完成，跳过执行")
        else:
            # 更新工作流状态：步骤7开始
            _update_workflow_state(workspace_id, 7, "生成测试", "in_progress")
        tests_result = generate_tests(workspace_id, default_test_path)
        if not tests_result.get("success"):
            raise AgentOrchestratorError(
                f"测试生成失败: {tests_result.get('error', '未知错误')}"
            )
        workflow_steps.append(
            {
                "step": 7,
                "name": "生成测试",
                "status": "completed",
                "result": {
                    "test_files": tests_result.get("test_files"),
                    "test_count": tests_result.get("test_count"),
                },
            }
        )
        logger.info(f"步骤7完成: 已生成 {tests_result.get('test_count')} 个测试文件")
        # 更新工作流状态
        _update_workflow_state(workspace_id, 7, "生成测试", "completed")

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"测试生成完成后工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )

        # 步骤8: 生成覆盖率报告
        logger.info("步骤8: 生成覆盖率报告")

        # 检查是否应该跳过步骤8
        if _should_skip_step(workspace_id, 8, "生成覆盖率报告"):
            workflow_steps.append(
                {
                    "step": 8,
                    "name": "生成覆盖率报告",
                    "status": "completed",
                    "result": {},
                }
            )
            logger.info("步骤8已完成，跳过执行")
        else:
            # 更新工作流状态：步骤8开始
            _update_workflow_state(workspace_id, 8, "生成覆盖率报告", "in_progress")

        # 检查覆盖率分析阶段是否就绪
        coverage_ready_check = check_stage_ready(workspace_id, "coverage")
        if not coverage_ready_check.get("ready"):
            logger.warning(
                f"覆盖率分析阶段未就绪: {coverage_ready_check.get('reason')}，"
                f"但继续执行"
            )
        else:
            logger.info(
                f"覆盖率分析阶段就绪检查通过: {coverage_ready_check.get('reason')}"
            )

        # 查询工作流状态
        workflow_status = get_workflow_status(workspace_id)
        logger.info(
            f"工作流状态: 已完成阶段={workflow_status.get('workflow_progress', {}).get('completed_stages')}, "
            f"可开始阶段={workflow_status.get('next_available_stages', [])}"
        )
        # 获取项目路径（如果未提供）
        if not project_path:
            config = Config()
            workspace_manager = WorkspaceManager(config=config)
            workspace = workspace_manager.get_workspace(workspace_id)
            project_path = workspace.get("project_path")
            if not project_path:
                raise AgentOrchestratorError("工作区缺少 project_path 字段")
        coverage_result = analyze_coverage(workspace_id, str(project_path))
        if not coverage_result.get("success"):
            raise AgentOrchestratorError(
                f"覆盖率分析失败: {coverage_result.get('error', '未知错误')}"
            )
        workflow_steps.append(
            {
                "step": 8,
                "name": "生成覆盖率报告",
                "status": "completed",
                "result": {
                    "coverage": coverage_result.get("coverage"),
                    "coverage_report_path": coverage_result.get("coverage_report_path"),
                },
            }
        )
        logger.info(
            f"步骤8完成: 覆盖率={coverage_result.get('coverage')}%, "
            f"报告路径={coverage_result.get('coverage_report_path')}"
        )
        # 更新工作流状态
        _update_workflow_state(workspace_id, 8, "生成覆盖率报告", "completed")

        # 获取最终状态
        final_status_result = get_workflow_status(workspace_id)
        final_status = final_status_result.get("stages", {})

        logger.info(f"完整工作流执行成功: {workspace_id}")

        return {
            "success": True,
            "workspace_id": workspace_id,
            "workflow_steps": workflow_steps,
            "final_status": {
                "prd_status": final_status.get("prd", {}).get("status"),
                "trd_status": final_status.get("trd", {}).get("status"),
                "tasks_status": final_status.get("tasks", {}).get("status"),
                "code_status": final_status.get("code", {}).get("status"),
                "test_status": final_status.get("test", {}).get("status"),
                "coverage_status": final_status.get("coverage", {}).get("status"),
            },
        }

    except (ValidationError, WorkspaceNotFoundError) as e:
        logger.error(f"工作流执行失败（参数错误）: {e}", exc_info=True)
        return {
            "success": False,
            "workspace_id": workspace_id,
            "workflow_steps": workflow_steps,
            "error": str(e),
        }
    except AgentOrchestratorError as e:
        logger.error(f"工作流执行失败: {e}", exc_info=True)
        return {
            "success": False,
            "workspace_id": workspace_id,
            "workflow_steps": workflow_steps,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"工作流执行异常: {e}", exc_info=True)
        return {
            "success": False,
            "workspace_id": workspace_id,
            "workflow_steps": workflow_steps,
            "error": f"工作流执行异常: {str(e)}",
        }
