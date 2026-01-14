# 多 Cursor 终端并发支持

## ✅ 已实现的功能

### 1. 文件锁机制

已实现跨平台文件锁工具 (`src/utils/file_lock.py`)，支持：

- **排他锁（`file_lock`）**：防止并发写入
- **共享锁（`read_lock`）**：允许多个进程同时读取
- **超时机制**：默认 30 秒超时，可配置
- **跨平台支持**：
  - Unix/Linux/macOS: 使用 `fcntl`
  - Windows: 使用 `msvcrt`

### 2. 工作区管理器并发安全

`WorkspaceManager` 已集成文件锁：

- ✅ `get_workspace()` - 使用读锁，允许多个进程同时读取
- ✅ `update_workspace_status()` - 使用排他锁，防止并发修改
- ✅ `create_workspace()` - 使用排他锁，防止并发创建冲突
- ✅ `_save_workspace_index()` - 使用排他锁，保护索引文件

### 3. 任务管理器并发安全

`TaskManager` 已集成文件锁：

- ✅ `get_tasks()` - 使用读锁，允许多个进程同时读取
- ✅ `update_task_status()` - 使用排他锁，支持多任务并行更新

## 📋 支持的使用场景

### ✅ 完全支持

1. **多个 Cursor 操作不同工作区**
   ```
   Cursor 1 → workspace-001 (PRD 生成)
   Cursor 2 → workspace-002 (TRD 生成)
   Cursor 3 → workspace-003 (代码生成)
   ```
   ✅ 完全安全，无冲突

2. **多个 Cursor 操作同一工作区的不同任务**
   ```
   Cursor 1 → workspace-001/task-001 (代码生成)
   Cursor 2 → workspace-001/task-002 (代码生成)
   Cursor 3 → workspace-001/task-003 (代码生成)
   ```
   ✅ 支持，文件锁确保原子性更新

### ⚠️ 部分支持（会序列化）

3. **多个 Cursor 同时修改同一工作区元数据**
   ```
   Cursor 1 → workspace-001 (更新 PRD 状态)
   Cursor 2 → workspace-001 (更新 TRD 状态)
   ```
   ⚠️ 支持，但会序列化执行（一个完成后另一个才能执行）

4. **多个 Cursor 同时修改同一任务**
   ```
   Cursor 1 → workspace-001/task-001 (更新状态)
   Cursor 2 → workspace-001/task-001 (更新状态)
   ```
   ⚠️ 支持，但会序列化执行

## 🔒 并发控制机制

### 文件锁工作原理

1. **获取锁**：
   - 尝试获取文件锁（非阻塞）
   - 如果锁被占用，等待并重试（默认间隔 0.1 秒）
   - 如果超时（默认 30 秒），抛出 `FileLockError`

2. **执行操作**：
   - 在锁保护下执行文件读写操作
   - 确保读取-修改-写入的原子性

3. **释放锁**：
   - 自动释放文件锁
   - 删除锁文件

### 锁文件位置

锁文件与目标文件在同一目录，扩展名为 `.lock`：

```
workspace.json → workspace.json.lock
tasks.json → tasks.json.lock
```

## 📊 性能影响

### 锁竞争场景

- **低竞争**：不同工作区或不同任务 → 几乎无影响
- **中等竞争**：同一工作区的不同任务 → 轻微延迟（毫秒级）
- **高竞争**：同一工作区元数据 → 会序列化，但保证数据一致性

### 超时处理

如果无法在 30 秒内获取锁，会抛出 `FileLockError`，提示：

```
FileLockError: 无法在 30 秒内获取文件锁: workspace.json. 
可能被其他进程占用。
```

## 🧪 测试覆盖

- ✅ 文件锁并发写入测试
- ✅ 文件锁超时测试
- ✅ 读锁多读者测试
- ✅ 工作区管理器集成测试
- ✅ 任务管理器集成测试

**测试覆盖率：91.30%** ✅

## 📝 使用示例

### 基本用法

```python
from src.utils.file_lock import file_lock, read_lock
from pathlib import Path

# 排他锁（写入）
with file_lock(Path("workspace.json")):
    workspace = json.load(...)
    workspace["status"] = "completed"
    json.dump(workspace, ...)

# 共享锁（读取）
with read_lock(Path("workspace.json")):
    workspace = json.load(...)
```

### 在管理器中使用

```python
from src.managers.workspace_manager import WorkspaceManager

manager = WorkspaceManager()

# 自动使用文件锁保护
manager.update_workspace_status(
    workspace_id="req-001",
    status_updates={"prd_status": "completed"}
)
```

## 🚀 最佳实践

1. **优先使用不同工作区**：如果可能，为不同任务创建不同工作区
2. **避免频繁更新**：减少对同一文件的频繁更新
3. **处理超时**：捕获 `FileLockError` 并重试或提示用户
4. **监控锁竞争**：如果频繁超时，考虑优化工作流

## 🔧 故障排除

### 问题：频繁出现 `FileLockError`

**可能原因**：
- 多个进程同时修改同一文件
- 某个进程持有锁时间过长

**解决方案**：
- 检查是否有进程卡住
- 增加超时时间（不推荐，应优化工作流）
- 使用不同工作区或任务隔离

### 问题：锁文件残留

**可能原因**：
- 进程异常退出，未释放锁

**解决方案**：
- 锁文件会在下次获取锁时自动清理
- 可以手动删除 `.lock` 文件（需谨慎）

## 📚 相关文档

- [并发分析文档](./CONCURRENCY_ANALYSIS.md)
- [架构文档](./ARCHITECTURE.md)
- [文件锁实现](./src/utils/file_lock.py)
