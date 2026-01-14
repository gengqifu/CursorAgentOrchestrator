"""Task Decomposer Skill 入口脚本。

本脚本是 task-decomposer skill 的执行入口，由 Agent 根据 SKILL.md 指导调用。

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
from src.tools.task_decomposer import decompose_tasks


def main():
    """命令行入口。"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="分解任务 - task-decomposer skill 入口"
    )
    parser.add_argument("workspace_id", help="工作区 ID")
    parser.add_argument("trd_path", nargs="?", help="TRD 文档路径（可选，默认使用工作区的 TRD.md）")
    
    args = parser.parse_args()
    
    # 如果没有提供 trd_path，使用工作区的默认 TRD.md
    if not args.trd_path:
        from src.core.config import Config
        config = Config()
        workspace_dir = config.get_workspace_path(args.workspace_id)
        args.trd_path = str(workspace_dir / "TRD.md")
    
    try:
        result = decompose_tasks(args.workspace_id, args.trd_path)
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
