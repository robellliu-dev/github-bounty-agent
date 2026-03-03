# GitHub Bounty Agent

自动化处理GitHub赏金任务的智能Agent

## 功能特性

- 🔍 自动搜索GitHub上的赏金任务
- 📊 分析任务可行性
- 🍴 自动Fork和克隆仓库
- 🔬 分析代码库结构
- 💡 生成解决方案
- ⚙️ 实现代码修改
- 🧪 运行测试
- 📤 自动提交和推送
- 🎯 创建Pull Request

## 安装

```bash
# 克隆或下载项目
cd github-bounty-agent

# 安装Python依赖
pip install -r bounty_requirements.txt
```

## 配置

### 1. 创建GitHub Personal Access Token

访问 https://github.com/settings/tokens 创建新token，需要以下权限:
- `repo` (完整仓库访问权限)
- `public_repo` (访问公共仓库)
- `workflow` (如果需要操作Actions)

### 2. 配置环境变量 (推荐)

```bash
export GITHUB_TOKEN="your_token_here"
export GITHUB_USERNAME="your_username"
```

或在项目根目录创建 `.env` 文件:
```
GITHUB_TOKEN=your_token_here
GITHUB_USERNAME=your_username
```

## 使用方法

### 交互模式

```bash
python3 github_bounty_agent.py
```

### 自动模式

```bash
# 自动运行完整流程
python3 github_bounty_agent.py --auto

# 指定编程语言
python3 github_bounty_agent.py --auto --languages python,javascript

# 指定工作目录
python3 github_bounty_agent.py --auto --work-dir ./my_workspace
```

### 运行测试

```bash
python3 test_agent.py
```

## 工作流程

Agent会自动执行以下步骤:

1. **搜索任务** - 查找GitHub上的赏金任务
2. **分析任务** - 评估任务的可行性和难度
3. **选择任务** - 选择要处理的任务
4. **获取详情** - 获取任务的完整信息
5. **Fork仓库** - 自动Fork目标仓库
6. **克隆代码** - 克隆到本地工作目录
7. **分析代码** - 分析代码库结构和技术栈
8. **生成方案** - 生成解决方案和实施计划
9. **人工审核** - 等待用户审核方案
10. **实现方案** - 实现代码修改
11. **运行测试** - 自动运行测试
12. **提交推送** - 提交并推送代码
13. **创建PR** - 创建Pull Request
14. **保存记录** - 保存所有操作记录

## 工作目录结构

```
workspace/
├── example-repo/           # 克隆的仓库
│   ├── CHANGES.txt        # 修改的文件
│   └── ...
├── solution_plan_*.json    # 解决方案计划
├── pr_info_*.json         # PR信息记录
└── logs/                   # 日志文件
```

## 重要提示

⚠️ **使用前请注意:**

1. **人工审核**: 在代码提交前，Agent会等待人工审核方案
2. **GitHub限制**: 注意API调用频率限制
3. **代码质量**: 确保提交的代码符合项目规范
4. **合规性**: 遵守GitHub的服务条款和项目的贡献指南
5. **测试**: 建议先在小项目上测试

## 故障排除

### Fork失败
- 检查Token权限
- 确认仓库是否允许Fork
- 检查API配额

### 克隆失败
- 检查网络连接
- 确认仓库是否公开
- 检查磁盘空间

### PR创建失败
- 确认代码已推送
- 检查分支名称
- 确认目标仓库接受PR

## 扩展功能

### 作为OpenCode Agent调用

#### 方法1: 直接调用模块

```python
from github_bounty_agent import GitHubBountyAgent

# 创建Agent实例
agent = GitHubBountyAgent(
    token=os.getenv("GITHUB_TOKEN"),
    username=os.getenv("GITHUB_USERNAME")
)

# 运行自动化流程
success = agent.auto_run(languages=["python"])
```

#### 方法2: 使用OpenCode集成接口

```python
from opencode_agent import OpenCodeBountyAgent

# 创建OpenCode Agent
agent = OpenCodeBountyAgent()

# 查找赏金任务
tasks = agent.find_bounty_tasks(languages=["python", "javascript"], limit=10)

# 处理完整的赏金任务（自动模式）
result = agent.process_bounty(languages=["python"], auto_confirm=True)

# 检查PR状态
status = agent.check_pr_status("https://github.com/owner/repo/pull/123")
```

#### 方法3: 命令行调用

```bash
# 查找任务
python3 opencode_agent.py --action find --languages python,javascript

# 处理任务（自动模式）
python3 opencode_agent.py --action process --languages python --auto

# 检查PR状态
python3 opencode_agent.py --action check --repo owner/repo --pr 123
```

### 在OpenCode中集成

在OpenCode环境中，可以直接调用 `OpenCodeBountyAgent` 类:

```python
# OpenCode Agent可以直接使用
from opencode_agent import OpenCodeBountyAgent

# Agent会自动从环境变量读取配置
agent = OpenCodeBountyAgent()

# 执行自动化流程
result = agent.process_bounty(languages=["python"])

if result["success"]:
    print(f"✅ PR已创建: {result['pr_url']}")
```

### 自定义任务搜索

```python
tasks = agent.search_bounty_tasks(languages=["python", "typescript"])
```

### 手动控制流程

```python
# 手动执行每个步骤
tasks = agent.search_bounty_tasks()
selected = agent.select_task(tasks)
details = agent.get_task_details(selected)
# ... 等等
```

## 日志和调试

所有操作记录保存在工作目录下:
- `solution_plan_*.json` - 解决方案
- `pr_info_*.json` - PR信息
- `agent_*.log` - 运行日志

## 许可证

MIT

## 免责声明

本工具仅供学习和研究使用。使用本工具产生的任何后果由使用者自行承担。
