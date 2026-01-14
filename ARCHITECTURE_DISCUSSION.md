# Agent Orchestrator 架构调整方案讨论

## 当前架构分析

### 现状

```
Cursor IDE
    ↓ MCP 协议
MCP Server (main.py)
    ↓ 直接调用
mcp-server/src/tools/*.py (8个工具)
    ↓ 使用
mcp-server/src/managers/*.py (WorkspaceManager, TaskManager)
    ↓ 使用
mcp-server/src/core/*.py (Config, Logger, Exceptions)
```

**问题**：
1. MCP Server 直接调用工具函数，不符合 Skill 设计理念
2. Skills 只有文档（SKILL.md），没有实现代码
3. Agent 无法根据 prompt 动态选择 skill

### 期望架构

```
用户 Prompt
    ↓
Agent (在 Cursor 中)
    ↓ 根据 prompt 选择 skill
Skill (SKILL.md + 实现代码)
    ↓ 调用
Python 脚本
    ↓ 使用
MCP Server 提供的 Managers/Core
```

## 方案对比

### 方案 1：Scripts 在 Skill 目录中（自包含）

**目录结构**：
```
skills/
├── prd-generator/
│   ├── SKILL.md                    # Skill 指导文档
│   └── scripts/
│       └── prd_generator.py        # 实现代码
├── trd-generator/
│   ├── SKILL.md
│   └── scripts/
│       └── trd_generator.py
└── ...

mcp-server/src/
├── core/                            # 核心模块（共享）
├── managers/                        # 管理器（共享）
└── main.py                          # MCP Server（不直接调用工具）
```

**调用流程**：
1. Agent 读取 `skills/prd-generator/SKILL.md`
2. Skill 文档指导：调用 `scripts/prd_generator.py`
3. 脚本导入 `mcp-server/src/` 中的模块

**优点**：
- ✅ Skill 自包含，便于分发和复用
- ✅ 符合 Skill 设计理念（文档 + 代码）
- ✅ 便于独立测试和维护每个 skill
- ✅ 可以单独打包和分发 skill

**缺点**：
- ⚠️ 脚本需要处理导入路径（需要导入 mcp-server 的模块）
- ⚠️ 代码分散，可能重复

**导入路径处理**：
```python
# skills/prd-generator/scripts/prd_generator.py
import sys
from pathlib import Path

# 添加 mcp-server 到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
mcp_server_path = project_root / "mcp-server"
if str(mcp_server_path) not in sys.path:
    sys.path.insert(0, str(mcp_server_path))

from src.core.config import Config
from src.managers.workspace_manager import WorkspaceManager
```

---

### 方案 2：Scripts 仍在 mcp-server，Skill 只包含文档（集中管理）

**目录结构**：
```
skills/
├── prd-generator/
│   └── SKILL.md                    # 说明如何调用 mcp-server/src/tools/prd_generator.py
├── trd-generator/
│   └── SKILL.md
└── ...

mcp-server/src/
├── core/
├── managers/
├── tools/                           # 工具代码集中管理
│   ├── prd_generator.py
│   ├── trd_generator.py
│   └── ...
└── main.py                          # MCP Server（不直接调用工具）
```

**调用流程**：
1. Agent 读取 `skills/prd-generator/SKILL.md`
2. Skill 文档指导：调用 `mcp-server/src/tools/prd_generator.py`
3. 脚本直接导入 `src.core` 和 `src.managers`

**优点**：
- ✅ 代码集中管理，便于维护
- ✅ 不需要处理复杂的导入路径
- ✅ 统一的代码风格和测试

**缺点**：
- ⚠️ Skill 和实现分离，不够自包含
- ⚠️ 不便于单独分发 skill
- ⚠️ 不符合"Skill 应该包含实现"的理念

---

### 方案 3：混合方案（推荐）

**目录结构**：
```
skills/
├── prd-generator/
│   ├── SKILL.md                    # Skill 指导文档
│   └── scripts/
│       └── prd_generator.py        # 实现代码（薄包装）
├── trd-generator/
│   ├── SKILL.md
│   └── scripts/
│       └── trd_generator.py
└── ...

mcp-server/src/
├── core/                            # 核心模块（共享）
├── managers/                        # 管理器（共享）
├── tools/                           # 工具实现（核心逻辑）
│   ├── prd_generator.py            # 实际实现
│   ├── trd_generator.py
│   └── ...
└── main.py                          # MCP Server（不直接调用工具）
```

**调用流程**：
1. Agent 读取 `skills/prd-generator/SKILL.md`
2. Skill 文档指导：调用 `scripts/prd_generator.py`
3. `scripts/prd_generator.py` 导入并调用 `mcp-server/src/tools/prd_generator.py`

**优点**：
- ✅ Skill 自包含（文档 + 入口脚本）
- ✅ 核心逻辑集中管理（在 mcp-server/src/tools/）
- ✅ 便于测试和维护
- ✅ 符合 Skill 设计理念

