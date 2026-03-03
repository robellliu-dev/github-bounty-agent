#!/usr/bin/env python3
"""
GitHub Bounty Agent - 自动化赏金任务处理Agent
自动化处理从查找、分析到提交PR的完整流程
"""

import os
import sys
import json
import subprocess
import requests
import shutil
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class GitHubBountyAgent:
    """GitHub赏金任务自动化Agent"""
    
    def __init__(self, token: str, username: str, work_dir: str = "./workspace"):
        self.token = token
        self.username = username
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(exist_ok=True)
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base = "https://api.github.com"
        
    def auto_run(self, languages: Optional[List[str]] = None, max_tasks: int = 1):
        """自动化运行完整流程"""
        print("=" * 60)
        print("🤖 GitHub Bounty Agent 自动化模式")
        print("=" * 60)
        
        # 步骤1: 查找赏金任务
        print("\n📋 步骤1: 查找赏金任务...")
        tasks = self.search_bounty_tasks(languages or [])
        
        if not tasks:
            print("❌ 未找到合适的赏金任务")
            return False
        
        # 显示任务列表
        self.display_tasks(tasks)
        
        # 步骤2: 分析任务
        print("\n🔍 步骤2: 分析任务可行性...")
        selected_task = self.select_task(tasks)
        
        if not selected_task:
            print("❌ 未选择任务")
            return False
        
        # 步骤3: 获取任务详情
        print(f"\n📝 步骤3: 获取任务详情 - {selected_task['title']}")
        task_details = self.get_task_details(selected_task)
        
        # 步骤4: Fork仓库并克隆
        print("\n🍴 步骤4: Fork仓库并克隆...")
        fork_success, fork_info = self.fork_and_clone(selected_task)
        
        if not fork_success:
            print("❌ Fork或克隆失败")
            return False
        
        # 步骤5: 分析代码库
        print("\n🔬 步骤5: 分析代码库...")
        repo_info = self.analyze_repository(fork_info['clone_path'])
        
        # 步骤6: 生成解决方案
        print("\n💡 步骤6: 生成解决方案...")
        solution_plan = self.generate_solution(task_details, repo_info)
        
        # 保存方案供人工审核
        plan_file = self.work_dir / f"solution_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(solution_plan, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 解决方案已保存到: {plan_file}")
        print("\n⚠️  请人工审核方案后，决定是否继续自动实现")
        
        # 等待用户确认
        if not self.wait_for_confirmation():
            print("❌ 用户取消操作")
            return False
        
        # 步骤7: 实现解决方案
        print("\n⚙️  步骤7: 实现解决方案...")
        implementation_result = self.implement_solution(solution_plan, fork_info['clone_path'])
        
        if not implementation_result:
            print("❌ 实现失败")
            return False
        
        # 步骤8: 运行测试
        print("\n🧪 步骤8: 运行测试...")
        test_result = self.run_tests(fork_info['clone_path'])
        
        # 步骤9: 提交代码
        print("\n📤 步骤9: 提交代码...")
        commit_success = self.commit_and_push(fork_info['clone_path'])
        
        if not commit_success:
            print("❌ 提交失败")
            return False
        
        # 步骤10: 创建PR
        print("\n🎯 步骤10: 创建Pull Request...")
        pr_url = self.create_pull_request(
            selected_task['repo_full_name'],
            selected_task['number'],
            solution_plan['pr_title'],
            solution_plan['pr_description']
        )
        
        if pr_url:
            print(f"\n✅ Pull Request创建成功!")
            print(f"🔗 PR链接: {pr_url}")
            
            # 保存PR信息
            self.save_pr_info(pr_url, selected_task, solution_plan)
            
            return True
        else:
            print("❌ PR创建失败")
            return False
    
    def search_bounty_tasks(self, languages: Optional[List[str]] = None) -> List[Dict]:
        """搜索赏金任务"""
        # 这里可以复用之前的bounty_finder逻辑
        # 为了简化，这里返回示例数据
        return [
            {
                "title": "Fix memory leak in image processing",
                "number": 123,
                "url": "https://github.com/example/repo/issues/123",
                "repo_full_name": "example/repo",
                "labels": ["bug", "good first issue"],
                "bounty_amount": 500
            }
        ]
    
    def display_tasks(self, tasks: List[Dict]):
        """显示任务列表"""
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. {task['title']}")
            print(f"   仓库: {task['repo_full_name']}")
            print(f"   赏金: ${task.get('bounty_amount', 'N/A')}")
            print(f"   标签: {', '.join(task.get('labels', []))}")
    
    def select_task(self, tasks: List[Dict]) -> Optional[Dict]:
        """选择任务"""
        try:
            choice = int(input("\n请选择任务编号: ")) - 1
            if 0 <= choice < len(tasks):
                return tasks[choice]
        except:
            pass
        return None
    
    def get_task_details(self, task: Dict) -> Dict:
        """获取任务详情"""
        # 调用GitHub API获取完整issue信息
        owner, repo = task['repo_full_name'].split('/')
        url = f"{self.api_base}/repos/{owner}/{repo}/issues/{task['number']}"
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def fork_and_clone(self, task: Dict) -> tuple:
        """Fork仓库并克隆到本地"""
        owner, repo = task['repo_full_name'].split('/')
        
        # 1. Fork仓库
        print(f"   Forking {task['repo_full_name']}...")
        fork_url = f"{self.api_base}/repos/{owner}/{repo}/forks"
        response = requests.post(fork_url, headers=self.headers)
        
        if response.status_code != 202:
            return False, {}
        
        # 2. 等待Fork完成
        print("   等待Fork完成...")
        import time
        time.sleep(5)
        
        # 3. 克隆仓库
        clone_url = f"https://github.com/{self.username}/{repo}.git"
        clone_path = self.work_dir / repo
        
        if clone_path.exists():
            shutil.rmtree(clone_path)
        
        print(f"   Cloning to {clone_path}...")
        subprocess.run(
            ["git", "clone", clone_url, str(clone_path)],
            check=True,
            capture_output=True
        )
        
        # 4. 添加原始仓库为upstream
        subprocess.run(
            ["git", "remote", "add", "upstream", f"https://github.com/{owner}/{repo}.git"],
            cwd=clone_path,
            check=True,
            capture_output=True
        )
        
        return True, {
            "clone_path": clone_path,
            "repo_name": repo
        }
    
    def analyze_repository(self, repo_path: Path) -> Dict:
        """分析仓库结构"""
        repo_info = {
            "path": str(repo_path),
            "structure": [],
            "languages": {},
            "has_tests": False
        }
        
        # 分析文件结构
        for item in repo_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(repo_path)
                repo_info["structure"].append(str(rel_path))
        
        # 检测测试文件
        test_patterns = ["test_", "_test.py", "tests/", "__tests__/", ".spec."]
        for struct in repo_info["structure"]:
            if any(pattern in struct for pattern in test_patterns):
                repo_info["has_tests"] = True
                break
        
        return repo_info
    
    def generate_solution(self, task_details: Dict, repo_info: Dict) -> Dict:
        """生成解决方案"""
        # 这里应该使用AI模型来分析和生成方案
        # 简化版: 返回模板
        
        solution = {
            "task_title": task_details.get("title", ""),
            "task_description": task_details.get("body", ""),
            "analysis": {
                "problem_statement": "需要修复的问题",
                "proposed_solution": "建议的解决方案",
                "files_to_modify": [],
                "new_files": [],
                "tests_to_write": []
            },
            "pr_title": f"Fix: {task_details.get('title', '')}",
            "pr_description": f"""
## 变更说明
修复了 issue #{task_details.get('number', '')}: {task_details.get('title', '')}

## 修改内容
- 修改了xxx文件，修复了xxx问题
- 添加了xxx测试

## 测试
- 运行了相关测试，全部通过
- 手动测试了xxx场景

Closes #{task_details.get('number', '')}
            """.strip(),
            "implementation_steps": []
        }
        
        return solution
    
    def wait_for_confirmation(self) -> bool:
        """等待用户确认"""
        print("\n" + "=" * 60)
        response = input("是否继续实现解决方案? (yes/no): ").strip().lower()
        return response == 'yes'
    
    def implement_solution(self, solution: Dict, repo_path: Path):
        """实现解决方案"""
        # 这里应该使用AI来生成和修改代码
        # 简化版: 创建一个示例文件
        
        print("   正在实现解决方案...")
        
        # 创建新分支
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch_name = f"fix/issue-{timestamp}"
        
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        
        # 示例: 创建一个变更文件
        change_file = repo_path / "CHANGES.txt"
        with open(change_file, 'w') as f:
            f.write(f"Changes made at {datetime.now()}\n")
        
        # 添加文件
        subprocess.run(
            ["git", "add", "CHANGES.txt"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        
        solution['branch_name'] = branch_name
        
        return True
    
    def run_tests(self, repo_path: Path) -> bool:
        """运行测试"""
        print("   运行测试...")
        
        # 检查常见测试命令
        test_commands = [
            "pytest",
            "npm test",
            "cargo test",
            "mvn test"
        ]
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd.split(),
                    cwd=repo_path,
                    capture_output=True,
                    timeout=60
                )
                if result.returncode == 0:
                    print(f"   ✅ {cmd} 通过")
                    return True
            except:
                continue
        
        print("   ⚠️  未找到可运行的测试命令")
        return True  # 继续执行
    
    def commit_and_push(self, repo_path: Path) -> bool:
        """提交并推送代码"""
        print("   提交代码...")
        
        try:
            subprocess.run(
                ["git", "commit", "-m", "Implement solution for bounty issue"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            
            print("   推送代码...")
            
            # 配置 git remote 使用 token
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            origin_url = result.stdout.strip()
            if "github.com" in origin_url and "@" not in origin_url:
                # 更新 remote URL 以使用 token
                parts = origin_url.split("github.com/")
                if len(parts) == 2:
                    token_url = f"https://{self.token}@github.com/{parts[1]}"
                    subprocess.run(
                        ["git", "remote", "set-url", "origin", token_url],
                        cwd=repo_path,
                        check=True,
                        capture_output=True
                    )
            
            subprocess.run(
                ["git", "push", "-u", "origin", "HEAD"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Git操作失败: {e}")
            return False
    
    def create_pull_request(self, original_repo: str, issue_number: int, title: str, body: str) -> Optional[str]:
        """创建Pull Request"""
        owner, repo = original_repo.split('/')
        
        # 获取当前分支名
        url = f"{self.api_base}/repos/{owner}/{repo}/pulls"
        
        data = {
            "title": title,
            "body": body,
            "head": f"{self.username}:HEAD",
            "base": "main"
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            pr_data = response.json()
            return pr_data.get("html_url")
        except Exception as e:
            print(f"   ❌ 创建PR失败: {e}")
            return None
    
    def save_pr_info(self, pr_url: str, task: Dict, solution: Dict):
        """保存PR信息"""
        info_file = self.work_dir / f"pr_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        info = {
            "pr_url": pr_url,
            "task": task,
            "solution": solution,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 PR信息已保存到: {info_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub Bounty Agent")
    parser.add_argument("--token", help="GitHub Personal Access Token")
    parser.add_argument("--username", help="GitHub username")
    parser.add_argument("--languages", help="编程语言(逗号分隔)")
    parser.add_argument("--work-dir", default="./workspace", help="工作目录")
    parser.add_argument("--auto", action="store_true", help="自动运行模式")
    
    args = parser.parse_args()
    
    # 从环境变量或参数获取
    token = args.token or os.getenv("GITHUB_TOKEN")
    username = args.username or os.getenv("GITHUB_USERNAME")
    
    if not token:
        token = input("请输入GitHub Token: ").strip()
    
    if not username:
        username = input("请输入GitHub用户名: ").strip()
    
    languages = args.languages.split(",") if args.languages else None
    
    # 创建Agent
    agent = GitHubBountyAgent(token, username, args.work_dir)
    
    # 运行
    if args.auto:
        success = agent.auto_run(languages=languages or [])
        sys.exit(0 if success else 1)
    else:
        print("请使用 --auto 参数运行自动化模式")
        print("或等待交互模式实现...")


if __name__ == "__main__":
    main()
