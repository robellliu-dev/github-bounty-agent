#!/usr/bin/env python3
"""
Bounty Hunter Assistant - 找到并分析GitHub赏金项目
帮助用户识别合适的赏金任务进行贡献
"""

import requests
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import sys

class BountyFinder:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base = "https://api.github.com"
    
    def search_bounty_issues(self, languages: Optional[List[str]] = None, limit: int = 20) -> List[Dict]:
        """搜索带有赏金标签的issue"""
        results = []
        
        # 常见赏金标签关键词
        bounty_keywords = [
            "bounty",
            "good first issue",
            "help wanted", 
            "hacktoberfest",
            "reward",
            "赏金"  # 中文标签
        ]
        
        for keyword in bounty_keywords:
            # 构建搜索查询
            query_parts = [f'label:"{keyword}"', 'is:issue', 'is:open']
            
            if languages:
                lang_query = " OR ".join([f'language:{lang}' for lang in languages])
                query_parts.append(f"({lang_query})")
            
            query = " ".join(query_parts)
            
            try:
                params = {
                    "q": query,
                    "per_page": 100,
                    "sort": "updated",
                    "order": "desc"
                }
                
                response = requests.get(
                    f"{self.api_base}/search/issues",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if "items" in data:
                    for item in data["items"]:
                        if "pull_request" not in item:  # 排除PR
                            issue_info = self._parse_issue(item)
                            if issue_info:
                                results.append(issue_info)
                                
            except Exception as e:
                print(f"搜索 '{keyword}' 时出错: {e}")
        
        # 去重
        unique_results = self._deduplicate_results(results)
        
        return unique_results[:limit]
    
    def _parse_issue(self, issue: Dict) -> Optional[Dict]:
        """解析issue数据"""
        repo_url = issue["repository_url"]
        parts = repo_url.split("/")
        owner = parts[-2]
        repo = parts[-1]
        
        # 提取可能的赏金金额
        bounty_amount = self._extract_bounty_amount(issue)
        
        # 评估任务难度
        difficulty = self._assess_difficulty(issue)
        
        return {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "repo_full_name": f"{owner}/{repo}",
            "repo_url": f"https://github.com/{owner}/{repo}",
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "labels": [label["name"] for label in issue.get("labels", [])],
            "bounty_amount": bounty_amount,
            "difficulty": difficulty,
            "comments": issue.get("comments", 0),
            "reactions": issue.get("reactions", {}).get("total_count", 0),
            "body": issue.get("body", "")[:500]  # 前言部分
        }
    
    def _extract_bounty_amount(self, issue: Dict) -> Optional[float]:
        """从标签或标题中提取赏金金额"""
        # 检查标签
        for label in issue.get("labels", []):
            label_name = label["name"].lower()
            if "$" in label_name:
                try:
                    amount_str = re.sub(r'[^\d.]', '', label_name)
                    return float(amount_str)
                except:
                    continue
        
        # 检查标题
        amount_pattern = r'\$([0-9,]+(?:\.[0-9]+)?)'
        matches = re.findall(amount_pattern, issue["title"])
        if matches:
            try:
                return float(matches[0].replace(",", ""))
            except:
                pass
        
        return None
    
    def _assess_difficulty(self, issue: Dict) -> str:
        """评估任务难度"""
        labels = [l.lower() for l in issue.get("labels", [])]
        
        if "good first issue" in labels:
            return "简单"
        elif "help wanted" in labels:
            return "中等"
        else:
            return "需评估"
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []
        for r in results:
            key = f"{r['repo_full_name']}#{r['number']}"
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
    
    def get_repo_stats(self, repo_full_name: str) -> Dict:
        """获取仓库统计信息"""
        try:
            response = requests.get(
                f"{self.api_base}/repos/{repo_full_name}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "language": data.get("language", "Unknown"),
                "description": data.get("description", ""),
                "updated_at": data.get("updated_at", "")
            }
        except Exception as e:
            print(f"获取仓库信息失败: {e}")
            return {}
    
    def analyze_issue(self, repo_full_name: str, issue_number: int) -> Dict:
        """深入分析issue详情"""
        try:
            response = requests.get(
                f"{self.api_base}/repos/{repo_full_name}/issues/{issue_number}",
                headers=self.headers
            )
            response.raise_for_status()
            issue = response.json()
            
            # 获取仓库统计
            repo_stats = self.get_repo_stats(repo_full_name)
            
            # 分析可行性
            feasibility = self._analyze_feasibility(issue, repo_stats)
            
            return {
                "issue": issue,
                "repo_stats": repo_stats,
                "feasibility": feasibility
            }
            
        except Exception as e:
            print(f"分析issue失败: {e}")
            return {}
    
    def _analyze_feasibility(self, issue: Dict, repo_stats: Dict) -> Dict:
        """分析任务可行性"""
        feasibility_score = 0
        reasons = []
        
        # 仓库活跃度
        if repo_stats.get("stars", 0) > 100:
            feasibility_score += 2
            reasons.append("仓库活跃度较高")
        elif repo_stats.get("stars", 0) > 20:
            feasibility_score += 1
            reasons.append("仓库有一定关注度")
        
        # 标签分析
        labels = [l.lower() for l in issue.get("labels", [])]
        if "good first issue" in labels:
            feasibility_score += 3
            reasons.append("适合新手的任务")
        elif "help wanted" in labels:
            feasibility_score += 2
            reasons.append("需要帮助的任务")
        
        # 讨论程度
        comments = issue.get("comments", 0)
        if comments < 5:
            feasibility_score += 1
            reasons.append("讨论较少，竞争可能较小")
        elif comments > 20:
            feasibility_score -= 1
            reasons.append("讨论较多，可能有竞争")
        
        # 代码语言
        lang = repo_stats.get("language", "")
        common_langs = ["Python", "JavaScript", "TypeScript", "Go", "Java"]
        if lang in common_langs:
            feasibility_score += 1
            reasons.append(f"使用常见语言: {lang}")
        
        # 生成评分
        if feasibility_score >= 5:
            grade = "⭐⭐⭐ 高"
        elif feasibility_score >= 3:
            grade = "⭐⭐ 中"
        else:
            grade = "⭐ 低"
        
        return {
            "score": feasibility_score,
            "grade": grade,
            "reasons": reasons
        }


def display_bounty_list(issues: List[Dict]):
    """显示赏金任务列表"""
    if not issues:
        print("\n❌ 没有找到符合条件的赏金任务")
        return
    
    print(f"\n✅ 找到 {len(issues)} 个潜在的赏金任务:\n")
    print("=" * 110)
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['title']}")
        print(f"   📦 仓库: {issue['repo_full_name']}")
        print(f"   🔗 链接: {issue['url']}")
        print(f"   🏷️  标签: {', '.join(issue['labels'])}")
        
        if issue['bounty_amount']:
            print(f"   💰 预估赏金: ${issue['bounty_amount']}")
        
        print(f"   📊 难度: {issue['difficulty']}")
        print(f"   📅 创建: {issue['created_at'][:10]} | 💬 评论: {issue['comments']}")
        
        if issue['body']:
            print(f"   📝 简介: {issue['body'][:100]}...")
        
        print("-" * 110)


