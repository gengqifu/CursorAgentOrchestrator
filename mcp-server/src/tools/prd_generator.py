"""PRD 生成工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

import json
from pathlib import Path

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def generate_prd(workspace_id: str, requirement_url: str) -> dict:
    """生成 PRD 文档。

    Args:
        workspace_id: 工作区ID
        requirement_url: 需求文档URL或文件路径

    Returns:
        包含 PRD 路径的字典

    Raises:
        ValidationError: 当参数无效时
    """
    # 验证参数
    if not requirement_url or not requirement_url.strip():
        raise ValidationError("需求URL不能为空")

    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    workspace_dir = config.get_workspace_path(workspace_id)

    # 读取需求文档
    requirement_content = _read_requirement(requirement_url)

    # 生成 PRD 内容
    prd_content = _generate_prd_content(requirement_content, workspace)

    # 保存 PRD 文件
    prd_path = workspace_dir / "PRD.md"
    prd_path.write_text(prd_content, encoding="utf-8")

    # 更新工作区状态
    workspace_manager.update_workspace_status(workspace_id, {"prd_status": "completed"})

    # 更新工作区文件路径
    workspace["files"]["prd_path"] = str(prd_path)
    meta_file = workspace_dir / "workspace.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(workspace, f, ensure_ascii=False, indent=2)

    logger.info(f"PRD 已生成: {prd_path}")

    return {"success": True, "prd_path": str(prd_path), "workspace_id": workspace_id}


def _read_requirement(requirement_url: str) -> str:
    """读取需求文档内容。

    Args:
        requirement_url: 需求文档URL或文件路径

    Returns:
        需求文档内容
    """
    path = Path(requirement_url)

    # 如果是文件路径
    if path.exists():
        return path.read_text(encoding="utf-8")

    # TODO: 如果是 URL，需要实现 HTTP 请求
    # 目前先返回占位内容
    return f"需求文档URL: {requirement_url}\n\n待实现：从URL读取需求文档"


def _generate_prd_content(requirement_content: str, workspace: dict) -> str:
    """生成 PRD 文档内容。

    Args:
        requirement_content: 需求文档内容
        workspace: 工作区信息

    Returns:
        PRD 文档内容
    """
    requirement_name = workspace.get("requirement_name", "未知需求")

    prd_template = f"""# PRD: {requirement_name}

## 1. 需求概述

### 1.1 需求背景
{requirement_content[:500]}

### 1.2 需求目标
待补充

## 2. 功能需求

### 2.1 核心功能
待补充

### 2.2 辅助功能
待补充

## 3. 非功能需求

### 3.1 性能要求
待补充

### 3.2 安全要求
待补充

## 4. 验收标准
待补充

## 5. 风险评估
待补充

---
*本文档由 Agent Orchestrator 自动生成*
"""
    return prd_template
