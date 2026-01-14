# 测试覆盖率修复指南

## 当前覆盖率问题

测试运行显示覆盖率为 88%，但要求是 90%。需要覆盖以下缺失的代码：

### 缺失覆盖的代码

1. **src/main.py** (0% 覆盖率)
   - 第 11-27 行：主程序逻辑
   - 需要添加测试

2. **src/core/logger.py** (92% 覆盖率)
   - 第 24 行：已有处理器时提前返回
   - 需要测试已有处理器的场景

3. **src/managers/workspace_manager.py** (96% 覆盖率)
   - 第 32-33 行：加载已存在的索引文件
   - 需要测试索引文件已存在的场景

## 已添加的测试

### 1. tests/test_main.py
- `test_main_can_be_imported` - 测试主程序可以导入
- `test_main_logger_is_setup` - 测试日志器设置
- `test_main_runs_without_error` - 测试主程序运行

### 2. tests/core/test_logger.py (更新)
- `test_logger_returns_existing_logger_when_handlers_exist` - 测试已有处理器时直接返回

### 3. tests/managers/test_workspace_manager.py (更新)
- `test_load_workspace_index_loads_existing_index` - 测试加载已存在的索引文件

## 运行测试

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行所有测试并查看覆盖率
PYTHONPATH=. python3 -m pytest --cov=src --cov-report=term-missing

# 应该达到 90%+ 覆盖率
```

## 如果覆盖率仍不足

可以临时降低覆盖率要求进行开发：

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=85",  # 临时降低到 85%
]
```

但最终目标仍然是 90%+ 覆盖率。
