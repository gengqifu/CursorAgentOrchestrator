---
name: prd-generator
description: >
  生成标准化产品需求文档（PRD）的技能。使用当你需要基于已有需求输入
  （URL 或本地文件）为某个工作区自动生成 PRD，并写入 .agent-orchestrator
  目录下的 workspace 元数据与 PRD.md 文件。
---

# PRD Generator Skill

本 Skill 指导一个具备文件读写能力的 Agent（例如在 Cursor 中运行的 Agent Orchestrator）
如何基于现有实现 `mcp-server/src/tools/prd_generator.py`，为指定工作区生成标准化 PRD 文档。

> 重点：**此 Skill 描述“怎么用现有代码完成 PRD 生成工作流”，而不是重新实现代码逻辑。**

---

## 一、适用场景

在以下情况下应优先使用本 Skill：

- 已经通过 WorkspaceManager 创建了工作区，并生成了 `workspace.json`
- 手上有一份需求文档（URL 或本地文件，例如 `.md` / `.pdf` 的解析结果）
- 希望为该工作区生成一份结构化、可继续编辑的 `PRD.md`
- 希望同时更新工作区状态（`prd_status`）与 `workspace.json` 中的 `files.prd_path`

不适用的情况：

- 需求还处于极度模糊阶段，只是零散想法（此时更适合先用通用对话整理需求）
- 目标文档不是“产品需求文档”而是 TRD/设计文档（应使用后续的 `trd-generator` Skill）

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

假设项目根目录为 `CursorAgentOrchestrator/`：

- **Skill 入口脚本**：`skills/prd-generator/scripts/prd_generator.py`
- **核心实现**：`mcp-server/src/tools/prd_generator.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/prd_generator.py`：入口脚本，由 Agent 调用

### 2. 工作区结构

本 Skill 依赖 Agent Orchestrator 定义的工作区结构：

```text
<AGENT_ORCHESTRATOR_ROOT>/
└── .agent-orchestrator/
    ├── .workspace-index.json
    └── requirements/
        └── {workspace_id}/
            ├── workspace.json   # 工作区元数据（必须存在）
            ├── PRD.md           # 本 Skill 生成
            ├── TRD.md           # 由 TRD Skill 生成
            └── tasks.json       # 由任务分解 Skill 生成
```

> `AGENT_ORCHESTRATOR_ROOT` 由环境变量或 `Config` 管理类控制，  
> `workspace.json` 由 `WorkspaceManager.create_workspace()` 创建。

### 3. Python 环境

- Python 版本：**3.9+**
- 依赖已安装：`mcp-server/requirements.txt`
- 运行前需要设置：

```bash
cd mcp-server
source venv/bin/activate      # 或等价方式
export AGENT_ORCHESTRATOR_ROOT=/path/to/your/project
```

---

## 三、输入与输出规范

### 1. 输入参数

- `workspace_id: str`
  - 已存在的工作区 ID，对应 `.agent-orchestrator/requirements/{workspace_id}/workspace.json`
  - 如果对应目录或 `workspace.json` 不存在，将触发 `WorkspaceNotFoundError`

- `requirement_url: str`
  - 可以是 HTTP(S) URL（当前实现会先返回占位内容，后续可扩展为真实抓取）
  - 也可以是本地文件路径（推荐使用解析过的 `.md` / `.txt` 文本）

### 2. 输出结构（Python dict）

`generate_prd()` 返回字典：

```python
{
    "success": True,                # 是否生成成功
    "prd_path": "<绝对路径>/PRD.md",
    "workspace_id": "<workspace_id>"
}
```

同时产生以下“副作用”：

1. 在工作区目录写入 / 覆盖 `PRD.md`
2. 调用 `WorkspaceManager.update_workspace_status()`，将：
   - `status.prd_status` 更新为 `"completed"`
3. 更新 `workspace.json` 中：
   - `files.prd_path` → `PRD.md` 的绝对路径

---

## 四、标准调用流程

### 步骤 0：确保工作区存在

在调用本 Skill 之前，应当已经通过工作区管理逻辑创建工作区，例如（伪代码）：

```python
from src.core.config import Config
from src.managers.workspace_manager import WorkspaceManager

config = Config()
workspace_manager = WorkspaceManager(config=config)

workspace_id = workspace_manager.create_workspace(
    project_path="/path/to/project",
    requirement_name="用户认证功能",
    requirement_url="https://example.com/req"
)
```

### 步骤 1：准备需求输入

有两种典型方式：

1. **URL 场景**：
   - 直接传入原始需求文档 URL
