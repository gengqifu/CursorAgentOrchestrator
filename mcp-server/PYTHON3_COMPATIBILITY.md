# Python 3 兼容性说明

## 版本要求

**本项目要求 Python 3.9 或更高版本**

### 检查 Python 版本

```bash
python3 --version
# 应该显示：Python 3.9.x 或更高
```

## 兼容性特性

### ✅ 已实现的 Python 3.9+ 特性

1. **内置类型提示**（Python 3.9+）
   - 使用 `dict` 而非 `typing.Dict`
   - 使用 `list` 而非 `typing.List`
   - 使用 `tuple` 而非 `typing.Tuple`

2. **类型注解**
   - 所有函数都有类型提示
   - 使用 `Optional` 表示可选类型
   - 使用 `-> None` 表示无返回值

3. **f-string**（Python 3.6+）
   - 所有字符串格式化使用 f-string

4. **Path 对象**（Python 3.4+）
   - 使用 `pathlib.Path` 进行路径操作

## 运行方式

### 方式 1：使用 PYTHONPATH（推荐）

```bash
cd mcp-server
PYTHONPATH=. python3 src/main.py
```

### 方式 2：使用模块方式

```bash
cd mcp-server
python3 -m src.main
```

### 方式 3：安装后运行

```bash
cd mcp-server
pip3 install -e .
python3 -m src.main
```

## 测试

### 运行测试

```bash
cd mcp-server
PYTHONPATH=. python3 -m pytest
```

### 测试会自动检查 Python 版本

测试配置中包含 Python 版本检查，如果版本不符合要求会自动跳过。

## 代码规范

### 类型提示示例

```python
# ✅ 正确：Python 3.9+ 风格
def process_data(items: list[str], config: dict[str, str] | None = None) -> dict[str, int]:
    pass

# ❌ 错误：旧式风格（Python 3.8 及以下）
from typing import Dict, List, Optional

def process_data(items: List[str], config: Optional[Dict[str, str]] = None) -> Dict[str, int]:
    pass
```

### 当前代码使用的类型提示

- `dict` - 字典类型
- `list` - 列表类型
- `Optional[T]` - 可选类型（从 typing 导入）
- `Path` - 路径类型（从 pathlib 导入）

## 配置文件

### pyproject.toml

```toml
[project]
requires-python = ">=3.9"

[tool.black]
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.mypy]
python_version = "3.9"
```

### setup.py

```python
python_requires=">=3.9"
```

## 验证 Python 3 兼容性

### 检查脚本

```bash
# 检查 Python 版本
python3 --version

# 检查语法
python3 -m py_compile src/**/*.py

# 运行类型检查
python3 -m mypy src
```

## 常见问题

### Q: 为什么需要 Python 3.9+？

A: 为了使用内置类型提示（`dict`, `list` 等），这些特性在 Python 3.9 中引入，使代码更简洁。

### Q: 可以在 Python 3.8 运行吗？

A: 不可以。需要修改所有类型提示为旧式写法（`Dict`, `List` 等），不推荐。

### Q: 如何确保使用 Python 3？

A: 
1. 使用 `python3` 命令而非 `python`
2. 检查版本：`python3 --version`
3. 使用虚拟环境：`python3 -m venv venv`

## 总结

✅ 项目完全支持 Python 3.9+  
✅ 所有代码使用 Python 3.9+ 类型提示语法  
✅ 运行前会自动检查 Python 版本  
✅ 测试包含版本检查  
