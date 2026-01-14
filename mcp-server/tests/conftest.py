"""pytest 配置和共享 fixtures。"""
import pytest
import sys
from pathlib import Path
from typing import Generator
import tempfile
import shutil


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