2. **本地文件场景**：
   - 先把需求整理为 `requirement.md` / `requirement.txt`
   - 将该文件路径传给 `generate_prd`

### 步骤 2：调用 Skill 脚本

**Agent 应该执行以下命令**：

```bash
python3 skills/prd-generator/scripts/prd_generator.py \
    <workspace_id> \
    <requirement_url>
```

**示例**：

```bash
python3 skills/prd-generator/scripts/prd_generator.py \
    req-20240101-120000-user-auth \
    /path/to/requirement.md
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "prd_path": "/path/to/.agent-orchestrator/requirements/req-xxx/PRD.md",
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
> - 脚本会自动处理导入路径，无需手动设置 PYTHONPATH
> - 如果 `requirement_url` 为空，会返回 `ValidationError`
> - 脚本输出 JSON 格式，便于 Agent 解析

### 步骤 3：后续处理

调用完成后，可以：

- 打开 `prd_path`，继续人工编辑
- 将 `files.prd_path` 作为输入传给 TRD 生成技能（`trd-generator`）
- 通过 `WorkspaceManager.get_workspace_status()` 查看 `prd_status`

---

## 五、PRD 文档结构约定

生成的 `PRD.md` 使用一个标准化模板，大致结构如下：

- `# PRD: {requirement_name}`
- `## 1. 需求概述`
  - `### 1.1 需求背景`（截取原始需求内容的前若干字符）
  - `### 1.2 需求目标`（待补充）
- `## 2. 功能需求`
  - `2.1 核心功能`（待补充）
  - `2.2 辅助功能`（待补充）
- `## 3. 非功能需求`
- `## 4. 验收标准`
- `## 5. 风险评估`
- 尾部标注：`*本文档由 Agent Orchestrator 自动生成*`

使用本 Skill 时：

- **不要**在 PRD 生成阶段尝试填满所有章节（那属于进一步的 AI 推理工作）
- 应优先保证：
  - 结构一致
  - 关键背景信息被正确嵌入

---

## 六、与其他 Skill 的协作关系

本 Skill 是整个 Agent Orchestrator 流程的 **入口之一**：

1. **先**通过本 Skill 生成 PRD（`PRD.md`）
2. **再**由 `trd-generator` Skill 基于 PRD 生成 TRD（`TRD.md`）
3. **然后**由 `task-decomposer` Skill 基于 TRD 生成 `tasks.json`
4. 之后的 `code-generator` / `code-reviewer` / `test-*` / `coverage-analyzer` 等围绕任务与代码继续工作

在设计复杂编排时，本 Skill 通常位于：

```text
需求输入 → [prd-generator] → PRD.md → [trd-generator] → TRD.md → ...
```

---

## 七、错误处理与边界情况

### 1. 工作区不存在

- 触发条件：`workspace_id` 无法在 `.agent-orchestrator/requirements/` 下找到对应 `workspace.json`
- 行为：抛出 `WorkspaceNotFoundError`
- 建议：
  - 在调用前总是通过 `WorkspaceManager.create_workspace` 或 `get_workspace` 检查

### 2. 需求 URL 为空

- 触发条件：`requirement_url` 为空字符串或仅包含空白
- 行为：抛出 `ValidationError("需求URL不能为空")`
- 建议：
  - 使用前做简单的空字符串校验

### 3. URL 尚未实现真实抓取

- 当前实现对于 HTTP(S) URL 只是返回占位文本：
  - `"需求文档URL: {requirement_url}\n\n待实现：从URL读取需求文档"`
- 建议：
  - 在未来扩展时，在 `_read_requirement` 中加入 HTTP 请求逻辑
  - 并在本 SKILL.md 中同步更新约定与安全注意事项（超时、鉴权等）

---

## 八、在更大工作流中的使用建议

当你在更复杂的 Agent Orchestrator Flow 中使用本 Skill 时，可以：

1. **将“需求收集”交给上游对话/Agent**：
   - 先由对话 Agent 或需求分析 Skill 把零散需求整理成结构化文本
   - 输出到本地 `requirement.md`，再调用本 Skill 生成 PRD

2. **保持单一职责**：
   - 本 Skill 只负责 **“把已有需求 → 标准化 PRD 文档 + 状态更新”**
   - 不负责代码设计、接口设计、任务拆分等（交给后续技能）

3. **在编排图中明确边界**：
   - 将本 Skill 视为“PRD 工厂”，输入是“已经整理好的需求”，输出是“结构化 PRD + 更新后的 workspace”

按照以上约定实现和调用，本 Skill 即视为“封装完备”的 `prd-generator` 能力模块，可安全复用到更大规模的智能开发编排中。

