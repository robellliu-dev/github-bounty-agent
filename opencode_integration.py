#!/usr/bin/env python3
"""
OpenCode CLI 集成模块
使用 OpenCode CLI 进行真正的代码分析和智能修复
"""

import os
import sys
import json
import subprocess
import re
import shutil
import requests
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging


@dataclass
class IssueContext:
    title: str
    number: int
    body: str
    url: str
    repo_full_name: str
    labels: List[str] = field(default_factory=list)
    issue_type: str = "bug"
    difficulty: str = "medium"


class OpenCodeClient:
    """OpenCode CLI 客户端"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.logger = logging.getLogger(__name__)
    
    def analyze_issue(self, issue: IssueContext, repo_path: Path) -> Dict:
        """使用 OpenCode 分析 issue"""
        self.logger.info(f"使用 OpenCode 分析 issue #{issue.number}: {issue.title}")
        
        prompt = self._build_analysis_prompt(issue, repo_path)
        
        try:
            result = self._run_opencode_command(
                prompt,
                cwd=str(repo_path),
                timeout=300
            )
            
            return {
                "success": True,
                "analysis": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"OpenCode 分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis": self._generate_fallback_analysis(issue)
            }
    
    def generate_fix(self, issue: IssueContext, repo_path: Path, analysis: Dict) -> Dict:
        """使用 OpenCode 生成修复代码"""
        self.logger.info(f"生成修复方案 for issue #{issue.number}")
        
        prompt = self._build_fix_prompt(issue, analysis, repo_path)
        
        try:
            result = self._run_opencode_command(
                prompt,
                cwd=str(repo_path),
                timeout=600
            )
            
            return {
                "success": True,
                "fix_plan": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"生成修复失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def implement_fix(self, repo_path: Path, fix_plan: Dict) -> bool:
        """实施修复"""
        self.logger.info(f"实施修复到 {repo_path}")
        
        prompt = f"""
请根据以下修复计划实施代码修改:

修复计划:
{json.dumps(fix_plan, indent=2, ensure_ascii=False)}

要求:
1. 直接修改相关文件
2. 确保代码风格一致
3. 添加必要的注释
4. 不要删除现有代码，只修改或添加

请直接实施修改，不需要解释。
"""
        
        try:
            result = self._run_opencode_command(
                prompt,
                cwd=str(repo_path),
                timeout=600
            )
            return True
        except Exception as e:
            self.logger.error(f"实施修复失败: {e}")
            return False
    
    def run_tests_and_fix(self, repo_path: Path, max_iterations: int = 3) -> Dict:
        """运行测试并自动修复失败"""
        self.logger.info(f"运行测试并修复: {repo_path}")
        
        for iteration in range(max_iterations):
            test_result = self._detect_and_run_tests(repo_path)
            
            if test_result["success"]:
                self.logger.info("测试通过!")
                return {"success": True, "iterations": iteration + 1}
            
            self.logger.warning(f"测试失败 (迭代 {iteration + 1}/{max_iterations})")
            
            if iteration < max_iterations - 1:
                fix_prompt = f"""
测试失败，请修复以下问题:

测试输出:
{test_result.get('output', '')}

错误信息:
{test_result.get('errors', '')}

请分析失败原因并修复代码。
"""
                try:
                    self._run_opencode_command(
                        fix_prompt,
                        cwd=str(repo_path),
                        timeout=300
                    )
                except Exception as e:
                    self.logger.error(f"自动修复测试失败: {e}")
        
        return {"success": False, "iterations": max_iterations}
    
    def review_code_quality(self, repo_path: Path) -> Dict:
        """审查代码质量"""
        prompt = """
请审查当前代码质量，检查:
1. 代码风格是否符合规范
2. 是否有明显的 bug 或安全问题
3. 是否有未使用的导入或变量
4. 注释是否充分
5. 变量命名是否合理

请列出发现的问题并给出修复建议。
"""
        
        try:
            result = self._run_opencode_command(
                prompt,
                cwd=str(repo_path),
                timeout=300
            )
            return {"success": True, "review": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_opencode_command(self, prompt: str, cwd: str = None, timeout: int = 300) -> str:
        """运行 OpenCode CLI 命令"""
        env = os.environ.copy()
        env["OPENCODE_NO_INTERACTIVE"] = "1"
        
        process = subprocess.Popen(
            ["opencode"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd or str(self.work_dir),
            env=env,
            text=True
        )
        
        try:
            stdout, stderr = process.communicate(input=prompt, timeout=timeout)
            
            if process.returncode != 0:
                self.logger.warning(f"OpenCode 返回非零状态: {stderr}")
            
            return stdout.strip()
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"OpenCode 命令超时 ({timeout}s)")
    
    def _build_analysis_prompt(self, issue: IssueContext, repo_path: Path) -> str:
        """构建分析提示"""
        return f"""
请分析以下 GitHub Issue 并提供详细的修复方案:

## Issue 信息
- 标题: {issue.title}
- 编号: #{issue.number}
- 类型: {issue.issue_type}
- 标签: {', '.join(issue.labels)}
- 链接: {issue.url}

