---
name: coverage-analyzer
description: >
  覆盖率分析技能。使用当你已经有可运行的测试，并希望统计项目的测试覆盖率、
  生成覆盖率报告（如 HTML），以评估测试完整度。
---

# Coverage Analyzer Skill

本 Skill 指导 Agent 基于 `mcp-server/src/tools/coverage_analyzer.py`，
对某个项目运行覆盖率分析，输出覆盖率百分比和报告路径。

---

## 一、适用场景

- 已经可以在项目内成功运行测试（`pytest` 或其他命令）
- 希望：
  - 获取整体覆盖率数值
  - 生成 HTML 覆盖率报告，供人工查看

---

## 二、前置条件与环境约定

### 1. 目录与代码位置

- **MCP 工具名称**：`analyze_coverage`
- **核心实现**：`mcp-server/src/tools/coverage_analyzer.py`
- **MCP Server 实现**：`mcp-server/src/mcp_server.py`

本 Skill 包含：
- `SKILL.md`：本文件，Skill 指导文档
- `scripts/coverage_analyzer.py`：保留用于向后兼容（已弃用，应通过 MCP Server 调用）

### 2. 前置条件

- 工作区存在，`workspace.json` 中有有效的 `project_path`
- 项目中已经配置好测试命令（当前实现基于 `coverage` 工具）

> 注意：如果本地未安装 `coverage` 命令，当前实现会记录 warning，并返回默认覆盖率数据。

---

## 三、输入输出

- 输入：
  - `workspace_id: str`
  - `project_path: str` —— 要分析的项目根路径
- 输出（Python dict）：

```python
{
    "success": True,
    "coverage": 83.0,                         # 覆盖率百分比（0~100）
    "coverage_report_path": "<path>/index.html",  # HTML 报告路径（若生成成功）
    "workspace_id": workspace_id,
}
```

在工作区下通常会生成：

```text
.agent-orchestrator/requirements/{workspace_id}/coverage_report/index.html
```

---

## 四、标准调用流程

### 步骤 1：通过 MCP Server 调用工具

**架构说明（符合 PDF 文档）**：

根据 PDF 文档架构，本 Skill 通过 **MCP Server** 暴露，作为中央编排服务的一部分：

```
Cursor CLI → MCP Server (中央编排服务) → analyze_coverage 工具 → 项目代码仓库
```

**Agent 应该通过 MCP Server 调用 `analyze_coverage` 工具**：

**MCP 工具调用**：
```json
{
  "tool": "analyze_coverage",
  "arguments": {
    "workspace_id": "req-20240101-120000-user-auth",
    "project_path": "/path/to/project"  // 可选，默认从工作区获取
  }
}
```

**在 Cursor IDE 中使用**：
```
# 使用工作区的项目路径
@agent-orchestrator analyze_coverage workspace_id="req-20240101-120000-user-auth"

# 指定项目路径
@agent-orchestrator analyze_coverage workspace_id="req-20240101-120000-user-auth" project_path="/path/to/project"
```

**返回结果**（JSON 格式）：

成功时：
```json
{
    "success": true,
    "coverage": 83.0,
    "coverage_report_path": "/path/to/.agent-orchestrator/requirements/req-xxx/coverage_report/index.html",
    "workspace_id": "req-20240101-120000-user-auth"
}
```

失败时：
```json
{
    "success": false,
    "error": "错误信息",
    "error_type": "ErrorType"
}
```

> **注意**：
> - 本工具通过 MCP Server 暴露，符合 PDF 文档架构
> - 如果不提供 `project_path`，工具会自动使用工作区的项目路径
> - 返回 JSON 格式，便于 Agent 解析
> - 核心实现在 `mcp-server/src/tools/coverage_analyzer.py`

---

## 五、常见边界情况

1. **未安装 coverage 工具**
   - `subprocess.run(["python3", "-m", "coverage", ...])` 可能抛出 `FileNotFoundError`
   - 实现会记录 warning，并返回 `success=True` 但覆盖率可能为 0 或默认值

2. **coverage JSON 输出无效**
   - 解析 JSON 时出错时，会 fallback 到默认覆盖率值

3. **项目路径无效**
   - 若 `project_path` 不存在，coverage 命令会失败，Skill 视实现行为而定：
     - 通常应先在上层逻辑中校验路径存在性

---

## 六、与其他 Skill 的关系

典型链路：

```text
代码 + 测试 → 运行测试 → [coverage-analyzer] → 覆盖率数据 + HTML 报告
```

可以在以下时机触发本 Skill：

- 某个开发迭代结束后，评估整体测试完整性
- 自动化流水线中，作为质量门槛的一环（例如要求覆盖率 >= 90%）

