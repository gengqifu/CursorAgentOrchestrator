"""配置管理模块 - TDD 第二步：最小实现。

Python 3.9+ 兼容：使用内置类型 dict, list 而非 typing.Dict, typing.List
"""
import os
from pathlib import Path


class Config:
    """统一配置管理。"""
    
    def __init__(self) -> None:
        """初始化配置管理器。"""
        # 工作区根目录
        self.workspace_root = Path(
            os.getenv("AGENT_ORCHESTRATOR_ROOT", os.getcwd())
        )
        
        # Agent Orchestrator 目录
        self.agent_orchestrator_dir = self.workspace_root / ".agent-orchestrator"
        self.agent_orchestrator_dir.mkdir(exist_ok=True)
        
        # 需求工作区目录
        self.requirements_dir = self.agent_orchestrator_dir / "requirements"
        self.requirements_dir.mkdir(exist_ok=True)
        
        # 工作区索引文件
        self.workspace_index_file = self.agent_orchestrator_dir / ".workspace-index.json"
        
        # 终端类型（iTerm 或 terminal）
        self.terminal_type = os.getenv("AGENT_ORCHESTRATOR_TERMINAL", "terminal")
        
        # AI 模型配置
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY", "")
        
        # 重试配置
        self.max_retry_attempts = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
        self.retry_delay = float(os.getenv("RETRY_DELAY", "1.0"))
        
        # Review 循环最大次数
        self.max_review_cycles = int(os.getenv("MAX_REVIEW_CYCLES", "5"))
    
    def get_workspace_path(self, workspace_id: str) -> Path:
        """获取工作区路径。
        
        Args:
            workspace_id: 工作区ID
        
        Returns:
            工作区路径对象
        """
        return self.requirements_dir / workspace_id
    
    def ensure_workspace_exists(self, workspace_id: str) -> Path:
        """确保工作区存在。
        
        Args:
            workspace_id: 工作区ID
        
        Returns:
            工作区路径对象
        """
        workspace_path = self.get_workspace_path(workspace_id)
        workspace_path.mkdir(parents=True, exist_ok=True)
        return workspace_path
