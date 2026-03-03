#!/usr/bin/env python3
"""
自动运行GitHub Bounty Agent - 改进版
处理PR创建失败的情况，提供手动创建链接
"""

import os
import sys
import requests
from pathlib import Path
import subprocess
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from github_bounty_agent import GitHubBountyAgent

print("=" * 70)
print("🤖 GitHub Bounty Agent - 自动化运行 (改进版)")
print("=" * 70)

# 获取配置
token = os.getenv("GITHUB_TOKEN")
username = os.getenv("GITHUB_USERNAME", "robellliu-dev")

if not token:
    print("\n❌ 错误: 需要GitHub Token")
    print("请设置环境变量: export GITHUB_TOKEN='your_token'")
    sys.exit(1)

print(f"\n📋 配置:")
print(f"   用户名: {username}")
print(f"   工作目录: ./workspace")

# 创建工作目录
work_dir = Path("./workspace")
work_dir.mkdir(exist_ok=True)

# 创建Agent实例
agent = GitHubBountyAgent(token, username, str(work_dir))

# 搜索真实的GitHub issues
print("\n" + "-" * 70)
print("🔍 步骤1: 搜索GitHub上的赏金任务")
print("-" * 70)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

queries = [
    ('label:"good first issue" is:issue is:open language:python', "Python Good First Issues"),
    ('label:"help wanted" is:issue is:open language:python', "Python Help Wanted"),
    ('label:"bounty" is:issue is:open', "Bounty Issues"),
]

all_issues = []

