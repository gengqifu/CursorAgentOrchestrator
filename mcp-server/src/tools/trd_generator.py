"""TRD 生成工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

import json
from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def generate_trd(workspace_id: str, prd_path: str | None = None) -> dict:
    """生成 TRD 文档。

    Args:
        workspace_id: 工作区ID
        prd_path: PRD 文档路径（可选，默认从工作区获取）

    Returns:
        包含 TRD 路径的字典

    Raises:
        ValidationError: 当 PRD 状态未完成、PRD 路径无效或 PRD 文件不存在时
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    status = workspace.get("status", {})
    files = workspace.get("files", {})

    # ✅ 新增：检查PRD状态
    if status.get("prd_status") != "completed":
        raise ValidationError("PRD尚未完成，无法生成TRD。请先完成PRD生成。")

    # 如果没有提供 prd_path，从工作区获取
    if not prd_path:
        prd_path = files.get("prd_path")
        if not prd_path:
            raise ValidationError("工作区中没有 PRD 文档，请先生成 PRD")

    # ✅ 新增：检查PRD文件存在
    prd_file = Path(prd_path)
    if not prd_file.exists():
        raise ValidationError(f"PRD 文件不存在: {prd_path}")

    # ✅ 新增：标记TRD为进行中
    workspace_manager.update_workspace_status(
        workspace_id, {"trd_status": "in_progress"}
    )

    workspace_dir = config.get_workspace_path(workspace_id)
    project_path = Path(workspace["project_path"])

    try:
        # 读取 PRD 内容
        prd_content = prd_file.read_text(encoding="utf-8")

        # 分析现有代码库
        codebase_info = _analyze_codebase(project_path)

        # 生成 TRD 内容
        trd_content = _generate_trd_content(prd_content, codebase_info, workspace)

        # 保存 TRD 文件
        trd_path = workspace_dir / "TRD.md"
        trd_path.write_text(trd_content, encoding="utf-8")

        # ✅ 新增：标记TRD为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # 更新工作区文件路径
        workspace = workspace_manager.get_workspace(workspace_id)
        workspace["files"]["trd_path"] = str(trd_path)
        meta_file = workspace_dir / "workspace.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(workspace, f, ensure_ascii=False, indent=2)

        logger.info(f"TRD 已生成: {trd_path}")

        return {
            "success": True,
            "trd_path": str(trd_path),
            "workspace_id": workspace_id,
        }
    except Exception as e:
        # ✅ 新增：标记TRD为失败
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "failed"}
        )
        logger.error(f"TRD 生成失败: {workspace_id}, 错误: {e}", exc_info=True)
        raise


def _analyze_codebase(project_path: Path) -> dict:
    """分析现有代码库。

    Args:
        project_path: 项目路径

    Returns:
        代码库分析信息
    """
    codebase_info = {"language": "unknown", "framework": "unknown", "structure": []}

    # 检测编程语言
    python_files = list(project_path.rglob("*.py"))
    if python_files:
        codebase_info["language"] = "python"

    # 检测框架（简化版）
    if (project_path / "requirements.txt").exists():
        codebase_info["framework"] = "python-standard"

    # 分析目录结构
    if project_path.exists():
        for item in project_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                codebase_info["structure"].append(item.name)

    return codebase_info


def _generate_trd_content(
    prd_content: str, codebase_info: dict, workspace: dict
) -> str:
    """生成 TRD 文档内容。

    Args:
        prd_content: PRD 文档内容
        codebase_info: 代码库分析信息
        workspace: 工作区信息

    Returns:
        TRD 文档内容
    """
    requirement_name = workspace.get("requirement_name", "未知需求")
    project_path = workspace.get("project_path", "")

    trd_template = f"""# TRD: {requirement_name}

## 1. 技术概述

### 1.1 技术栈
- 编程语言: {codebase_info.get('language', 'unknown')}
- 框架: {codebase_info.get('framework', 'unknown')}
- 项目路径: {project_path}

### 1.2 现有代码库结构
{chr(10).join(f'- {item}' for item in codebase_info.get('structure', []))}

## 2. 架构设计

### 2.1 系统架构
待补充

### 2.2 模块划分
待补充

## 3. 接口设计

### 3.1 API 接口
待补充

### 3.2 数据模型
待补充

## 4. 实现方案

### 4.1 核心功能实现
待补充

### 4.2 关键技术点
待补充

## 5. 测试策略
待补充

## 6. 风险评估
待补充

---
*本文档由 Agent Orchestrator 自动生成*
*基于 PRD: {workspace.get('requirement_name', 'N/A')}*
"""
    return trd_template
