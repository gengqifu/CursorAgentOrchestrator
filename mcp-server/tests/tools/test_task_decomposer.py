"""任务分解工具测试 - TDD 第一步：编写失败的测试。"""

import json
from pathlib import Path

import pytest

from src.core.config import Config
from src.core.exceptions import ValidationError
from src.tools.task_decomposer import decompose_tasks
from tests.conftest import create_test_workspace


class TestTaskDecomposer:
    """任务分解工具测试类。"""

    def test_decompose_tasks_with_valid_trd(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用有效 TRD 分解任务。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        # 创建测试 TRD 文件
        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD: 测试需求\n\n## 实现方案\n\n### 功能1\n### 功能2")

        # ✅ 新增：更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Act
        result = decompose_tasks(workspace_id, str(trd_file))

        # Assert
        assert result["success"] is True
        assert "tasks_json_path" in result
        tasks_file = Path(result["tasks_json_path"])
        assert tasks_file.exists()

        # 验证 tasks.json 内容
        with open(tasks_file, encoding="utf-8") as f:
            tasks_data = json.load(f)
        assert "tasks" in tasks_data
        assert isinstance(tasks_data["tasks"], list)
        assert len(tasks_data["tasks"]) > 0

    def test_decompose_tasks_with_invalid_trd_path(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用无效 TRD 路径应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )
        trd_path = "/nonexistent/trd.md"

        # Act & Assert
        with pytest.raises(ValidationError):
            decompose_tasks(workspace_id, trd_path)

    def test_decompose_tasks_creates_valid_tasks_json(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试生成有效的 tasks.json 文件。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD\n\n## 实现方案\n\n需要实现功能A和功能B")

        # ✅ 新增：更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Act
        result = decompose_tasks(workspace_id, str(trd_file))

        # Assert
        tasks_file = Path(result["tasks_json_path"])
        with open(tasks_file, encoding="utf-8") as f:
            tasks_data = json.load(f)

        # 验证任务结构
        for task in tasks_data["tasks"]:
            assert "task_id" in task
            assert "description" in task
            assert "status" in task
            assert task["status"] == "pending"

    def test_decompose_tasks_with_empty_trd(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试使用空 TRD 文件的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("")  # 空文件

        # ✅ 新增：更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Act
        result = decompose_tasks(workspace_id, str(trd_file))

        # Assert
        assert result["success"] is True
        assert "tasks_json_path" in result
        tasks_file = Path(result["tasks_json_path"])
        assert tasks_file.exists()

        # 应该创建默认任务
        with open(tasks_file, encoding="utf-8") as f:
            tasks_data = json.load(f)
        assert "tasks" in tasks_data
        assert len(tasks_data["tasks"]) > 0  # 应该有默认任务

    def test_decompose_tasks_with_trd_containing_features(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试 TRD 包含功能点的情况。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text(
            """# TRD

## 实现方案

### 功能1：用户登录
需要实现用户登录功能，包括用户名密码验证。

### 功能2：用户注册
需要实现用户注册功能，包括表单验证。

### 功能3：密码重置
需要实现密码重置功能。
"""
        )

        # ✅ 新增：更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Act
        result = decompose_tasks(workspace_id, str(trd_file))

        # Assert
        assert result["success"] is True
        tasks_file = Path(result["tasks_json_path"])
        with open(tasks_file, encoding="utf-8") as f:
            tasks_data = json.load(f)

        # 应该提取到多个任务
        assert len(tasks_data["tasks"]) >= 3
        task_descriptions = [task["description"] for task in tasks_data["tasks"]]
        # 检查是否包含功能描述
        assert any(
            "登录" in desc or "注册" in desc or "重置" in desc
            for desc in task_descriptions
        )

    def test_decompose_tasks_with_trd_not_completed(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试TRD未完成时分解任务应该失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD: 测试需求")

        # TRD状态保持为 pending（默认状态）

        # Act & Assert
        with pytest.raises(ValidationError, match="TRD尚未完成"):
            decompose_tasks(workspace_id, str(trd_file))

    def test_decompose_tasks_with_trd_path_from_workspace(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试从工作区获取TRD路径分解任务。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD: 测试需求\n\n## 实现方案\n\n### 功能1")

        # 更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # 更新工作区文件路径
        from src.utils.file_lock import file_lock

        meta_file = workspace_dir / "workspace.json"
        with file_lock(meta_file):
            with open(meta_file, encoding="utf-8") as f:
                workspace = json.load(f)
            workspace["files"]["trd_path"] = str(trd_file)
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(workspace, f, ensure_ascii=False, indent=2)

        # Act - 不提供 trd_path，应该从工作区获取
        result = decompose_tasks(workspace_id)

        # Assert
        assert result["success"] is True
        assert "tasks_json_path" in result
        assert Path(result["tasks_json_path"]).exists()

    def test_decompose_tasks_marks_status_in_progress(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试分解任务时标记状态为进行中。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD: 测试需求\n\n## 实现方案\n\n### 功能1")

        # 更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Act
        result = decompose_tasks(workspace_id, str(trd_file))

        # Assert
        assert result["success"] is True
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["status"]["tasks_status"] == "completed"

    def test_decompose_tasks_marks_status_failed_on_error(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试分解任务失败时标记状态为失败。"""
        # Arrange
        workspace_id = create_test_workspace(
            workspace_manager, sample_project_dir, requirement_name="测试需求"
        )

        config = Config()
        workspace_dir = config.get_workspace_path(workspace_id)
        trd_file = workspace_dir / "TRD.md"
        trd_file.write_text("# TRD: 测试需求")

        # 更新TRD状态为已完成
        workspace_manager.update_workspace_status(
            workspace_id, {"trd_status": "completed"}
        )

        # Mock _decompose_tasks_from_trd 抛出异常（模拟任务分解失败）
        from unittest.mock import patch

        with patch(
            "src.tools.task_decomposer._decompose_tasks_from_trd",
            side_effect=ValueError("任务分解失败"),
        ):
            # Act & Assert
            with pytest.raises(ValueError):
                decompose_tasks(workspace_id, str(trd_file))

            # 验证状态被标记为失败
            workspace = workspace_manager.get_workspace(workspace_id)
            assert workspace["status"]["tasks_status"] == "failed"
