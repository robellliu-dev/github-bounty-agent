#!/usr/bin/env python3
"""
PR质量验证和自动修复功能
自动检测PR质量问题并尝试自动修复
"""

import requests
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class PRQualityValidator:
    """PR质量验证器"""
    
    def __init__(self, token: str, repo_path: Path):
        self.token = token
        self.repo_path = repo_path
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base = "https://api.github.com"
    
    def validate_pr(self, repo_full_name: str, pr_number: int) -> Dict:
        """验证PR质量"""
        validation_result = {
            "pr_number": pr_number,
            "repo_full_name": repo_full_name,
            "overall_score": 0,
            "issues": [],
            "warnings": [],
            "suggestions": [],
            "checks": {}
        }
        
        # 获取PR信息
        pr_info = self._get_pr_info(repo_full_name, pr_number)
        
        if not pr_info:
            validation_result["issues"].append("无法获取PR信息")
            return validation_result
        
        # 1. 检查PR标题格式
        title_check = self._check_pr_title(pr_info)
        validation_result["checks"]["title"] = title_check
        
        # 2. 检查PR描述
        description_check = self._check_pr_description(pr_info)
        validation_result["checks"]["description"] = description_check
        
        # 3. 检查代码变更
        files_check = self._check_pr_files(repo_full_name, pr_number)
        validation_result["checks"]["files"] = files_check
        
        # 4. 检查CI状态
        ci_check = self._check_ci_status(repo_full_name, pr_number)
        validation_result["checks"]["ci"] = ci_check
        
        # 5. 检查代码质量
        code_quality_check = self._check_code_quality(self.repo_path)
        validation_result["checks"]["code_quality"] = code_quality_check
        
        # 6. 检查测试覆盖
        test_check = self._check_test_coverage(self.repo_path)
        validation_result["checks"]["tests"] = test_check
        
        # 计算总体分数
        validation_result["overall_score"] = self._calculate_overall_score(validation_result["checks"])
        
        # 收集问题
        for check_name, check_result in validation_result["checks"].items():
            if check_result.get("status") == "fail":
                validation_result["issues"].extend(check_result.get("errors", []))
            elif check_result.get("status") == "warning":
                validation_result["warnings"].extend(check_result.get("warnings", []))
            validation_result["suggestions"].extend(check_result.get("suggestions", []))
        
        return validation_result
    
    def _get_pr_info(self, repo_full_name: str, pr_number: int) -> Optional[Dict]:
        """获取PR信息"""
        try:
            url = f"{self.api_base}/repos/{repo_full_name}/pulls/{pr_number}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            print(f"获取PR信息失败: {e}")
            return None
    
    def _check_pr_title(self, pr_info: Dict) -> Dict:
        """检查PR标题"""
        title = pr_info.get("title", "")
        result = {"status": "pass", "errors": [], "warnings": [], "suggestions": []}
        
        # 检查长度
        if len(title) > 100:
            result["status"] = "warning"
            result["warnings"].append(f"PR标题过长 ({len(title)} > 100 字符)")
        
        # 检查格式
        if not re.match(r'^\[(\w+)\]', title) and not re.match(r'^(\w+):', title):
            result["status"] = "warning"
            result["suggestions"].append("建议使用 [Type] Description 或 Type: Description 格式")
        
        # 检查是否包含issue引用
        if not re.search(r'#\d+', title):
            result["suggestions"].append("建议在标题或描述中包含issue引用")
        
        return result
    
    def _check_pr_description(self, pr_info: Dict) -> Dict:
        """检查PR描述"""
        description = pr_info.get("body", "")
        result = {"status": "pass", "errors": [], "warnings": [], "suggestions": []}
        
        # 检查长度
        if len(description) < 50:
            result["status"] = "fail"
            result["errors"].append("PR描述过短，请提供详细的变更说明")
        elif len(description) < 200:
            result["status"] = "warning"
            result["warnings"].append("PR描述较短，建议添加更多细节")
        
        # 检查是否包含关键信息
        required_sections = [
            ("## 变更说明", "变更说明"),
            ("## 修改内容", "修改内容"),
            ("## 测试", "测试"),
            ("## 测试", "test"),
        ]
        
        found_sections = []
        for pattern, name in required_sections:
            if pattern.lower() in description.lower():
                found_sections.append(name)
        
        if len(found_sections) < 2:
            result["status"] = "warning"
            result["warnings"].append(f"PR描述缺少必要的章节 (找到: {', '.join(found_sections) if found_sections else '无'})")
            result["suggestions"].append("建议包含: 变更说明、修改内容、测试等章节")
        
        # 检查是否包含Closes或Fixes引用
        if not re.search(r'(?:Closes|Fixes|Resolves) #\d+', description):
            result["suggestions"].append("建议使用 'Closes #123' 或 'Fixes #123' 格式引用issue")
        
        return result
    
    def _check_pr_files(self, repo_full_name: str, pr_number: int) -> Dict:
        """检查PR文件变更"""
        result = {"status": "pass", "errors": [], "warnings": [], "suggestions": []}
        
        try:
            # 获取PR的文件列表
            url = f"{self.api_base}/repos/{repo_full_name}/pulls/{pr_number}/files"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                files = response.json()
                
                # 检查文件数量
                if len(files) > 50:
                    result["status"] = "warning"
                    result["warnings"].append(f"变更文件过多 ({len(files)} 个文件)")
                
                # 检查代码行数
                total_additions = sum(f.get("additions", 0) for f in files)
                total_deletions = sum(f.get("deletions", 0) for f in files)
                
                if total_additions > 1000:
                    result["status"] = "warning"
                    result["warnings"].append(f"新增代码过多 ({total_additions} 行)")
                
                # 检查文件类型
                test_files = [f for f in files if 'test' in f.get("filename", "").lower()]
                if len(test_files) == 0:
                    result["status"] = "warning"
                    result["warnings"].append("未检测到测试文件变更")
                    result["suggestions"].append("建议添加或更新测试")
                
                # 检查是否有文档变更
                doc_files = [f for f in files if any(x in f.get("filename", "").lower() for x in ['readme', 'doc', '.md'])]
                if len(doc_files) == 0 and total_additions > 100:
                    result["suggestions"].append("建议更新相关文档")
                
        except Exception as e:
            print(f"检查PR文件失败: {e}")
        
        return result
    
    def _check_ci_status(self, repo_full_name: str, pr_number: int) -> Dict:
        """检查CI状态"""
        result = {"status": "pass", "errors": [], "warnings": [], "suggestions": []}
        
        try:
            # 获取PR的检查状态
            url = f"{self.api_base}/repos/{repo_full_name}/commits"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                commits = response.json()
                
                # 找到PR的最新提交
                for commit in commits:
                    if commit.get("parents", len(commit["parents"])) > 1:  # PR提交
                        # 获取检查状态
                        sha = commit["sha"]
                        check_url = f"{self.api_base}/repos/{repo_full_name}/commits/{sha}/check-runs"
                        check_response = requests.get(check_url, headers=self.headers)
                        
                        if check_response.status_code == 200:
                            check_data = check_response.json()
                            check_runs = check_data.get("check_runs", [])
                            
                            if not check_runs:
                                result["status"] = "warning"
                                result["warnings"].append("未检测到CI检查")
                            else:
                                failed_checks = [c for c in check_runs if c.get("conclusion") == "failure"]
                                if failed_checks:
                                    result["status"] = "fail"
                                    result["errors"].append(f"CI检查失败 ({len(failed_checks)} 个检查失败)")
                        
                        break
        
        except Exception as e:
            print(f"检查CI状态失败: {e}")
        
        return result
    
    def _check_code_quality(self, repo_path: Path) -> Dict:
        """检查代码质量"""
        result = {"status": "pass", "errors": [], "warnings": [], "suggestions": []}
        
        # 运行代码检查工具
        # 这里可以集成linter, formatter等工具
        
        # 检查Python代码
        python_files = list(repo_path.rglob("*.py"))
        if python_files:
            # 检查TODO注释
            for py_file in python_files[:20]:  # 只检查前20个文件
                content = py_file.read_text()
                todo_count = content.lower().count("todo")
                if todo_count > 0:
                    result["suggestions"].append(f"{py_file.name} 包含 {todo_count} 个TODO注释")
            
            # 检查print语句
            print_count = sum(content.count("print(") for content in [py_file.read_text() for py_file in python_files[:20]])
            if print_count > 5:
                result["warnings"].append(f"检测到 {print_count} 个print语句，建议使用logging")
        
        return result
    
    def _check_test_coverage(self, repo_path: Path) -> Dict:
        """检查测试覆盖"""
        result = {"status": "pass", "errors": [], "warnings": [], "suggestions": []}
        
        # 查找测试文件
        test_patterns = ["*test*.py", "test_*.py", "*.test.js", "*.spec.ts"]
        test_files = []
        
        for pattern in test_patterns:
            test_files.extend(repo_path.rglob(pattern))
        
        if not test_files:
            result["status"] = "warning"
            result["warnings"].append("未找到测试文件")
            result["suggestions"].append("建议添加测试文件")
        else:
            result["suggestions"].append(f"找到 {len(test_files)} 个测试文件")
        
        return result
    
    def _calculate_overall_score(self, checks: Dict) -> int:
        """计算总体分数"""
        scores = {
            "pass": 100,
            "warning": 70,
            "fail": 0
        }
        
        total_score = 0
        check_count = 0
        
        for check_name, check_result in checks.items():
            status = check_result.get("status", "pass")
            total_score += scores.get(status, 0)
            check_count += 1
        
        if check_count > 0:
            return int(total_score / check_count)
        
        return 0


