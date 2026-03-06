#!/usr/bin/env python3
"""
代码修复AI模块
集成LLM进行代码分析和修复方案生成
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import subprocess


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
    
    def detect_language(self) -> str:
        """检测项目主要编程语言"""
        language_files = {
            "Python": ["*.py"],
            "JavaScript": ["*.js", "*.jsx"],
            "TypeScript": ["*.ts", "*.tsx"],
            "Go": ["*.go"],
            "Java": ["*.java"],
            "C++": ["*.cpp", "*.cc", "*.cxx"],
            "C": ["*.c"],
            "Rust": ["*.rs"],
            "Ruby": ["*.rb"],
            "PHP": ["*.php"],
        }
        
        file_counts = {}
        
        for lang, patterns in language_files.items():
            count = 0
            for pattern in patterns:
                result = subprocess.run(
                    ["find", str(self.repo_path), "-name", pattern],
                    capture_output=True,
                    text=True
                )
                count += len([f for f in result.stdout.split('\n') if f])
            
            if count > 0:
                file_counts[lang] = count
        
        # 返回文件最多的语言
        if file_counts:
            return max(file_counts.items(), key=lambda x: x[1])[0]
        
        return "Unknown"
    
    def find_test_files(self) -> List[Path]:
        """查找测试文件"""
        test_patterns = [
            "*test*.py",
            "test_*.py",
            "_test.py",
            "*test*.js",
            "*.test.js",
            "*.spec.js",
            "*test*.ts",
            "*.test.ts",
            "*.spec.ts",
            "*test*.go",
            "*_test.go",
        ]
        
        test_files = []
        
        for pattern in test_patterns:
            result = subprocess.run(
                ["find", str(self.repo_path), "-name", pattern],
                capture_output=True,
                text=True
            )
            
            for file_path in result.stdout.split('\n'):
                if file_path:
                    test_files.append(Path(file_path))
        
        return test_files
    
    def find_related_files(self, issue_keywords: List[str]) -> List[Path]:
        """根据issue关键词查找相关文件"""
        related_files = []
        
        # 搜索包含关键词的文件
        for keyword in issue_keywords:
            result = subprocess.run(
                ["grep", "-rl", keyword, str(self.repo_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                for file_path in result.stdout.split('\n'):
                    if file_path:
                        path = Path(file_path)
                        # 排除测试文件和文档
                        if not any(x in path.name.lower() for x in ['test', 'doc', 'readme', 'license']):
                            related_files.append(path)
        
        return list(set(related_files))
    
    def analyze_code_structure(self, file_path: Path) -> Dict:
        """分析代码结构"""
        if not file_path.exists():
            return {}
        
        content = file_path.read_text()
        
        structure = {
            "path": str(file_path.relative_to(self.repo_path)),
            "size": len(content),
            "lines": len(content.split('\n')),
            "imports": [],
            "functions": [],
            "classes": []
        }
        
        # 根据语言进行不同的分析
        if file_path.suffix == '.py':
            structure.update(self._analyze_python(content))
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            structure.update(self._analyze_javascript(content))
        elif file_path.suffix == '.go':
            structure.update(self._analyze_go(content))
        
        return structure
    
    def _analyze_python(self, content: str) -> Dict:
        """分析Python代码"""
        imports = re.findall(r'^(?:from|import)\s+(.+)', content, re.MULTILINE)
        functions = re.findall(r'def\s+(\w+)\s*\(', content)
        classes = re.findall(r'class\s+(\w+)\s*[:\(]', content)
        
        return {
            "imports": imports,
            "functions": functions,
            "classes": classes
        }
    
    def _analyze_javascript(self, content: str) -> Dict:
        """分析JavaScript/TypeScript代码"""
        imports = re.findall(r'^(?:import|export|require)\s+(.+)', content, re.MULTILINE)
        functions = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\()', content)
        classes = re.findall(r'class\s+(\w+)', content)
        
        return {
            "imports": imports,
            "functions": [f[0] or f[1] for f in functions if f],
            "classes": classes
        }
    
    def _analyze_go(self, content: str) -> Dict:
        """分析Go代码"""
        imports = re.findall(r'import\s+(?:\(\s*)?"([^"]+)"', content)
        functions = re.findall(r'func\s+(?:\(\s*\w+\s+\*\s*\w+\s*\)\s+)?(\w+)\s*\(', content)
        
        return {
            "imports": imports,
            "functions": functions,
            "classes": []
        }


class IssueAnalyzer:
    """Issue分析器"""
    
    def __init__(self):
        pass
    
    def extract_keywords(self, issue_text: str) -> List[str]:
        """从issue中提取关键词"""
        keywords = []
        
        # 常见的错误关键词
        error_patterns = [
            r'error[:\s]+([A-Z]\w+Error)',
            r'exception[:\s]+([A-Z]\w+Exception)',
            r'(\w+Error)',
            r'(\w+Exception)',
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, issue_text, re.IGNORECASE)
            keywords.extend(matches)
        
        # 函数/方法名称
        function_patterns = [
            r'`(\w+)\(',
            r'(\w+)\(\)',
            r'method\s+(\w+)',
            r'function\s+(\w+)',
        ]
        
        for pattern in function_patterns:
            matches = re.findall(pattern, issue_text, re.IGNORECASE)
            keywords.extend(matches)
        
        # 文件名
        file_patterns = [
            r'([\w\-/]+\.(?:py|js|ts|go|java|cpp|c|rs))',
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, issue_text, re.IGNORECASE)
            keywords.extend(matches)
        
        return list(set(keywords))
    
    def classify_issue_type(self, issue: Dict) -> str:
        """分类issue类型"""
        title = issue.get("title", "").lower()
        body = issue.get("body", "").lower()
        text = title + " " + body
        
        # Bug
        bug_keywords = ["bug", "error", "crash", "fail", "fix", "broken", "exception", "segfault"]
        if any(kw in text for kw in bug_keywords):
            return "bug"
        
        # Feature
        feature_keywords = ["feature", "add", "implement", "support", "new", "enhancement"]
        if any(kw in text for kw in feature_keywords):
            return "feature"
        
        # Documentation
        doc_keywords = ["doc", "documentation", "readme", "typo", "spelling"]
        if any(kw in text for kw in doc_keywords):
            return "docs"
        
        # Refactor
        refactor_keywords = ["refactor", "optimize", "performance", "clean", "improve"]
        if any(kw in text for kw in refactor_keywords):
            return "refactor"
        
        # Test
        test_keywords = ["test", "testing", "coverage", "spec"]
        if any(kw in text for kw in test_keywords):
            return "test"
        
        return "other"
    
    def estimate_difficulty(self, issue: Dict, repo_stats: Dict) -> str:
        """评估任务难度"""
        labels = [l.lower() for l in issue.get("labels", [])]
        
        # 根据标签判断
        if "good first issue" in labels:
            return "easy"
        elif "help wanted" in labels:
            return "medium"
        
        # 根据内容长度判断
        text_length = len(issue.get("body", ""))
        if text_length < 500:
            return "easy"
        elif text_length < 1500:
            return "medium"
        else:
            return "hard"
        
        return "medium"


class CodeFixGenerator:
    """代码修复方案生成器"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
    
    def generate_fix_plan(self, 
                          issue: Dict, 
                          code_analysis: Dict,
                          repo_info: Dict) -> Dict:
        """生成修复方案"""
        issue_analyzer = IssueAnalyzer()
        issue_type = issue_analyzer.classify_issue_type(issue)
        keywords = issue_analyzer.extract_keywords(issue.get("body", ""))
        
        fix_plan = {
            "issue_number": issue.get("number"),
            "issue_title": issue.get("title"),
            "issue_type": issue_type,
            "difficulty": issue_analyzer.estimate_difficulty(issue, repo_info),
            "keywords": keywords,
            "analysis": {},
            "solution": {},
            "implementation": {}
        }
        
        # 分析阶段
        fix_plan["analysis"] = {
            "description": self._analyze_issue(issue),
            "affected_files": self._identify_affected_files(keywords, code_analysis),
            "dependencies": self._identify_dependencies(code_analysis),
            "risks": self._identify_risks(issue_type, code_analysis)
        }
        
        # 解决方案阶段
        fix_plan["solution"] = {
            "approach": self._determine_approach(issue_type, issue),
            "changes": self._propose_changes(issue_type, issue, code_analysis),
            "testing_strategy": self._propose_tests(issue_type, code_analysis),
            "backwards_compatibility": self._check_backwards_compatibility(issue_type, code_analysis)
        }
        
        # 实现阶段
        fix_plan["implementation"] = {
            "steps": self._generate_implementation_steps(issue_type, code_analysis),
            "code_changes": self._generate_code_changes(issue_type, issue, code_analysis),
            "tests": self._generate_test_code(issue_type, code_analysis),
            "documentation": self._generate_documentation_updates(issue_type)
        }
        
        # 如果有OpenAI API key，使用LLM增强分析
        if self.openai_api_key:
            try:
                enhanced_plan = self._enhance_with_llm(fix_plan)
                fix_plan.update(enhanced_plan)
            except Exception as e:
                print(f"LLM增强失败，使用基础分析: {e}")
        
        return fix_plan
    
    def _analyze_issue(self, issue: Dict) -> str:
        """分析issue"""
        return f"分析 {issue.get('title')}: {issue.get('body', '')[:200]}..."
    
    def _identify_affected_files(self, keywords: List[str], code_analysis: Dict) -> List[str]:
        """识别受影响的文件"""
        return code_analysis.get("related_files", [])
    
    def _identify_dependencies(self, code_analysis: Dict) -> List[str]:
        """识别依赖关系"""
        dependencies = []
        for file_info in code_analysis.get("file_structures", []):
            dependencies.extend(file_info.get("imports", []))
        return list(set(dependencies))
    
    def _identify_risks(self, issue_type: str, code_analysis: Dict) -> List[str]:
        """识别风险"""
        risks = []
        
        if issue_type == "bug":
            risks.append("可能影响现有功能")
            risks.append("需要充分的测试覆盖")
        
        if issue_type == "feature":
            risks.append("可能需要更新文档")
            risks.append("可能影响API兼容性")
        
        if issue_type == "refactor":
            risks.append("可能引入新的bug")
            risks.append("需要完整的回归测试")
        
        return risks
    
    def _determine_approach(self, issue_type: str, issue: Dict) -> str:
        """确定修复方法"""
        if issue_type == "bug":
            return "修复bug，添加测试防止回归"
        elif issue_type == "feature":
            return "实现新功能，添加文档和测试"
        elif issue_type == "docs":
            return "更新相关文档"
        elif issue_type == "refactor":
            return "重构代码，保持功能不变"
        elif issue_type == "test":
            return "添加或改进测试"
        else:
            return "根据具体情况处理"
    
    def _propose_changes(self, issue_type: str, issue: Dict, code_analysis: Dict) -> List[str]:
        """提出变更建议"""
        changes = []
        
        if issue_type == "bug":
            changes.append("定位并修复bug")
            changes.append("添加单元测试")
            changes.append("验证修复有效")
        
        elif issue_type == "feature":
            changes.append("实现新功能")
            changes.append("编写API文档")
            changes.append("添加集成测试")
        
        elif issue_type == "docs":
            changes.append("更新README")
            changes.append("更新代码注释")
            changes.append("添加使用示例")
        
        return changes
    
    def _propose_tests(self, issue_type: str, code_analysis: Dict) -> str:
        """提出测试策略"""
        if issue_type == "bug":
            return "添加单元测试覆盖bug场景，添加回归测试防止未来出现同样问题"
        elif issue_type == "feature":
            return "添加单元测试和集成测试，确保新功能正常工作"
        elif issue_type == "refactor":
            return "运行完整的回归测试套件，确保重构没有破坏现有功能"
        else:
            return "根据具体情况添加相应测试"
    
    def _check_backwards_compatibility(self, issue_type: str, code_analysis: Dict) -> bool:
        """检查向后兼容性"""
        if issue_type in ["bug", "test"]:
            return True
        elif issue_type == "feature":
            return False
        elif issue_type == "refactor":
            return True
        else:
            return True
    
    def _generate_implementation_steps(self, issue_type: str, code_analysis: Dict) -> List[str]:
        """生成实施步骤"""
        steps = [
            "1. Fork并克隆仓库",
            "2. 创建新的feature分支",
            "3. 分析相关代码",
            "4. 实施代码变更",
            "5. 编写测试",
            "6. 运行测试并修复失败",
            "7. 更新文档（如果需要）",
            "8. 提交代码",
            "9. 推送到远程仓库",
            "10. 创建Pull Request"
        ]
        
        return steps
    
    def _generate_code_changes(self, issue_type: str, issue: Dict, code_analysis: Dict) -> List[Dict]:
        """生成代码变更"""
        return [
            {
                "file": "path/to/file.ext",
                "type": "modify",
                "description": "修改以修复问题"
            }
        ]
    
    def _generate_test_code(self, issue_type: str, code_analysis: Dict) -> List[str]:
        """生成测试代码"""
        return [
            "def test_fix_for_issue():",
            "    # 测试代码",
            "    pass"
        ]
    
    def _generate_documentation_updates(self, issue_type: str) -> List[str]:
        """生成文档更新"""
        updates = []
        
        if issue_type in ["feature", "refactor"]:
            updates.append("更新README.md")
            updates.append("更新API文档")
        
        return updates
    
    def _enhance_with_llm(self, fix_plan: Dict) -> Dict:
        """使用LLM增强分析"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            prompt = f"""
            分析以下GitHub issue并提供详细的修复方案:
            
            Issue标题: {fix_plan['issue_title']}
            Issue类型: {fix_plan['issue_type']}
            难度: {fix_plan['difficulty']}
            关键词: {', '.join(fix_plan['keywords'])}
            
            当前分析:
            {json.dumps(fix_plan, indent=2, ensure_ascii=False)}
            
            请提供:
            1. 更详细的根因分析
            2. 具体的代码修改建议
            3. 完整的测试方案
            4. 潜在的边缘情况和注意事项
            
            以JSON格式返回，包含以下字段:
            - root_cause: 根本原因分析
            - detailed_changes: 详细的代码变更建议
            - edge_cases: 需要考虑的边缘情况
            - additional_tests: 额外的测试建议
            """
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的软件开发者，擅长分析GitHub issue并提供高质量的修复方案。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            llm_response = response.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                enhanced = json.loads(llm_response)
                return enhanced
            except:
                # 如果无法解析JSON，返回原始文本
                return {
                    "llm_analysis": llm_response
                }
            
        except ImportError:
            print("未安装openai库，跳过LLM增强")
            return {}
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return {}


def main():
    """测试代码分析"""
    import sys
    
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    analyzer = CodeAnalyzer(Path(repo_path))
    language = analyzer.detect_language()
    print(f"检测到语言: {language}")
    
    test_files = analyzer.find_test_files()
    print(f"找到 {len(test_files)} 个测试文件")
    
    # 测试issue分析
    issue = {
        "title": "Fix memory leak in image processing",
        "body": "The image processing module has a memory leak when processing large images. Need to fix the resource cleanup in the process_image function.",
        "labels": ["bug", "good first issue"]
    }
    
    issue_analyzer = IssueAnalyzer()
    issue_type = issue_analyzer.classify_issue_type(issue)
    keywords = issue_analyzer.extract_keywords(issue.get("body", ""))
    
    print(f"\nIssue类型: {issue_type}")
    print(f"关键词: {keywords}")


if __name__ == "__main__":
    main()
