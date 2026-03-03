#!/usr/bin/env python3
"""
GitHub Bounty Agent - 完整演示
展示如何自动查找、分析、fork 并提交 PR 到悬赏项目
"""

import os
import sys
import requests
from pathlib import Path
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🤖 GitHub Bounty Agent - 完整自动化演示")
print("=" * 80)

# 获取配置
token = os.getenv("GITHUB_TOKEN")
username = os.getenv("GITHUB_USERNAME", "robellliu-dev")

if not token:
    print("\n❌ 错误: 需要GitHub Token")
    print("请设置环境变量: export GITHUB_TOKEN='your_token'")
    sys.exit(1)

print(f"\n📋 配置:")
print(f"   用户名: {username}")
print(f"   Token: {'已设置' if token else '未设置'}")

# 搜索配置
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

# 步骤1: 搜索悬赏任务
print("\n" + "=" * 80)
print("🔍 步骤1: 搜索 GitHub 悬赏任务")
print("=" * 80)

search_queries = [
    ('label:"good first issue" is:issue is:open language:python', "Python Good First Issues"),
    ('label:"help wanted" is:issue is:open language:python', "Python Help Wanted"),
    ('label:"bug" is:issue is:open language:python', "Python Bug Reports"),
    ('label:"enhancement" is:issue is:open language:python', "Python Enhancement Requests"),
]

all_issues = []

for query, label in search_queries:
    print(f"\n📂 搜索: {label}")
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
            print(f"   ✅ 找到 {len(items)} 个 issues")
            all_issues.extend(items)
        else:
            print(f"   ❌ 搜索失败: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 错误: {e}")

# 去重
seen = set()
unique_issues = []
for issue in all_issues:
    key = f"{issue['repository_url']}#{issue['number']}"
    if key not in seen:
        seen.add(key)
        unique_issues.append(issue)

# 步骤2: 分析和评分
print("\n" + "=" * 80)
print("📊 步骤2: 分析任务可行性")
print("=" * 80)

scored_issues = []
for issue in unique_issues[:20]:  # 只分析前20个
    try:
        repo_url = issue["repository_url"]
        parts = repo_url.split("/")
        owner = parts[-2]
        repo_name = parts[-1]
        
        # 获取仓库统计信息
        repo_response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}",
            headers=headers
        )
        
        if repo_response.status_code == 200:
            repo_data = repo_response.json()
            
            # 计算分数
            score = 0
            factors = []
            
            # 星星数
            stars = repo_data.get("stargazers_count", 0)
            if stars > 1000:
                score += 5
                factors.append(f"高活跃度 ({stars} stars)")
            elif stars > 100:
                score += 3
                factors.append(f"中等活跃度 ({stars} stars)")
            elif stars > 10:
                score += 1
                factors.append(f"一定关注度 ({stars} stars)")
            
            # 标签分析
            labels = [l['name'].lower() for l in issue.get('labels', [])]
            if 'good first issue' in labels:
                score += 4
                factors.append("适合新手")
            elif 'help wanted' in labels:
                score += 3
                factors.append("需要帮助")
            elif 'bug' in labels:
                score += 2
                factors.append("Bug修复")
            
            # 讨论程度
            comments = issue.get('comments', 0)
            if comments == 0:
                score += 2
                factors.append("无评论，竞争少")
            elif comments < 5:
                score += 1
                factors.append("少评论")
            elif comments > 10:
                score -= 2
                factors.append("多评论，竞争大")
            
            # 语言流行度
            language = repo_data.get('language', '')
            if language in ['Python', 'JavaScript', 'TypeScript', 'Go']:
                score += 1
                factors.append(f"流行语言: {language}")
            
            # 最近更新
            updated = repo_data.get('updated_at', '')
            if updated:
                # 简化的时间检查
                if '2026' in updated or '2025' in updated:
                    score += 1
                    factors.append("最近活跃")
            
            scored_issues.append({
                "title": issue['title'],
                "number": issue['number'],
                "repo_full_name": f"{owner}/{repo_name}",
                "url": issue['html_url'],
                "labels": [l['name'] for l in issue.get('labels', [])],
                "score": score,
                "factors": factors,
                "stars": stars,
                "comments": comments,
                "language": language
            })
            
    except Exception as e:
        continue

# 按分数排序
scored_issues.sort(key=lambda x: x['score'], reverse=True)

# 显示排名
print(f"\n✅ 分析了 {len(scored_issues)} 个任务")
print("\n🏆 推荐任务 (按可行性排序):")
print("-" * 80)

for i, issue in enumerate(scored_issues[:10], 1):
    emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
    print(f"\n{emoji} #{i} - 分数: {issue['score']}")
    print(f"   标题: {issue['title']}")
    print(f"   仓库: {issue['repo_full_name']} ⭐{issue['stars']} | 💬{issue['comments']}")
    print(f"   语言: {issue['language']}")
    print(f"   标签: {', '.join(issue['labels'][:3])}")
    print(f"   理由: {', '.join(issue['factors'][:3])}")
    print(f"   链接: {issue['url']}")

