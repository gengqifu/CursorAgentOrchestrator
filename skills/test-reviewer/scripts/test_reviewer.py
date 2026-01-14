"""Test Reviewer Skill 入口脚本。

本脚本是 test-reviewer skill 的执行入口，由 Agent 根据 SKILL.md 指导调用。

Python 3.9+ 兼容
"""
import sys
import json
from pathlib import Path

# 添加 mcp-server 到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
mcp_server_path = project_root / "mcp-server"
if str(mcp_server_path) not in sys.path:
    sys.path.insert(0, str(mcp_server_path))

# 导入核心实现
from src.tools.test_reviewer import review_tests


def main():
    """命令行入口。"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="审查测试 - test-reviewer skill 入口"
    )
    parser.add_argument("workspace_id", help="工作区 ID")
    parser.add_argument("test_files", nargs="*", help="测试文件路径列表（可选）")
    
    args = parser.parse_args()
    
    # 如果没有提供 test_files，从工作区中查找测试文件
    if not args.test_files:
        from src.core.config import Config
        from src.managers.workspace_manager import WorkspaceManager
        
        config = Config()
        workspace_manager = WorkspaceManager(config=config)
        workspace = workspace_manager.get_workspace(args.workspace_id)
        project_path = Path(workspace["project_path"])
        tests_dir = project_path / "tests"
        
        if tests_dir.exists():
            args.test_files = [str(f) for f in tests_dir.rglob("test_*.py")]
        else:
            args.test_files = []
    
    try:
        result = review_tests(args.workspace_id, args.test_files)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
        print(json.dumps(error_result, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
