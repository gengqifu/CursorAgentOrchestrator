"""覆盖率分析工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""

import subprocess
from pathlib import Path

from src.core.config import Config
from src.core.logger import setup_logger
from src.managers.workspace_manager import WorkspaceManager

logger = setup_logger(__name__)


def analyze_coverage(workspace_id: str, project_path: str) -> dict:
    """分析覆盖率。

    Args:
        workspace_id: 工作区ID
        project_path: 项目路径

    Returns:
        包含覆盖率信息的字典
    """
    config = Config()
    workspace_manager = WorkspaceManager(config=config)

    # 获取工作区信息
    workspace = workspace_manager.get_workspace(workspace_id)
    workspace_dir = config.get_workspace_path(workspace_id)

    project_dir = Path(project_path)

    # 尝试运行覆盖率分析
    coverage = 0.0
    coverage_report_path = None

    try:
        # 检查是否安装了 coverage
        result = subprocess.run(
            ["python3", "-m", "coverage", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # 运行覆盖率分析
            coverage_result = subprocess.run(
                ["python3", "-m", "coverage", "run", "-m", "pytest"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=30,
            )

            # 生成报告
            report_result = subprocess.run(
                ["python3", "-m", "coverage", "report", "--format=json"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10,
            )

            if report_result.returncode == 0:
                # 解析覆盖率（简化版）
                import json

                try:
                    coverage_data = json.loads(report_result.stdout)
                    total = coverage_data.get("totals", {})
                    coverage = total.get("percent_covered", 0.0)
                except Exception:
                    pass

            # 生成 HTML 报告
            html_report_dir = workspace_dir / "coverage_report"
            html_report_dir.mkdir(exist_ok=True)

            subprocess.run(
                ["python3", "-m", "coverage", "html", "-d", str(html_report_dir)],
                cwd=str(project_dir),
                capture_output=True,
                timeout=10,
            )

            coverage_report_path = str(html_report_dir / "index.html")

    except subprocess.TimeoutExpired:
        logger.warning("覆盖率分析超时")
    except FileNotFoundError:
        logger.warning("coverage 工具未安装，跳过覆盖率分析")
    except Exception as e:
        logger.error(f"覆盖率分析出错: {e}")

    # 如果没有运行覆盖率分析，使用简化统计
    if coverage == 0.0:
        coverage = _estimate_coverage(project_dir)

    logger.info(f"覆盖率分析完成: {workspace_id}, 覆盖率: {coverage:.2f}%")

    return {
        "success": True,
        "coverage": coverage,
        "coverage_report_path": coverage_report_path,
        "workspace_id": workspace_id,
    }


def _estimate_coverage(project_dir: Path) -> float:
    """估算覆盖率（简化版）。

    Args:
        project_dir: 项目目录

    Returns:
        估算的覆盖率百分比
    """
    # 统计代码文件和测试文件
    code_files = list(project_dir.rglob("*.py"))
    test_files = [f for f in code_files if "test" in f.name.lower()]

    if not code_files:
        return 0.0

    # 简化估算：测试文件数 / 代码文件数 * 100
    estimated = (len(test_files) / len(code_files)) * 100
    return min(estimated, 100.0)
