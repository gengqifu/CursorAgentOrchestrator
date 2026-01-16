"""总编排器询问工具测试 - TDD 第一步：编写失败的测试。"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import ValidationError
from src.tools.orchestrator_questions import (
    ask_orchestrator_questions,
    submit_orchestrator_answers,
)


class TestOrchestratorQuestions:
    """总编排器询问工具测试类。"""

    def test_ask_orchestrator_questions(self):
        """测试询问问题。

        验证返回的字典包含所有必需字段，questions 列表包含4个问题，
        每个问题包含 id, question, type, required, placeholder。
        """
        # Act
        result = ask_orchestrator_questions()

        # Assert
        assert result["success"] is True
        assert result["interaction_required"] is True
        assert result["interaction_type"] == "questions"
        assert "questions" in result
        assert len(result["questions"]) == 4

        # 验证每个问题的结构
        questions = result["questions"]
        required_fields = ["id", "question", "type", "required", "placeholder"]

        for question in questions:
            for field in required_fields:
                assert field in question, f"问题缺少字段: {field}"

        # 验证问题ID
        question_ids = [q["id"] for q in questions]
        assert "project_path" in question_ids
        assert "requirement_name" in question_ids
        assert "requirement_url" in question_ids
        assert "workspace_path" in question_ids

        # 验证必填字段
        project_path_q = next(q for q in questions if q["id"] == "project_path")
        requirement_name_q = next(q for q in questions if q["id"] == "requirement_name")
        requirement_url_q = next(q for q in questions if q["id"] == "requirement_url")
        workspace_path_q = next(q for q in questions if q["id"] == "workspace_path")

        assert project_path_q["required"] is True
        assert requirement_name_q["required"] is True
        assert requirement_url_q["required"] is True
        assert workspace_path_q["required"] is False

    def test_submit_orchestrator_answers_success(
        self, temp_dir, monkeypatch, workspace_manager, sample_project_dir
    ):
        """测试提交答案成功。

        验证成功创建时返回 workspace_id。
        """
        # Arrange
        answers = {
            "project_path": str(sample_project_dir),
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/requirement.md",
            "workspace_path": None,  # 可选字段
        }

        # Act
        result = submit_orchestrator_answers(answers)

        # Assert
        assert result["success"] is True
        assert "workspace_id" in result
        assert result["workspace_id"].startswith("req-")

        # 验证工作区已创建
        workspace_id = result["workspace_id"]
        workspace = workspace_manager.get_workspace(workspace_id)
        assert workspace["workspace_id"] == workspace_id
        assert workspace["requirement_name"] == "测试需求"
        assert workspace["requirement_url"] == "https://example.com/requirement.md"

    def test_submit_orchestrator_answers_missing_required(self):
        """测试缺少必填项。

        验证缺少必填字段时抛出 ValidationError。
        """
        # Test missing project_path
        with pytest.raises(ValidationError, match="必填字段缺失或为空: project_path"):
            submit_orchestrator_answers(
                {
                    "requirement_name": "测试需求",
                    "requirement_url": "https://example.com/requirement.md",
                }
            )

        # Test missing requirement_name
        with pytest.raises(
            ValidationError, match="必填字段缺失或为空: requirement_name"
        ):
            submit_orchestrator_answers(
                {
                    "project_path": "/tmp",
                    "requirement_url": "https://example.com/requirement.md",
                }
            )

        # Test missing requirement_url
        with pytest.raises(
            ValidationError, match="必填字段缺失或为空: requirement_url"
        ):
            submit_orchestrator_answers(
                {"project_path": "/tmp", "requirement_name": "测试需求"}
            )

        # Test empty project_path
        with pytest.raises(ValidationError, match="必填字段缺失或为空: project_path"):
            submit_orchestrator_answers(
                {
                    "project_path": "",
                    "requirement_name": "测试需求",
                    "requirement_url": "https://example.com/requirement.md",
                }
            )

        # Test empty requirement_name
        with pytest.raises(
            ValidationError, match="必填字段缺失或为空: requirement_name"
        ):
            submit_orchestrator_answers(
                {
                    "project_path": "/tmp",
                    "requirement_name": "",
                    "requirement_url": "https://example.com/requirement.md",
                }
            )

        # Test empty requirement_url
        with pytest.raises(
            ValidationError, match="必填字段缺失或为空: requirement_url"
        ):
            submit_orchestrator_answers(
                {
                    "project_path": "/tmp",
                    "requirement_name": "测试需求",
                    "requirement_url": "",
                }
            )

    def test_submit_orchestrator_answers_invalid_path(self, temp_dir):
        """测试无效路径。

        验证无效路径时抛出 ValidationError。
        """
        # Test non-existent path
        with pytest.raises(ValidationError, match="项目路径不存在"):
            submit_orchestrator_answers(
                {
                    "project_path": "/nonexistent/path",
                    "requirement_name": "测试需求",
                    "requirement_url": "https://example.com/requirement.md",
                }
            )

        # Test file instead of directory
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test")

        with pytest.raises(ValidationError, match="项目路径不是目录"):
            submit_orchestrator_answers(
                {
                    "project_path": str(test_file),
                    "requirement_name": "测试需求",
                    "requirement_url": "https://example.com/requirement.md",
                }
            )

    def test_submit_orchestrator_answers_workspace_creation_error(
        self, temp_dir, sample_project_dir
    ):
        """测试创建工作区时发生异常。

        验证当 WorkspaceManager.create_workspace 抛出非 ValidationError 异常时，
        会被捕获并转换为 ValidationError。
        """
        # Arrange
        answers = {
            "project_path": str(sample_project_dir),
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/requirement.md",
        }

        # Mock WorkspaceManager.create_workspace 抛出异常
        with patch(
            "src.tools.orchestrator_questions.WorkspaceManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.create_workspace.side_effect = RuntimeError("创建工作区失败")

            # Act & Assert
            with pytest.raises(ValidationError, match="创建工作区失败: 创建工作区失败"):
                submit_orchestrator_answers(answers)

    def test_submit_orchestrator_answers_workspace_manager_validation_error(
        self, temp_dir, sample_project_dir
    ):
        """测试 WorkspaceManager.create_workspace 抛出 ValidationError。

        验证当 WorkspaceManager.create_workspace 抛出 ValidationError 时，
        会被重新抛出（不转换）。
        """
        # Arrange
        answers = {
            "project_path": str(sample_project_dir),
            "requirement_name": "测试需求",
            "requirement_url": "https://example.com/requirement.md",
        }

        # Mock WorkspaceManager.create_workspace 抛出 ValidationError
        with patch(
            "src.tools.orchestrator_questions.WorkspaceManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            original_error = ValidationError("WorkspaceManager 验证失败")
            mock_manager.create_workspace.side_effect = original_error

            # Act & Assert
            with pytest.raises(
                ValidationError, match="WorkspaceManager 验证失败"
            ) as exc_info:
                submit_orchestrator_answers(answers)

            # 验证是同一个异常对象（重新抛出）
            assert exc_info.value is original_error
