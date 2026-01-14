# Agent Orchestrator 架构实施方案（方案 3）

## 方案 3 确认

✅ **采用方案 3（混合方案）**

## execute_skill 工具的作用

### 场景对比

#### 场景 A：Agent 直接调用 Skill（推荐，无需 execute_skill）

```
用户 Prompt: "为工作区 req-001 生成 PRD，需求文档在 /path/to/req.md"

Agent 流程：
1. 识别意图：需要生成 PRD
2. 选择 skill: prd-generator
3. 读取 skills/prd-generator/SKILL.md
4. 按照 SKILL.md 指导，直接执行：
   python3 skills/prd-generator/scripts/prd_generator.py req-001 /path/to/req.md
5. 解析返回结果
```

**优点**：
- ✅ Agent 完全控制执行流程
- ✅ 可以动态选择 skill
- ✅ 不需要额外的 MCP 工具

**前提**：Agent 需要能够执行 Python 脚本（Cursor 中的 Agent 通常可以）

---

#### 场景 B：Agent 通过 MCP Server 调用 Skill（需要 execute_skill）

```
用户 Prompt: "为工作区 req-001 生成 PRD"

Agent 流程：
1. 识别意图：需要生成 PRD
2. 选择 skill: prd-generator
3. 调用 MCP Server 工具：
   execute_skill(
       skill_name="prd-generator",
       workspace_id="req-001",
       requirement_url="/path/to/req.md"
   )
4. MCP Server 内部执行 skill 脚本
5. 返回结果给 Agent
```

**优点**：
- ✅ 统一执行入口
- ✅ 可以添加统一的错误处理和日志
- ✅ 如果 Agent 无法直接执行 Python 脚本，可以通过 MCP 执行

**缺点**：
- ⚠️ 增加一层调用
- ⚠️ 需要维护 execute_skill 工具

---

### execute_skill 工具的实现示例

```python
# mcp-server/src/mcp_server.py

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "execute_skill":
        skill_name = arguments["skill_name"]
        workspace_id = arguments["workspace_id"]
        
        # 根据 skill_name 调用对应的脚本
        if skill_name == "prd-generator":
            from skills.prd_generator.scripts.prd_generator import generate_prd
            result = generate_prd(
                workspace_id=workspace_id,
                requirement_url=arguments["requirement_url"]
            )
        elif skill_name == "trd-generator":
            # ...
        
        return [TextContent(type="text", text=json.dumps(result))]
```

---

## 方案 3 下的 Agent 调用流程

### 核心问题：Agent 如何触发 Skill？

**答案**：是的，在 LLM Agent 中输入合适的 prompt，就可以触发对应的 skill 执行。

### 详细流程

#### 1. Agent 识别用户意图

```
用户 Prompt: "为工作区 req-001 生成 PRD，需求文档在 /path/to/req.md"

Agent 分析：
- 意图：生成 PRD
- 相关 skill：prd-generator
- 参数：workspace_id="req-001", requirement_url="/path/to/req.md"
```

#### 2. Agent 读取 Skill 文档

Agent 读取 `skills/prd-generator/SKILL.md`，了解：
- 如何调用脚本
- 需要什么参数
- 返回什么结果

#### 3. Agent 执行 Skill 脚本

**方式 A：直接执行 Python 脚本（推荐）**

```python
# Agent 在 Cursor 中可以执行：
import subprocess
import json

result = subprocess.run(
    [
        "python3",
        "skills/prd-generator/scripts/prd_generator.py",
        "req-001",
        "/path/to/req.md"
    ],
    capture_output=True,
    text=True
)

output = json.loads(result.stdout)
# output = {"success": True, "prd_path": "...", "workspace_id": "req-001"}
```

**方式 B：通过 MCP Server 的 execute_skill 工具**

```python
# Agent 调用 MCP 工具
result = mcp_client.call_tool(
    "execute_skill",
    {
        "skill_name": "prd-generator",
        "workspace_id": "req-001",
        "requirement_url": "/path/to/req.md"
    }
)
```

#### 4. Agent 处理结果

Agent 根据返回结果：
- 如果成功：告知用户 PRD 已生成，路径在哪里
- 如果失败：分析错误原因，提供解决方案

---

## 方案 3 实施细节

### 目录结构

```
CursorAgentOrchestrator/
├── skills/                          # Skills 目录
│   ├── prd-generator/
│   │   ├── SKILL.md                # Skill 指导文档
│   │   └── scripts/
│   │       └── prd_generator.py    # 入口脚本（薄包装）
│   ├── trd-generator/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── trd_generator.py
│   └── ...
│
└── mcp-server/
    └── src/
        ├── core/                   # 核心模块（共享）
        ├── managers/                # 管理器（共享）
        ├── tools/                   # 工具实现（核心逻辑）
        │   ├── prd_generator.py    # 实际实现
        │   ├── trd_generator.py
        │   └── ...
        └── main.py                  # MCP Server（只提供基础设施工具）
```