**缺点**：
- ⚠️ 需要维护两处代码（skill 脚本和 mcp-server 工具）
- ⚠️ 可能增加一层调用开销

**实现示例**：
```python
# skills/prd-generator/scripts/prd_generator.py
import sys
from pathlib import Path

# 添加 mcp-server 到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
mcp_server_path = project_root / "mcp-server"
if str(mcp_server_path) not in sys.path:
    sys.path.insert(0, str(mcp_server_path))

# 导入并重新导出
from src.tools.prd_generator import generate_prd

# 可以在这里添加 skill 特定的逻辑
# 例如：参数验证、日志记录等
```

---

## MCP Server 职责调整

### 当前职责（需要调整）

- ❌ 直接调用 8 个工具函数
- ✅ 提供工作区管理工具（create_workspace, get_workspace）

### 调整后职责

- ✅ **只提供基础设施工具**：
  - `create_workspace` - 创建工作区
  - `get_workspace` - 获取工作区信息
  - `update_workspace_status` - 更新工作区状态
  - `get_tasks` - 获取任务列表
  - `update_task_status` - 更新任务状态

- ✅ **可选：提供 Skill 执行工具**（如果 Agent 需要）：
  - `execute_skill(skill_name, workspace_id, ...)` - 执行指定 skill
  - 这个工具内部会调用 skill 的脚本

- ❌ **不再直接调用工具**：工具由 Agent 通过 skill 调用

---

## Agent 调用流程

### 流程 1：Agent 直接调用 Skill（推荐）

```
用户: "为工作区 req-001 生成 PRD，需求文档在 /path/to/req.md"

Agent:
1. 识别需要 "生成 PRD"
2. 选择 skill: prd-generator
3. 读取 skills/prd-generator/SKILL.md
4. 按照 SKILL.md 的指导：
   - 调用 scripts/prd_generator.py
   - 传入参数：workspace_id="req-001", requirement_url="/path/to/req.md"
5. 脚本执行，返回结果
```

### 流程 2：Agent 通过 MCP Server 调用 Skill（备选）

```
用户: "为工作区 req-001 生成 PRD"

Agent:
1. 识别需要 "生成 PRD"
2. 调用 MCP Server 工具：execute_skill("prd-generator", workspace_id="req-001", ...)
3. MCP Server 内部调用 skill 脚本
4. 返回结果
```

**建议**：优先使用流程 1，让 Agent 直接调用 skill，更灵活。

---

## 推荐方案

### 推荐：方案 3（混合方案）

**理由**：
1. ✅ 符合 Skill 设计理念：Skill 自包含（文档 + 入口脚本）
2. ✅ 核心逻辑集中管理：便于维护和测试
3. ✅ 灵活性：Skill 脚本可以添加 skill 特定的逻辑
4. ✅ 可扩展性：便于添加新的 skill

### 实施步骤

1. **保持 mcp-server/src/tools/ 中的核心实现**
   - 这些是实际的工具实现
   - 保持现有的测试用例

2. **在 skills/*/scripts/ 中创建薄包装脚本**
   - 导入 mcp-server 的工具函数
   - 可以添加 skill 特定的逻辑（如参数验证、日志）

3. **更新 SKILL.md 文档**
   - 说明如何调用本地的 `scripts/*.py`
   - 说明参数和返回值

4. **调整 MCP Server**
   - 移除直接调用工具的逻辑
   - 只保留工作区管理工具
   - 可选：添加 `execute_skill` 工具

5. **更新测试**
   - 测试 skill 脚本的导入和执行
   - 保持对 mcp-server/src/tools/ 的测试

---

## 问题讨论

### Q1: Skill 脚本是否需要命令行入口？

**建议**：是，便于独立测试和调试。

```python
# skills/prd-generator/scripts/prd_generator.py
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace_id")
    parser.add_argument("requirement_url")
    args = parser.parse_args()
    
    result = generate_prd(args.workspace_id, args.requirement_url)
    print(json.dumps(result, indent=2))
```

### Q2: 如何处理技能之间的依赖？

**建议**：在 SKILL.md 中明确说明依赖关系。

例如，`trd-generator` 的 SKILL.md 中说明：
- 前置条件：需要先执行 `prd-generator` skill
- 输入：PRD.md 文件路径

### Q3: MCP Server 是否需要提供 `execute_skill` 工具？

**建议**：可选，但推荐不提供。

- **不提供**：让 Agent 直接调用 skill，更灵活
- **提供**：如果 Agent 无法直接执行 Python 脚本，可以通过 MCP Server 执行

### Q4: 如何处理技能的错误和日志？

**建议**：
- 错误：通过异常抛出，Agent 捕获并处理
- 日志：使用 `src.core.logger`，统一日志格式

---

## 总结

**推荐方案**：方案 3（混合方案）

**关键点**：
1. Skills 自包含（文档 + 入口脚本）
2. 核心逻辑集中在 mcp-server/src/tools/
3. MCP Server 只提供基础设施工具
4. Agent 直接调用 skill，不通过 MCP Server

**下一步**：确认方案后，开始实施重构。
