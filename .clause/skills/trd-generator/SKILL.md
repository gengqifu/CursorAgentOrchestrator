---
name: trd-generator
description: >
  生成技术设计文档（TRD）的技能。使用当你已经有标准化 PRD 文档和项目代码仓库，
  需要为某个工作区生成 TRD.md，并更新工作区状态与元数据，用于后续任务分解与实现。
---

# TRD Generator Skill

本 Skill 指导一个具备文件系统访问与 Python 运行环境的 Agent（例如 Cursor 中的
Agent Orchestrator），基于现有实现 `mcp-server/src/tools/trd_generator.py`，
为指定工作区生成技术设计文档（TRD.md）。

> 重点：**本 Skill 说明“如何正确调用 TRD 生成逻辑”，而不是重写逻辑本身。**

---

## 一、适用场景

在以下场景应优先使用本 Skill：

- 已经完成 PRD 生成（`PRD.md` 存在且基本可用）
- 工作区已绑定到一个实际的项目代码仓库（`workspace["project_path"]` 有效）
- 希望生成一份初步的 TRD 草稿，包含：
  - 技术栈信息（语言、框架）
  - 现有代码库的顶层目录结构
  - 标准 TRD 章节骨架（架构设计、接口设计、实现方案、测试策略、风险评估等）

不适用的情况：

- 尚未生成 PRD（没有 `PRD.md`）
- 工作区没有有效的 `project_path`（未指向真实代码仓库）
- 只是需要对现有 TRD 做小幅编辑（可以直接编辑文件，无需重新生成）

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

假设项目根目录为 `CursorAgentOrchestrator/`：

- **MCP 工具名称**：`generate_trd`
- **核心实现**：`mcp-server/src/tools/trd_generator.py`
- **MCP Server 实现**：`mcp-server/src/mcp_server.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/trd_generator.py`：保留用于向后兼容（已弃用，应通过 MCP Server 调用）

### 2. 工作区结构

本 Skill 与 PRD Skill 共用统一的工作区结构（由 `WorkspaceManager` 管理）：

```text
<AGENT_ORCHESTRATOR_ROOT>/
└── .agent-orchestrator/
    ├── .workspace-index.json
    └── requirements/
        └── {workspace_id}/
            ├── workspace.json   # 工作区元数据（必须存在）
            ├── PRD.md           # PRD 文档（本 Skill 的输入）
            ├── TRD.md           # 本 Skill 生成
            └── tasks.json       # 由任务分解 Skill 生成
```

`workspace.json` 中至少包含：

- `project_path`: 指向该需求对应的代码仓库根目录
- `requirement_name`: 需求名称
- `files.prd_path`: 已生成的 PRD 路径（推荐，但本实现是通过显式参数 `prd_path` 传入）

### 3. Python 环境

- Python 版本：**3.9+**
- 依赖：已按 `mcp-server/requirements.txt` 安装

示例环境准备：

```bash
cd mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export AGENT_ORCHESTRATOR_ROOT=/path/to/your/project-root
```

---

## 三、输入与输出规范

### 1. 输入参数

- `workspace_id: str`
  - 必须对应一个存在的工作区目录和 `workspace.json`

- `prd_path: str`
  - 需指向一个已存在的 PRD 文件（通常为工作区目录下的 `PRD.md`）
  - 若路径不存在，将抛出 `ValidationError`

### 2. 输出结构（Python dict）

`generate_trd()` 返回：

```python
{
    "success": True,                # 是否生成成功
    "trd_path": "<绝对路径>/TRD.md",
    "workspace_id": "<workspace_id>"
}
```

与此同时，它还会：

1. 在工作区目录写入 / 覆盖 `TRD.md`
2. 调用 `WorkspaceManager.update_workspace_status()` 更新：
   - `status.trd_status = "completed"`
3. 更新 `workspace.json` 中：
   - `files.trd_path` → `TRD.md` 的绝对路径

---

## 四、标准调用流程

### 步骤 0：先完成 PRD 生成

建议先通过 `prd-generator` Skill 生成 PRD，示例（伪代码）：

```python
from src.tools.prd_generator import generate_prd

prd_result = generate_prd(workspace_id, requirement_url)
prd_path = prd_result["prd_path"]
```

确保：

- `prd_path` 指向一个存在的文件
- 工作区元数据已更新（`files.prd_path` 与 `prd_status`）

### 步骤 1：通过 MCP Server 调用工具

**架构说明（符合 PDF 文档）**：

根据 PDF 文档架构，本 Skill 通过 **MCP Server** 暴露，作为中央编排服务的一部分：

```
Cursor CLI → MCP Server (中央编排服务) → generate_trd 工具 → 项目代码仓库
```

**Agent 应该通过 MCP Server 调用 `generate_trd` 工具**：

**MCP 工具调用**：
```json
{
  "tool": "generate_trd",
  "arguments": {
    "workspace_id": "req-20240101-120000-user-auth",
    "prd_path": "/path/to/PRD.md"  // 可选，默认从工作区获取
  }
}
```

**在 Cursor IDE 中使用**：
```
# 使用工作区的默认 PRD.md
@agent-orchestrator generate_trd workspace_id="req-20240101-120000-user-auth"

# 指定 PRD 路径
@agent-orchestrator generate_trd workspace_id="req-20240101-120000-user-auth" prd_path="/path/to/PRD.md"
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "trd_path": "/path/to/.agent-orchestrator/requirements/req-xxx/TRD.md",
    "workspace_id": "req-20240101-120000-user-auth"
}
```

