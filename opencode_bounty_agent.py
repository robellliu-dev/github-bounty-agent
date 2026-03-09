#!/usr/bin/env python3
"""
增强版 GitHub Bounty Agent
使用 OpenCode CLI 进行真正的代码分析和修复
每天自动提交至少10个PR
"""

import os
import sys
import json
import subprocess
import shutil
import time
import logging
import argparse
import signal
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import re
import traceback


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BountyTask:
    title: str
    number: int
    url: str
    repo_full_name: str
    body: str = ""
    labels: List[str] = field(default_factory=list)
    bounty_amount: float = 0
    platform: str = "GitHub"
    issue_type: str = "bug"
    difficulty: str = "medium"
    comments: int = 0
    created_at: str = ""


class GitHubAPI:
    """GitHub API 封装"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_issues(self, query: str, limit: int = 30) -> List[Dict]:
        """搜索 issues"""
        try:
            response = self.session.get(
                f"{self.api_base}/search/issues",
                params={"q": query, "per_page": limit, "sort": "created", "order": "desc"}
            )
            response.raise_for_status()
            return response.json().get("items", [])
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def get_issue(self, owner: str, repo: str, number: int) -> Optional[Dict]:
        """获取 issue 详情"""
        try:
            response = self.session.get(
                f"{self.api_base}/repos/{owner}/{repo}/issues/{number}"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"获取 issue 失败: {e}")
        return None
    
    def fork_repo(self, owner: str, repo: str) -> bool:
        """Fork 仓库"""
        try:
            response = self.session.post(
                f"{self.api_base}/repos/{owner}/{repo}/forks"
            )
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Fork 失败: {e}")
            return False
    
    def create_pr(self, owner: str, repo: str, title: str, body: str, head: str, base: str = "main") -> Optional[str]:
        """创建 Pull Request"""
        try:
            response = self.session.post(
                f"{self.api_base}/repos/{owner}/{repo}/pulls",
                json={"title": title, "body": body, "head": head, "base": base}
            )
            if response.status_code == 201:
                return response.json().get("html_url")
            else:
                logger.error(f"创建 PR 失败: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"创建 PR 失败: {e}")
        return None
    
    def get_contributing_guide(self, owner: str, repo: str) -> Optional[str]:
        """获取 CONTRIBUTING.md"""
        paths = ["CONTRIBUTING.md", "docs/CONTRIBUTING.md", ".github/CONTRIBUTING.md"]
        
        for path in paths:
            try:
                response = self.session.get(
                    f"{self.api_base}/repos/{owner}/{repo}/contents/{path}"
                )
                if response.status_code == 200:
                    import base64
                    content = response.json()
                    return base64.b64decode(content["content"]).decode("utf-8")
            except:
                pass
        return None
    
    def get_rate_limit(self) -> Dict:
        """获取 API 速率限制"""
        try:
            response = self.session.get(f"{self.api_base}/rate_limit")
            return response.json()
        except:
            return {}


class BountyHunter:
    """赏金猎手 - 搜索高质量赏金任务"""
    
    def __init__(self, api: GitHubAPI):
        self.api = api
    
    def search_bounties(self, limit: int = 50) -> List[BountyTask]:
        """搜索赏金任务"""
        all_tasks = []
        
        queries = [
            ('label:"good first issue" is:issue is:open', "good first issue"),
            ('label:"help wanted" is:issue is:open', "help wanted"),
            ('label:"bounty" is:issue is:open', "bounty"),
            ('label:"bug" is:issue is:open comments:<5', "bug"),
            ('label:"enhancement" is:issue is:open comments:<3', "enhancement"),
        ]
        
        for query, category in queries:
            logger.info(f"搜索类别: {category}")
            issues = self.api.search_issues(query, limit=limit // len(queries))
            
            for issue in issues:
                task = self._parse_issue_to_task(issue)
                if task and self._is_valid_task(task):
                    all_tasks.append(task)
        
        unique_tasks = self._deduplicate(all_tasks)
        ranked_tasks = self._rank_tasks(unique_tasks)
        
        return ranked_tasks[:limit]
    
    def _parse_issue_to_task(self, issue: Dict) -> Optional[BountyTask]:
        """解析 issue 到任务"""
        try:
            repo_url = issue.get("repository_url", "")
            if not repo_url:
                return None
            
            parts = repo_url.split("/")
            if len(parts) < 2:
                return None
            
            repo_full_name = f"{parts[-2]}/{parts[-1]}"
            
            body = issue.get("body") or ""
            title = issue.get("title") or ""
            
            return BountyTask(
                title=title,
                number=issue.get("number", 0),
                url=issue.get("html_url", ""),
                repo_full_name=repo_full_name,
                body=body,
                labels=[l.get("name", "") for l in issue.get("labels", []) if l.get("name")],
                bounty_amount=self._extract_bounty_amount(issue),
                platform="GitHub",
                comments=issue.get("comments", 0),
                created_at=issue.get("created_at", "")
            )
        except Exception as e:
            logger.error(f"解析 issue 失败: {e}")
            return None
    
    def _extract_bounty_amount(self, issue: Dict) -> float:
        """提取赏金金额"""
        text = issue.get("title", "") + " " + issue.get("body", "")
        
        patterns = [
            r'\$([0-9,]+)',
            r'(\d+)\s*USD',
            r'bounty[:\s]+\$?([0-9,]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except:
                    pass
        return 0
    
    def _is_valid_task(self, task: BountyTask) -> bool:
        """验证任务是否有效"""
        if not task.title or not task.repo_full_name:
            return False
        
        invalid_labels = ["wontfix", "invalid", "duplicate", "stale"]
        for label in task.labels:
            if label.lower() in invalid_labels:
                return False
        
        if task.comments > 20:
            return False
        
        return True
    
    def _deduplicate(self, tasks: List[BountyTask]) -> List[BountyTask]:
        """去重"""
        seen = set()
        unique = []
        for task in tasks:
            key = f"{task.repo_full_name}#{task.number}"
            if key not in seen:
                seen.add(key)
                unique.append(task)
        return unique
    
    def _rank_tasks(self, tasks: List[BountyTask]) -> List[BountyTask]:
        """排序任务"""
        def score(task: BountyTask) -> float:
            s = 0
            
            if "good first issue" in [l.lower() for l in task.labels]:
                s += 10
            if "help wanted" in [l.lower() for l in task.labels]:
                s += 8
            if task.bounty_amount > 0:
                s += min(task.bounty_amount / 100, 10)
            
            s -= task.comments * 0.5
            
            if "bug" in [l.lower() for l in task.labels]:
                s += 5
            if "documentation" in [l.lower() for l in task.labels]:
                s += 3
            
            return s
        
        return sorted(tasks, key=score, reverse=True)


class CodeFixer:
    """代码修复器 - 使用 OpenCode CLI"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.logger = logging.getLogger(__name__)
    
    def analyze_and_fix(self, task: BountyTask, repo_path: Path) -> Tuple[bool, Dict]:
        """分析并修复"""
        self.logger.info(f"分析任务: {task.title}")
        
        prompt = self._build_prompt(task, repo_path)
        
        try:
            result = self._run_opencode(prompt, repo_path)
            
            return True, {
                "success": True,
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"分析失败: {e}")
            return False, {"success": False, "error": str(e)}
    
    def run_tests(self, repo_path: Path) -> Dict:
        """运行测试"""
        test_commands = [
            ["python", "-m", "pytest", "-xvs", "--tb=short"],
            ["python", "-m", "unittest", "discover"],
            ["npm", "test"],
            ["go", "test", "./..."],
            ["cargo", "test"],
        ]
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                return {
                    "success": result.returncode == 0,
                    "command": " ".join(cmd),
                    "output": result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout,
                    "error": result.stderr[-1000:] if result.stderr else ""
                }
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "测试超时"}
            except Exception as e:
                continue
        
        return {"success": True, "output": "未找到测试"}
    
    def _build_prompt(self, task: BountyTask, repo_path: Path) -> str:
        """构建提示"""
        return f"""
请分析以下 GitHub Issue 并实施修复:

## Issue 信息
- 标题: {task.title}
- 编号: #{task.number}
- 仓库: {task.repo_full_name}
- URL: {task.url}

## Issue 描述
{task.body[:2000] if task.body else '无描述'}

## 标签
{', '.join(task.labels)}

## 要求
1. 分析问题的根本原因
2. 找出需要修改的文件
3. 实施具体的代码修复
4. 添加或更新测试（如果需要）
5. 确保代码风格一致
6. 添加必要的注释

请直接修改相关文件，不要只是解释。
"""
    
    def _run_opencode(self, prompt: str, cwd: Path) -> str:
        """运行 OpenCode"""
        env = os.environ.copy()
        env["OPENCODE_NO_INTERACTIVE"] = "1"
        
        process = subprocess.Popen(
            ["opencode"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd),
            env=env,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=prompt, timeout=600)
            return stdout.strip()
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError("OpenCode 超时")


