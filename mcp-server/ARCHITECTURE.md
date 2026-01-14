# Agent Orchestrator 架构设计

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Cursor IDE                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              MCP Client                               │  │
│  │  - 工具调用                                            │  │
│  │  - 上下文管理                                          │  │
│  └──────────────────┬─────────────────────────────────────┘  │
└─────────────────────┼─────────────────────────────────────────┘
                      │ stdio (JSON-RPC)
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│           Agent Orchestrator MCP Server                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    Core Layer                          │  │
│  │  - Config (配置管理)                                   │  │
│  │  - Logger (日志系统)                                    │  │
│  │  - Exceptions (异常处理)                                │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                 Manager Layer                          │  │
│  │  - WorkspaceManager (工作区管理)                        │  │
│  │  - TaskManager (任务管理)                               │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                  Tools Layer                           │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │PRD Gen.  │ │TRD Gen.  │ │Task Dec.│ │Code Gen. │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │  │
│  │  │Code Rev. │ │Test Gen. │ │Test Rev. │ │Coverage  │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                      │
                      │ 文件系统操作
                      │ Git 操作
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│                   项目代码仓库                                │
│  - 源代码文件                                                │
│  - 测试文件                                                  │
│  - 文档文件                                                  │
│  - Git 历史                                                  │
└───────────────────────────────────────────────────────────────┘
```

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

### 3. 代码生成流程

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
    "tasks_json_path": ".agent-orchestrator/requirements/req-xxx/tasks.json"
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

### MCP 协议调用

```
Cursor IDE
    ↓ JSON-RPC Request
MCP Server (main.py)
    ↓ 解析请求
Tool Router
    ↓ 调用对应工具
SKILL Tool (e.g., generate_prd)
    ↓ 使用 Manager
WorkspaceManager / TaskManager
    ↓ 文件系统操作
项目文件系统
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
