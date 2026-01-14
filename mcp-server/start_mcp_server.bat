@echo off
REM Agent Orchestrator MCP Server 启动脚本（Windows）
REM 用于 Cursor IDE 集成

cd /d "%~dp0"

REM 检查 Python 版本
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python >&2
    exit /b 1
)

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 设置环境变量
if not defined AGENT_ORCHESTRATOR_ROOT (
    set "AGENT_ORCHESTRATOR_ROOT=%~dp0.."
)
set "PYTHONPATH=%~dp0;%PYTHONPATH%"

REM 运行 MCP Server
python src\main.py