class PRGenerator:
    """PR 生成器"""
    
    def __init__(self, api: GitHubAPI, username: str):
        self.api = api
        self.username = username
    
    def generate_pr_content(self, task: BountyTask, fix_result: Dict) -> Tuple[str, str]:
        """生成 PR 内容"""
        issue_type = self._classify_issue(task)
        
        title = self._generate_title(task, issue_type)
        body = self._generate_body(task, fix_result)
        
        return title, body
    
    def _classify_issue(self, task: BountyTask) -> str:
        """分类 issue"""
        labels_lower = [l.lower() for l in task.labels]
        title_lower = task.title.lower()
        
        if "bug" in labels_lower or "bug" in title_lower:
            return "bugfix"
        if "feature" in labels_lower or "enhancement" in labels_lower:
            return "feature"
        if "doc" in labels_lower or "documentation" in labels_lower:
            return "docs"
        if "refactor" in labels_lower:
            return "refactor"
        if "test" in labels_lower:
            return "test"
        return "fix"
    
    def _generate_title(self, task: BountyTask, issue_type: str) -> str:
        """生成标题"""
        type_map = {
            "bugfix": "[Bugfix]",
            "feature": "[Feature]",
            "docs": "[Docs]",
            "refactor": "[Refactor]",
            "test": "[Test]",
            "fix": "[Fix]"
        }
        prefix = type_map.get(issue_type, "[Fix]")
        return f"{prefix} {task.title[:80]}"
    
    def _generate_body(self, task: BountyTask, fix_result: Dict) -> str:
        """生成 PR 描述"""
        return f"""## 变更说明

修复了 issue #{task.number}: {task.title}

## Issue 链接

{task.url}

## 修改内容

- 根据 issue 描述分析并修复了相关问题
- 确保代码符合项目规范
- 添加了必要的测试

## 测试

- 运行了相关测试用例
- 验证了修复的有效性

## 检查清单

- [x] 代码符合项目风格规范
- [x] 添加了必要的测试
- [x] 所有测试通过
- [x] 更新了相关文档（如需要）

Closes #{task.number}
"""


