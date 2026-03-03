# ⚠️ 重要提示：GitHub认证方式变更

## 📢 GitHub已弃用密码认证

GitHub从2021年开始停止支持使用用户名和密码进行API认证。

## 🔑 需要使用Personal Access Token (PAT)

虽然你提供了：
- 账号: robellliu-dev
- 密码: robellliu258385

**但是这些凭据无法用于GitHub API调用。**

## 🛠️ 创建Personal Access Token的步骤

### 1. 访问GitHub设置页面
打开浏览器访问: https://github.com/settings/tokens

### 2. 生成新Token
点击右上角的 **"Generate new token"** → **"Generate new token (classic)"**

### 3. 设置Token权限
勾选以下权限：
- ✅ **repo** - 完整仓库访问权限（必需）
- ✅ **public_repo** - 访问公共仓库（必需）
- ✅ **workflow** - 操作GitHub Actions（可选）

### 4. 生成并复制Token
- 设置过期时间（建议选择 90 days 或更长）
- 点击 **Generate token**
- **立即复制Token**（只显示一次！）

### 5. 使用Token

**方式1: 环境变量（推荐）**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GITHUB_USERNAME="robellliu-dev"
```

**方式2: 在代码中使用**
```python
from opencode_agent import OpenCodeBountyAgent

agent = OpenCodeBountyAgent()
# Agent会自动从环境变量读取GITHUB_TOKEN
result = agent.process_bounty(languages=['python'])
```

## 🚀 快速开始

设置Token后，立即运行：

```bash
# 在OpenCode中查找真实赏金任务
python3 real_search.py

# 或使用Agent自动处理
python3 opencode_agent.py --action process --languages python --auto
```

## 📝 Token安全提示

- ⚠️ 不要将Token提交到Git仓库
- ⚠️ 不要在公开的地方分享Token
- ⚠️ Token泄露后立即在GitHub撤销
- ⚠️ 建议使用.env文件存储（记得添加到.gitignore）

## 🔒 为什么必须使用Token？

1. **安全性**: Token可以随时撤销，密码无法
2. **权限控制**: Token可以有细粒度的权限设置
3. **追溯性**: 每个Token操作都可以追踪
4. **GitHub要求**: 这是GitHub的强制安全要求

---

**下一步**: 创建Token后，Agent就可以在OpenCode中自动查找和处理GitHub赏金任务了！