# 步骤3: 选择最佳任务并自动处理
if scored_issues:
    best_task = scored_issues[0]
    
    print("\n" + "=" * 80)
    print("📌 步骤3: 自动处理最佳任务")
    print("=" * 80)
    
    print(f"\n选择任务: {best_task['title']}")
    print(f"分数: {best_task['score']}")
    print(f"仓库: {best_task['repo_full_name']}")
    
    # 调用自动化处理脚本
    print("\n🚀 开始自动化处理...")
    
    # 导入自动化模块
    from github_bounty_agent import GitHubBountyAgent
    
    # 转换为 Agent 需要的格式
    task = {
        "title": best_task['title'],
        "number": best_task['number'],
        "url": best_task['url'],
        "repo_full_name": best_task['repo_full_name'],
        "labels": best_task['labels'],
        "bounty_amount": 0
    }
    
    # 创建 Agent
    work_dir = Path("./workspace")
    work_dir.mkdir(exist_ok=True)
    agent = GitHubBountyAgent(token, username, str(work_dir))
    
    # Fork 并克隆
    print("\n🍴 Fork 并克隆仓库...")
    fork_success, fork_info = agent.fork_and_clone(task)
    
    if fork_success:
        print(f"✅ Fork 成功，克隆到: {fork_info['clone_path']}")
        
        # 分析仓库
        print("\n🔬 分析代码库...")
        repo_info = agent.analyze_repository(fork_info['clone_path'])
        
        # 获取详情
        print("\n📝 获取任务详情...")
        task_details = agent.get_task_details(task)
        
        # 生成解决方案
        print("\n💡 生成解决方案...")
        solution = agent.generate_solution(task_details, repo_info)
        
        # 保存方案
        solution_file = work_dir / f"solution_plan_{task['number']}.json"
        with open(solution_file, 'w', encoding='utf-8') as f:
            json.dump(solution, f, indent=2, ensure_ascii=False)
        
        # 实现方案
        print("\n⚙️ 实现解决方案...")
        agent.implement_solution(solution, fork_info['clone_path'])
        
        # 运行测试
        print("\n🧪 运行测试...")
        agent.run_tests(fork_info['clone_path'])
        
        # 提交推送
        print("\n📤 提交并推送代码...")
        if agent.commit_and_push(fork_info['clone_path']):
            print("✅ 代码已推送")
            
            # 尝试创建 PR
            print("\n🎯 尝试创建 Pull Request...")
            
            owner, repo = best_task['repo_full_name'].split('/')
            branch_name = solution.get('branch_name', 'main')
            
            pr_data = {
                "title": solution['pr_title'],
                "body": solution['pr_description'],
                "head": f"{username}:{branch_name}",
                "base": "main"
            }
            
            try:
                response = requests.post(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls",
                    headers=headers,
                    json=pr_data
                )
                
                if response.status_code == 201:
                    pr = response.json()
                    print(f"✅ Pull Request 创建成功!")
                    print(f"🔗 PR 链接: {pr.get('html_url')}")
                    pr_url = pr.get('html_url')
                else:
                    # 提供手动创建链接
                    manual_pr_url = f"https://github.com/{owner}/{repo}/compare/main...{username}:{branch_name}"
                    print(f"⚠️  PR 创建失败，请手动创建:")
                    print(f"🔗 {manual_pr_url}")
                    pr_url = manual_pr_url
                    
            except Exception as e:
                print(f"❌ 创建 PR 时出错: {e}")
                pr_url = None
            
            # 保存最终结果
            result = {
                "task": best_task,
                "fork_url": f"https://github.com/{username}/{repo}",
                "branch_name": branch_name,
                "pr_url": pr_url,
                "solution": solution,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            
            result_file = work_dir / f"demo_result_{task['number']}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n📝 结果已保存到: {result_file}")
        else:
            print("❌ 代码推送失败")
    else:
        print("❌ Fork 或克隆失败")

# 总结
print("\n" + "=" * 80)
print("✅ 演示完成!")
print("=" * 80)

if scored_issues:
    print(f"\n📊 总结:")
    print(f"   - 搜索到 {len(unique_issues)} 个任务")
    print(f"   - 分析了 {len(scored_issues)} 个任务")
    print(f"   - 推荐最佳任务: {scored_issues[0]['title']}")
    print(f"   - 可行性分数: {scored_issues[0]['score']}")
    
    print(f"\n💡 下一步操作:")
    print(f"   1. 查看分析结果和推荐任务")
    print(f"   2. 访问任务链接了解详情")
    print(f"   3. 运行自动化脚本处理任务")
    print(f"   4. 查看 workspace 目录中的结果文件")

print("\n" + "=" * 80)