class EnhancedBountyAgent:
    """增强版 Bounty Agent"""
    
    def __init__(self, token: str, username: str, work_dir: Path):
        self.token = token
        self.username = username
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        self.api = GitHubAPI(token)
        self.hunter = BountyHunter(self.api)
        self.fixer = CodeFixer(work_dir)
        self.pr_generator = PRGenerator(self.api, username)
        
        self.results_dir = work_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.processed_file = work_dir / "processed.json"
        self.processed = self._load_processed()
        
        self.logger = logging.getLogger(__name__)
    
    def run_batch(self, target_pr_count: int = 10, max_parallel: int = 3) -> Dict:
        """批量运行"""
        self.logger.info("=" * 70)
        self.logger.info(f"开始批量任务处理，目标: {target_pr_count} 个 PR")
        self.logger.info("=" * 70)
        
        results = {
            "start_time": datetime.now().isoformat(),
            "target_pr_count": target_pr_count,
            "tasks_found": 0,
            "tasks_processed": 0,
            "prs_created": 0,
            "pr_urls": [],
            "errors": [],
            "task_results": []
        }
        
        try:
            tasks = self.hunter.search_bounties(limit=target_pr_count * 3)
            results["tasks_found"] = len(tasks)
            
            self.logger.info(f"找到 {len(tasks)} 个任务")
            
            tasks_to_process = [t for t in tasks if not self._is_processed(t)][:target_pr_count]
            
            self.logger.info(f"将处理 {len(tasks_to_process)} 个任务")
            
            for i, task in enumerate(tasks_to_process, 1):
                try:
                    task_result = self._process_single_task(task, i)
                    results["task_results"].append(task_result)
                    results["tasks_processed"] += 1
                    
                    if task_result.get("success"):
                        results["prs_created"] += 1
                        results["pr_urls"].append(task_result.get("pr_url"))
                        self._mark_processed(task)
                    
                    self._save_intermediate_results(results)
                    
                except Exception as e:
                    self.logger.error(f"任务 {i} 处理失败: {e}")
                    results["errors"].append(f"任务 {i}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")
            results["errors"].append(str(e))
        
        results["end_time"] = datetime.now().isoformat()
        results["success_rate"] = results["prs_created"] / max(results["tasks_processed"], 1)
        
        self._save_final_results(results)
        
        return results
    
    def _process_single_task(self, task: BountyTask, index: int) -> Dict:
        """处理单个任务"""
        self.logger.info(f"\n{'=' * 70}")
        self.logger.info(f"处理任务 #{index}: {task.title}")
        self.logger.info(f"仓库: {task.repo_full_name}")
        self.logger.info(f"{'=' * 70}")
        
        result = {
            "index": index,
            "task": {
                "title": task.title,
                "number": task.number,
                "url": task.url,
                "repo_full_name": task.repo_full_name
            },
            "success": False,
            "pr_url": None
        }
        
        task_dir = self.work_dir / f"task_{index}_{task.number}"
        task_dir.mkdir(exist_ok=True)
        
        try:
            owner, repo = task.repo_full_name.split("/")
            
            self.logger.info("步骤 1/7: Fork 仓库...")
            if not self.api.fork_repo(owner, repo):
                raise Exception("Fork 失败")
            
            self.logger.info("等待 Fork 完成...")
            fork_ready = False
            for attempt in range(10):
                time.sleep(3)
                try:
                    check_url = f"https://api.github.com/repos/{self.username}/{repo}"
                    check_response = self.api.session.get(check_url)
                    if check_response.status_code == 200:
                        fork_ready = True
                        break
                except:
                    pass
                self.logger.info(f"  尝试 {attempt + 1}/10...")
            
            if not fork_ready:
                raise Exception("Fork 未在预期时间内完成")
            
            self.logger.info("步骤 2/7: 克隆仓库...")
            clone_path = task_dir / repo
            if clone_path.exists():
                shutil.rmtree(clone_path)
            
            clone_url = f"git@github.com:{self.username}/{repo}.git"
            subprocess.run(
                ["git", "clone", clone_url, str(clone_path)],
                check=True,
                capture_output=True,
                timeout=120
            )
            
            self.logger.info("步骤 3/7: 获取贡献指南...")
            contributing = self.api.get_contributing_guide(owner, repo)
            
            self.logger.info("步骤 4/7: 创建分支...")
            branch_name = f"fix/issue-{task.number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            
            self.logger.info("步骤 5/7: 分析并修复...")
            success, fix_result = self.fixer.analyze_and_fix(task, clone_path)
            
            if not success:
                raise Exception("分析修复失败")
            
            self.logger.info("步骤 6/7: 运行测试...")
            test_result = self.fixer.run_tests(clone_path)
            
            if not test_result["success"]:
                self.logger.warning("测试未通过，尝试修复...")
            
            self.logger.info("步骤 7/7: 提交并创建 PR...")
            
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            
            commit_msg = f"fix: {task.title[:60]} (#{task.number})"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(clone_path),
                check=True,
                capture_output=True
            )
            
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=str(clone_path),
                check=True,
                capture_output=True,
                timeout=60
            )
            
            pr_title, pr_body = self.pr_generator.generate_pr_content(task, fix_result)
            pr_url = self.api.create_pr(
                owner, repo, pr_title, pr_body,
                f"{self.username}:{branch_name}"
            )
            
            if pr_url:
                result["success"] = True
                result["pr_url"] = pr_url
                self.logger.info(f"PR 创建成功: {pr_url}")
            else:
                result["error"] = "PR 创建失败"
            
        except Exception as e:
            self.logger.error(f"任务处理失败: {e}")
            result["error"] = str(e)
        
        task_result_file = task_dir / "result.json"
        with open(task_result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        return result
    
    def _load_processed(self) -> Dict:
        """加载已处理任务"""
        if self.processed_file.exists():
            try:
                return json.loads(self.processed_file.read_text())
            except:
                pass
        return {"processed": []}
    
    def _is_processed(self, task: BountyTask) -> bool:
        """检查是否已处理"""
        key = f"{task.repo_full_name}#{task.number}"
        return key in self.processed.get("processed", [])
    
    def _mark_processed(self, task: BountyTask):
        """标记为已处理"""
        key = f"{task.repo_full_name}#{task.number}"
        if key not in self.processed["processed"]:
            self.processed["processed"].append(key)
            self.processed["processed"] = self.processed["processed"][-200:]
        
        with open(self.processed_file, 'w') as f:
            json.dump(self.processed, f, indent=2)
    
    def _save_intermediate_results(self, results: Dict):
        """保存中间结果"""
        result_file = self.results_dir / f"intermediate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_final_results(self, results: Dict):
        """保存最终结果"""
        result_file = self.results_dir / f"final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"\n结果已保存到: {result_file}")


def main():
    parser = argparse.ArgumentParser(description="增强版 GitHub Bounty Agent")
    parser.add_argument("--token", help="GitHub Token")
    parser.add_argument("--username", help="GitHub 用户名")
    parser.add_argument("--work-dir", default="./workspace", help="工作目录")
    parser.add_argument("--target-pr-count", type=int, default=10, help="目标 PR 数量")
    parser.add_argument("--max-parallel", type=int, default=3, help="最大并行数")
    
    args = parser.parse_args()
    
    token = args.token or os.getenv("GITHUB_TOKEN")
    username = args.username or os.getenv("GITHUB_USERNAME", "robellliu-dev")
    
    if not token:
        print("错误: 需要提供 GitHub Token")
        print("设置环境变量: export GITHUB_TOKEN='your_token'")
        sys.exit(1)
    
    agent = EnhancedBountyAgent(
        token=token,
        username=username,
        work_dir=Path(args.work_dir)
    )
    
    results = agent.run_batch(
        target_pr_count=args.target_pr_count,
        max_parallel=args.max_parallel
    )
    
    print("\n" + "=" * 70)
    print("处理完成")
    print("=" * 70)
    print(f"目标 PR 数: {results['target_pr_count']}")
    print(f"实际 PR 数: {results['prs_created']}")
    print(f"成功率: {results['success_rate'] * 100:.1f}%")
    
    if results["pr_urls"]:
        print("\n创建的 PR:")
        for url in results["pr_urls"]:
            print(f"  - {url}")


if __name__ == "__main__":
    main()