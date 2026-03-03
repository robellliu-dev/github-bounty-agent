# OpenCode Agent 配置

## 作为OpenCode Agent使用

这个项目可以直接集成到OpenCode环境中，作为一个自主规划的Agent。

### 环境变量配置

在OpenCode中设置以下环境变量:

```bash
GITHUB_TOKEN=your_github_token_here
GITHUB_USERNAME=your_github_username
WORK_DIR=./workspace
```

### Agent能力

`OpenCodeBountyAgent` 提供以下核心能力:

1. **find_bounty_tasks(languages, limit)** - 查找GitHub赏金任务
2. **analyze_task(repo_full_name, issue_number)** - 分析具体任务详情
3. **process_bounty(languages, auto_confirm)** - 完整处理赏金任务
4. **check_pr_status(pr_url)** - 检查PR状态

### 使用示例

```python
# 在OpenCode环境中调用
from opencode_agent import OpenCodeBountyAgent

agent = OpenCodeBountyAgent()

# 1. 查找Python相关的赏金任务
tasks = agent.find_bounty_tasks(languages=["python"], limit=10)

# 2. 自动处理一个任务
result = agent.process_bounty(languages=["python"], auto_confirm=False)

# 3. 检查PR状态
if result["success"]:
    status = agent.check_pr_status(result["pr_url"])
```

### 自主规划流程

Agent会自主执行以下规划:

```
1. 搜索 → 筛选合适的赏金任务
2. 分析 → 评估任务难度和可行性
3. Fork → 自动Fork目标仓库
4. 克隆 → 克隆到工作目录
5. 研究 → 分析代码库和技术栈
6. 规划 → 生成解决方案
7. 暂停 → 等待人工审核（可选）
8. 实现 → 自动实现代码修改
9. 测试 → 运行测试验证
10. 提交 → 提交并推送代码
11. 创建 → 创建Pull Request
12. 监控 → 跟踪PR状态
```

### 安全机制

- 🔒 所有操作需要GitHub Token认证
- ✅ 关键步骤支持人工审核确认
- 📝 所有操作都会记录日志
- 🔄 支持中断和恢复

### 下一步扩展

要使Agent更加智能，可以考虑:

1. **集成AI代码生成** - 使用LLM自动生成代码
2. **智能任务选择** - 基于历史数据选择最佳任务
3. **自动响应反馈** - 自动回复PR评论
4. **多任务并行** - 同时处理多个任务
5. **持续学习** - 从成功/失败的PR中学习
