# 安装指南

## Python 版本要求

**需要 Python 3.9 或更高版本**

```bash
# 检查 Python 版本
python3 --version
```

## 安装步骤

### 1. 创建虚拟环境（推荐）

```bash
cd mcp-server

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 2. 安装依赖

```bash
# 确保虚拟环境已激活（命令行前应该有 (venv) 提示）
pip install -r requirements.txt
```

### 3. 验证安装

```bash
# 检查 pytest 是否安装
python3 -m pytest --version

# 运行测试
PYTHONPATH=. python3 -m pytest

# 运行主程序
PYTHONPATH=. python3 src/main.py
```

## 不使用虚拟环境（不推荐）

如果必须系统级安装，可以使用：

```bash
# 使用 --user 标志（推荐）
pip3 install --user -r requirements.txt

# 或使用 --break-system-packages（不推荐，可能破坏系统）
pip3 install --break-system-packages -r requirements.txt
```

## 常见问题

### Q: 为什么需要虚拟环境？

A: 虚拟环境可以：
- 隔离项目依赖，避免冲突
- 不污染系统 Python 环境
- 便于项目部署和分享

### Q: 如何退出虚拟环境？

A: 运行 `deactivate` 命令

### Q: 忘记激活虚拟环境怎么办？

A: 每次进入项目目录时运行：
```bash
source venv/bin/activate  # macOS/Linux
```

### Q: 虚拟环境已创建但找不到 pytest？

A: 确保：
1. 虚拟环境已激活（命令行前有 `(venv)`）
2. 在虚拟环境中安装了依赖：`pip install -r requirements.txt`

## 快速开始脚本

创建 `setup.sh` 脚本：

```bash
#!/bin/bash
# 创建并激活虚拟环境，安装依赖

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "安装完成！使用 'source venv/bin/activate' 激活虚拟环境"
```

运行：
```bash
chmod +x setup.sh
./setup.sh
```
