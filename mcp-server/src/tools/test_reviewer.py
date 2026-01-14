"""测试审查工具 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""
from pathlib import Path

from src.core.logger import setup_logger

logger = setup_logger(__name__)


def review_tests(workspace_id: str, test_files: list[str]) -> dict:
    """审查测试。
    
    Args:
        workspace_id: 工作区ID
        test_files: 测试文件路径列表
    
    Returns:
        包含审查结果的字典
    """
    if not test_files:
        return {
            "success": True,
            "passed": False,
            "review_report": "警告：没有测试文件需要审查",
            "workspace_id": workspace_id
        }
    
    review_report = _review_test_files(test_files)
    passed = _evaluate_test_review(review_report)
    
    logger.info(f"测试审查完成: {workspace_id}, 通过: {passed}")
    
    return {
        "success": True,
        "passed": passed,
        "review_report": review_report,
        "workspace_id": workspace_id
    }


def _review_test_files(test_files: list[str]) -> str:
    """审查测试文件。
    
    Args:
        test_files: 测试文件路径列表
    
    Returns:
        审查报告
    """
    report_lines = ["# 测试审查报告"]
    report_lines.append(f"\n审查文件数: {len(test_files)}")
    
    valid_files = 0
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            try:
                content = path.read_text(encoding='utf-8')
                # 基础检查
                checks = []
                if "import pytest" in content or "import unittest" in content:
                    checks.append("✅ 导入测试框架")
                if "def test_" in content or "class Test" in content:
                    checks.append("✅ 包含测试函数/类")
                if "assert" in content:
                    checks.append("✅ 包含断言")
                else:
                    checks.append("⚠️ 缺少断言")
                
                report_lines.append(f"\n{path.name}:")
                report_lines.extend(f"  {check}" for check in checks)
                valid_files += 1
            except Exception as e:
                report_lines.append(f"\n❌ {path.name}: 读取失败 - {e}")
        else:
            report_lines.append(f"\n❌ {file_path}: 文件不存在")
    
    report_lines.append(f"\n\n结论: 审查了 {valid_files}/{len(test_files)} 个有效文件")
    
    return "\n".join(report_lines)


def _evaluate_test_review(review_report: str) -> bool:
    """评估测试审查结果。
    
    Args:
        review_report: 审查报告
    
    Returns:
        是否通过
    """
    # 简化逻辑：如果有有效测试文件，则认为通过
    if "审查了 0/" in review_report or "❌" in review_report:
        return False
    return True
