#!/usr/bin/env python3
"""
测试GitHub Bounty Agent的功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from github_bounty_agent import GitHubBountyAgent


def test_search_tasks():
    """测试搜索任务功能"""
    print("\n" + "=" * 60)
    print("🧪 测试1: 搜索任务")
    print("=" * 60)
    
    # 使用mock token测试
    agent = GitHubBountyAgent("test_token", "test_user")
    
    tasks = agent.search_bounty_tasks()
    
    print(f"✅ 找到 {len(tasks)} 个测试任务")
    for task in tasks:
        print(f"   - {task['title']}")
    
    return len(tasks) > 0


def test_analyze_repo():
    """测试仓库分析功能"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 仓库分析")
    print("=" * 60)
    
    agent = GitHubBountyAgent("test_token", "test_user")
    
    # 测试分析当前项目
    repo_info = agent.analyze_repository(Path.cwd())
    
    print(f"✅ 分析完成")
    print(f"   文件数: {len(repo_info['structure'])}")
    print(f"   有测试: {repo_info['has_tests']}")
    
    return True


def test_generate_solution():
    """测试生成解决方案"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 生成解决方案")
    print("=" * 60)
    
    agent = GitHubBountyAgent("test_token", "test_user")
    
    task_details = {
        "title": "Test Issue",
        "number": 123,
        "body": "This is a test issue description"
    }
    
    repo_info = agent.analyze_repository(Path.cwd())
    
    solution = agent.generate_solution(task_details, repo_info)
    
    print(f"✅ 解决方案生成完成")
    print(f"   PR标题: {solution['pr_title']}")
    print(f"   包含分析: {len(solution['analysis']) > 0}")
    
    return 'pr_title' in solution


def run_all_tests():
    """运行所有测试"""
    print("\n🔬 开始测试 GitHub Bounty Agent\n")
    
    tests = [
        test_search_tasks,
        test_analyze_repo,
        test_generate_solution
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"❌ {test.__name__} 失败: {e}")
            results.append((test.__name__, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