## Issue 描述
{issue.body}

## 仓库信息
- 路径: {repo_path}
- 主要语言: {self._detect_language(repo_path)}

请:
1. 分析问题的根本原因
2. 找出需要修改的文件
3. 提出具体的修复方案
4. 列出需要注意的边界情况
"""
    
    def _build_fix_prompt(self, issue: IssueContext, analysis: Dict, repo_path: Path) -> str:
        """构建修复提示"""
        return f"""
根据以下分析实施代码修复:

## 原始 Issue
标题: {issue.title}

## 分析结果
{json.dumps(analysis, indent=2, ensure_ascii=False)}

请:
1. 实施具体的代码修改
2. 添加必要的测试
3. 更新相关文档（如果需要）
4. 确保修改不破坏现有功能
"""
    
    def _detect_language(self, repo_path: Path) -> str:
        """检测仓库主要语言"""
        language_files = {
            "Python": ["*.py", "requirements.txt", "setup.py", "pyproject.toml"],
            "JavaScript": ["*.js", "package.json"],
            "TypeScript": ["*.ts", "*.tsx", "tsconfig.json"],
            "Go": ["*.go", "go.mod"],
            "Rust": ["*.rs", "Cargo.toml"],
            "Java": ["*.java", "pom.xml", "build.gradle"],
        }
        
        for lang, patterns in language_files.items():
            for pattern in patterns:
                if list(repo_path.glob(pattern)):
                    return lang
        return "Unknown"
    
    def _detect_and_run_tests(self, repo_path: Path) -> Dict:
        """检测并运行测试"""
        test_commands = []
        
        if (repo_path / "pytest.ini").exists() or (repo_path / "setup.cfg").exists():
            test_commands.append(["python", "-m", "pytest", "-xvs"])
        elif list(repo_path.glob("test_*.py")) or list(repo_path.glob("*_test.py")):
            test_commands.append(["python", "-m", "pytest", "-xvs"])
        
        if (repo_path / "package.json").exists():
            test_commands.append(["npm", "test"])
            test_commands.append(["yarn", "test"])
        
        if (repo_path / "go.mod").exists():
            test_commands.append(["go", "test", "./..."])
        
        if (repo_path / "Cargo.toml").exists():
            test_commands.append(["cargo", "test"])
        
        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                return {
                    "success": result.returncode == 0,
                    "command": " ".join(cmd),
                    "output": result.stdout,
                    "errors": result.stderr
                }
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "command": " ".join(cmd),
                    "errors": "测试超时"
                }
        
        return {"success": True, "command": None, "output": "未找到测试"}
    
    def _generate_fallback_analysis(self, issue: IssueContext) -> Dict:
        """生成备用分析"""
        return {
            "root_cause": "需要进一步分析",
            "affected_files": [],
            "proposed_fix": "请手动分析并修复",
            "difficulty": issue.difficulty
        }


class IntelligentCodeAnalyzer:
    """智能代码分析器"""
    
    def __init__(self, token: str, work_dir: Path):
        self.token = token
        self.work_dir = work_dir
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.logger = logging.getLogger(__name__)
    
    def analyze_repository_structure(self, repo_path: Path) -> Dict:
        """分析仓库结构"""
        structure = {
            "language": self._detect_primary_language(repo_path),
            "test_framework": self._detect_test_framework(repo_path),
            "build_system": self._detect_build_system(repo_path),
            "ci_config": self._detect_ci_config(repo_path),
            "key_files": self._find_key_files(repo_path),
            "dependencies": self._extract_dependencies(repo_path)
        }
        return structure
    
    def find_related_code(self, repo_path: Path, issue: IssueContext) -> List[Path]:
        """查找与 issue 相关的代码文件"""
        related_files = []
        keywords = self._extract_keywords(issue)
        
        for keyword in keywords[:5]:
            try:
                result = subprocess.run(
                    ["grep", "-rl", keyword, str(repo_path)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                for file_path in result.stdout.strip().split('\n'):
                    if file_path and not self._is_excluded_file(file_path):
                        related_files.append(Path(file_path))
            except:
                pass
        
        return list(set(related_files))[:20]
    
    def classify_issue_type(self, issue: IssueContext) -> str:
        """分类 issue 类型"""
        title = issue.title.lower()
        body = issue.body.lower()
        text = title + " " + body
        
        bug_keywords = ["bug", "error", "crash", "fail", "broken", "exception", "fix"]
        if any(kw in text for kw in bug_keywords):
            return "bug"
        
        feature_keywords = ["feature", "add", "implement", "support", "enhancement"]
        if any(kw in text for kw in feature_keywords):
            return "feature"
        
        doc_keywords = ["doc", "documentation", "readme", "typo", "spelling"]
        if any(kw in text for kw in doc_keywords):
            return "docs"
        
        refactor_keywords = ["refactor", "optimize", "performance", "clean"]
        if any(kw in text for kw in refactor_keywords):
            return "refactor"
        
        test_keywords = ["test", "testing", "coverage", "spec"]
        if any(kw in text for kw in test_keywords):
            return "test"
        
        return "other"
    
    def estimate_difficulty(self, issue: IssueContext, repo_structure: Dict) -> str:
        """评估 issue 难度"""
        labels = [l.lower() for l in issue.labels]
        
        if "good first issue" in labels:
            return "easy"
        
        if "help wanted" in labels:
            return "medium"
        
        body_length = len(issue.body)
        if body_length < 200:
            return "easy"
        elif body_length < 1000:
            return "medium"
        else:
            return "hard"
    
    def _detect_primary_language(self, repo_path: Path) -> str:
        """检测主要语言"""
        if list(repo_path.glob("*.py")):
            return "Python"
        if list(repo_path.glob("*.ts")) or list(repo_path.glob("*.tsx")):
            return "TypeScript"
        if list(repo_path.glob("*.js")):
            return "JavaScript"
        if list(repo_path.glob("*.go")):
            return "Go"
        if list(repo_path.glob("*.rs")):
            return "Rust"
        if list(repo_path.glob("*.java")):
            return "Java"
        return "Unknown"
    
    def _detect_test_framework(self, repo_path: Path) -> Optional[str]:
        """检测测试框架"""
        if (repo_path / "pytest.ini").exists() or list(repo_path.glob("test_*.py")):
            return "pytest"
        if (repo_path / "jest.config.js").exists() or list(repo_path.glob("*.test.js")):
            return "jest"
        if list(repo_path.glob("*_test.go")):
            return "go test"
        return None
    
    def _detect_build_system(self, repo_path: Path) -> Optional[str]:
        """检测构建系统"""
        if (repo_path / "setup.py").exists() or (repo_path / "pyproject.toml").exists():
            return "setuptools/pip"
        if (repo_path / "package.json").exists():
            return "npm/yarn"
        if (repo_path / "go.mod").exists():
            return "go modules"
        if (repo_path / "Cargo.toml").exists():
            return "cargo"
        if (repo_path / "pom.xml").exists():
            return "maven"
        return None
    
    def _detect_ci_config(self, repo_path: Path) -> Optional[str]:
        """检测 CI 配置"""
        if (repo_path / ".github" / "workflows").exists():
            return "GitHub Actions"
        if (repo_path / ".travis.yml").exists():
            return "Travis CI"
        if (repo_path / ".circleci").exists():
            return "CircleCI"
        return None
    
    def _find_key_files(self, repo_path: Path) -> List[str]:
        """查找关键文件"""
        key_files = []
        important_files = [
            "README.md", "CONTRIBUTING.md", "LICENSE",
            "setup.py", "pyproject.toml", "requirements.txt",
            "package.json", "go.mod", "Cargo.toml",
            "Makefile", "Dockerfile"
        ]
        
        for f in important_files:
            if (repo_path / f).exists():
                key_files.append(f)
        
        return key_files
    
    def _extract_dependencies(self, repo_path: Path) -> List[str]:
        """提取依赖"""
        dependencies = []
        
        if (repo_path / "requirements.txt").exists():
            content = (repo_path / "requirements.txt").read_text()
            dependencies.extend([
                line.split("==")[0].split(">=")[0].strip()
                for line in content.split('\n')
                if line.strip() and not line.startswith('#')
            ])
        
        if (repo_path / "package.json").exists():
            try:
                content = json.loads((repo_path / "package.json").read_text())
                dependencies.extend(list(content.get("dependencies", {}).keys()))
                dependencies.extend(list(content.get("devDependencies", {}).keys()))
            except:
                pass
        
        return dependencies[:20]
    
    def _extract_keywords(self, issue: IssueContext) -> List[str]:
        """从 issue 中提取关键词"""
        text = issue.title + " " + issue.body
        
        patterns = [
            r'`(\w+)`',
            r'(\w+Error)',
            r'(\w+Exception)',
            r'function\s+(\w+)',
            r'method\s+(\w+)',
            r'([\w\-]+\.(?:py|js|ts|go|java|rs))',
        ]
        
        keywords = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend(matches)
        
        words = re.findall(r'\b[A-Z][a-z]{3,}\b', text)
        keywords.extend(words)
        
        return list(set(keywords))[:10]
    
    def _is_excluded_file(self, file_path: str) -> bool:
        """判断是否为排除文件"""
        excluded_patterns = [
            "node_modules", ".git", "__pycache__", "venv", ".venv",
            "dist", "build", ".eggs", "*.egg-info", "test_", "_test."
        ]
        return any(pattern in file_path for pattern in excluded_patterns)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("OpenCode CLI 集成模块测试")
    
    test_issue = IssueContext(
        title="Fix memory leak in image processing",
        number=123,
        body="There is a memory leak when processing large images...",
        url="https://github.com/example/repo/issues/123",
        repo_full_name="example/repo",
        labels=["bug", "good first issue"],
        issue_type="bug",
        difficulty="easy"
    )
    
    client = OpenCodeClient(Path("."))
    print(f"测试 issue: {test_issue.title}")