失败时：
```json
{
    "success": false,
    "error": "错误信息",
    "error_type": "ValidationError"
}
```

> **注意**：
> - 本工具通过 MCP Server 暴露，符合 PDF 文档架构
> - 如果不提供 `prd_path`，工具会自动使用工作区的 `PRD.md`
> - 返回 JSON 格式，便于 Agent 解析
> - 核心实现在 `mcp-server/src/tools/trd_generator.py`

assert result["success"] is True
trd_path = result["trd_path"]
```

### 步骤 2：检查结果

1. 文件检查：
   - `TRD.md` 存在于 `.agent-orchestrator/requirements/{workspace_id}/TRD.md`
2. 元数据检查：
   - `workspace.json.status.trd_status == "completed"`
   - `workspace.json.files.trd_path` 已更新为 `TRD.md` 的绝对路径

---

## 五、TRD 文档内容结构

生成的 `TRD.md` 采用标准化模板，主要结构为：

- `# TRD: {requirement_name}`
- `## 1. 技术概述`
  - `### 1.1 技术栈`
    - 编程语言（来自代码库分析）
    - 框架信息（例如 `python-standard`）
    - 项目路径
  - `### 1.2 现有代码库结构`
    - 使用项目根目录下的一层子目录列表生成项目结构概览
- `## 2. 架构设计`
- `## 3. 接口设计`
- `## 4. 实现方案`
- `## 5. 测试策略`
- `## 6. 风险评估`
- 尾部附注：
  - `*本文档由 Agent Orchestrator 自动生成*`
  - `*基于 PRD: {requirement_name}*`

当前实现中：

- 核心章节内容以“待补充”为占位，留给后续 AI 或人工进一步完善
- `codebase_info["structure"]` 构成 “现有代码库结构” 列表

---

## 六、代码库分析逻辑概要

本 Skill 依赖 `_analyze_codebase(project_path: Path) -> dict`，其行为概要为：

1. **检测语言**：
   - 若项目下存在任意 `*.py` 文件，则：
     - `language = "python"`
2. **检测框架**（简化版）：
   - 若项目根目录存在 `requirements.txt`：
     - `framework = "python-standard"`
3. **分析目录结构**：
   - 枚举 `project_path` 下第一层非隐藏子目录（不以 `.` 开头）
   - 将这些目录名加入 `structure` 列表

示例输出：

```python
{
    "language": "python",
    "framework": "python-standard",
    "structure": ["src", "tests", "docs"]
}
```

这些信息将被嵌入 TRD 模板中的“技术栈”和“现有代码库结构”部分。

---

## 七、与其他 Skill 的协作关系

在完整的 Agent Orchestrator 流程中，本 Skill 处于 **PRD 之后，任务分解之前**：

```text
需求输入
  ↓
[prd-generator]  →  PRD.md
  ↓
[trd-generator]  →  TRD.md
  ↓
[task-decomposer] → tasks.json
  ↓
[code-generator / code-reviewer / test-* / coverage-analyzer]
```

建议的编排方式：

1. 使用 `prd-generator` 确保需求被结构化到 PRD
2. 使用 `trd-generator` 将业务需求映射为技术设计框架
3. 再由 `task-decomposer` 把 TRD 拆分为可执行任务单元

---

## 八、错误与边界情况处理

### 1. PRD 文件不存在

- 条件：`prd_path` 指定的路径不存在
- 行为：抛出 `ValidationError(f"PRD 文件不存在: {prd_path}")`
- 建议：
  - 在调用前用 `Path(prd_path).exists()` 预检
  - 或统一通过工作区的 `files.prd_path` 来获取已存在的 PRD 路径

### 2. 工作区不存在或损坏

- 若 `workspace_id` 对应的 `workspace.json` 不存在或不可读，将在
  `WorkspaceManager.get_workspace(workspace_id)` 处抛出异常
- 建议：
  - 在更高层编排处捕获 `WorkspaceNotFoundError`，提示用户重新创建工作区

### 3. 项目路径无效

- 若 `workspace["project_path"]` 指向不存在目录：
  - `_analyze_codebase` 的结果会是较为空的结构，但不会直接抛异常
- 建议：
  - 在调用前（或在 Workspace 创建时）校验 `project_path` 存在性
  - 或在未来为此情况新增显式的 ValidationError

---

## 九、在更大工作流中的使用建议

1. **保持 TRD 的“骨架”角色**：
   - 当前实现更偏向生成“技术设计骨架 + 代码库概览”
   - 详细的接口定义、数据模型、实现方案可以由后续 AI 步骤补充

2. **配合代码库演进**：
   - 若项目目录结构变化较大（如重构 src/tests/docs 等），可以重新运行本 Skill 以更新 TRD 的“现有代码库结构”部分

3. **与任务分解 Skill 紧密配合**：
   - `task-decomposer` 可以依赖 TRD 中的“架构设计 / 功能拆分”章节，生成粒度更合适的开发任务

通过以上约定与调用方式，本 `trd-generator` Skill 即作为 Agent Orchestrator 中的“技术设计生成能力模块”，与 `prd-generator` 等其他 Skill 协同，为智能开发编排提供完整的设计阶段支持。

