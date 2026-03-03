#!/usr/bin/env python3
"""
在OpenCode中使用GitHub Bounty Agent的演示
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🤖 在OpenCode中使用 GitHub Bounty Agent")
print("=" * 70)

# 检查环境变量
print("\n📋 检查环境配置...")

token = os.getenv("GITHUB_TOKEN")
username = os.getenv("GITHUB_USERNAME")

if not token:
    print("\n⚠️  GITHUB_TOKEN 未设置")
    print("   要使用完整功能，请创建GitHub Personal Access Token:")
    print("   1. 访问: https://github.com/settings/tokens")
    print("   2. 点击 'Generate new token' → 'Generate new token (classic)'")
    print("   3. 选择权限: repo, public_repo")
    print("   4. 复制token")
    print("\n   然后设置环境变量:")
    print("   export GITHUB_TOKEN='your_token_here'")
    print("   export GITHUB_USERNAME='robellliu-dev'")
    
if not username:
    print("\n⚠️  GITHUB_USERNAME 未设置")
    print("   export GITHUB_USERNAME='robellliu-dev'")

print("\n" + "-" * 70)
print("📚 可用的Agent方法:")
print("-" * 70)

print("\n1️⃣  OpenCodeBountyAgent - OpenCode集成接口")
print("   from opencode_agent import OpenCodeBountyAgent")
print("   agent = OpenCodeBountyAgent()")
print("   result = agent.process_bounty(languages=['python'])")

print("\n2️⃣  GitHubBountyAgent - 核心Agent")
print("   from github_bounty_agent import GitHubBountyAgent")
print("   agent = GitHubBountyAgent(token, username)")
print("   agent.auto_run(languages=['python'])")

print("\n" + "-" * 70)
print("🔍 演示模式 - 查找赏金任务（无需token）")
print("-" * 70)

try:
    # 导入并创建demo agent
    from opencode_agent import OpenCodeBountyAgent
    
    # 设置临时的测试环境
    os.environ["GITHUB_TOKEN"] = "demo_token_for_testing"
    os.environ["GITHUB_USERNAME"] = "robellliu-dev"
    
    # 创建agent
    agent = OpenCodeBountyAgent()
    
    print(f"\n✅ Agent创建成功")
    print(f"   用户名: {agent.username}")
    print(f"   工作目录: {agent.work_dir}")
    
    # 查找任务
    print("\n🔍 正在查找赏金任务...")
    tasks = agent.find_bounty_tasks(languages=["python", "javascript"], limit=5)
    
    print(f"\n✅ 找到 {len(tasks)} 个任务:")
    for i, task in enumerate(tasks, 1):
        print(f"\n   {i}. {task['title']}")
        print(f"      仓库: {task['repo_full_name']}")
        print(f"      标签: {', '.join(task['labels'])}")
        if task.get('bounty_amount'):
            print(f"      💰 赏金: ${task['bounty_amount']}")
    
    print("\n" + "-" * 70)
    print("🎯 下一步 - 处理赏金任务")
    print("-" * 70)
    
    print("\n要处理赏金任务，需要真实的GitHub Token:")
    print("\n设置环境变量:")
    print("  export GITHUB_TOKEN='your_real_token'")
    print("  export GITHUB_USERNAME='robellliu-dev'")
    print("\n然后运行:")
    print("  python3 opencode_agent.py --action process --languages python --auto")
    
    print("\n或者在OpenCode中调用:")
    print("  from opencode_agent import OpenCodeBountyAgent")
    print("  agent = OpenCodeBountyAgent()")
    print("  result = agent.process_bounty(languages=['python'], auto_confirm=False)")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ 演示完成")
print("=" * 70 + "\n")