### Skill 脚本示例

```python
# skills/prd-generator/scripts/prd_generator.py
"""PRD Generator Skill 入口脚本。

本脚本是 prd-generator skill 的执行入口，由 Agent 根据 SKILL.md 指导调用。
"""
import sys
import json
from pathlib import Path

# 添加 mcp-server 到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
mcp_server_path = project_root / "mcp-server"
if str(mcp_server_path) not in sys.path:
    sys.path.insert(0, str(mcp_server_path))

# 导入核心实现
from src.tools.prd_generator import generate_prd


def main():
    """命令行入口。"""
    import argparse
    
    parser = argparse.ArgumentParser(description="生成 PRD 文档")
    parser.add_argument("workspace_id", help="工作区 ID")
    parser.add_argument("requirement_url", help="需求文档 URL 或文件路径")
    
    args = parser.parse_args()
    
    try:
        result = generate_prd(args.workspace_id, args.requirement_url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### SKILL.md 更新

```markdown
## 四、标准调用流程

### 步骤 1：Agent 调用脚本

Agent 应该按照以下方式调用本 skill：

**方式 A：直接执行 Python 脚本（推荐）**

```bash
python3 skills/prd-generator/scripts/prd_generator.py \
    <workspace_id> \
    <requirement_url>
```

**方式 B：通过 MCP Server 的 execute_skill 工具**

```python
result = mcp_client.call_tool(
    "execute_skill",
    {
        "skill_name": "prd-generator",
        "workspace_id": "<workspace_id>",
        "requirement_url": "<requirement_url>"
    }
)
```

### 步骤 2：处理返回结果

脚本返回 JSON 格式：

```json
{
    "success": true,
    "prd_path": "/path/to/PRD.md",
    "workspace_id": "req-001"
}
```

如果失败：

```json
{
    "success": false,
    "error": "错误信息"
}
```
```

---

## 是否需要 execute_skill 工具？

### 推荐：不提供 execute_skill 工具

**理由**：
1. ✅ Agent 可以直接执行 Python 脚本（Cursor 支持）
2. ✅ 减少 MCP Server 的复杂度
3. ✅ Agent 有更多控制权
4. ✅ 符合 Skill 设计理念（Skill 是独立的可执行单元）

### 备选：提供 execute_skill 工具

**适用场景**：
- Agent 无法直接执行 Python 脚本
- 需要统一的错误处理和日志
- 需要权限控制或审计

**实现建议**：
- 如果提供，应该是一个通用的工具，可以执行任何 skill
- 不应该为每个 skill 单独创建 MCP 工具

---

## Agent Prompt 示例

### 示例 1：生成 PRD

```
用户: "为工作区 req-001 生成 PRD，需求文档在 /path/to/req.md"

Agent 应该：
1. 识别需要执行 prd-generator skill
2. 读取 skills/prd-generator/SKILL.md
3. 执行：python3 skills/prd-generator/scripts/prd_generator.py req-001 /path/to/req.md
4. 解析返回结果，告知用户 PRD 已生成
```

### 示例 2：完整流程

```
用户: "为工作区 req-001 完成从 PRD 到代码生成的完整流程"

Agent 应该：
1. 执行 prd-generator skill（如果还没有 PRD）
2. 执行 trd-generator skill（基于 PRD）
3. 执行 task-decomposer skill（基于 TRD）
4. 执行 code-generator skill（为每个任务生成代码）
5. 执行 code-reviewer skill（审查代码）
6. 执行 test-generator skill（生成测试）
7. 执行 test-reviewer skill（审查测试）
8. 执行 coverage-analyzer skill（分析覆盖率）
```

---

## 总结

### 方案 3 的关键点

1. ✅ **Skill 自包含**：每个 skill 包含 SKILL.md + scripts/入口脚本
2. ✅ **核心逻辑集中**：实际实现在 mcp-server/src/tools/
3. ✅ **Agent 直接调用**：Agent 根据 prompt 选择 skill，直接执行脚本
4. ✅ **MCP Server 简化**：只提供基础设施工具，不直接调用工具

### execute_skill 工具

- **推荐不提供**：让 Agent 直接执行 skill 脚本
- **如果提供**：应该是通用的，可以执行任何 skill

### Agent 触发流程

✅ **是的**，在 LLM Agent 中输入合适的 prompt，就可以触发对应的 skill 执行。

流程：
1. 用户输入 prompt
2. Agent 识别意图，选择 skill
3. Agent 读取 SKILL.md，了解如何调用
4. Agent 执行 skill 脚本
5. Agent 处理结果，反馈给用户
