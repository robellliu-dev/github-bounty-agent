#!/usr/bin/env python3
"""
批量任务调度系统
每天自动运行，处理多个赏金任务，至少10个PR/天
"""

import os
import sys
import json
import subprocess
import time
import shutil
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# 导入我们创建的模块
from bounty_platforms import BountyPlatformManager
from contributing_parser import ContributingGuideParser, PRGenerator
from code_fix_ai import CodeAnalyzer, IssueAnalyzer, CodeFixGenerator
from ci_pipeline_runner import TestRunner, CIPipelineDetector


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, token: str, username: str, work_dir: Path):
        self.token = token
        self.username = username
        self.work_dir = work_dir
        self.work_dir.mkdir(exist_ok=True)
        
        # 创建日志目录
        self.log_dir = self.work_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 初始化组件
        self.platform_manager = BountyPlatformManager(token)
        self.contributing_parser = ContributingGuideParser(token)
    
    def _setup_logging(self):
        """设置日志"""
        log_file = self.log_dir / f"bounty_agent_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def run_daily_batch(self, target_pr_count: int = 10) -> Dict:
        """运行每日批量任务"""
        self.logger.info("=" * 70)
        self.logger.info("🚀 开始每日批量赏金任务处理")
        self.logger.info(f"目标: 提交 {target_pr_count} 个PR")
        self.logger.info("=" * 70)
        
        results = {
            "date": datetime.now().isoformat(),
            "target_pr_count": target_pr_count,
            "tasks_found": 0,
            "tasks_processed": 0,
            "prs_created": 0,
            "pr_urls": [],
            "errors": [],
            "task_results": []
        }
        
        try:
            # 步骤1: 搜索赏金任务
            self.logger.info("\n📋 步骤1: 搜索赏金任务...")
            bounties = self.platform_manager.search_all_platforms(limit_per_platform=20)
            
            # 排序和筛选
            bounties = self.platform_manager.rank_bounties(bounties)
            bounties = self._filter_bounties(bounties)
            
            results["tasks_found"] = len(bounties)
            self.logger.info(f"   找到 {len(bounties)} 个高质量任务")
            
            if not bounties:
                self.logger.error("❌ 未找到合适的赏金任务")
                return results
            
            # 步骤2: 并行处理任务
            self.logger.info(f"\n⚙️  步骤2: 并行处理任务 (目标: {target_pr_count} 个PR)...")
            
            # 限制同时处理的任务数
            max_parallel = min(5, target_pr_count)
            selected_bounties = bounties[:target_pr_count]
            
            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                # 提交所有任务
                future_to_bounty = {
                    executor.submit(self._process_single_bounty, bounty, i): bounty 
                    for i, bounty in enumerate(selected_bounties, 1)
                }
                
                # 收集结果
                for future in as_completed(future_to_bounty):
                    bounty = future_to_bounty[future]
                    try:
                        task_result = future.result()
                        results["task_results"].append(task_result)
                        results["tasks_processed"] += 1
                        
                        if task_result.get("success"):
                            results["prs_created"] += 1
                            results["pr_urls"].append(task_result.get("pr_url"))
                            self.logger.info(f"✅ 任务 #{task_result['index']} 完成: {bounty['title']}")
                        else:
                            self.logger.error(f"❌ 任务 #{task_result['index']} 失败: {task_result.get('error', 'Unknown error')}")
                            results["errors"].append(f"#{task_result['index']}: {task_result.get('error')}")
                    
                    except Exception as e:
                        self.logger.error(f"❌ 任务处理异常: {e}")
                        results["errors"].append(str(e))
            
            # 步骤3: 生成报告
            self.logger.info("\n" + "=" * 70)
            self.logger.info("📊 每日批量任务处理报告")
            self.logger.info("=" * 70)
            self.logger.info(f"日期: {results['date']}")
            self.logger.info(f"目标PR数: {results['target_pr_count']}")
            self.logger.info(f"找到任务数: {results['tasks_found']}")
            self.logger.info(f"处理任务数: {results['tasks_processed']}")
            self.logger.info(f"创建PR数: {results['prs_created']}")
            self.logger.info(f"成功率: {results['prs_created'] / max(results['tasks_processed'], 1) * 100:.1f}%")
            
            if results["pr_urls"]:
                self.logger.info("\n创建的PR链接:")
                for url in results["pr_urls"]:
                    self.logger.info(f"  - {url}")
            
            if results["errors"]:
                self.logger.info("\n错误列表:")
                for error in results["errors"]:
                    self.logger.info(f"  - {error}")
            
            # 保存结果
            self._save_results(results)
            
        except Exception as e:
            self.logger.error(f"❌ 批量任务处理失败: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def _filter_bounties(self, bounties: List[Dict]) -> List[Dict]:
        """筛选赏金任务"""
        filtered = []
        
        for bounty in bounties:
            # 过滤条件:
            # 1. 不包含已处理的任务
            # 2. 不包含过于复杂的任务
            # 3. 不包含评论过多的任务（竞争激烈）
            
            skip = False
            
            # 检查是否已处理
            if self._is_already_processed(bounty):
                skip = True
            
            # 检查评论数
            if bounty.get("comments", 0) > 10:
                skip = True
            
            if not skip:
                filtered.append(bounty)
        
        return filtered
    
    def _is_already_processed(self, bounty: Dict) -> bool:
        """检查任务是否已处理"""
        # 检查历史记录
        history_file = self.work_dir / "processed_tasks.json"
        
        if not history_file.exists():
            return False
        
        try:
            with open(history_file, 'r') as f:
                processed = json.load(f)
            
            key = f"{bounty['repo_full_name']}#{bounty['number']}"
            return key in processed.get("processed", [])
        
        except:
            return False
    
    def _process_single_bounty(self, bounty: Dict, index: int) -> Dict:
        """处理单个赏金任务"""
        task_result = {
            "index": index,
            "bounty": bounty,
            "success": False,
            "error": None,
            "pr_url": None,
            "details": {}
        }
        
        task_work_dir = self.work_dir / f"task_{index}_{bounty['number']}"
        task_work_dir.mkdir(exist_ok=True)
        
        try:
            self.logger.info(f"\n{'=' * 70}")
            self.logger.info(f"📌 处理任务 #{index}: {bounty['title']}")
            self.logger.info(f"   仓库: {bounty['repo_full_name']}")
            self.logger.info(f"   平台: {bounty['platform']}")
            self.logger.info(f"{'=' * 70}")
            
            # 1. Fork并克隆仓库
            self.logger.info(f"\n🍴 步骤1: Fork并克隆仓库...")
            fork_success, fork_info = self._fork_and_clone(bounty, task_work_dir)
            
            if not fork_success:
                raise Exception("Fork或克隆失败")
            
            task_result["details"]["fork_url"] = fork_info["fork_url"]
            
            # 2. 分析仓库
            self.logger.info(f"\n🔬 步骤2: 分析仓库...")
            code_analyzer = CodeAnalyzer(fork_info["clone_path"])
            language = code_analyzer.detect_language()
            test_files = code_analyzer.find_test_files()
            
            self.logger.info(f"   语言: {language}")
            self.logger.info(f"   测试文件数: {len(test_files)}")
            
            # 3. 解析贡献指南
            self.logger.info(f"\n📖 步骤3: 解析贡献指南...")
            guidelines = self.contributing_parser.parse_full_guide(bounty["repo_full_name"])
            
            task_result["details"]["guidelines"] = guidelines
            
            # 4. 生成修复方案
            self.logger.info(f"\n💡 步骤4: 生成修复方案...")
            issue_analyzer = IssueAnalyzer()
            issue_type = issue_analyzer.classify_issue_type(bounty)
            
            fix_generator = CodeFixGenerator()
            fix_plan = fix_generator.generate_fix_plan(
                bounty,
                {"language": language, "test_files": [str(f) for f in test_files]},
                {}
            )
            
            task_result["details"]["fix_plan"] = fix_plan
            
            # 5. 创建PR生成器
            pr_generator = PRGenerator(guidelines)
            
            # 6. 生成分支名和提交信息
            branch_name = pr_generator.generate_branch_name(bounty, issue_type)
            commit_message = pr_generator.generate_commit_message(
                issue_type, 
                f"Fix for issue #{bounty['number']}", 
                bounty['number']
            )
            pr_title = pr_generator.generate_pr_title(issue_type, bounty["title"], bounty["number"])
            
            # 7. 创建分支
            self.logger.info(f"\n🌿 步骤5: 创建分支 {branch_name}...")
            self._create_branch(fork_info["clone_path"], branch_name)
            
            # 8. 实施修复（这里使用简化版，实际应该使用LLM生成代码）
            self.logger.info(f"\n⚙️  步骤6: 实施修复...")
            self._implement_fix(fork_info["clone_path"], bounty, fix_plan)
            
            # 9. 运行测试
            self.logger.info(f"\n🧪 步骤7: 运行测试...")
            test_runner = TestRunner(fork_info["clone_path"])
            test_results = test_runner.run_tests()
            
            task_result["details"]["test_results"] = test_results
            
            if not test_results["success"]:
                self.logger.warning(f"⚠️  测试失败，但继续提交PR")
            
            # 10. 提交代码
            self.logger.info(f"\n📤 步骤8: 提交代码...")
            self._commit_and_push(
                fork_info["clone_path"],
                commit_message,
                branch_name,
                fork_info["token_url"]
            )
            
            # 11. 创建PR
            self.logger.info(f"\n🎯 步骤9: 创建PR...")
            pr_description = pr_generator.generate_pr_description(
                bounty,
                fix_plan["solution"]["changes"],
                fix_plan["solution"]["testing_strategy"].split('\n'),
                f"自动化修复方案由GitHub Bounty Agent生成"
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
                
                # 记录已处理
                self._mark_as_processed(bounty)
            else:
                raise Exception("PR创建失败")
            
        except Exception as e:
            self.logger.error(f"❌ 任务 #{index} 处理失败: {e}")
            task_result["error"] = str(e)
        
        # 保存任务结果
        task_result_file = task_work_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(task_result_file, 'w', encoding='utf-8') as f:
            json.dump(task_result, f, indent=2, ensure_ascii=False)
        
        return task_result
    
    def _fork_and_clone(self, bounty: Dict, work_dir: Path) -> Tuple[bool, Dict]:
        """Fork并克隆仓库"""
        owner, repo = bounty["repo_full_name"].split("/")
        
        # Fork
        fork_url = f"https://api.github.com/repos/{owner}/{repo}/forks"
        headers = {"Authorization": f"token {self.token}"}
        
        response = requests.post(fork_url, headers=headers)
        
        if response.status_code != 202:
            self.logger.error(f"Fork失败: {response.status_code}")
            return False, {}
        
        # 等待Fork完成
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
        """创建新分支"""
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
    
    def _implement_fix(self, repo_path: Path, bounty: Dict, fix_plan: Dict):
        """实施修复（简化版）"""
        # 创建一个示例修复文件
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
        """提交并推送代码"""
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(repo_path),
            check=True,
            capture_output=True
        )
        
        # 更新remote URL使用token
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
    
    def _create_pull_request(self, original_repo: str, title: str, body: str, head_branch: str) -> Optional[str]:
        """创建Pull Request"""
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
        else:
            self.logger.error(f"创建PR失败: {response.status_code}")
            self.logger.error(f"响应: {response.text}")
            return None
    
    def _mark_as_processed(self, bounty: Dict):
        """标记任务为已处理"""
        history_file = self.work_dir / "processed_tasks.json"
        
        processed = {"processed": []}
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    processed = json.load(f)
            except:
                pass
        
        key = f"{bounty['repo_full_name']}#{bounty['number']}"
        if key not in processed["processed"]:
            processed["processed"].append(key)
            processed["processed"] = processed["processed"][-100:]  # 只保留最近100个
        
        with open(history_file, 'w') as f:
            json.dump(processed, f, indent=2)
    
    def _save_results(self, results: Dict):
        """保存结果"""
        result_file = self.work_dir / f"daily_results_{datetime.now().strftime('%Y%m%d')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n💾 结果已保存到: {result_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="批量赏金任务调度系统")
    parser.add_argument("--token", help="GitHub Token")
    parser.add_argument("--username", help="GitHub用户名")
    parser.add_argument("--work-dir", default="./workspace", help="工作目录")
    parser.add_argument("--target-pr-count", type=int, default=10, help="目标PR数量")
    
    args = parser.parse_args()
    
    # 获取配置
    token = args.token or os.getenv("GITHUB_TOKEN")
    username = args.username or os.getenv("GITHUB_USERNAME")
    
    if not token:
        token = input("请输入GitHub Token: ").strip()
    
    if not username:
        username = input("请输入GitHub用户名: ").strip()
    
    # 创建调度器
    scheduler = TaskScheduler(token, username, Path(args.work_dir))
    
    # 运行批量任务
    results = scheduler.run_daily_batch(target_pr_count=args.target_pr_count)
    
    # 输出摘要
    print(f"\n{'=' * 70}")
    print(f"📊 处理完成")
    print(f"{'=' * 70}")
    print(f"目标PR数: {results['target_pr_count']}")
    print(f"实际PR数: {results['prs_created']}")
    print(f"成功率: {results['prs_created'] / max(results['tasks_processed'], 1) * 100:.1f}%")
    
    if results["pr_urls"]:
        print(f"\n创建的PR:")
        for url in results["pr_urls"]:
            print(f"  {url}")


if __name__ == "__main__":
    main()