def main():
    print("=" * 50)
    print("GitHub 赏金任务查找助手")
    print("=" * 50)
    
    # 获取token
    token = input("\n请输入GitHub个人访问令牌 (Personal Access Token): ").strip()
    if not token:
        print("❌ Token不能为空")
        return
    
    finder = BountyFinder(token)
    
    # 选择编程语言
    print("\n请选择要筛选的编程语言 (用逗号分隔, 直接回车表示不限制):")
    print("  常见: Python, JavaScript, TypeScript, Go, Java, Rust, C++")
    lang_input = input("语言: ").strip()
    languages = [l.strip() for l in lang_input.split(",")] if lang_input else None
    
    # 搜索
    print("\n🔍 正在搜索赏金任务...")
    issues = finder.search_bounty_issues(languages=languages, limit=20)
    
    # 显示结果
    display_bounty_list(issues)
    
    # 选择要深入分析的任务
    if issues:
        print("\n" + "=" * 50)
        choice = input("\n是否要深入分析某个任务? (输入编号, 0=退出): ").strip()
        
        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(issues):
            idx = int(choice) - 1
            selected = issues[idx]
            
            print(f"\n🔍 正在分析任务: {selected['title']}")
            analysis = finder.analyze_issue(selected['repo_full_name'], selected['number'])
            
            if analysis:
                print(f"\n📊 仓库统计:")
                repo_stats = analysis['repo_stats']
                print(f"   ⭐ Stars: {repo_stats.get('stars', 0)}")
                print(f"   🍴 Forks: {repo_stats.get('forks', 0)}")
                print(f"   🐛 Issues: {repo_stats.get('open_issues', 0)}")
                print(f"   💻 语言: {repo_stats.get('language', 'Unknown')}")
                print(f"   📝 描述: {repo_stats.get('description', 'N/A')[:80]}...")
                
                print(f"\n✅ 可行性分析:")
                feasible = analysis['feasibility']
                print(f"   评级: {feasible['grade']}")
                print(f"   分数: {feasible['score']}")
                print(f"   理由:")
                for reason in feasible['reasons']:
                    print(f"     • {reason}")
        
        # 保存结果
        save = input("\n💾 保存搜索结果到文件? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"bounty_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(issues, f, indent=2, ensure_ascii=False)
            print(f"✅ 结果已保存到: {filename}")
    
    print("\n👋 谢谢使用!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
