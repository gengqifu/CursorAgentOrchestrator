"""pytest 配置和共享 fixtures。"""

import shutil
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.core.config import Config
from src.managers.workspace_manager import WorkspaceManager


# 确保使用 Python 3.9+
@pytest.fixture(scope="session", autouse=True)
def check_python_version():
    """检查 Python 版本是否符合要求。"""
    if sys.version_info < (3, 9):
        pytest.skip(f"需要 Python 3.9+，当前版本: {sys.version}")


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录用于测试。"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_project_dir(temp_dir: Path) -> Path:
    """创建示例项目目录。"""
    project_dir = temp_dir / "sample_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def workspace_manager(temp_dir, monkeypatch):
    """创建工作区管理器实例。"""
    monkeypatch.setenv("AGENT_ORCHESTRATOR_ROOT", str(temp_dir))
    config = Config()
    return WorkspaceManager(config=config)


def create_test_workspace(
    workspace_manager: WorkspaceManager,
    project_dir: Path,
    workspace_id: str = None,  # type: ignore
    requirement_name: str = "测试需求",
    requirement_url: str = "https://example.com/test",
) -> str:
    """创建测试工作区的辅助函数。

    Args:
        workspace_manager: 工作区管理器实例
        project_dir: 项目目录
        workspace_id: 可选的工作区ID（如果不提供则自动生成）
        requirement_name: 需求名称
        requirement_url: 需求URL

    Returns:
        工作区ID
    """
    # 确保项目目录存在
    project_dir.mkdir(parents=True, exist_ok=True)

    # 创建工作区
    workspace_id = workspace_manager.create_workspace(
        project_path=str(project_dir),
        requirement_name=requirement_name,
        requirement_url=requirement_url,
    )

    return workspace_id


@pytest.fixture
def create_test_workspace_fixture(temp_dir, sample_project_dir, workspace_manager):
    """创建测试工作区的 fixture。"""
    return create_test_workspace(
        workspace_manager=workspace_manager, project_dir=sample_project_dir
    )
