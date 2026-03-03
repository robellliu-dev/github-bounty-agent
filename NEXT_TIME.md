# GitHub Bounty Agent - 下次使用指南

## 📍 项目位置

```
/home/robell/github-bounty-agent/
```

## 🚀 重启后快速开始

### 1. 进入项目目录
```bash
cd /home/robell/github-bounty-agent
```

### 2. 查看项目状态
```bash
ls -lh
```

### 3. 运行测试（验证功能）
```bash
bash test.sh
```

### 4. 设置GitHub Token（必需）

**创建Token**: https://github.com/settings/tokens
- 点击 "Generate new token" → "Generate new token (classic)"
- 勾选: `repo`, `public_repo`
- 复制生成的Token

**设置环境变量**:
```bash
export GITHUB_TOKEN="ghp_你的token"
export GITHUB_USERNAME="robellliu-dev"
```

### 5. 在OpenCode中使用

**查找赏金任务**:
```bash
python3 real_search.py
```

**查看演示**:
```bash
python3 opencode_demo.py
```

**运行Agent**:
```bash
python3 opencode_agent.py --action find --languages python
```

## 📁 主要文件

| 文件 | 说明 |
|------|------|
| `opencode_agent.py` | OpenCode集成接口 ⭐ |
| `real_search.py` | 搜索真实赏金任务 ⭐ |
| `test.sh` | 快速测试 |
| `demo.py` | 完整流程演示 |
| `README.md` | 完整文档 |
| `TOKEN_SETUP.md` | Token设置指南 |

## 🔑 账号信息

- GitHub用户名: `robellliu-dev`

⚠️ **重要**: GitHub已弃用密码认证，必须使用Personal Access Token

## ✅ 项目状态

- 测试通过: ✅ 3/3
- 可用性: ✅ 已就绪
- OpenCode集成: ✅ 已完成

---

**下次直接运行**:
```bash
cd /home/robell/github-bounty-agent && bash test.sh
```
