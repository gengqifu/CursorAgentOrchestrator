"""Test Generator Skill 入口脚本。

本脚本是 test-generator skill 的执行入口，由 Agent 根据 SKILL.md 指导调用。

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
from src.tools.test_generator import generate_tests


def main():
    """命令行入口。"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="生成测试 - test-generator skill 入口"
    )
    parser.add_argument("workspace_id", help="工作区 ID")
    parser.add_argument("test_output_dir", nargs="?", help="测试输出目录（可选）")
    
    args = parser.parse_args()
    
    # 如果没有提供 test_output_dir，使用工作区的项目路径下的 tests 目录
    if not args.test_output_dir:
        from src.core.config import Config
        from src.managers.workspace_manager import WorkspaceManager
        
        config = Config()
        workspace_manager = WorkspaceManager(config=config)
        workspace = workspace_manager.get_workspace(args.workspace_id)
        project_path = Path(workspace["project_path"])
        args.test_output_dir = str(project_path / "tests")
    
    try:
        result = generate_tests(args.workspace_id, args.test_output_dir)
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
