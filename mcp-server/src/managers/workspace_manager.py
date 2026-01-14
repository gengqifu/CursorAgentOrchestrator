"""工作区管理器 - TDD 第二步：最小实现。

Python 3.9+ 兼容：使用内置类型 dict 而非 typing.Dict
"""
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.core.config import Config
from src.core.logger import setup_logger
from src.core.exceptions import WorkspaceNotFoundError, ValidationError

logger = setup_logger(__name__)


class WorkspaceManager:
    """工作区管理器。"""
    
    def __init__(self, config: Optional[Config] = None) -> None:
        """初始化工作区管理器。
        
        Args:
            config: 配置管理器，如果为 None 则创建默认配置
        """
        self.config = config or Config()
        self._load_workspace_index()
    
    def _load_workspace_index(self) -> dict:
        """加载工作区索引。"""
        if self.config.workspace_index_file.exists():
            with open(self.config.workspace_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_workspace_index(self, index: dict) -> None:
        """保存工作区索引。"""
        with open(self.config.workspace_index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _validate_project_path(self, project_path: str) -> Path:
        """验证并返回项目路径对象。"""
        path = Path(project_path)
        if not path.exists():
            raise ValidationError(f"Project path does not exist: {project_path}")
        if not path.is_dir():
            raise ValidationError(f"Project path is not a directory: {project_path}")
        return path.absolute()
    
    def _generate_workspace_id(self, requirement_name: str) -> str:
        """生成工作区ID。"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_name = requirement_name[:20].replace(' ', '-')
        return f"req-{timestamp}-{safe_name}"
    
    def create_workspace(
        self,
        project_path: str,
        requirement_name: str,
        requirement_url: str
    ) -> str:
        """创建工作区。
        
        Args:
            project_path: 项目路径
            requirement_name: 需求名称
            requirement_url: 需求URL
        
        Returns:
            工作区ID
        
        Raises:
            ValidationError: 当项目路径无效时
        """
        # 验证项目路径
        validated_path = self._validate_project_path(project_path)
        
        # 生成工作区ID
        workspace_id = self._generate_workspace_id(requirement_name)
        
        # 创建工作区目录
        workspace_dir = self.config.ensure_workspace_exists(workspace_id)
        
        # 创建工作区元数据
        workspace_meta = {
            "workspace_id": workspace_id,
            "project_path": str(validated_path),
            "requirement_name": requirement_name,
            "requirement_url": requirement_url,
            "created_at": datetime.now().isoformat(),
            "status": {
                "prd_status": "pending",
                "trd_status": "pending",
                "tasks_status": "pending",
                "code_status": "pending",
                "test_status": "pending"
            },
            "files": {
                "prd_path": None,
                "trd_path": None,
                "tasks_json_path": None
            }
        }
        
        # 保存工作区元数据
        meta_file = workspace_dir / "workspace.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(workspace_meta, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        index = self._load_workspace_index()
        index[workspace_id] = {
            "workspace_id": workspace_id,
            "project_path": str(validated_path),
            "requirement_name": requirement_name,
            "created_at": workspace_meta["created_at"]
        }
        self._save_workspace_index(index)
        
        logger.info(f"创建工作区: {workspace_id}")
        return workspace_id
    
    def get_workspace(self, workspace_id: str) -> dict:
        """获取工作区信息。
        
        Args:
            workspace_id: 工作区ID
        
        Returns:
            工作区信息字典
        
        Raises:
            WorkspaceNotFoundError: 当工作区不存在时
        """
        workspace_dir = self.config.get_workspace_path(workspace_id)
        meta_file = workspace_dir / "workspace.json"
        
        if not meta_file.exists():
            raise WorkspaceNotFoundError(f"Workspace not found: {workspace_id}")
        
        with open(meta_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_workspace_status(self, workspace_id: str) -> dict:
        """获取工作区状态。
        
        Args:
            workspace_id: 工作区ID
        
        Returns:
            工作区状态字典
        """
        workspace = self.get_workspace(workspace_id)
        return workspace.get("status", {})
