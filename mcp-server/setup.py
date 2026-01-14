"""setup.py - 确保 Python 版本要求。"""
from setuptools import setup, find_packages
import sys

# 检查 Python 版本
if sys.version_info < (3, 9):
    raise RuntimeError("需要 Python 3.9 或更高版本")

setup(
    name="cursor-agent-orchestrator",
    version="0.1.0",
    description="Cursor Agent Orchestrator MCP Server",
    python_requires=">=3.9",
    packages=find_packages(where="."),
    package_dir={"": "."},
    install_requires=[
        "mcp>=0.1.0",
        "pydantic>=2.0.0",
    ],
)
