# 多 Cursor 终端并发执行分析

## 当前架构状态

### ✅ 支持的情况

1. **多个 Cursor 终端操作不同的工作区**
   - 每个 Cursor 启动独立的 MCP Server 进程
   - 通过 `workspace_id` 隔离，互不干扰
   - **状态**：✅ 完全支持

2. **多个 Cursor 终端操作同一工作区的不同任务**
   - 理论上可以，但存在文件冲突风险
   - **状态**：⚠️ 部分支持（有风险）

### ❌ 不支持/有风险的情况

1. **多个 Cursor 同时修改同一工作区元数据**
   - 多个进程同时读写 `workspace.json`
   - 可能导致数据丢失或覆盖
   - **状态**：❌ 不支持

2. **多个 Cursor 同时修改同一 `tasks.json`**
   - 多个进程同时读写任务文件
   - 可能导致任务状态丢失
   - **状态**：❌ 不支持

## 问题根源

### 1. MCP Server 连接模式

```
Cursor Terminal 1 → 独立 MCP Server 进程 1 → workspace.json
Cursor Terminal 2 → 独立 MCP Server 进程 2 → workspace.json (冲突!)
Cursor Terminal 3 → 独立 MCP Server 进程 3 → tasks.json (冲突!)
```

**问题**：每个 Cursor 实例启动独立的 MCP Server 进程，多个进程同时访问同一文件。

### 2. 缺少并发控制机制

当前代码中：
- ❌ 没有文件锁（`file_lock.py` 不存在）
- ❌ 没有读写锁机制
- ❌ 没有事务性更新
- ❌ 没有乐观锁/版本控制

### 3. 文件读写模式

```python
# workspace_manager.py - 直接覆盖写入
with open(meta_file, 'w', encoding='utf-8') as f:
    json.dump(workspace, f, ...)

# task_manager.py - 读取-修改-写入（非原子）
with open(tasks_file, 'r') as f:
    data = json.load(f)
# ... 修改 data ...
with open(tasks_file, 'w') as f:
    json.dump(data, f, ...)
```

**问题**：读取-修改-写入不是原子操作，多进程并发时可能丢失更新。

## 需要的改进

### 方案 1：文件锁机制（推荐）

为关键文件操作添加文件锁：

```python
# src/utils/file_lock.py
import fcntl  # Unix
# 或 msvcrt (Windows)
from contextlib import contextmanager

@contextmanager
def file_lock(file_path: Path):
    """文件锁上下文管理器。"""
    lock_file = file_path.with_suffix(file_path.suffix + '.lock')
    with open(lock_file, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # 排他锁
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

使用示例：

```python
# workspace_manager.py
from src.utils.file_lock import file_lock

def update_workspace_status(self, workspace_id: str, status_updates: dict):
    workspace_dir = self.config.get_workspace_path(workspace_id)
    meta_file = workspace_dir / "workspace.json"
    
    with file_lock(meta_file):
        workspace = self.get_workspace(workspace_id)
        workspace["status"].update(status_updates)
        with open(meta_file, 'w') as f:
            json.dump(workspace, f, ...)
```

### 方案 2：版本控制/乐观锁

在 `workspace.json` 和 `tasks.json` 中添加版本号：

```json
{
  "version": 1,
  "workspace_id": "...",
  ...
}
```

更新时检查版本：

```python
def update_workspace_status(self, workspace_id: str, status_updates: dict, expected_version: int):
    with file_lock(meta_file):
        workspace = self.get_workspace(workspace_id)
        if workspace.get("version") != expected_version:
            raise ConcurrentModificationError("工作区已被其他进程修改")
        workspace["version"] += 1
        workspace["status"].update(status_updates)
        # ... 保存
```

### 方案 3：任务级隔离

为每个任务创建独立的文件或目录：

```
.agent-orchestrator/requirements/{workspace_id}/
├── workspace.json
├── tasks.json
├── tasks/
│   ├── task-001.json  # 独立文件
│   ├── task-002.json
│   └── task-003.json
```

这样不同任务的操作不会相互干扰。

## 推荐方案

**组合方案**：文件锁 + 任务级隔离

1. **立即实施**：添加文件锁机制
   - 保护 `workspace.json` 的并发写入
   - 保护 `tasks.json` 的并发写入

2. **中期优化**：任务级文件隔离
   - 每个任务独立文件：`tasks/task-{id}.json`
   - 减少锁竞争

3. **长期优化**：版本控制
   - 添加乐观锁机制
   - 提供更好的冲突检测和错误提示

## 当前使用建议

### ✅ 安全的使用方式

1. **不同工作区并行**：
   ```
   Cursor 1 → workspace-001 (PRD 生成)
   Cursor 2 → workspace-002 (TRD 生成)
   Cursor 3 → workspace-003 (代码生成)
   ```
   ✅ 完全安全

2. **同一工作区的顺序执行**：
   ```
   Cursor 1: PRD → TRD → 任务分解 (顺序执行)
   ```
   ✅ 安全（单进程）

### ⚠️ 有风险的使用方式

1. **同一工作区并行执行不同阶段**：
   ```
   Cursor 1: PRD 生成 (修改 workspace.json)
   Cursor 2: TRD 生成 (修改 workspace.json) ← 可能冲突
   ```
   ⚠️ 有风险，需要文件锁

2. **同一工作区并行执行不同任务**：
   ```
   Cursor 1: task-001 代码生成 (修改 tasks.json)
   Cursor 2: task-002 代码生成 (修改 tasks.json) ← 可能冲突
   ```
   ⚠️ 有风险，需要文件锁或任务级隔离

## 总结

**当前状态**：
- ✅ 支持多个 Cursor 操作不同工作区
- ⚠️ 支持多个 Cursor 操作同一工作区的不同任务（但有文件冲突风险）
- ❌ 不支持多个 Cursor 同时修改同一工作区元数据（需要文件锁）

**建议**：
1. 如果需要多终端并发，优先使用不同的 `workspace_id`
2. 如果必须在同一工作区并发，需要先实现文件锁机制
3. 长期考虑任务级文件隔离，减少锁竞争
