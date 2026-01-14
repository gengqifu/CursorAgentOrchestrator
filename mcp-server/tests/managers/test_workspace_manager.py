"""工作区管理器测试 - TDD 第一步：编写失败的测试。"""
import pytest
from pathlib import Path
from src.managers.workspace_manager import WorkspaceManager
from src.core.exceptions import WorkspaceNotFoundError, ValidationError
from src.core.config import Config


class TestWorkspaceManager:
    """工作区管理器测试类。"""
    
    @pytest.fixture
    def config(self, temp_dir, monkeypatch):
        """创建测试用配置。"""
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        return Config()
    
    @pytest.fixture
    def manager(self, config):
        """创建工作区管理器实例。"""
        return WorkspaceManager(config=config)
    
    def test_create_workspace_success(self, manager, sample_project_dir):
        """测试成功创建工作区。"""
        # Act
        workspace_id = manager.create_workspace(
            project_path=str(sample_project_dir),
            requirement_name="用户认证功能",
            requirement_url="https://example.com/req"
        )
        
        # Assert
        assert workspace_id is not None
        assert isinstance(workspace_id, str)
        assert len(workspace_id) > 0
        assert workspace_id.startswith("req-")
    
    def test_create_workspace_with_invalid_path(self, manager):
        """测试使用无效路径创建工作区应该失败。"""
        # Act & Assert
        with pytest.raises(ValidationError):
            manager.create_workspace(
                project_path="/nonexistent/path",
                requirement_name="测试需求",
                requirement_url="https://example.com/req"
            )
    
    def test_create_workspace_with_file_path_not_directory(self, manager, temp_dir):
        """测试项目路径是文件不是目录应该失败。"""
        # Arrange
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")
        
        # Act & Assert
        with pytest.raises(ValidationError):
            manager.create_workspace(
                project_path=str(file_path),
                requirement_name="测试需求",
                requirement_url="https://example.com/req"
            )
    
    def test_get_workspace_success(self, manager, sample_project_dir):
        """测试成功获取工作区。"""
        # Arrange
        workspace_id = manager.create_workspace(
            project_path=str(sample_project_dir),
            requirement_name="测试需求",
            requirement_url="https://example.com/req"
        )
        
        # Act
        workspace = manager.get_workspace(workspace_id)
        
        # Assert
        assert workspace is not None
        assert workspace["workspace_id"] == workspace_id
        assert workspace["requirement_name"] == "测试需求"
        assert workspace["requirement_url"] == "https://example.com/req"
    
    def test_get_workspace_not_found_raises_exception(self, manager):
        """测试获取不存在的工作区抛出异常。"""
        # Act & Assert
        with pytest.raises(WorkspaceNotFoundError) as exc_info:
            manager.get_workspace("non_existent_id")
        
        assert "non_existent_id" in str(exc_info.value)
    
    def test_get_workspace_status_returns_status(self, manager, sample_project_dir):
        """测试获取工作区状态。"""
        # Arrange
        workspace_id = manager.create_workspace(
            project_path=str(sample_project_dir),
            requirement_name="测试需求",
            requirement_url="https://example.com/req"
        )
        
        # Act
        status = manager.get_workspace_status(workspace_id)
        
        # Assert
        assert isinstance(status, dict)
        assert "prd_status" in status
        assert "trd_status" in status
        assert "tasks_status" in status
    
    def test_load_workspace_index_loads_existing_index(self, temp_dir, monkeypatch):
        """测试加载已存在的工作区索引文件。"""
        # Arrange
        monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
        import json
        from src.core.config import Config
        from src.managers.workspace_manager import WorkspaceManager
        
        # 创建索引文件
        config = Config()
        index_file = config.workspace_index_file
        index_file.parent.mkdir(parents=True, exist_ok=True)
        test_index = {
            "test-workspace-001": {
                "workspace_id": "test-workspace-001",
                "project_path": str(temp_dir / "test_project"),
                "requirement_name": "测试需求",
                "created_at": "2024-01-01T00:00:00"
            }
        }
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(test_index, f, ensure_ascii=False, indent=2)
        
        # 创建测试项目目录
        test_project_dir = temp_dir / "test_project"
        test_project_dir.mkdir()
        
        # Act - 重新创建管理器以触发索引加载
        new_manager = WorkspaceManager(config=config)
        
        # Assert - 验证索引被加载（通过创建新工作区后检查索引文件）
        workspace_id = new_manager.create_workspace(
            project_path=str(test_project_dir),
            requirement_name="新需求",
            requirement_url="https://example.com/new"
        )
        
        # 验证索引文件包含新旧工作区
        with open(index_file, 'r', encoding='utf-8') as f:
            loaded_index = json.load(f)
        
        assert "test-workspace-001" in loaded_index
        assert workspace_id in loaded_index
