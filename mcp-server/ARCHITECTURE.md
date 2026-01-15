# Agent Orchestrator 架构设计

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Cursor CLI (用户界面)                     │
│  - 命令行接口                                                │
│  - Cursor IDE 集成                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              MCP Server (中央编排服务)                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              总编排器                                   │  │
│  │  - 接收 MCP 请求                                        │  │
│  │  - 路由到对应的工具                                      │  │
│  └──────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────┴─────────────────────────────────────┐  │
│  │              MCP 工具层                                 │  │
│  │  - 基础设施工具：工作区管理、任务管理                    │  │
│  │  - 工作流编排工具：用户交互、确认循环                    │  │
│  │  - SKILL 工具：8 个核心 SKILL 模块                      │  │
│  └──────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────┴─────────────────────────────────────┐  │
│  │              业务管理器层                               │  │
│  │  - WorkspaceManager (工作区管理)                        │  │
│  │  - TaskManager (任务管理)                               │  │
│  └──────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────┴─────────────────────────────────────┐  │
│  │              基础设施层                                 │  │
│  │  - Config (配置管理)                                    │  │
│  │  - Logger (日志系统)                                    │  │
│  │  - Exceptions (异常处理)                                │  │
│  │  - FileLock (文件锁)                                    │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────┬─────────────────────────────────────────┘
                      ↓
