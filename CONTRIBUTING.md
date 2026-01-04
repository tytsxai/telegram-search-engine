# 贡献指南

感谢你对本项目的关注！欢迎任何形式的贡献。

## 如何贡献

### 报告 Bug

1. 在 [Issues](https://github.com/tytsxai/telegram-search-engine/issues) 中搜索是否已有相同问题
2. 如果没有，创建新 Issue，包含：
   - 问题描述
   - 复现步骤
   - 期望行为
   - 环境信息（Python 版本、操作系统等）

### 提交功能建议

1. 在 Issues 中描述你的想法
2. 说明使用场景和预期效果
3. 等待讨论确认后再开始开发

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

## 开发环境

```bash
# 克隆仓库
git clone https://github.com/tytsxai/telegram-search-engine.git
cd telegram-search-engine

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装开发依赖
pip install -e ".[dev]"
```

## 代码规范

- 使用 `ruff` 进行代码检查
- 使用 `mypy` 进行类型检查
- 提交前运行测试：`pytest`

```bash
ruff check .
mypy telegram_search
pytest
```

## Commit 规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 问题？

如有疑问，欢迎在 Issues 中提问。
