#!/usr/bin/env python3
"""
CI/CD流水线检测和测试运行器
自动检测项目的CI/CD配置，运行测试并验证代码质量
"""

import subprocess
import json
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time


class CIPipelineDetector:
    """CI/CD流水线检测器"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def detect_ci_system(self) -> Dict:
        """检测CI系统"""
        ci_info = {
            "system": None,
            "config_files": [],
            "workflows": [],
            "test_commands": []
        }
        
        # 检测GitHub Actions
        github_actions_dir = self.repo_path / ".github" / "workflows"
        if github_actions_dir.exists():
            ci_info["system"] = "GitHub Actions"
            
            for workflow_file in github_actions_dir.glob("*.yml"):
                ci_info["config_files"].append(str(workflow_file))
                workflows = self._parse_github_actions(workflow_file)
                ci_info["workflows"].extend(workflows)
        
        # 检测Travis CI
        travis_file = self.repo_path / ".travis.yml"
        if travis_file.exists():
            ci_info["system"] = "Travis CI"
            ci_info["config_files"].append(str(travis_file))
            workflows = self._parse_travis_ci(travis_file)
            ci_info["workflows"].extend(workflows)
        
        # 检测CircleCI
        circle_file = self.repo_path / ".circleci" / "config.yml"
        if circle_file.exists():
            ci_info["system"] = "CircleCI"
            ci_info["config_files"].append(str(circle_file))
            workflows = self._parse_circle_ci(circle_file)
            ci_info["workflows"].extend(workflows)
        
        # 检测Jenkins
        jenkins_file = self.repo_path / "Jenkinsfile"
        if jenkins_file.exists():
            ci_info["system"] = "Jenkins"
            ci_info["config_files"].append(str(jenkins_file))
            workflows = self._parse_jenkins(jenkins_file)
            ci_info["workflows"].extend(workflows)
        
        # 提取测试命令
        ci_info["test_commands"] = self._extract_test_commands(ci_info["workflows"])
        
        return ci_info
    
    def _parse_github_actions(self, workflow_file: Path) -> List[Dict]:
        """解析GitHub Actions工作流"""
        workflows = []
        
        try:
            with open(workflow_file, 'r') as f:
                config = yaml.safe_load(f)
            
            for job_name, job_config in config.get("jobs", {}).items():
                workflow = {
                    "name": job_name,
                    "type": "GitHub Actions",
                    "steps": []
                }
                
                steps = job_config.get("steps", [])
                for step in steps:
                    step_name = step.get("name", "")
                    step_run = step.get("run", "")
                    
                    if step_run and any(kw in step_run.lower() for kw in ["test", "check", "lint", "build"]):
                        workflow["steps"].append({
                            "name": step_name,
                            "command": step_run,
                            "type": self._classify_step(step_run)
                        })
                
                if workflow["steps"]:
                    workflows.append(workflow)
                    
        except Exception as e:
            print(f"解析GitHub Actions失败: {e}")
        
        return workflows
    
    def _parse_travis_ci(self, config_file: Path) -> List[Dict]:
        """解析Travis CI配置"""
        workflows = []
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            script_commands = config.get("script", [])
            if isinstance(script_commands, str):
                script_commands = [script_commands]
            
            if script_commands:
                workflow = {
                    "name": "build",
                    "type": "Travis CI",
                    "steps": []
                }
                
                for cmd in script_commands:
                    workflow["steps"].append({
                        "name": "",
                        "command": cmd,
                        "type": self._classify_step(cmd)
                    })
                
                workflows.append(workflow)
                
        except Exception as e:
            print(f"解析Travis CI失败: {e}")
        
        return workflows
    
    def _parse_circle_ci(self, config_file: Path) -> List[Dict]:
        """解析CircleCI配置"""
        workflows = []
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            jobs = config.get("jobs", {})
            for job_name, job_config in jobs.items():
                steps = job_config.get("steps", [])
                
                workflow = {
                    "name": job_name,
                    "type": "CircleCI",
                    "steps": []
                }
                
                for step in steps:
                    if "run" in step:
                        run_config = step["run"]
                        command = run_config if isinstance(run_config, str) else run_config.get("command", "")
                        
                        workflow["steps"].append({
                            "name": run_config.get("name", "") if isinstance(run_config, dict) else "",
                            "command": command,
                            "type": self._classify_step(command)
                        })
                
                if workflow["steps"]:
                    workflows.append(workflow)
                    
        except Exception as e:
            print(f"解析CircleCI失败: {e}")
        
        return workflows
    
    def _parse_jenkins(self, config_file: Path) -> List[Dict]:
        """解析Jenkins配置"""
        workflows = []
        
        try:
            content = config_file.read_text()
            
            # 提取stage名称
            stages = re.findall(r'stage\s*[\'"]([^\'"]+)[\'"]', content)
            
            for stage in stages:
                workflow = {
                    "name": stage,
                    "type": "Jenkins",
                    "steps": []
                }
                
                workflows.append(workflow)
                
        except Exception as e:
            print(f"解析Jenkins失败: {e}")
        
        return workflows
    
    def _classify_step(self, command: str) -> str:
        """分类步骤类型"""
        command_lower = command.lower()
        
        if any(kw in command_lower for kw in ["pytest", "test", "unittest", "jest", "mocha"]):
            return "test"
        elif any(kw in command_lower for kw in ["lint", "flake8", "eslint", "pylint"]):
            return "lint"
        elif any(kw in command_lower for kw in ["build", "compile", "make"]):
            return "build"
        elif any(kw in command_lower for kw in ["check", "validate"]):
            return "check"
        else:
            return "other"
    
    def _extract_test_commands(self, workflows: List[Dict]) -> List[str]:
        """提取测试命令"""
        test_commands = []
        
        for workflow in workflows:
            for step in workflow["steps"]:
                if step["type"] == "test":
                    test_commands.append(step["command"])
        
        return test_commands


class TestRunner:
    """测试运行器"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.ci_detector = CIPipelineDetector(repo_path)
    
    def detect_language(self) -> str:
        """检测项目语言"""
        # 检查package.json
        if (self.repo_path / "package.json").exists():
            return "javascript"
        
        # 检查requirements.txt or setup.py or pyproject.toml
        if any(f.exists() for f in [
            self.repo_path / "requirements.txt",
            self.repo_path / "setup.py",
            self.repo_path / "pyproject.toml"
        ]):
            return "python"
        
        # 检查go.mod
        if (self.repo_path / "go.mod").exists():
            return "go"
        
        # 检查Cargo.toml
        if (self.repo_path / "Cargo.toml").exists():
            return "rust"
        
        # 检查pom.xml
        if (self.repo_path / "pom.xml").exists():
            return "java"
        
        return "unknown"
    
    def get_test_commands(self) -> List[str]:
        """获取测试命令"""
        ci_info = self.ci_detector.detect_ci_system()
        
        # 如果检测到CI配置，使用其中的测试命令
        if ci_info.get("test_commands"):
            return ci_info["test_commands"]
        
        # 根据语言返回默认测试命令
        language = self.detect_language()
        
        default_commands = {
            "python": ["python -m pytest", "python -m unittest"],
            "javascript": ["npm test", "yarn test", "jest"],
            "typescript": ["npm test", "yarn test", "jest", "npm run test"],
            "go": ["go test ./..."],
            "rust": ["cargo test"],
            "java": ["mvn test", "gradle test"],
        }
        
        return default_commands.get(language, [])
    
    def run_tests(self, timeout: int = 300) -> Dict:
        """运行测试"""
        test_commands = self.get_test_commands()
        
        results = {
            "language": self.detect_language(),
            "commands_run": [],
            "success": False,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "output": ""
        }
        
        for cmd in test_commands:
            print(f"\n运行测试命令: {cmd}")
            try:
                # 拆分命令
                cmd_parts = cmd.split()
                
                result = subprocess.run(
                    cmd_parts,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                results["commands_run"].append({
                    "command": cmd,
                    "return_code": result.returncode,
                    "success": result.returncode == 0
                })
                
                # 解析测试结果
                test_results = self._parse_test_output(result.stdout, result.stderr)
                
                results["passed"] += test_results.get("passed", 0)
                results["failed"] += test_results.get("failed", 0)
                results["skipped"] += test_results.get("skipped", 0)
                
                if result.returncode != 0:
                    results["errors"].append(f"命令 '{cmd}' 失败")
                    results["output"] += result.stderr + "\n"
                else:
                    results["output"] += result.stdout + "\n"
                    results["success"] = True
                    break  # 测试成功，不需要运行其他命令
                
            except subprocess.TimeoutExpired:
                results["errors"].append(f"命令 '{cmd}' 超时")
            except FileNotFoundError:
                results["errors"].append(f"命令 '{cmd}' 未找到")
            except Exception as e:
                results["errors"].append(f"命令 '{cmd}' 出错: {e}")
        
        return results
    
    def _parse_test_output(self, stdout: str, stderr: str) -> Dict:
        """解析测试输出"""
        test_results = {"passed": 0, "failed": 0, "skipped": 0}
        output = stdout + stderr
        
        # pytest
        pytest_match = re.search(r'(\d+) passed, (\d+) failed(?:, (\d+) skipped)?', output)
        if pytest_match:
            test_results["passed"] = int(pytest_match.group(1))
            test_results["failed"] = int(pytest_match.group(2))
            if pytest_match.group(3):
                test_results["skipped"] = int(pytest_match.group(3))
            return test_results
        
        # unittest
        unittest_match = re.search(r'Ran (\d+) tests?.*OK.*(\d+) failed', output, re.DOTALL)
        if not unittest_match:
            unittest_match = re.search(r'Ran (\d+) tests? in', output)
            if unittest_match:
                test_results["passed"] = int(unittest_match.group(1))
        
        # Jest
        jest_match = re.search(r'Tests:\s+(\d+) passed, (\d+) failed', output)
        if jest_match:
            test_results["passed"] = int(jest_match.group(1))
            test_results["failed"] = int(jest_match.group(2))
        
        # Go test
        go_match = re.search(r'PASS|FAIL', output)
        if go_match:
            if "PASS" in output and "FAIL" not in output:
                test_results["passed"] = 1
            else:
                test_results["failed"] = 1
        
        # Cargo test
        cargo_match = re.search(r'test result: ok\. (\d+) passed', output)
        if cargo_match:
            test_results["passed"] = int(cargo_match.group(1))
        
        return test_results
    
    def run_linters(self) -> Dict:
        """运行代码检查工具"""
        language = self.detect_language()
        
        linters = {
            "python": [
                {"command": ["flake8", "--max-line-length=100"], "name": "flake8"},
                {"command": ["pylint", "--errors-only"], "name": "pylint"},
                {"command": ["mypy", "--ignore-missing-imports"], "name": "mypy"},
            ],
            "javascript": [
                {"command": ["eslint", "."], "name": "eslint"},
            ],
            "typescript": [
                {"command": ["eslint", "."], "name": "eslint"},
                {"command": ["tsc", "--noEmit"], "name": "tsc"},
            ],
            "go": [
                {"command": ["gofmt", "-l", "."], "name": "gofmt"},
                {"command": ["go", "vet", "./..."], "name": "go vet"},
            ],
        }
        
        results = {
            "language": language,
            "linters_run": [],
            "success": True,
            "issues": []
        }
        
        for linter in linters.get(language, []):
            try:
                print(f"\n运行 {linter['name']}: {' '.join(linter['command'])}")
                
                result = subprocess.run(
                    linter["command"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                linter_result = {
                    "name": linter["name"],
                    "command": " ".join(linter["command"]),
                    "return_code": result.returncode,
                    "output": result.stdout + result.stderr,
                    "success": result.returncode == 0
                }
                
                results["linters_run"].append(linter_result)
                
                if result.returncode != 0:
                    results["success"] = False
                    results["issues"].append(f"{linter['name']} 检测到问题")
                
            except FileNotFoundError:
                print(f"{linter['name']} 未安装，跳过")
            except Exception as e:
                print(f"运行 {linter['name']} 失败: {e}")
        
        return results
    
    def check_build(self) -> Dict:
        """检查构建"""
        language = self.detect_language()
        
        build_commands = {
            "python": [
                ["python", "-m", "build"],
                ["pip", "install", "-e", "."],
            ],
            "javascript": [
                ["npm", "install"],
                ["npm", "run", "build"],
            ],
            "typescript": [
                ["npm", "install"],
                ["npm", "run", "build"],
                ["tsc"],
            ],
            "go": [
                ["go", "build", "./..."],
            ],
            "rust": [
                ["cargo", "build"],
            ],
            "java": [
                ["mvn", "compile"],
            ],
        }
        
        results = {
            "language": language,
            "commands_run": [],
            "success": True,
            "errors": []
        }
        
        for cmd in build_commands.get(language, []):
            try:
                print(f"\n运行构建命令: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                results["commands_run"].append({
                    "command": " ".join(cmd),
                    "return_code": result.returncode,
                    "success": result.returncode == 0
                })
                
                if result.returncode != 0:
                    results["success"] = False
                    results["errors"].append(f"构建命令 {' '.join(cmd)} 失败")
                    break  # 构建失败，停止其他命令
                
            except FileNotFoundError:
                print(f"命令 {' '.join(cmd)} 未找到，跳过")
            except Exception as e:
                print(f"运行构建命令 {' '.join(cmd)} 失败: {e}")
        
        return results
    
    def run_full_ci_pipeline(self) -> Dict:
        """运行完整的CI流水线"""
        print("\n" + "=" * 70)
        print("🔄 运行完整的CI流水线")
        print("=" * 70)
        
        pipeline_results = {
            "lint": None,
            "build": None,
            "test": None,
            "overall_success": False
        }
        
        # 1. 运行代码检查
        print("\n📋 步骤1: 运行代码检查...")
        pipeline_results["lint"] = self.run_linters()
        if pipeline_results["lint"]["success"]:
            print("✅ 代码检查通过")
        else:
            print("⚠️  代码检查发现问题，但继续...")
        
        # 2. 运行构建
        print("\n🔨 步骤2: 运行构建...")
        pipeline_results["build"] = self.check_build()
        if not pipeline_results["build"]["success"]:
            print("❌ 构建失败")
            return pipeline_results
        print("✅ 构建成功")
        
        # 3. 运行测试
        print("\n🧪 步骤3: 运行测试...")
        pipeline_results["test"] = self.run_tests()
        if pipeline_results["test"]["success"]:
            print("✅ 测试通过")
            pipeline_results["overall_success"] = True
        else:
            print("❌ 测试失败")
        
        return pipeline_results


def main():
    """测试CI/CD检测和测试运行"""
    import sys
    
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    # 检测CI/CD
    ci_detector = CIPipelineDetector(Path(repo_path))
    ci_info = ci_detector.detect_ci_system()
    
    print("\nCI/CD配置:")
    print(json.dumps(ci_info, indent=2, ensure_ascii=False))
    
    # 运行测试
    test_runner = TestRunner(Path(repo_path))
    test_results = test_runner.run_tests()
    
    print("\n测试结果:")
    print(json.dumps(test_results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
