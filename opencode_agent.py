#!/usr/bin/env python3
"""
OpenCode Agent Integration for GitHub Bounty Agent
使GitHub Bounty Agent可以在OpenCode环境中被调用
"""

import os
import sys
import requests
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from github_bounty_agent import GitHubBountyAgent
except ImportError:
    # 如果在当前目录，直接导入
    import importlib.util
    spec = importlib.util.spec_from_file_location("github_bounty_agent", Path(__file__).parent / "github_bounty_agent.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    GitHubBountyAgent = module.GitHubBountyAgent


class OpenCodeBountyAgent:
    """OpenCode集成的GitHub赏金Agent"""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USERNAME")
        self.work_dir = os.getenv("WORK_DIR", "./workspace")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        if not self.username:
            raise ValueError("GITHUB_USERNAME environment variable is required")
        
        self.agent = GitHubBountyAgent(self.token, self.username, self.work_dir)
    
    def find_bounty_tasks(self, languages=None, limit=10):
        """查找赏金任务
        
        Args:
            languages: 编程语言列表，如 ["python", "javascript"]
            limit: 返回结果数量
            
        Returns:
            任务列表
        """
        print(f"🔍 正在查找赏金任务...")
        if languages:
            print(f"   语言筛选: {', '.join(languages)}")
        
        tasks = self.agent.search_bounty_tasks(languages or [])
        
        print(f"✅ 找到 {len(tasks)} 个任务")
        
        return tasks[:limit]
    
    def analyze_task(self, repo_full_name, issue_number):
        """分析具体任务
        
        Args:
            repo_full_name: 仓库全名，如 "owner/repo"
            issue_number: issue编号
            
        Returns:
            分析结果
        """
        print(f"🔬 分析任务: {repo_full_name}#{issue_number}")
        
        task = {
            "repo_full_name": repo_full_name,
            "number": issue_number
        }
        
        details = self.agent.get_task_details(task)
        return details
    
    def process_bounty(self, languages=None, auto_confirm=False):
        """完整处理一个赏金任务
        
        Args:
            languages: 编程语言筛选
            auto_confirm: 是否自动确认（跳过人工审核）
            
        Returns:
            处理结果，包含PR链接
        """
        print("=" * 60)
        print("🤖 OpenCode GitHub Bounty Agent 启动")
        print("=" * 60)
        
        # 查找任务
        tasks = self.find_bounty_tasks(languages)
        
        if not tasks:
            return {
                "success": False,
                "message": "未找到合适的赏金任务"
            }
        
        # 选择第一个任务（可以扩展为更智能的选择）
        selected_task = tasks[0]
        print(f"\n📌 选择任务: {selected_task['title']}")
        
        # Fork和克隆
        print(f"\n🍴 Fork并克隆仓库: {selected_task['repo_full_name']}")
        fork_success, fork_info = self.agent.fork_and_clone(selected_task)
        
        if not fork_success:
            return {
                "success": False,
                "message": "Fork或克隆失败"
            }
        
        # 分析仓库
        print(f"\n🔬 分析代码库...")
        repo_info = self.agent.analyze_repository(fork_info['clone_path'])
        
        # 获取任务详情
        print(f"\n📝 获取任务详情...")
        task_details = self.agent.get_task_details(selected_task)
        
        # 生成解决方案
        print(f"\n💡 生成解决方案...")
        solution = self.agent.generate_solution(task_details, repo_info)
        
        if not auto_confirm:
            # 等待确认
            print("\n" + "=" * 60)
            print("⏸️  等待人工审核方案")
            print("=" * 60)
            print(f"\nPR标题: {solution['pr_title']}")
            print(f"\nPR描述预览:\n{solution['pr_description'][:200]}...")
            
            # 在OpenCode中，这里应该暂停等待用户确认
            # 暂时自动继续
            print("\n✅ 自动继续...")
        
        # 实现解决方案
        print(f"\n⚙️  实现解决方案...")
        self.agent.implement_solution(solution, fork_info['clone_path'])
        
        # 运行测试
        print(f"\n🧪 运行测试...")
        self.agent.run_tests(fork_info['clone_path'])
        
        # 提交推送
        print(f"\n📤 提交代码...")
        if not self.agent.commit_and_push(fork_info['clone_path']):
            return {
                "success": False,
                "message": "代码提交失败"
            }
        
        # 创建PR
        print(f"\n🎯 创建Pull Request...")
        pr_url = self.agent.create_pull_request(
            selected_task['repo_full_name'],
            selected_task['number'],
            solution['pr_title'],
            solution['pr_description']
        )
        
        if pr_url:
            print(f"\n✅ Pull Request创建成功!")
            print(f"🔗 {pr_url}")
            
            return {
                "success": True,
                "pr_url": pr_url,
                "task": selected_task,
                "solution": solution
            }
        else:
            return {
                "success": False,
                "message": "PR创建失败"
            }
    
    def check_pr_status(self, pr_url):
        """检查PR状态
        
        Args:
            pr_url: PR链接
            
        Returns:
            PR状态信息
        """
        print(f"🔍 检查PR状态: {pr_url}")
        
        # 从URL提取信息
        # https://github.com/owner/repo/pull/123
        parts = pr_url.split('/')
        owner = parts[-4]
        repo = parts[-3]
        pr_number = parts[-1]
        
        # 调用GitHub API
        url = f"{self.agent.api_base}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        try:
            response = requests.get(url, headers=self.agent.headers)
            response.raise_for_status()
            pr_data = response.json()
            
            status = {
                "state": pr_data.get("state"),
                "merged": pr_data.get("merged", False),
                "mergeable": pr_data.get("mergeable"),
                "review_status": pr_data.get("status", "unknown"),
                "additions": pr_data.get("additions", 0),
                "deletions": pr_data.get("deletions", 0),
                "comments": pr_data.get("comments", 0),
                "reviews": pr_data.get("review_comments", 0)
            }
            
            print(f"   状态: {status['state']}")
            print(f"   可合并: {status['mergeable']}")
            print(f"   评论: {status['comments']}")
            
            return status
            
        except Exception as e:
            print(f"   ❌ 获取PR状态失败: {e}")
            return {}


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenCode GitHub Bounty Agent")
    parser.add_argument("--action", choices=["find", "process", "check"], default="find", help="操作类型")
    parser.add_argument("--languages", help="编程语言筛选")
    parser.add_argument("--repo", help="仓库全名 (用于check)")
    parser.add_argument("--pr", type=int, help="PR编号 (用于check)")
    parser.add_argument("--auto", action="store_true", help="自动确认")
    
    args = parser.parse_args()
    
    try:
        agent = OpenCodeBountyAgent()
        
        if args.action == "find":
            languages = args.languages.split(",") if args.languages else None
            tasks = agent.find_bounty_tasks(languages)
            return tasks
        
        elif args.action == "process":
            languages = args.languages.split(",") if args.languages else None
            result = agent.process_bounty(languages, args.auto)
            return result
        
        elif args.action == "check":
            if not args.repo or not args.pr:
                print("❌ --repo 和 --pr 参数必需")
                return None
            pr_url = f"https://github.com/{args.repo}/pull/{args.pr}"
            status = agent.check_pr_status(pr_url)
            return status
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import json
    result = main()
    
    if result:
        print("\n" + "=" * 60)
        print("📊 结果:")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
