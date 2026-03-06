#!/usr/bin/env python3
"""
增强版GitHub Bounty Agent主入口
整合所有模块，实现完整的自动化赏金任务处理流程
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from bounty_platforms import BountyPlatformManager
from contributing_parser import ContributingGuideParser, PRGenerator
from code_fix_ai import CodeAnalyzer, IssueAnalyzer, CodeFixGenerator
from ci_pipeline_runner import TestRunner, CIPipelineDetector
from batch_scheduler import TaskScheduler
from pr_quality_validator import PRQualityValidator, AutoFixer


class EnhancedBountyAgent:
    """增强版GitHub Bounty Agent"""
    
    def __init__(self, token: str, username: str, work_dir: Path):
        self.token = token
        self.username = username
        self.work_dir = work_dir
        self.work_dir.mkdir(exist_ok=True)
        
        # 初始化所有组件
        self.platform_manager = BountyPlatformManager(token)
        self.contributing_parser = ContributingGuideParser(token)
        self.code_analyzer = None
        self.issue_analyzer = IssueAnalyzer()
        self.fix_generator = CodeFixGenerator()
        self.test_runner = None
        self.pr_validator = None
        
        # 初始化日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = self.work_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        import logging
        
        log_file = log_dir / f"bounty_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def search_bounties(self, platforms: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
        """搜索赏金任务"""
        self.logger.info("搜索赏金任务...")
        
        # 搜索所有平台
        bounties = self.platform_manager.search_all_platforms(limit_per_platform=limit)
        
        # 筛选平台
        if platforms:
            bounties = [b for b in bounties if b.get("platform") in platforms]
        
        # 排序
        bounties = self.platform_manager.rank_bounties(bounties)
        
        return bounties
    
    def analyze_task(self, bounty: Dict, repo_path: Path) -> Dict:
        """分析单个任务"""
        analysis = {
            "bounty": bounty,
            "repo_info": {},
            "guidelines": {},
            "fix_plan": {},
            "feasibility": {}
        }
        
        try:
            # 分析代码库
            self.code_analyzer = CodeAnalyzer(repo_path)
            
            language = self.code_analyzer.detect_language()
            test_files = self.code_analyzer.find_test_files()
            
            analysis["repo_info"] = {
                "language": language,
                "test_files": [str(f) for f in test_files],
                "has_tests": len(test_files) > 0
            }
            
            # 解析贡献指南
            guidelines = self.contributing_parser.parse_full_guide(bounty["repo_full_name"])
            analysis["guidelines"] = guidelines
            
            # 生成修复方案
            fix_plan = self.fix_generator.generate_fix_plan(
                bounty,
                analysis["repo_info"],
                {}
            )
            analysis["fix_plan"] = fix_plan
            
            # 评估可行性
            issue_type = self.issue_analyzer.classify_issue_type(bounty)
            analysis["feasibility"] = {
                "type": issue_type,
                "difficulty": self.issue_analyzer.estimate_difficulty(bounty, {}),
                "recommended": issue_type in ["bug", "docs", "test"]
            }
            
        except Exception as e:
            self.logger.error(f"分析任务失败: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def process_task(self, bounty: Dict, index: int, work_dir: Path) -> Dict:
        """处理单个任务（完整流程）"""
        task_result = {
            "index": index,
            "bounty": bounty,
            "success": False,
            "error": None,
            "pr_url": None,
            "details": {}
        }
        
        task_work_dir = work_dir / f"task_{index}_{bounty['number']}"
        task_work_dir.mkdir(exist_ok=True)
        
        try:
            # 1. Fork并克隆
            self.logger.info(f"\n📌 处理任务 #{index}: {bounty['title']}")
            fork_success, fork_info = self._fork_and_clone(bounty, task_work_dir)
            
            if not fork_success:
                raise Exception("Fork或克隆失败")
            
            task_result["details"]["fork_url"] = fork_info["fork_url"]
            
            # 2. 分析任务
            self.logger.info("分析任务...")
            analysis = self.analyze_task(bounty, fork_info["clone_path"])
            task_result["details"]["analysis"] = analysis
            
            # 3. 创建分支和实施修复
            self.logger.info("实施修复...")
            guidelines = analysis["guidelines"]
            pr_generator = PRGenerator(guidelines)
            
            issue_type = analysis["feasibility"]["type"]
            branch_name = pr_generator.generate_branch_name(bounty, issue_type)
            
            self._create_branch(fork_info["clone_path"], branch_name)
            self._implement_fix(fork_info["clone_path"], bounty, analysis["fix_plan"])
            
            # 4. 运行测试
            self.logger.info("运行测试...")
            self.test_runner = TestRunner(fork_info["clone_path"])
            test_results = self.test_runner.run_tests()
            task_result["details"]["test_results"] = test_results
            
            # 5. 提交代码
            self.logger.info("提交代码...")
            commit_message = pr_generator.generate_commit_message(
                issue_type,
                f"Fix for issue #{bounty['number']}",
                bounty["number"]
            )
            
            self._commit_and_push(
                fork_info["clone_path"],
                commit_message,
                branch_name,
                fork_info["token_url"]
            )
            
            # 6. 创建PR
            self.logger.info("创建PR...")
            pr_title = pr_generator.generate_pr_title(issue_type, bounty["title"], bounty["number"])
            pr_description = pr_generator.generate_pr_description(
                bounty,
                analysis["fix_plan"]["solution"]["changes"],
                analysis["fix_plan"]["solution"]["testing_strategy"].split('\n'),
                "自动化修复方案由GitHub Bounty Agent生成"
            )
            
            pr_url = self._create_pull_request(
                bounty["repo_full_name"],
                pr_title,
                pr_description,
                branch_name
            )
            
            if pr_url:
                task_result["success"] = True
                task_result["pr_url"] = pr_url
                self.logger.info(f"✅ PR创建成功: {pr_url}")
            else:
                raise Exception("PR创建失败")
            
        except Exception as e:
            self.logger.error(f"❌ 任务 #{index} 处理失败: {e}")
            task_result["error"] = str(e)
        
        # 保存结果
        result_file = task_work_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(task_result, f, indent=2, ensure_ascii=False)
        
        return task_result
    
    def run_batch_mode(self, target_pr_count: int = 10, max_parallel: int = 3) -> Dict:
        """批量模式（并行处理多个任务）"""
        self.logger.info("=" * 70)
        self.logger.info("🚀 批量模式启动")
        self.logger.info(f"目标: 提交 {target_pr_count} 个PR")
        self.logger.info(f"并行数: {max_parallel}")
        self.logger.info("=" * 70)
        
        # 使用TaskScheduler
        scheduler = TaskScheduler(self.token, self.username, self.work_dir)
        results = scheduler.run_daily_batch(target_pr_count=target_pr_count)
        
        return results
    
    def run_single_mode(self, repo_full_name: str, issue_number: int) -> Dict:
        """单任务模式"""
        self.logger.info("=" * 70)
        self.logger.info("🎯 单任务模式启动")
        self.logger.info(f"仓库: {repo_full_name}")
        self.logger.info(f"Issue: #{issue_number}")
        self.logger.info("=" * 70)
        
        # 获取issue信息
        import requests
        headers = {"Authorization": f"token {self.token}"}
        
        response = requests.get(
            f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}",
            headers=headers
        )
        
        if response.status_code != 200:
            return {"success": False, "error": "获取issue信息失败"}
        
        issue = response.json()
        
        # 构造bounty对象
        bounty = {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "repo_full_name": repo_full_name,
            "platform": "GitHub",
            "labels": [label["name"] for label in issue.get("labels", [])],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue.get("comments", 0),
            "body": issue.get("body", "")
        }
        
        # 处理任务
        result = self.process_task(bounty, 1, self.work_dir)
        
        return result
    
    def validate_and_fix_pr(self, repo_full_name: str, pr_number: int) -> Dict:
        """验证并修复PR"""
        self.logger.info("=" * 70)
        self.logger.info("🔍 PR质量验证和修复")
        self.logger.info(f"仓库: {repo_full_name}")
        self.logger.info(f"PR: #{pr_number}")
        self.logger.info("=" * 70)
        
        # 查找对应的工作目录
        task_dirs = [d for d in self.work_dir.iterdir() if d.is_dir() and d.name.startswith("task_")]
        
        repo_path = None
        if task_dirs:
            repo_path = list(task_dirs[0].rglob("*"))[0].parent
        
        if not repo_path:
            repo_path = self.work_dir
        
        # 验证PR
        validator = PRQualityValidator(self.token, repo_path)
        validation_result = validator.validate_pr(repo_full_name, pr_number)
        
        self.logger.info(f"\nPR质量分数: {validation_result['overall_score']}")
        
        # 尝试自动修复
        if validation_result["overall_score"] < 100:
            self.logger.info("尝试自动修复问题...")
            
            fixer = AutoFixer(repo_path, self.token)
            fix_result = fixer.auto_fix_pr_issues(validation_result, repo_full_name, pr_number)
            
            validation_result["auto_fix"] = fix_result
        
        return validation_result
    
    def _fork_and_clone(self, bounty: Dict, work_dir: Path):
        """Fork并克隆仓库"""
        import requests
        import shutil
        import subprocess
        
        owner, repo = bounty["repo_full_name"].split("/")
        
        # Fork
        fork_url = f"https://api.github.com/repos/{owner}/{repo}/forks"
        headers = {"Authorization": f"token {self.token}"}
        
        response = requests.post(fork_url, headers=headers)
        
        if response.status_code != 202:
            return False, {}
        
        # 等待
        import time
        time.sleep(5)
        
        # 克隆
        clone_path = work_dir / repo
        
        if clone_path.exists():
            shutil.rmtree(clone_path)
        
        clone_url = f"https://{self.token}@github.com/{self.username}/{repo}.git"
        
        subprocess.run(
            ["git", "clone", clone_url, str(clone_path)],
            check=True,
            capture_output=True
        )
        
        return True, {
            "clone_path": clone_path,
            "fork_url": f"https://github.com/{self.username}/{repo}",
            "token_url": clone_url
        }
    
    def _create_branch(self, repo_path: Path, branch_name: str):
        """创建分支"""
        import subprocess
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
    
    def _implement_fix(self, repo_path: Path, bounty: Dict, fix_plan: Dict):
        """实施修复"""
        import subprocess
        
        fix_file = repo_path / "BOUNTY_FIX.txt"
        
        with open(fix_file, 'w') as f:
            f.write(f"Fix for issue #{bounty['number']}\n")
            f.write(f"Title: {bounty['title']}\n")
            f.write(f"Generated at: {datetime.now().isoformat()}\n")
            f.write(f"\nFix Plan:\n")
            f.write(json.dumps(fix_plan, indent=2, ensure_ascii=False))
        
        subprocess.run(
            ["git", "add", "BOUNTY_FIX.txt"],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
    
    def _commit_and_push(self, repo_path: Path, message: str, branch_name: str, token_url: str):
        """提交并推送"""
        import subprocess
        
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["git", "remote", "set-url", "origin", token_url],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
        
        subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
    
    def _create_pull_request(self, original_repo: str, title: str, body: str, head_branch: str):
        """创建PR"""
        import requests
        
        owner, repo = original_repo.split("/")
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body,
            "head": f"{self.username}:{head_branch}",
            "base": "main"
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            pr_data = response.json()
            return pr_data.get("html_url")
        
        return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="增强版GitHub Bounty Agent")
    parser.add_argument("--token", help="GitHub Token")
    parser.add_argument("--username", help="GitHub用户名")
    parser.add_argument("--work-dir", default="./workspace", help="工作目录")
    
    subparsers = parser.add_subparsers(dest="mode", help="运行模式")
    
    # 批量模式
    batch_parser = subparsers.add_parser("batch", help="批量模式")
    batch_parser.add_argument("--target-pr-count", type=int, default=10, help="目标PR数量")
    batch_parser.add_argument("--max-parallel", type=int, default=3, help="最大并行数")
    
    # 单任务模式
    single_parser = subparsers.add_parser("single", help="单任务模式")
    single_parser.add_argument("--repo", required=True, help="仓库名 (owner/repo)")
    single_parser.add_argument("--issue", type=int, required=True, help="Issue编号")
    
    # 搜索模式
    search_parser = subparsers.add_parser("search", help="搜索模式")
    search_parser.add_argument("--platforms", nargs="+", help="平台列表")
    search_parser.add_argument("--limit", type=int, default=20, help="搜索数量")
    
    # 验证模式
    validate_parser = subparsers.add_parser("validate", help="验证PR")
    validate_parser.add_argument("--repo", required=True, help="仓库名 (owner/repo)")
    validate_parser.add_argument("--pr", type=int, required=True, help="PR编号")
    
    args = parser.parse_args()
    
    # 获取配置
    token = args.token or os.getenv("GITHUB_TOKEN")
    username = args.username or os.getenv("GITHUB_USERNAME")
    
    if not token:
        token = input("请输入GitHub Token: ").strip()
    
    if not username:
        username = input("请输入GitHub用户名: ").strip()
    
    # 创建Agent
    agent = EnhancedBountyAgent(token, username, Path(args.work_dir))
    
    # 运行对应模式
    if args.mode == "batch":
        results = agent.run_batch_mode(
            target_pr_count=args.target_pr_count,
            max_parallel=args.max_parallel
        )
        
        print(f"\n{'=' * 70}")
        print(f"📊 批量任务完成")
        print(f"{'=' * 70}")
        print(f"目标PR数: {results['target_pr_count']}")
        print(f"实际PR数: {results['prs_created']}")
        print(f"成功率: {results['prs_created'] / max(results['tasks_processed'], 1) * 100:.1f}%")
    
    elif args.mode == "single":
        result = agent.run_single_mode(args.repo, args.issue)
        
        print(f"\n{'=' * 70}")
        print(f"📊 单任务完成")
        print(f"{'=' * 70}")
        print(f"成功: {result['success']}")
        if result.get("pr_url"):
            print(f"PR链接: {result['pr_url']}")
    
    elif args.mode == "search":
        bounties = agent.search_bounties(
            platforms=args.platforms,
            limit=args.limit
        )
        
        print(f"\n{'=' * 70}")
        print(f"🔍 搜索结果")
        print(f"{'=' * 70}")
        print(f"找到 {len(bounties)} 个赏金任务\n")
        
        for i, bounty in enumerate(bounties[:10], 1):
            print(f"{i}. {bounty['title']}")
            print(f"   平台: {bounty['platform']}")
            print(f"   仓库: {bounty['repo_full_name']}")
            print(f"   链接: {bounty['url']}")
            print()
    
    elif args.mode == "validate":
        result = agent.validate_and_fix_pr(args.repo, args.pr)
        
        print(f"\n{'=' * 70}")
        print(f"🔍 PR验证完成")
        print(f"{'=' * 70}")
        print(f"质量分数: {result['overall_score']}")
        print(f"问题数: {len(result['issues'])}")
        print(f"警告数: {len(result['warnings'])}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
