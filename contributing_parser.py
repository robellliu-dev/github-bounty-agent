#!/usr/bin/env python3
"""
CONTRIBUTING.md规范解析和PR生成器
自动解析项目的贡献指南，生成符合规范的PR
"""

import requests
import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class ContributingGuideParser:
    """贡献指南解析器"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def fetch_contributing_guide(self, repo_full_name: str) -> Optional[str]:
        """获取项目的CONTRIBUTING.md文件"""
        try:
            # 尝试多种可能的路径
            possible_paths = [
                "CONTRIBUTING.md",
                "docs/CONTRIBUTING.md",
                ".github/CONTRIBUTING.md",
                "CONTRIBUTING",
                "contributing.md",
            ]
            
            for path in possible_paths:
                url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    content = response.json()
                    if content.get("encoding") == "base64":
                        import base64
                        return base64.b64decode(content["content"]).decode("utf-8")
            
            return None
            
        except Exception as e:
            print(f"获取CONTRIBUTING.md失败: {e}")
            return None
    
    def parse_commit_message_format(self, contributing_text: str) -> Dict:
        """解析提交信息格式规范"""
        commit_rules = {
            "format": None,
            "conventional_commits": False,
            "max_length": None,
            "prefixes": [],
            "examples": []
        }
        
        # 检测Conventional Commits
        if "conventional commits" in contributing_text.lower():
            commit_rules["conventional_commits"] = True
            commit_rules["format"] = "conventional"
        
        # 检测常见前缀
        prefixes = re.findall(r'(?:type|prefix|category)[:\s]+\[?([^\]\n]+)\]?', contributing_text, re.IGNORECASE)
        if prefixes:
            for prefix_list in prefixes:
                for p in re.split(r'[,|/]', prefix_list):
                    p = p.strip().lower()
                    if p and p not in commit_rules["prefixes"]:
                        commit_rules["prefixes"].append(p)
        
        # 检测提交信息长度限制
        max_length = re.search(r'(?:max.*length|maximum.*length)[:\s]+(\d+)', contributing_text, re.IGNORECASE)
        if max_length:
            commit_rules["max_length"] = int(max_length.group(1))
        
        # 提取示例
        examples = re.findall(r'example[:\s]*\n(?:\s*[-*]?\s*(.+?)(?:\n|$))+', contributing_text, re.IGNORECASE)
        for example in examples:
            example = example.strip()
            if example and example not in commit_rules["examples"]:
                commit_rules["examples"].append(example)
        
        return commit_rules
    
    def parse_pr_guidelines(self, contributing_text: str) -> Dict:
        """解析PR指南"""
        pr_rules = {
            "title_format": None,
            "title_prefixes": [],
            "description_template": None,
            "required_sections": [],
            "checklist": [],
            "reviewers": None
        }
        
        # 解析PR标题格式
        title_formats = re.findall(r'(?:pr.*title|pull.*request.*title)[:\s]+([^\n]+)', contributing_text, re.IGNORECASE)
        if title_formats:
            pr_rules["title_format"] = title_formats[0].strip()
        
        # 提取PR前缀
        pr_prefixes = re.findall(r'(?:pr.*prefix|title.*prefix)[:\s]+\[?([^\]\n]+)\]?', contributing_text, re.IGNORECASE)
        if pr_prefixes:
            for prefix_list in pr_prefixes:
                for p in re.split(r'[,|/]', prefix_list):
                    p = p.strip()
                    if p and p not in pr_rules["title_prefixes"]:
                        pr_rules["title_prefixes"].append(p)
        
        # 提取必需的描述部分
        required_sections = re.findall(r'(?:must|should|include|contain)[:\s]+(?:a|an|the)?\s*(?:section|part|area|item)[:\s]+\[?([^\]\n]+)\]?', 
                                        contributing_text, re.IGNORECASE)
        for section in required_sections:
            section = section.strip().lower()
            if section and section not in pr_rules["required_sections"]:
                pr_rules["required_sections"].append(section)
        
        # 提取检查清单
        checklist_items = re.findall(r'\s*[-*]\s*\[?\s*?\]\s*(.+?)(?:\n|$)', contributing_text)
        for item in checklist_items:
            item = item.strip()
            if item and len(item) < 200 and item not in pr_rules["checklist"]:
                pr_rules["checklist"].append(item)
        
        return pr_rules
    
    def parse_code_style_rules(self, contributing_text: str) -> Dict:
        """解析代码风格规范"""
        code_rules = {
            "linter": None,
            "formatter": None,
            "style_guide": None,
            "testing_required": False,
            "coverage_required": False
        }
        
        # 检测linter
        linters = re.findall(r'(?:linter|linting)[:\s]+([^\n]+)', contributing_text, re.IGNORECASE)
        if linters:
            code_rules["linter"] = linters[0].strip()
        
        # 检测formatter
        formatters = re.findall(r'(?:formatter|formatting)[:\s]+([^\n]+)', contributing_text, re.IGNORECASE)
        if formatters:
            code_rules["formatter"] = formatters[0].strip()
        
        # 检测风格指南
        style_guides = re.findall(r'(?:style.*guide|code.*style|pep|google.*style|airbnb.*style)[:\s]+([^\n]+)', 
                                  contributing_text, re.IGNORECASE)
        if style_guides:
            code_rules["style_guide"] = style_guides[0].strip()
        
        # 检测测试要求
        if re.search(r'(?:test|testing)[:\s]+(?:required|must|mandatory)', contributing_text, re.IGNORECASE):
            code_rules["testing_required"] = True
        
        # 检测覆盖率要求
        coverage = re.search(r'coverage[:\s]+(\d+)%', contributing_text, re.IGNORECASE)
        if coverage:
            code_rules["coverage_required"] = True
            code_rules["coverage_threshold"] = int(coverage.group(1))
        
        return code_rules
    
    def parse_branching_strategy(self, contributing_text: str) -> Dict:
        """解析分支策略"""
        branch_rules = {
            "default_branch": "main",
            "branch_naming": None,
            "rebase_required": False,
            "squash_commits": False
        }
        
        # 检测默认分支
        default_branch = re.search(r'(?:default.*branch|main.*branch)[:\s]+([^\s,]+)', contributing_text, re.IGNORECASE)
        if default_branch:
            branch_rules["default_branch"] = default_branch.group(1).strip()
        else:
            # 常见的默认分支
            if "master" in contributing_text:
                branch_rules["default_branch"] = "master"
        
        # 检测分支命名规范
        branch_naming = re.search(r'(?:branch.*naming|naming.*convention)[:\s]+([^\n]+)', contributing_text, re.IGNORECASE)
        if branch_naming:
            branch_rules["branch_naming"] = branch_naming.group(1).strip()
        
        # 检测rebase要求
        if re.search(r'(?:rebase)[:\s]+(?:required|must)', contributing_text, re.IGNORECASE):
            branch_rules["rebase_required"] = True
        
        # 检测squash要求
        if re.search(r'(?:squash)[:\s]+(?:required|must|commits)', contributing_text, re.IGNORECASE):
            branch_rules["squash_commits"] = True
        
        return branch_rules
    
    def parse_full_guide(self, repo_full_name: str) -> Dict:
        """解析完整的贡献指南"""
        contributing_text = self.fetch_contributing_guide(repo_full_name)
        
        if not contributing_text:
            print(f"未找到 {repo_full_name} 的CONTRIBUTING.md，使用默认规范")
            return self.get_default_guidelines()
        
        guidelines = {
            "commit_rules": self.parse_commit_message_format(contributing_text),
            "pr_rules": self.parse_pr_guidelines(contributing_text),
            "code_rules": self.parse_code_style_rules(contributing_text),
            "branch_rules": self.parse_branching_strategy(contributing_text)
        }
        
        return guidelines
    
    def get_default_guidelines(self) -> Dict:
        """获取默认的贡献指南"""
        return {
            "commit_rules": {
                "format": "conventional",
                "conventional_commits": True,
                "max_length": 72,
                "prefixes": ["feat", "fix", "docs", "style", "refactor", "test", "chore"],
                "examples": []
            },
            "pr_rules": {
                "title_format": None,
                "title_prefixes": [],
                "description_template": None,
                "required_sections": ["description", "type of change", "testing"],
                "checklist": [
                    "My code follows the style guidelines of this project",
                    "I have performed a self-review of my code",
                    "I have commented my code, particularly in hard-to-understand areas",
                    "I have made corresponding changes to the documentation",
                    "My changes generate no new warnings",
                    "I have added tests that prove my fix is effective or that my feature works",
                    "New and existing unit tests pass locally with my changes"
                ],
                "reviewers": None
            },
            "code_rules": {
                "linter": None,
                "formatter": None,
                "style_guide": None,
                "testing_required": True,
                "coverage_required": False
            },
            "branch_rules": {
                "default_branch": "main",
                "branch_naming": None,
                "rebase_required": False,
                "squash_commits": False
            }
        }


class PRGenerator:
    """PR生成器"""
    
    def __init__(self, guidelines: Dict):
        self.guidelines = guidelines
    
    def generate_commit_message(self, change_type: str, description: str, issue_number: Optional[int] = None) -> str:
        """生成符合规范的提交信息"""
        commit_rules = self.guidelines["commit_rules"]
        
        # Conventional Commits格式
        if commit_rules.get("conventional_commits") or commit_rules.get("format") == "conventional":
            # 使用前缀
            prefix = change_type.lower()
            if commit_rules.get("prefixes") and prefix not in commit_rules["prefixes"]:
                # 使用第一个前缀作为默认
                prefix = commit_rules["prefixes"][0]
            
            # 构建提交信息
            commit_msg = f"{prefix}: {description}"
            
            # 添加issue引用
            if issue_number:
                commit_msg += f" (#{issue_number})"
            
            # 检查长度限制
            max_length = commit_rules.get("max_length", 72)
            if len(commit_msg) > max_length:
                commit_msg = commit_msg[:max_length-3] + "..."
            
            return commit_msg
        
        # 简单格式
        else:
            commit_msg = description
            if issue_number:
                commit_msg += f" (#{issue_number})"
            return commit_msg
    
    def generate_pr_title(self, change_type: str, description: str, issue_number: Optional[int] = None) -> str:
        """生成符合规范的PR标题"""
        pr_rules = self.guidelines["pr_rules"]
        
        # 如果有特定的标题格式
        if pr_rules.get("title_format"):
            title = pr_rules["title_format"]
            title = title.replace("{type}", change_type)
            title = title.replace("{description}", description)
            if issue_number:
                title = title.replace("{issue}", str(issue_number))
            return title
        
        # 如果有前缀要求
        elif pr_rules.get("title_prefixes"):
            prefix = change_type
            if prefix not in pr_rules["title_prefixes"]:
                prefix = pr_rules["title_prefixes"][0]
            return f"[{prefix}] {description}"
        
        # 默认格式
        else:
            if issue_number:
                return f"Fix #{issue_number}: {description}"
            return f"{change_type}: {description}"
    
    def generate_pr_description(self, 
                                issue: Dict, 
                                changes: List[str], 
                                tests: List[str],
                                additional_info: Optional[str] = None) -> str:
        """生成符合规范的PR描述"""
        pr_rules = self.guidelines["pr_rules"]
        commit_rules = self.guidelines["commit_rules"]
        
        description = []
        
        # 标题
        description.append(f"## 变更说明")
        description.append(f"")
        description.append(f"修复了 issue #{issue.get('number', 'N/A')}: {issue.get('title', 'N/A')}")
        description.append(f"")
        
        # 变更类型
        if commit_rules.get("conventional_commits"):
            description.append(f"**变更类型:** {issue.get('change_type', 'fix')}")
            description.append(f"")
        
        # 修改内容
        description.append(f"## 修改内容")
        for change in changes:
            description.append(f"- {change}")
        description.append(f"")
        
        # 测试
        if tests:
            description.append(f"## 测试")
            for test in tests:
                description.append(f"- {test}")
            description.append(f"")
        
        # 检查清单
        if pr_rules.get("checklist"):
            description.append(f"## 检查清单")
            for item in pr_rules["checklist"]:
                description.append(f"- [x] {item}")
            description.append(f"")
        
        # 额外信息
        if additional_info:
            description.append(f"## 额外信息")
            description.append(additional_info)
            description.append(f"")
        
        # Closes
        description.append(f"Closes #{issue.get('number', 'N/A')}")
        
        return "\n".join(description)
    
    def generate_branch_name(self, issue: Dict, change_type: str) -> str:
        """生成符合规范的分支名"""
        branch_rules = self.guidelines["branch_rules"]
        pr_rules = self.guidelines["pr_rules"]
        
        # 如果有特定的分支命名规范
        if branch_rules.get("branch_naming"):
            branch = branch_rules["branch_naming"]
            branch = branch.replace("{type}", change_type.lower())
            branch = branch.replace("{issue}", str(issue.get("number", "")))
            branch = branch.replace("{title}", issue.get("title", "").lower().replace(" ", "-"))
            return branch
        
        # 默认分支命名
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d')
            prefix = change_type.lower()
            title_slug = re.sub(r'[^a-z0-9]+', '-', issue.get("title", "").lower()).strip('-')
            return f"{prefix}/{issue.get('number')}-{title_slug[:30]}-{timestamp}"


def test_parser():
    """测试解析器"""
    import sys
    
    token = sys.argv[1] if len(sys.argv) > 1 else input("请输入GitHub Token: ").strip()
    repo = sys.argv[2] if len(sys.argv) > 2 else input("请输入仓库名 (如: owner/repo): ").strip()
    
    parser = ContributingGuideParser(token)
    guidelines = parser.parse_full_guide(repo)
    
    print(json.dumps(guidelines, indent=2, ensure_ascii=False))


def test_generator():
    """测试生成器"""
    # 测试数据
    guidelines = {
        "commit_rules": {
            "format": "conventional",
            "conventional_commits": True,
            "max_length": 72,
            "prefixes": ["feat", "fix", "docs", "style", "refactor", "test", "chore"]
        },
        "pr_rules": {
            "title_prefixes": ["Bugfix", "Feature", "Refactor", "Docs"],
            "required_sections": ["description", "type of change", "testing"],
            "checklist": [
                "My code follows the style guidelines of this project",
                "I have performed a self-review of my code",
                "I have added tests that prove my fix is effective"
            ]
        },
        "code_rules": {
            "testing_required": True
        },
        "branch_rules": {
            "default_branch": "main"
        }
    }
    
    generator = PRGenerator(guidelines)
    
    # 测试提交信息
    commit_msg = generator.generate_commit_message("fix", "Fix memory leak in image processing", 123)
    print(f"提交信息: {commit_msg}")
    
    # 测试PR标题
    pr_title = generator.generate_pr_title("fix", "Fix memory leak in image processing", 123)
    print(f"PR标题: {pr_title}")
    
    # 测试分支名
    issue = {"number": 123, "title": "Fix memory leak in image processing"}
    branch_name = generator.generate_branch_name(issue, "fix")
    print(f"分支名: {branch_name}")
    
    # 测试PR描述
    issue = {"number": 123, "title": "Fix memory leak in image processing"}
    pr_desc = generator.generate_pr_description(
        issue,
        ["Fixed memory leak in image processing module", "Added proper resource cleanup"],
        ["Added unit tests for memory cleanup", "Verified no memory leaks with valgrind"]
    )
    print(f"\nPR描述:\n{pr_desc}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_parser()
    else:
        test_generator()
