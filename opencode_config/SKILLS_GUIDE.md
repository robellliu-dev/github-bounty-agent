# OpenCode Skills 配置说明

## 📦 已安装的主流 Skills

### 1. Antigravity Skills (60+ skills)
**来源:** https://github.com/guanyang/antigravity-skills
**路径:** `~/.local/share/opencode/skills/antigravity-skills/skills/`

#### 主要 Skills 及用途:

| Skill 名称 | 用途 |
|-----------|------|
| `brainstorming` | 创意工作前的需求探索和设计 |
| `context-fundamentals` | 理解和管理 AI 上下文 |
| `context-optimization` | 优化上下文使用，降低 token 成本 |
| `dispatching-parallel-agents` | 并行处理多个独立任务 |
| `frontend-design` | 前端设计和 UI/UX 最佳实践 |
| `mcp-builder` | 构建 MCP (Model Context Protocol) 服务器 |
| `test-driven-development` | 测试驱动开发流程 |
| `git-workflow` | Git 工作流和版本控制 |
| `doc-coauthoring` | 文档协作编写 |
| `evaluation` | AI Agent 性能评估 |
| `notebooklm` | Google NotebookLM 集成 |
| `canvas-design` | 视觉设计和艺术创作 |

### 2. Sanjay AI Skills (20+ skills)
**来源:** https://github.com/sanjay3290/ai-skills
**路径:** `~/.local/share/opencode/skills/sanjay-ai-skills/skills/`

#### 主要 Skills 及用途:

| Skill 名称 | 用途 |
|-----------|------|
| `postgres` | PostgreSQL 数据库操作 |
| `mysql` | MySQL 数据库操作 |
| `mssql` | Microsoft SQL Server 操作 |
| `google-drive` | Google Drive 文件管理 |
| `gmail` | Gmail 邮件处理 |
| `google-calendar` | Google 日历管理 |
| `google-sheets` | Google Sheets 操作 |
| `google-docs` | Google Docs 文档处理 |
| `google-slides` | Google Slides 演示文稿 |
| `google-tts` | Google 文字转语音 |
| `elevenlabs` | ElevenLabs 语音合成 |
| `imagen` | Google Imagen 图像生成 |
| `atlassian` | Atlassian 工具集成 (Jira, Confluence) |
| `azure-devops` | Azure DevOps 集成 |
| `deep-research` | 深度研究和信息收集 |

---

## 🔧 Skills 切换方式

### 方法 1: 在对话中指定 Skill

```
使用 brainstorming skill 帮我设计一个新功能
```

### 方法 2: 通过命令行参数

```bash
opencode --agent build --prompt "使用 frontend-design skill"
```

### 方法 3: 在配置文件中设置默认 Skills

编辑 `~/.config/opencode/config.json`:

```json
{
  "skills": {
    "enabled": [
      "brainstorming",
      "frontend-design",
      "test-driven-development"
    ]
  }
}
```

---

## 📋 已启用的默认 Skills

以下 Skills 已在配置中启用，会在相关场景自动激活:

1. **brainstorming** - 任何创意工作前自动触发
2. **context-fundamentals** - 理解上下文相关问题
3. **context-optimization** - 优化 token 使用
4. **dispatching-parallel-agents** - 多任务并行处理
5. **frontend-design** - 前端开发
6. **mcp-builder** - 构建 MCP 服务
7. **test-driven-development** - 测试相关任务
8. **git-workflow** - Git 操作
9. **notebooklm** - NotebookLM 集成
10. **postgres/mysql** - 数据库操作
11. **google-*** - Google 服务集成
12. **gmail** - 邮件处理

---

## 🌐 GitHub Token 配置

已配置到 OpenCode 环境变量中:

```
GITHUB_TOKEN: YOUR_GITHUB_TOKEN_HERE
GITHUB_USERNAME: robellliu-dev
```

**用途:**
- 自动访问 GitHub API
- 创建和管理 PR
- Fork 和克隆仓库
- 无需每次输入 token

---

## 🔒 Git SSH 协议配置

已默认配置使用 SSH 协议:

```json
{
  "git": {
    "protocol": "ssh"
  }
}
```

**好处:**
- 更安全的身份验证
- 无需每次输入密码
- 更快的传输速度
- 支持密钥管理

---

## 📝 使用示例

### 示例 1: 使用 brainstorming skill 设计新功能

```
使用 brainstorming skill 帮我设计一个用户认证系统
```

### 示例 2: 使用 TDD skill 编写测试

```
使用 test-driven-development skill 为登录功能编写测试
```

### 示例 3: 使用数据库 skill

```
使用 postgres skill 设计用户表结构
```

### 示例 4: 使用并行处理 skill

```
使用 dispatching-parallel-agents skill 同时处理这3个独立的 API 开发任务
```

---

## 🔄 更新 Skills

```bash
cd ~/.local/share/opencode/skills/antigravity-skills && git pull
cd ~/.local/share/opencode/skills/sanjay-ai-skills && git pull
```

---

## 📚 更多 Skills

可以访问以下资源获取更多 Skills:

1. **AI Skill Store Marketplace:** https://github.com/aiskillstore/marketplace
2. **Antigravity Skills:** https://github.com/guanyang/antigravity-skills
3. **GitHub AI Skills Topic:** https://github.com/topics/ai-skills

---

## ⚙️ 配置文件位置

- **主配置:** `~/.config/opencode/config.json`
- **Skills 目录:** `~/.local/share/opencode/skills/`
- **数据目录:** `~/.local/share/opencode/`

---

**最后更新:** 2026-03-11