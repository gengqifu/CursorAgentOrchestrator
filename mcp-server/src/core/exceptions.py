"""异常定义 - TDD 第二步：最小实现。

Python 3.9+ 兼容
"""


class AgentOrchestratorError(Exception):
    """基础异常类。"""

    pass


class WorkspaceNotFoundError(AgentOrchestratorError):
    """工作区不存在异常。"""

    pass


class WorkspaceAlreadyExistsError(AgentOrchestratorError):
    """工作区已存在异常。"""

    pass


class TaskNotFoundError(AgentOrchestratorError):
    """任务不存在异常。"""

    pass


class ValidationError(AgentOrchestratorError):
    """参数验证错误异常。"""

    pass


class ToolExecutionError(AgentOrchestratorError):
    """工具执行错误异常。"""

    pass


class GitError(AgentOrchestratorError):
    """Git 操作错误异常。"""

    pass
