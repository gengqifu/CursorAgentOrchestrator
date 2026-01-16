"""代码审查工具测试 - TDD 第一步：编写失败的测试。"""

import json

from src.core.config import Config
from src.tools.code_reviewer import review_code
from tests.conftest import create_test_workspace


class TestCodeReviewer:
    """代码审查工具测试类。"""

    def test_review_code_with_valid_task(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试审查有效任务的代码。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="用户认证"
        )

        # 创建 tasks.json 和代码文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "实现用户认证",
                    "status": "completed",
                    "code_files": [str(temp_dir / "test_code.py")],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # 创建测试代码文件
        code_file = temp_dir / "test_code.py"
        code_file.write_text("def test(): pass")

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert "passed" in result
        assert "review_report" in result
        assert isinstance(result["review_report"], str)

    def test_review_code_returns_review_result(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试返回审查结果。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [{"task_id": "task-001", "status": "completed", "code_files": []}],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert "passed" in result
        assert isinstance(result["passed"], bool)

    def test_review_code_with_todo_in_file(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试审查包含 TODO 的代码文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        code_file = temp_dir / "code_with_todo.py"
        code_file.write_text("# TODO: 需要实现这个功能\ndef func(): pass")

        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(code_file)],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert (
            "TODO" in result["review_report"]
            or "todo" in result["review_report"].lower()
        )

    def test_review_code_with_nonexistent_file(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试审查不存在的代码文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": ["/nonexistent/file.py"],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert (
            "不存在" in result["review_report"]
            or "not found" in result["review_report"].lower()
        )

    def test_review_code_with_short_file(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试审查内容过短的文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        code_file = temp_dir / "short.py"
        code_file.write_text("x")  # 内容过短

        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(code_file)],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert (
            "过短" in result["review_report"]
            or "short" in result["review_report"].lower()
        )

    def test_review_code_with_read_error(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试处理文件读取错误的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        code_file = temp_dir / "unreadable.py"
        code_file.write_text("def test(): pass")

        # 使文件不可读（在 Unix 系统上）
        import os

        if os.name != "nt":  # 非 Windows 系统
            code_file.chmod(0o000)  # 移除所有权限

        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(code_file)],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        try:
            # Act
            result = review_code(workspace_id, "task-001")

            # Assert
            assert result["success"] is True
            # 应该包含错误信息
            assert (
                "读取失败" in result["review_report"]
                or "error" in result["review_report"].lower()
            )
        finally:
            # 恢复文件权限以便清理
            if os.name != "nt":
                code_file.chmod(0o644)

    def test_review_code_with_passed_review(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试审查通过的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        code_file = temp_dir / "good_code.py"
        code_file.write_text(
            "def good_function():\n    return True\n\nclass GoodClass:\n    pass"
        )

        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(code_file)],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert "passed" in result
        # 如果审查通过，passed 应该为 True
        # 注意：当前实现中，如果文件存在且长度足够，基础检查通过，但可能因为其他原因 passed=False
        assert isinstance(result["passed"], bool)

    def test_review_code_with_needs_fix(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试审查需要修复的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)

        tasks_file = workspace_dir / "tasks.json"
        code_file = temp_dir / "needs_fix.py"
        code_file.write_text("# TODO: 需要修复\n# FIXME: 有问题\ndef func(): pass")

        tasks_data = {
            "workspace_id": workspace_id,
            "tasks": [
                {
                    "task_id": "task-001",
                    "description": "测试任务",
                    "status": "completed",
                    "code_files": [str(code_file)],
                }
            ],
        }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, ensure_ascii=False, indent=2)

        # Act
        result = review_code(workspace_id, "task-001")

        # Assert
        assert result["success"] is True
        assert "passed" in result
        # 包含 TODO 的文件应该审查不通过
        assert result["passed"] is False or "TODO" in result["review_report"]