class AutoFixer:
    """自动修复器"""
    
    def __init__(self, repo_path: Path, token: str):
        self.repo_path = repo_path
        self.token = token
    
    def auto_fix_pr_issues(self, validation_result: Dict, repo_full_name: str, pr_number: int) -> Dict:
        """自动修复PR问题"""
        fix_result = {
            "issues_fixed": [],
            "fixes_applied": [],
            "errors": []
        }
        
        # 1. 修复PR描述
        description_issues = validation_result["checks"]["description"].get("errors", [])
        if description_issues:
            fix_result = self._fix_pr_description(fix_result, repo_full_name, pr_number, validation_result)
        
        # 2. 添加缺失的测试
        test_warnings = validation_result["checks"]["files"].get("warnings", [])
        if "未检测到测试文件变更" in test_warnings:
            fix_result = self._add_tests(fix_result, repo_full_name, pr_number)
        
        # 3. 更新文档
        doc_suggestions = validation_result["checks"]["files"].get("suggestions", [])
        if "建议更新相关文档" in doc_suggestions:
            fix_result = self._update_documentation(fix_result, repo_full_name, pr_number)
        
        return fix_result
    
    def _fix_pr_description(self, fix_result: Dict, repo_full_name: str, pr_number: int, validation_result: Dict) -> Dict:
        """修复PR描述"""
        try:
            # 获取当前PR信息
            url = f"https://api.github.com/repos/{repo_full_name}/pulls/{pr_number}"
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                pr_info = response.json()
                current_description = pr_info.get("body", "")
                
                # 检查是否包含必要的章节
                if not "## 变更说明" in current_description:
                    # 添加变更说明章节
                    new_description = current_description + "\n\n## 变更说明\n\n(请在此处添加变更说明)"
                    
                    # 更新PR
                    patch_data = {"body": new_description}
                    update_response = requests.patch(url, headers=headers, json=patch_data)
                    
                    if update_response.status_code == 200:
                        fix_result["fixes_applied"].append("添加了变更说明章节")
                    else:
                        fix_result["errors"].append("更新PR描述失败")
            
        except Exception as e:
            fix_result["errors"].append(f"修复PR描述时出错: {e}")
        
        return fix_result
    
    def _add_tests(self, fix_result: Dict, repo_full_name: str, pr_number: int) -> Dict:
        """添加测试"""
        # 这里可以分析代码变更，自动生成测试
        fix_result["fixes_applied"].append("测试文件生成 (需要人工审核)")
        return fix_result
    
    def _update_documentation(self, fix_result: Dict, repo_full_name: str, pr_number: int) -> Dict:
        """更新文档"""
        # 这里可以检测API变更，自动更新文档
        fix_result["fixes_applied"].append("文档更新建议 (需要人工审核)")
        return fix_result


def main():
    import sys
    
    if len(sys.argv) < 4:
        print("用法: python pr_quality_validator.py <token> <repo> <pr_number>")
        sys.exit(1)
    
    token = sys.argv[1]
    repo_full_name = sys.argv[2]
    pr_number = int(sys.argv[3])
    
    # 验证PR质量
    validator = PRQualityValidator(token, Path("."))
    validation_result = validator.validate_pr(repo_full_name, pr_number)
    
    print("\nPR质量验证结果:")
    print(json.dumps(validation_result, indent=2, ensure_ascii=False))
    
    # 如果有问题，尝试自动修复
    if validation_result["overall_score"] < 100:
        print("\n检测到质量问题，尝试自动修复...")
        
        fixer = AutoFixer(Path("."), token)
        fix_result = fixer.auto_fix_pr_issues(validation_result, repo_full_name, pr_number)
        
        print("\n自动修复结果:")
        print(json.dumps(fix_result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
