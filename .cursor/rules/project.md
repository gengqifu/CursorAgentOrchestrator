# 项目规则

## Python 版本要求

**本项目严格要求使用 Python 3.9 或更高版本**

### 要求

1. **所有代码必须在 Python 3.9+ 环境下运行**
2. **使用 Python 3.9+ 的类型提示语法**
   - 使用内置类型：`dict`, `list`, `tuple` 而非 `typing.Dict`, `typing.List`, `typing.Tuple`
   - 使用 `Optional[T]` 或 `T | None` (Python 3.10+)
3. **运行命令必须使用 `python3`**
   - 不要使用 `python` 命令（可能是 Python 2）
   - 所有脚本和文档中的命令都使用 `python3`

### 代码示例

```python
# ✅ 正确：Python 3.9+ 风格
def process_data(items: list[str], config: dict[str, str] | None = None) -> dict[str, int]:
    pass

# ❌ 错误：旧式风格
from typing import Dict, List, Optional

def process_data(items: List[str], config: Optional[Dict[str, str]] = None) -> Dict[str, int]:
    pass
```

### 运行示例

```bash
# ✅ 正确
python3 src/main.py
python3 -m pytest
python3 -m pip install -r requirements.txt

# ❌ 错误
python src/main.py  # 可能指向 Python 2
```

### 版本检查

- 所有脚本应在开头检查 Python 版本
- 测试配置中包含 Python 版本检查
- CI/CD 中验证 Python 版本

## Git 提交信息规范

**所有 Git 提交信息必须使用中文**

### 提交信息格式

```
<类型>: <简短描述>

<详细描述（可选）>
```

### 提交类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具链相关
- `perf`: 性能优化

### 示例

```bash
# ✅ 正确
git commit -m "feat: 添加工作区管理器功能"
git commit -m "fix: 修复日志写入已关闭文件流的错误"
git commit -m "docs: 更新安装指南"
git commit -m "test: 添加工作区管理器测试用例"

# ✅ 正确：多行提交信息
git commit -m "feat: 实现 MCP Server 基础架构

- 添加核心模块（config, logger, exceptions）
- 实现工作区管理器
- 添加优雅关闭机制
- 支持 Python 3.9+"

# ❌ 错误：使用英文
git commit -m "feat: Add workspace manager"
git commit -m "fix: Fix logger error"
```

### 提交信息要求

1. **必须使用中文**：所有提交信息使用中文描述
2. **简洁明了**：第一行不超过 50 个字符
3. **类型明确**：使用标准的提交类型前缀
4. **描述清晰**：说明做了什么，为什么做（如果需要）

### 代码审查检查点

在代码审查时，检查：
- [ ] 提交信息使用中文
- [ ] 提交类型正确
- [ ] 描述清晰明了
- [ ] 代码在 Python 3.9+ 环境下运行
- [ ] 使用 `python3` 命令而非 `python`

## 相关文档

- Python 编码规范：`.cursor/rules/python.md`
- TDD 规范：`.cursor/rules/tdd.md`
- Python 3 兼容性：`mcp-server/PYTHON3_COMPATIBILITY.md`
