#!/usr/bin/env python3
"""
GitHub Bounty Agent 使用文档
详细说明如何使用优化后的Agent
"""

# ===================== 快速开始 =====================

## 安装依赖
```bash
cd /home/robell/github-bounty-agent
pip install -r bounty_requirements.txt
```

## 配置GitHub Token
```bash
export GITHUB_TOKEN="your_github_token"
export GITHUB_USERNAME="your_username"
```

## 基本使用

### 1. 搜索赏金任务
```bash
python3 enhanced_bounty_agent.py search --limit 20
```

### 2. 处理单个任务
```bash
python3 enhanced_bounty_agent.py single --repo owner/repo --issue 123
```

### 3. 批量处理任务（推荐）
```bash
# 默认目标10个PR
python3 enhanced_bounty_agent.py batch

# 自定义目标PR数量和并行数
python3 enhanced_bounty_agent.py batch --target-pr-count 20 --max-parallel 5
```

### 4. 验证PR质量
```bash
python3 enhanced_bounty_agent.py validate --repo owner/repo --pr 456
```

# ===================== 核心模块 =====================

## 1. 主流赏金平台集成 (bounty_platforms.py)
支持的平台：
- Gitcoin
- Algorand Foundation
- Ethereum Foundation
- Solana Foundation

使用示例：
```python
from bounty_platforms import BountyPlatformManager

manager = BountyPlatformManager(token)
bounties = manager.search_all_platforms(limit_per_platform=10)
bounties = manager.rank_bounties(bounties)
```

## 2. 贡献指南解析 (contributing_parser.py)
自动解析项目的CONTRIBUTING.md，生成符合规范的PR。

使用示例：
```python
from contributing_parser import ContributingGuideParser, PRGenerator

parser = ContributingGuideParser(token)
guidelines = parser.parse_full_guide("owner/repo")

generator = PRGenerator(guidelines)
pr_title = generator.generate_pr_title("fix", "Fix bug", 123)
pr_description = generator.generate_pr_description(issue, changes, tests)
```

## 3. 代码修复AI (code_fix_ai.py)
集成LLM进行代码分析和修复方案生成。

使用示例：
```python
from code_fix_ai import CodeAnalyzer, IssueAnalyzer, CodeFixGenerator

analyzer = CodeAnalyzer(repo_path)
language = analyzer.detect_language()

issue_analyzer = IssueAnalyzer()
issue_type = issue_analyzer.classify_issue_type(issue)

fix_generator = CodeFixGenerator(api_key)
fix_plan = fix_generator.generate_fix_plan(issue, code_analysis, repo_info)
```

## 4. CI/CD流水线 (ci_pipeline_runner.py)
自动检测项目的CI/CD配置，运行测试和代码检查。

使用示例：
```python
from ci_pipeline_runner import TestRunner, CIPipelineDetector

detector = CIPipelineDetector(repo_path)
ci_info = detector.detect_ci_system()

runner = TestRunner(repo_path)
test_results = runner.run_tests()
lint_results = runner.run_linters()
build_results = runner.check_build()

# 运行完整流水线
pipeline_results = runner.run_full_ci_pipeline()
```

## 5. 批量任务调度 (batch_scheduler.py)
每天自动运行，处理多个赏金任务，支持并行处理。

使用示例：
```python
from batch_scheduler import TaskScheduler

scheduler = TaskScheduler(token, username, work_dir)
results = scheduler.run_daily_batch(target_pr_count=10)

print(f"创建的PR数: {results['prs_created']}")
print(f"PR链接: {results['pr_urls']}")
```

## 6. PR质量验证 (pr_quality_validator.py)
自动检测PR质量问题并尝试自动修复。

使用示例：
```python
from pr_quality_validator import PRQualityValidator, AutoFixer

validator = PRQualityValidator(token, repo_path)
validation_result = validator.validate_pr("owner/repo", 123)

fixer = AutoFixer(repo_path, token)
fix_result = fixer.auto_fix_pr_issues(validation_result, "owner/repo", 123)
```

# ===================== 高级功能 =====================

## 使用OpenAI API增强代码分析

```python
from code_fix_ai import CodeFixGenerator

# 设置OpenAI API Key
export OPENAI_API_KEY="your_openai_api_key"

# 使用时自动调用LLM增强分析
fix_generator = CodeFixGenerator()
fix_plan = fix_generator.generate_fix_plan(issue, code_analysis, repo_info)
```

## 自定义任务筛选

```python
from bounty_platforms import BountyPlatformManager

manager = BountyPlatformManager(token)
bounties = manager.search_all_platforms()

# 自定义筛选条件
filtered = manager.filter_by_criteria(
    bounties,
    min_bounty=100,  # 最小赏金金额
    languages=["Python", "JavaScript"],  # 编程语言
    min_comments=0,  # 最小评论数
    days_old=30  # 最近30天
)
```

## 并行处理多个任务

```python
from concurrent.futures import ThreadPoolExecutor

def process_task(bounty):
    # 处理单个任务
    return result

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_task, bounty) for bounty in bounties]
    results = [f.result() for f in as_completed(futures)]
```

# ===================== 工作流程 =====================

## 完整的自动化流程

1. **搜索任务**
   - 搜索主流平台的赏金任务
   - 评估任务难度和可行性
   - 排序和筛选最佳任务

2. **分析任务**
   - Fork并克隆仓库
   - 分析代码库结构
   - 解析贡献指南
   - 生成修复方案

3. **实施修复**
   - 创建新分支
   - 实施代码修改
   - 运行测试
   - 代码检查

4. **提交PR**
   - 提交代码
   - 推送到远程
   - 创建PR（符合项目规范）

5. **验证质量**
   - 检查CI/CD状态
   - 验证PR质量
   - 自动修复问题

# ===================== 配置选项 =====================

## 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| GITHUB_TOKEN | GitHub Personal Access Token | ✅ |
| GITHUB_USERNAME | GitHub用户名 | ✅ |
| OPENAI_API_KEY | OpenAI API密钥（可选） | ❌ |
| WORK_DIR | 工作目录（默认：./workspace） | ❌ |

## GitHub Token权限

需要以下权限：
- `repo` - 完整仓库访问权限
- `public_repo` - 访问公共仓库
- `workflow` - 操作Actions（可选）

# ===================== 注意事项 =====================

1. **API限制**：GitHub API有速率限制，注意控制调用频率
2. **代码质量**：确保提交的代码符合项目规范
3. **测试优先**：在正式使用前，先在小项目上测试
4. **人工审核**：重要PR建议人工审核后再提交
5. **合规性**：遵守GitHub的服务条款和项目的贡献指南

# ===================== 故障排除 =====================

## Fork失败
- 检查Token权限
- 确认仓库是否允许Fork
- 检查API配额

## 测试失败
- 检查测试配置
- 查看测试输出
- 确认测试框架正确安装

## PR创建失败
- 确认代码已推送
- 检查分支名称
- 确认目标仓库接受PR

# ===================== 最佳实践 =====================

1. **批量处理**：使用批量模式，每天处理10+个任务
2. **并行执行**：使用多线程并行处理，提高效率
3. **质量优先**：确保代码质量和测试覆盖
4. **持续优化**：根据反馈持续优化Agent
5. **学习改进**：从成功/失败的PR中学习

# ===================== 下一步计划 =====================

- [ ] 添加更多赏金平台支持
- [ ] 增强AI代码生成能力
- [ ] 实现自动回复PR评论
- [ ] 添加任务优先级排序
- [ ] 从PR中学习改进
- [ ] 智能选择最佳赏金任务
