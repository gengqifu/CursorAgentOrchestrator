# MCP Server 关闭指南

## MCP Server 关闭方式

MCP Server 支持多种关闭方式，取决于运行模式。

## 关闭方式

### 1. 自动关闭（推荐）

**当 MCP Server 通过 stdio 与 Cursor 连接时：**

- **客户端断开时自动关闭**：当 Cursor 关闭或断开连接时，MCP Server 会自动检测到 stdin 关闭并退出
- **无需手动操作**：这是最常用的方式，Server 会随客户端生命周期自动管理

### 2. 信号关闭（命令行运行）

**如果直接运行 `python3 src/main.py`：**

```bash
# 方式 1：使用 Ctrl+C（发送 SIGINT）
# 在运行 MCP Server 的终端按 Ctrl+C

# 方式 2：使用 kill 命令（发送 SIGTERM）
# 找到进程 ID
ps aux | grep "src/main.py"

# 发送 SIGTERM 信号
kill <PID>

# 或强制关闭（不推荐）
kill -9 <PID>
```

### 3. 通过 Cursor 关闭

**在 Cursor 中：**

1. 关闭 Cursor 应用
2. MCP Server 会自动检测连接断开并退出
3. 无需手动操作

## 优雅关闭机制

MCP Server 实现了优雅关闭机制：

### 信号处理

- **SIGINT** (Ctrl+C)：优雅关闭，清理资源
- **SIGTERM**：优雅关闭，清理资源
- **SIGQUIT**：立即退出（用于调试）

### 关闭流程

1. 接收关闭信号
2. 停止接受新请求
3. 等待当前请求完成
4. 清理资源（关闭文件、释放锁等）
5. 退出进程

## 验证 Server 是否已关闭

```bash
# 检查进程是否还在运行
ps aux | grep "src/main.py"

# 如果没有输出，说明 Server 已关闭
```

## 常见问题

### Q: Server 卡住无法关闭怎么办？

A: 使用强制关闭：
```bash
# 找到进程 ID
ps aux | grep "src/main.py" | grep -v grep

# 强制关闭
kill -9 <PID>
```

### Q: 如何确认 Server 已正常关闭？

A: 检查日志输出，应该看到：
```
INFO - MCP Server 正在关闭...
INFO - 清理资源...
INFO - MCP Server 已关闭
```

### Q: 关闭时数据会丢失吗？

A: 不会。优雅关闭会：
- 保存所有工作区状态
- 提交未完成的 Git 操作
- 释放文件锁
- 确保数据完整性

## 开发模式下的关闭

**在开发调试时：**

```bash
# 运行 Server
PYTHONPATH=. python3 src/main.py

# 在另一个终端关闭
pkill -f "src/main.py"

# 或使用 Ctrl+C（在运行 Server 的终端）
```

## 生产环境下的关闭

**在 Cursor 配置中运行时：**

- Server 由 Cursor 管理
- 关闭 Cursor 时自动关闭 Server
- 无需手动操作
