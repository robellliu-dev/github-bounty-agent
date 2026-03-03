#!/usr/bin/env python3
"""
在OpenCode中实际使用GitHub Bounty Agent查找真实的GitHub赏金任务
"""

import os
import sys
import requests
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🔍 使用GitHub Bounty Agent查找真实赏金任务")
print("=" * 70)

# 设置环境变量（使用你的账号信息）
os.environ["GITHUB_USERNAME"] = "robellliu-dev"

print("\n📋 账户配置:")
print(f"   用户名: robellliu-dev")

# 检查是否有token
token = os.getenv("GITHUB_TOKEN")

if not token:
    print("\n⚠️  需要GitHub Personal Access Token")
    print("\n请按以下步骤创建Token:")
    print("\n1️⃣  访问: https://github.com/settings/tokens")
    print("2️⃣  点击 'Generate new token' → 'Generate new token (classic)'")
    print("3️⃣  选择权限:")
    print("     ✅ repo (完整仓库访问)")
    print("     ✅ public_repo (访问公共仓库)")
    print("4️⃣  点击生成，复制token")
    print("\n5️⃣  然后设置环境变量:")
    print("     export GITHUB_TOKEN='your_copied_token'")
    print("\n或者直接在下面输入token (仅演示用，不会保存):")
else:
    print("\n✅ GitHub Token 已设置")

# 尝试使用API直接搜索真实的GitHub issues
print("\n" + "-" * 70)
print("🔍 搜索GitHub上带有赏金标签的issues")
print("-" * 70)

if token:
    print("\n使用Token进行搜索...")
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 搜索带有bounty、good first issue、help wanted标签的issues
    queries = [
        'label:"good first issue" is:issue is:open language:python',
        'label:"help wanted" is:issue is:open language:python',
        'label:"bounty" is:issue is:open'
    ]
    
    all_issues = []
    
    for query in queries:
        print(f"\n搜索: {query}")
        
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
    
    # 显示结果
    if all_issues:
        print("\n" + "-" * 70)
        print("✅ 找到以下潜在赏金任务:")
        print("-" * 70)
        
        # 去重
        seen = set()
        unique_issues = []
        for issue in all_issues:
            key = f"{issue['repository_url']}#{issue['number']}"
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        for i, issue in enumerate(unique_issues[:10], 1):
            repo_url = issue["repository_url"]
            parts = repo_url.split("/")
            owner = parts[-2]
            repo_name = parts[-1]
            
            print(f"\n{i}. {issue['title']}")
            print(f"   仓库: {owner}/{repo_name}")
            print(f"   链接: {issue['html_url']}")
            print(f"   标签: {', '.join([l['name'] for l in issue.get('labels', [])])}")
            print(f"   评论: {issue.get('comments', 0)}")
            print(f"   创建: {issue['created_at'][:10]}")
        
        print("\n" + "-" * 70)
        print("💡 提示:")
        print("-" * 70)
        print("\n这些是GitHub上标记为'good first issue'或'help wanted'的任务")
        print("虽然不是直接的赏金任务，但很多项目会为这些任务提供报酬")
        print("\n要使用Agent自动处理这些任务:")
        print("1. 选择一个感兴趣的任务")
        print("2. 运行: python3 opencode_agent.py --action process --auto")
        print("3. Agent会自动Fork、克隆、修改、测试、提交PR")
        
    else:
        print("\n未找到匹配的issues")
else:
    print("\n⏭️  请先设置GITHUB_TOKEN环境变量后再运行")
    print("\n设置方法:")
    print("export GITHUB_TOKEN='your_token_here'")
    print("python3 real_search.py")

print("\n" + "=" * 70)
print("✅ 搜索完成")
print("=" * 70 + "\n")
