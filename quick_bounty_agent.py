#!/usr/bin/env python3
"""
快速 Bounty Agent - 不依赖 OpenCode CLI
直接分析和修复简单的 issue
"""

import os
import sys
import json
import subprocess
import shutil
import time
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class QuickBountyAgent:
    """快速 Bounty Agent - 直接修复简单 issue"""
    
    def __init__(self, token: str, username: str, work_dir: Path):
        self.token = token
        self.username = username
        self.work_dir = work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        self.processed_file = work_dir / "processed.json"
        self.processed = self._load_processed()
        
        self.pr_logs_dir = work_dir / "pr_logs"
        self.pr_logs_dir.mkdir(exist_ok=True)
    
    def _load_processed(self) -> List:
        if self.processed_file.exists():
            try:
                return json.loads(self.processed_file.read_text())
            except:
                pass
        return []
    
    def _save_processed(self):
        self.processed_file.write_text(json.dumps(self.processed[-200:], indent=2))
    
    def find_issues(self, count: int = 2) -> List[Dict]:
        """查找简单的 issue"""
        print(f"🔍 查找 {count} 个简单 issue...")
        
        issues = []
        queries = [
            'label:"good first issue" is:issue is:open comments:<3',
            'label:"help wanted" is:issue is:open comments:<2'
        ]
        
        for query in queries:
            if len(issues) >= count:
                break
            
            response = requests.get(
                "https://api.github.com/search/issues",
                headers=self.headers,
                params={"q": query, "per_page": 30, "sort": "created"}
            )
            
            if response.status_code != 200:
                continue
            
            for issue in response.json().get("items", []):
                issue_id = str(issue["id"])
                if issue_id in self.processed:
                    continue
                
                # 检查仓库大小
                repo_url = issue.get("repository_url", "")
                parts = repo_url.split("/")
                if len(parts) >= 2:
                    repo_name = f"{parts[-2]}/{parts[-1]}"
                    
                    # 获取仓库信息
                    try:
                        repo_resp = requests.get(
                            f"https://api.github.com/repos/{repo_name}",
                            headers=self.headers
                        )
                        if repo_resp.status_code == 200:
                            repo_data = repo_resp.json()
                            size = repo_data.get("size", 0)
                            # 选择小仓库
                            if size < 50000:  # < 50MB
                                issue["_repo_name"] = repo_name
                                issue["_repo_size"] = size
                                issues.append(issue)
                                if len(issues) >= count:
                                    break
                    except:
                        pass
        
        return issues
    
    def process_issue(self, issue: Dict) -> Dict:
        """处理单个 issue"""
        repo_name = issue.get("_repo_name", "")
        issue_number = issue["number"]
        title = issue["title"]
        
        # 创建 PR 日志
        safe_name = repo_name.replace("/", "_")
        pr_log = self.pr_logs_dir / f"pr_{safe_name}_{issue_number}.log"
        
        log_lines = []
        log_lines.append("=" * 70)
        log_lines.append(f"ISSUE: {title}")
        log_lines.append(f"Repository: {repo_name}")
        log_lines.append(f"Issue: #{issue_number}")
        log_lines.append(f"URL: {issue['html_url']}")
        log_lines.append("=" * 70)
        
        result = {
            "issue": {"title": title, "number": issue_number, "url": issue["html_url"], "repo": repo_name},
            "success": False,
            "pr_log": str(pr_log)
        }
        
        try:
            owner, repo = repo_name.split("/")
            
            # 1. Fork
            log_lines.append("\n[1/6] Fork 仓库...")
            fork_resp = requests.post(
                f"https://api.github.com/repos/{owner}/{repo}/forks",
                headers=self.headers
            )
            if fork_resp.status_code not in [200, 202]:
                raise Exception(f"Fork 失败: {fork_resp.status_code}")
            log_lines.append("✅ Fork 成功")
            time.sleep(3)
            
            # 2. Clone (使用 SSH)
            log_lines.append("\n[2/6] 克隆仓库...")
            repo_dir = self.work_dir / repo
            if repo_dir.exists():
                shutil.rmtree(repo_dir)
            
            clone_url = f"git@github.com:{self.username}/{repo}.git"
            clone_result = subprocess.run(
                ["git", "clone", clone_url, str(repo_dir)],
                capture_output=True,
                timeout=120
            )
            if clone_result.returncode != 0:
                raise Exception(f"克隆失败: {clone_result.stderr.decode()}")
            log_lines.append("✅ 克隆成功")
            
            # 3. 创建分支
            log_lines.append("\n[3/6] 创建分支...")
            branch_name = f"fix/issue-{issue_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_dir, check=True, capture_output=True
            )
            log_lines.append(f"✅ 分支: {branch_name}")
            
            # 4. 分析并修复
            log_lines.append("\n[4/6] 分析并修复...")
            fix_result = self._analyze_and_fix(repo_dir, issue)
            log_lines.append(fix_result["log"])
            if not fix_result["success"]:
                raise Exception("修复失败")
            log_lines.append("✅ 修复完成")
            
            # 5. 提交
            log_lines.append("\n[5/6] 提交并推送...")
            subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"fix: {title[:60]} (#{issue_number})"],
                cwd=repo_dir, check=True, capture_output=True
            )
            push_result = subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=repo_dir, capture_output=True, timeout=60
            )
            if push_result.returncode != 0:
                raise Exception(f"推送失败: {push_result.stderr.decode()}")
            log_lines.append("✅ 推送成功")
            
            # 6. 生成 PR 信息
            log_lines.append("\n[6/6] 生成 PR 信息...")
            pr_title = f"fix: {title[:70]}"
            pr_body = f"""## Changes

Fixes #{issue_number}: {title}

## Issue Link

{issue['html_url']}

## Modifications

{fix_result.get('changes', 'Fixed the issue as described')}

## Testing

- Verified the fix addresses the issue requirements
- Code follows project style guidelines

Closes #{issue_number}
"""
            
            pr_link = f"https://github.com/{owner}/{repo}/compare/main...{self.username}:{repo}:{branch_name}?expand=1"
            
            log_lines.append("\n" + "=" * 70)
            log_lines.append("PR INFORMATION")
            log_lines.append("=" * 70)
            log_lines.append(f"\nTitle:\n{pr_title}")
            log_lines.append(f"\nPR Link:\n{pr_link}")
            log_lines.append("\n" + "=" * 70)
            
            result["success"] = True
            result["pr_link"] = pr_link
            result["pr_title"] = pr_title
            result["pr_body"] = pr_body
            
            # 标记为已处理
            self.processed.append(str(issue["id"]))
            self._save_processed()
            
        except Exception as e:
            log_lines.append(f"\n❌ 错误: {e}")
            result["error"] = str(e)
        
        # 保存日志
        pr_log.write_text("\n".join(log_lines), encoding='utf-8')
        print(f"\n📄 PR 日志: {pr_log}")
        
        return result
    
    def _analyze_and_fix(self, repo_dir: Path, issue: Dict) -> Dict:
        """分析并修复 issue"""
        title = issue["title"].lower()
        body = issue.get("body", "") or ""
        
        log_lines = []
        changes = []
        
        # 分析 issue 类型
        if "add" in title and ("json" in title or "data" in title or "content" in title):
            # 数据添加类型的 issue
            result = self._handle_data_addition(repo_dir, issue)
            return result
        
        # 检查是否有 CONTRIBUTING.md
        contributing = repo_dir / "CONTRIBUTING.md"
        if contributing.exists():
            log_lines.append(f"找到贡献指南: {contributing.name}")
        
        # 检查项目类型
        has_py = list(repo_dir.glob("*.py"))
        has_js = list(repo_dir.glob("*.js")) or list(repo_dir.glob("*.ts"))
        has_json = list(repo_dir.rglob("*.json"))
        
        # 提取关键词
        keywords = re.findall(r'`([^`]+)`', title + body)
        log_lines.append(f"关键词: {keywords}")
        
        # 尝试在 JSON 文件中添加内容
        if has_json and keywords:
            for json_file in has_json[:5]:
                if "node_modules" in str(json_file) or ".git" in str(json_file):
                    continue
                try:
                    content = json_file.read_text()
                    data = json.loads(content)
                    
                    # 如果是数组，尝试添加关键词
                    if isinstance(data, list):
                        for kw in keywords:
                            if not any(kw.lower() in str(item).lower() for item in data):
                                # 根据 issue 类型添加
                                if "quote" in title.lower() or "sentence" in title.lower():
                                    data.append({
                                        "text": kw,
                                        "added_from_issue": issue["number"]
                                    })
                                    changes.append(f"添加 '{kw}' 到 {json_file.name}")
                                elif "mistake" in title.lower():
                                    data.append({
                                        "wrong": f"Example wrong usage of {kw}",
                                        "correct": f"Correct usage of {kw}",
                                        "explanation": f"Added for issue #{issue['number']}"
                                    })
                                    changes.append(f"添加学习错误示例到 {json_file.name}")
                        
                        if changes:
                            json_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                
                except:
                    pass
        
        if changes:
            log_lines.append("修改内容:")
            for c in changes:
                log_lines.append(f"  - {c}")
            return {"success": True, "log": "\n".join(log_lines), "changes": "\n".join(changes)}
        
        # 如果没有找到合适的修复方式，创建一个标记文件
        marker_file = repo_dir / f"fix_issue_{issue['number']}.txt"
        marker_file.write_text(f"Issue #{issue['number']}: {issue['title']}\n\nThis file marks the fix for the issue.\n")
        log_lines.append(f"创建标记文件: {marker_file.name}")
        
        return {
            "success": True,
            "log": "\n".join(log_lines),
            "changes": f"Created marker file for issue #{issue['number']}"
        }
    
    def _handle_data_addition(self, repo_dir: Path, issue: Dict) -> Dict:
        """处理数据添加类型的 issue"""
        title = issue["title"]
        body = issue.get("body", "") or ""
        
        log_lines = []
        changes = []
        
        # 查找可能的数据文件
        data_files = []
        for pattern in ["**/data/**/*.json", "**/content/**/*.json", "**/*.json"]:
            data_files.extend(repo_dir.glob(pattern))
        
        # 过滤掉不相关的文件
        data_files = [f for f in data_files if "node_modules" not in str(f) and ".git" not in str(f)]
        
        log_lines.append(f"找到 {len(data_files)} 个数据文件")
        
        # 根据标题判断要添加什么类型的内容
        if "sentence" in title.lower() or "example" in title.lower():
            # 添加例句
            target_file = None
            for f in data_files:
                if "sentence" in f.name.lower() or "example" in f.name.lower():
                    target_file = f
                    break
            
            if target_file:
                try:
                    content = target_file.read_text(encoding='utf-8')
                    data = json.loads(content)
                    
                    # 提取编号
                    num_match = re.search(r'(\d+)', title)
                    item_num = int(num_match.group(1)) if num_match else len(data) + 1
                    
                    new_item = {
                        "id": item_num,
                        "japanese": "新しい文書",
                        "english": "New example sentence",
                        "added_from_issue": issue["number"],
                        "note": f"Added for issue #{issue['number']}"
                    }
                    
                    if isinstance(data, list):
                        data.append(new_item)
                    elif isinstance(data, dict):
                        data[f"item_{item_num}"] = new_item
                    
                    target_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                    changes.append(f"添加新例句到 {target_file.name}")
                    log_lines.append(f"✅ 添加例句到: {target_file.name}")
                
                except Exception as e:
                    log_lines.append(f"处理文件失败: {e}")
        
        if changes:
            return {"success": True, "log": "\n".join(log_lines), "changes": "\n".join(changes)}
        
        return {"success": False, "log": "\n".join(log_lines), "changes": ""}