┌─────────────────────▼─────────────────────────────────────────┐
│                    8个子SKILL模块                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │PRD生成   │ │TRD生成   │ │任务分解  │ │代码生成  │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │代码审查  │ │测试生成  │ │测试审查  │ │覆盖率分析│        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                              │
│  核心实现：mcp-server/src/tools/*.py                        │
└─────────────────────┬─────────────────────────────────────────┘
                      ↓
┌─────────────────────▼─────────────────────────────────────────┐
│                    项目代码仓库                              │
│  - 源代码文件                                                │
│  - 测试文件                                                  │
│  - 文档文件                                                  │
│  - Git 历史                                                  │
└───────────────────────────────────────────────────────────────┘
```

**架构说明**（符合 PDF 文档）：
- **Cursor CLI**：用户界面层（命令行或 Cursor IDE），对应 PDF 中的 "Kiro CLI"
- **MCP Server**：中央编排服务，通过 MCP 协议暴露所有工具（基础设施工具 + 8 个 SKILL 工具）
- **8个子SKILL模块**：核心业务逻辑，通过 MCP Server 调用，对应 PDF 中的 "8个子SKILL模块"
- **项目代码仓库**：目标项目文件系统

## 数据流

### 1. 工作区创建流程

```
用户请求 → WorkspaceManager.create_workspace()
    ↓
创建 .agent-orchestrator/requirements/{workspace_id}/
    ↓
创建 workspace.json (元数据)
    ↓
更新 .workspace-index.json
    ↓
返回 workspace_id
```

### 2. PRD 生成流程

```
用户请求 → PRDGenerator.generate_prd()
    ↓
读取需求文档 (URL 或文件)
    ↓
生成 PRD 内容
    ↓
保存 PRD.md
    ↓
更新 workspace.json
    ↓
更新工作区状态
```

### 3. 任务执行流程

```
用户请求 → TaskExecutor.execute_task()
    ↓
获取任务信息 (TaskManager)
    ↓
Review 循环开始
    ├─ 生成代码 (CodeGenerator.generate_code())
    ├─ Review 代码 (CodeReviewer.review_code())
    ├─ 判断是否通过
    ├─ 如果未通过，重试（最多 max_review_retries 次）
    └─ 如果通过，返回成功
    ↓
更新任务状态
    ↓
返回执行结果
```

### 4. 代码生成流程

```
用户请求 → CodeGenerator.generate_code()
    ↓
获取任务信息 (TaskManager)
    ↓
调用 AI API (TODO: 集成 Cursor AI)
    ↓
生成代码文件
    ↓
生成测试文件
    ↓
更新任务状态
    ↓
返回文件路径列表
```

## 目录结构

```
.agent-orchestrator/
├── .workspace-index.json      # 工作区索引
└── requirements/
    └── {workspace_id}/
        ├── workspace.json     # 工作区元数据
        ├── PRD.md             # PRD 文档
        ├── TRD.md             # TRD 文档
        ├── tasks.json         # 任务列表
        └── coverage_report/   # 覆盖率报告
```

## 工作区元数据格式

```json
{
  "workspace_id": "req-20240101-120000-user-auth",
  "project_path": "/path/to/project",
  "requirement_name": "用户认证功能",
  "requirement_url": "https://example.com/req",
  "created_at": "2024-01-01T12:00:00",
  "status": {
    "prd_status": "completed",
    "trd_status": "completed",
    "tasks_status": "completed",
    "code_status": "in_progress",
    "test_status": "pending"
  },
  "files": {
    "prd_path": ".agent-orchestrator/requirements/req-xxx/PRD.md",
    "trd_path": ".agent-orchestrator/requirements/req-xxx/TRD.md",
    "tasks_json_path": ".agent-orchestrator/requirements/req-xxx/tasks.json",
    "test_path": "/path/to/project/tests/mock"
  }
}
```

## 任务格式

```json
{
  "workspace_id": "req-xxx",
  "tasks": [
    {
      "task_id": "task-001",
      "description": "实现用户登录功能",
      "status": "completed",
      "code_files": [
        "src/auth/login.py",
        "tests/test_login.py"
      ],
      "review_passed": true,
      "review_report": "..."
    }
  ]
}
```

## 工具调用流程

### MCP Server 工具调用流程（符合 PDF 架构）

```
用户请求（Cursor CLI / Cursor IDE）
    ↓
MCP Client (JSON-RPC)
    ↓
MCP Server (中央编排服务)
    ↓ 路由到对应工具
MCP 工具层
    ├─ 基础设施工具 (create_workspace, get_workspace 等)
    ├─ 工作流编排工具 (orchestrator_questions, prd_confirmation, trd_confirmation, test_path_question, task_executor)
    └─ SKILL 工具 (generate_prd, generate_trd 等)
        ↓ 调用核心实现
mcp-server/src/tools/*.py (工作流编排工具 + 8个子SKILL模块)
    ↓ 使用 Manager
WorkspaceManager / TaskManager
    ↓ 文件系统操作
项目文件系统
```

### 示例：生成 PRD

```
用户: "为工作区 req-001 生成 PRD，需求文档在 /path/to/req.md"
    ↓
Cursor IDE / MCP Client
    ↓ 调用 MCP 工具
MCP Server.call_tool("generate_prd", {
    "workspace_id": "req-001",
    "requirement_url": "/path/to/req.md"
})
    ↓ 调用核心实现
src.tools.prd_generator.generate_prd(...)
    ↓ 使用 Manager
WorkspaceManager.get_workspace(...)
    ↓ 文件系统操作
保存 PRD.md 到工作区目录
```

### 示例：执行任务

```
用户: "为工作区 req-001 执行任务 task-001"
    ↓
Cursor IDE / MCP Client
    ↓ 调用 MCP 工具
MCP Server.call_tool("execute_task", {
    "workspace_id": "req-001",
    "task_id": "task-001",
    "max_review_retries": 3
})
    ↓ 调用核心实现
src.tools.task_executor.execute_task(...)
    ↓ Review 循环
    ├─ CodeGenerator.generate_code(...)
    ├─ CodeReviewer.review_code(...)
    ├─ 如果未通过，重试（最多 max_review_retries 次）
    └─ 如果通过，返回成功
    ↓ 使用 Manager
TaskManager.update_task_status(...)
    ↓ 文件系统操作
更新任务状态到 tasks.json
```

## 错误处理

### 异常层次结构

```
Exception
├── ValidationError          # 参数验证错误
├── WorkspaceNotFoundError   # 工作区不存在
├── TaskNotFoundError        # 任务不存在
└── ToolExecutionError       # 工具执行错误
```

### 错误处理流程

```
工具执行
    ↓
捕获异常
    ↓
记录日志
    ↓
返回错误响应
    ↓
Cursor 显示错误信息
```

## 配置管理

### 环境变量

- `AGENT_ORCHESTRATOR_ROOT`: 工作区根目录
- `GEMINI_API_KEY`: Gemini API 密钥
- `CLAUDE_API_KEY`: Claude API 密钥
- `MAX_RETRY_ATTEMPTS`: 最大重试次数
- `MAX_REVIEW_CYCLES`: 最大审查循环次数

### 配置文件

- `workspace.json`: 工作区元数据
- `.workspace-index.json`: 工作区索引
- `tasks.json`: 任务列表

## 安全考虑

1. **文件权限**: 工作区文件使用适当的文件权限
2. **路径验证**: 所有路径都经过验证，防止路径遍历攻击
3. **API 密钥**: 通过环境变量管理，不存储在代码中
4. **输入验证**: 所有用户输入都经过验证和清理

## 性能优化

1. **缓存**: 工作区元数据缓存
2. **异步处理**: 长时间运行的任务使用异步处理
3. **批量操作**: 支持批量任务处理
4. **资源清理**: 及时释放文件句柄和锁

## 扩展性

### 添加新工具

1. 在 `src/tools/` 创建新工具文件
2. 实现工具函数
3. 在 MCP Server 中注册工具
4. 添加测试用例

### 添加新 Manager

1. 在 `src/managers/` 创建新 Manager
2. 实现 Manager 类
3. 在工具中使用 Manager
4. 添加测试用例

## 未来改进

- [ ] 实现 FastMCP 集成
- [ ] 添加 AI API 集成（Gemini, Claude）
- [ ] 实现并发任务处理
- [ ] 添加 Web UI 界面
- [ ] 实现实时进度通知
- [ ] 添加更多代码生成模板