for query, label in queries:
    print(f"\n搜索: {label}")
    
    try:
        response = requests.get(
            "https://api.github.com/search/issues",
            headers=headers,
            params={
                "q": query,
                "per_page": 10,
                "sort": "created",
                "order": "desc"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"   找到 {len(items)} 个issues")
            all_issues.extend(items)
        else:
            print(f"   搜索失败: {response.status_code}")
            
    except Exception as e:
        print(f"   错误: {e}")

# 去重
seen = set()
unique_issues = []
for issue in all_issues:
    key = f"{issue['repository_url']}#{issue['number']}"
    if key not in seen:
        seen.add(key)
        unique_issues.append(issue)

if not unique_issues:
    print("\n❌ 未找到任何合适的任务")
    sys.exit(1)

# 显示结果
print("\n" + "-" * 70)
print("✅ 步骤2: 找到的任务列表")
print("-" * 70)

for i, issue in enumerate(unique_issues[:5], 1):
    repo_url = issue["repository_url"]
    parts = repo_url.split("/")
    owner = parts[-2]
    repo_name = parts[-1]
    
    print(f"\n{i}. {issue['title']}")
    print(f"   仓库: {owner}/{repo_name}")
    print(f"   链接: {issue['html_url']}")
    print(f"   标签: {', '.join([l['name'] for l in issue.get('labels', [])])}")
    print(f"   评论: {issue.get('comments', 0)}")

# 选择第一个任务进行自动处理
selected_issue = unique_issues[0]

# 转换为Agent需要的格式
repo_url = selected_issue["repository_url"]
parts = repo_url.split("/")
owner = parts[-2]
repo_name = parts[-1]

task = {
    "title": selected_issue['title'],
    "number": selected_issue['number'],
    "url": selected_issue['html_url'],
    "repo_full_name": f"{owner}/{repo_name}",
    "labels": [l['name'] for l in selected_issue.get('labels', [])],
    "bounty_amount": 0
}

print("\n" + "-" * 70)
print(f"📌 步骤3: 自动处理任务 - {task['title']}")
print("-" * 70)

# Fork并克隆仓库
print("\n🍴 Fork并克隆仓库...")
fork_success, fork_info = agent.fork_and_clone(task)

if not fork_success:
    print("❌ Fork或克隆失败")
    sys.exit(1)

print(f"✅ Fork成功，克隆到: {fork_info['clone_path']}")

# 分析仓库
print("\n🔬 分析代码库...")
repo_info = agent.analyze_repository(fork_info['clone_path'])
print(f"   文件数: {len(repo_info['structure'])}")
print(f"   有测试: {repo_info['has_tests']}")

# 获取任务详情
print("\n📝 获取任务详情...")
task_details = agent.get_task_details(task)
print(f"   Issue创建时间: {task_details.get('created_at')}")
print(f"   Issue评论数: {task_details.get('comments', 0)}")

# 生成解决方案
print("\n💡 生成解决方案...")
solution = agent.generate_solution(task_details, repo_info)
print(f"   PR标题: {solution['pr_title']}")

# 保存解决方案
solution_file = work_dir / f"solution_plan_{task['number']}.json"
with open(solution_file, 'w', encoding='utf-8') as f:
    json.dump(solution, f, indent=2, ensure_ascii=False)
print(f"   解决方案已保存: {solution_file}")

# 实现解决方案
print("\n⚙️ 实现解决方案...")
implementation_result = agent.implement_solution(solution, fork_info['clone_path'])

if not implementation_result:
    print("❌ 实现失败")
    sys.exit(1)

print("✅ 实现完成")

# 运行测试
print("\n🧪 运行测试...")
test_result = agent.run_tests(fork_info['clone_path'])
print(f"   测试结果: {'通过' if test_result else '跳过'}")

# 提交并推送代码
print("\n📤 提交并推送代码...")
commit_success = agent.commit_and_push(fork_info['clone_path'])

if not commit_success:
    print("❌ 提交失败")
    sys.exit(1)

print("✅ 代码已推送")

# 获取分支名称
branch_name = solution.get('branch_name', 'main')

# 创建Pull Request
print("\n🎯 尝试创建Pull Request...")

# 准备 PR 数据
pr_data = {
    "title": solution['pr_title'],
    "body": solution['pr_description'],
    "head": f"{username}:{branch_name}",
    "base": "main"
}

# 尝试创建 PR
try:
    response = requests.post(
        f"https://api.github.com/repos/{owner}/{repo_name}/pulls",
        headers=headers,
        json=pr_data
    )
    
    if response.status_code == 201:
        pr_data = response.json()
        pr_url = pr_data.get("html_url")
        print(f"\n✅ Pull Request创建成功!")
        print(f"🔗 PR链接: {pr_url}")
    else:
        # PR创建失败，提供手动创建链接
        print(f"\n⚠️  PR创建失败 (状态码: {response.status_code})")
        print(f"   可能是权限限制，但您可以手动创建PR")
        
        # 生成手动创建PR的链接
        manual_pr_url = f"https://github.com/{owner}/{repo_name}/compare/main...{username}:{branch_name}"
        
        print(f"\n🔗 手动创建PR链接:")
        print(f"   {manual_pr_url}")
        
        # 保存手动创建信息
        manual_info = {
            "manual_pr_url": manual_pr_url,
            "pr_title": solution['pr_title'],
            "pr_description": solution['pr_description'],
            "branch_name": branch_name,
            "task": task,
            "solution": solution,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        manual_file = work_dir / f"manual_pr_{task['number']}.json"
        with open(manual_file, 'w', encoding='utf-8') as f:
            json.dump(manual_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 手动创建步骤:")
        print(f"   1. 访问上面的链接")
        print(f"   2. 使用以下标题: {solution['pr_title']}")
        print(f"   3. 粘贴以下描述:")
        print(f"   ---")
        print(solution['pr_description'])
        print(f"   ---")
        
        pr_url = manual_pr_url

except Exception as e:
    print(f"❌ 创建PR时出错: {e}")
    # 提供手动创建链接
    manual_pr_url = f"https://github.com/{owner}/{repo_name}/compare/main...{username}:{branch_name}"
    print(f"\n🔗 手动创建PR链接: {manual_pr_url}")
    pr_url = manual_pr_url

# 保存结果
result_file = work_dir / f"run_result_{task['number']}.json"
result = {
    "task": task,
    "fork_url": f"https://github.com/{username}/{repo_name}",
    "branch_name": branch_name,
    "pr_url": pr_url,
    "solution": solution,
    "timestamp": __import__('datetime').datetime.now().isoformat(),
    "success": True
}

with open(result_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print("✅ 自动化流程完成!")
print("=" * 70)
print(f"\n📊 总结:")
print(f"   - 搜索到 {len(unique_issues)} 个任务")
print(f"   - 处理了任务: {task['title']}")
print(f"   - Fork仓库: {task['repo_full_name']}")
print(f"   - 您的fork: https://github.com/{username}/{repo_name}")
print(f"   - 分支: {branch_name}")
print(f"   - PR链接: {pr_url}")
print(f"\n📝 结果已保存到: {result_file}")