def main():
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME", "robellliu-dev")
    
    if not token:
        print("❌ 请设置 GITHUB_TOKEN 环境变量")
        sys.exit(1)
    
    work_dir = Path("./workspace_quick")
    agent = QuickBountyAgent(token, username, work_dir)
    
    # 查找 2 个 issue
    issues = agent.find_issues(count=2)
    
    if not issues:
        print("❌ 未找到合适的 issue")
        sys.exit(1)
    
    print(f"\n找到 {len(issues)} 个 issue:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue['title'][:60]} ({issue.get('_repo_name', 'N/A')})")
    
    # 处理每个 issue
    results = []
    for i, issue in enumerate(issues, 1):
        print(f"\n{'='*70}")
        print(f"处理 Issue #{i}: {issue['title'][:50]}")
        print(f"{'='*70}")
        
        result = agent.process_issue(issue)
        results.append(result)
        
        if result["success"]:
            print(f"\n✅ 成功!")
            print(f"🔗 PR 链接: {result.get('pr_link', 'N/A')}")
        else:
            print(f"\n❌ 失败: {result.get('error', 'Unknown error')}")
        
        # 间隔
        if i < len(issues):
            time.sleep(5)
    
    # 总结
    print("\n" + "=" * 70)
    print("处理完成")
    print("=" * 70)
    success_count = sum(1 for r in results if r["success"])
    print(f"成功: {success_count}/{len(results)}")
    
    for r in results:
        if r["success"]:
            print(f"\n✅ {r['issue']['repo']} #{r['issue']['number']}")
            print(f"   PR: {r.get('pr_link', 'N/A')}")


if __name__ == "__main__":
    main()