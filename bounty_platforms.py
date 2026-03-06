#!/usr/bin/env python3
"""
主流赏金平台集成模块
支持Gitcoin, Algorand Grants, Ethereum Foundation等主流平台
"""

import requests
import json
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class BountyPlatform:
    """赏金平台基类"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base = "https://api.github.com"


class GitcoinPlatform(BountyPlatform):
    """Gitcoin平台集成"""
    
    def search_bounties(self, limit: int = 20) -> List[Dict]:
        """搜索Gitcoin赏金任务"""
        bounties = []
        
        # Gitcoin通常使用特定标签和仓库
        gitcoin_queries = [
            'label:"gitcoin" is:issue is:open',
            'label:"gitcoin-grants" is:issue is:open',
            'label:"grant" is:issue is:open',
        ]
        
        for query in gitcoin_queries:
            try:
                response = requests.get(
                    f"{self.api_base}/search/issues",
                    headers=self.headers,
                    params={
                        "q": query,
                        "per_page": limit,
                        "sort": "created",
                        "order": "desc"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        if "pull_request" not in item:
                            bounty = self._parse_bounty(item, "Gitcoin")
                            if bounty:
                                bounties.append(bounty)
                                
            except Exception as e:
                print(f"Gitcoin搜索错误: {e}")
        
        return bounties[:limit]
    
    def _parse_bounty(self, issue: Dict, platform: str) -> Optional[Dict]:
        """解析赏金信息"""
        repo_url = issue["repository_url"]
        parts = repo_url.split("/")
        owner = parts[-2]
        repo = parts[-1]
        
        # 尝试提取赏金金额
        bounty_amount = self._extract_bounty_amount(issue)
        
        return {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "repo_full_name": f"{owner}/{repo}",
            "platform": platform,
            "labels": [label["name"] for label in issue.get("labels", [])],
            "bounty_amount": bounty_amount,
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue.get("comments", 0),
            "reactions": issue.get("reactions", {}).get("total_count", 0)
        }
    
    def _extract_bounty_amount(self, issue: Dict) -> Optional[float]:
        """提取赏金金额"""
        # 检查标签
        for label in issue.get("labels", []):
            label_name = label["name"].lower()
            if "$" in label_name or "usd" in label_name:
                try:
                    # 提取数字
                    amount = re.sub(r'[^\d.]', '', label_name)
                    if amount:
                        return float(amount)
                except:
                    continue
        
        # 检查标题和正文
        text = issue.get("title", "") + " " + issue.get("body", "")
        amount_pattern = r'\$([0-9,]+(?:\.[0-9]+)?)'
        matches = re.findall(amount_pattern, text)
        if matches:
            try:
                return float(matches[0].replace(",", ""))
            except:
                pass
        
        return None


class AlgorandPlatform(BountyPlatform):
    """Algorand Foundation赏金平台"""
    
    def search_bounties(self, limit: int = 20) -> List[Dict]:
        """搜索Algorand赏金任务"""
        bounties = []
        
        # Algorand相关的仓库
        algorand_repos = [
            "algorand/go-algorand",
            "algorand/algorand-sdk-go",
            "algorand/algorand-sdk-js",
            "algorand/algorand-sdk-python",
            "algorand/py-algorand-sdk",
        ]
        
        for repo in algorand_repos:
            try:
                # 搜索带有赏金相关标签的issue
                response = requests.get(
                    f"{self.api_base}/repos/{repo}/issues",
                    headers=self.headers,
                    params={
                        "state": "open",
                        "labels": "bounty,grant,reward,good first issue,help wanted",
                        "per_page": 10,
                        "sort": "created",
                        "direction": "desc"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        if "pull_request" not in item:
                            bounty = self._parse_algorand_bounty(item, repo)
                            if bounty:
                                bounties.append(bounty)
                                
            except Exception as e:
                print(f"Algorand搜索错误 ({repo}): {e}")
        
        return bounties[:limit]
    
    def _parse_algorand_bounty(self, issue: Dict, repo_full_name: str) -> Optional[Dict]:
        """解析Algorand赏金信息"""
        bounty_amount = self._extract_bounty_amount(issue)
        
        return {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "repo_full_name": repo_full_name,
            "platform": "Algorand Foundation",
            "labels": [label["name"] for label in issue.get("labels", [])],
            "bounty_amount": bounty_amount,
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue.get("comments", 0),
            "reactions": issue.get("reactions", {}).get("total_count", 0)
        }
    
    def _extract_bounty_amount(self, issue: Dict) -> Optional[float]:
        """提取赏金金额"""
        text = issue.get("title", "") + " " + issue.get("body", "")
        
        # Algorand赏金通常以ALGO计价
        algo_pattern = r'(\d+(?:,\d+)*(?:\.\d+)?)\s*ALGO'
        matches = re.findall(algo_pattern, text)
        
        if matches:
            try:
                return float(matches[0].replace(",", ""))
            except:
                pass
        
        # USD赏金
        usd_pattern = r'\$([0-9,]+(?:\.[0-9]+)?)'
        usd_matches = re.findall(usd_pattern, text)
        if usd_matches:
            try:
                return float(usd_matches[0].replace(",", ""))
            except:
                pass
        
        return None


class EthereumPlatform(BountyPlatform):
    """Ethereum Foundation赏金平台"""
    
    def search_bounties(self, limit: int = 20) -> List[Dict]:
        """搜索Ethereum赏金任务"""
        bounties = []
        
        # Ethereum相关的仓库
        ethereum_repos = [
            "ethereum/execution-specs",
            "ethereum/consensus-specs",
            "ethereum/ethereum-org-website",
            "ethereum/solidity",
            "ethereum/web3.py",
            "ethereum/py-evm",
        ]
        
        for repo in ethereum_repos:
            try:
                response = requests.get(
                    f"{self.api_base}/repos/{repo}/issues",
                    headers=self.headers,
                    params={
                        "state": "open",
                        "labels": "good first issue,help wanted,bounty",
                        "per_page": 10,
                        "sort": "created",
                        "direction": "desc"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        if "pull_request" not in item:
                            bounty = self._parse_ethereum_bounty(item, repo)
                            if bounty:
                                bounties.append(bounty)
                                
            except Exception as e:
                print(f"Ethereum搜索错误 ({repo}): {e}")
        
        return bounties[:limit]
    
    def _parse_ethereum_bounty(self, issue: Dict, repo_full_name: str) -> Optional[Dict]:
        """解析Ethereum赏金信息"""
        bounty_amount = self._extract_bounty_amount(issue)
        
        return {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "repo_full_name": repo_full_name,
            "platform": "Ethereum Foundation",
            "labels": [label["name"] for label in issue.get("labels", [])],
            "bounty_amount": bounty_amount,
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue.get("comments", 0),
            "reactions": issue.get("reactions", {}).get("total_count", 0)
        }
    
    def _extract_bounty_amount(self, issue: Dict) -> Optional[float]:
        """提取赏金金额"""
        text = issue.get("title", "") + " " + issue.get("body", "")
        
        # ETH赏金
        eth_pattern = r'(\d+(?:\.\d+)?)\s*ETH'
        matches = re.findall(eth_pattern, text)
        
        if matches:
            try:
                # 简单假设1 ETH = $2000
                return float(matches[0]) * 2000
            except:
                pass
        
        # USD赏金
        usd_pattern = r'\$([0-9,]+(?:\.[0-9]+)?)'
        usd_matches = re.findall(usd_pattern, text)
        if usd_matches:
            try:
                return float(usd_matches[0].replace(",", ""))
            except:
                pass
        
        return None


class SolanaPlatform(BountyPlatform):
    """Solana Foundation赏金平台"""
    
    def search_bounties(self, limit: int = 20) -> List[Dict]:
        """搜索Solana赏金任务"""
        bounties = []
        
        # Solana相关的仓库
        solana_repos = [
            "solana-labs/solana",
            "solana-labs/solana-program-library",
            "solana-labs/solana-web3.js",
            "solana-labs/solana-py",
        ]
        
        for repo in solana_repos:
            try:
                response = requests.get(
                    f"{self.api_base}/repos/{repo}/issues",
                    headers=self.headers,
                    params={
                        "state": "open",
                        "labels": "good first issue,help wanted,bounty,hackathon",
                        "per_page": 10,
                        "sort": "created",
                        "direction": "desc"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        if "pull_request" not in item:
                            bounty = self._parse_solana_bounty(item, repo)
                            if bounty:
                                bounties.append(bounty)
                                
            except Exception as e:
                print(f"Solana搜索错误 ({repo}): {e}")
        
        return bounties[:limit]
    
    def _parse_solana_bounty(self, issue: Dict, repo_full_name: str) -> Optional[Dict]:
        """解析Solana赏金信息"""
        bounty_amount = self._extract_bounty_amount(issue)
        
        return {
            "title": issue["title"],
            "number": issue["number"],
            "url": issue["html_url"],
            "repo_full_name": repo_full_name,
            "platform": "Solana Foundation",
            "labels": [label["name"] for label in issue.get("labels", [])],
            "bounty_amount": bounty_amount,
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "comments": issue.get("comments", 0),
            "reactions": issue.get("reactions", {}).get("total_count", 0)
        }
    
    def _extract_bounty_amount(self, issue: Dict) -> Optional[float]:
        """提取赏金金额"""
        text = issue.get("title", "") + " " + issue.get("body", "")
        
        # SOL赏金
        sol_pattern = r'(\d+(?:,\d+)*(?:\.\d+)?)\s*SOL'
        matches = re.findall(sol_pattern, text)
        
        if matches:
            try:
                # 简单假设1 SOL = $100
                return float(matches[0].replace(",", "")) * 100
            except:
                pass
        
        # USD赏金
        usd_pattern = r'\$([0-9,]+(?:\.[0-9]+)?)'
        usd_matches = re.findall(usd_pattern, text)
        if usd_matches:
            try:
                return float(usd_matches[0].replace(",", ""))
            except:
                pass
        
        return None


class BountyPlatformManager:
    """赏金平台管理器"""
    
    def __init__(self, token: str):
        self.token = token
        self.platforms = [
            GitcoinPlatform(token),
            AlgorandPlatform(token),
            EthereumPlatform(token),
            SolanaPlatform(token),
        ]
    
    def search_all_platforms(self, limit_per_platform: int = 10) -> List[Dict]:
        """搜索所有平台的赏金任务"""
        all_bounties = []
        
        for platform in self.platforms:
            print(f"\n搜索 {platform.__class__.__name__}...")
            try:
                bounties = platform.search_bounties(limit=limit_per_platform)
                all_bounties.extend(bounties)
                print(f"   找到 {len(bounties)} 个任务")
            except Exception as e:
                print(f"   错误: {e}")
        
        # 去重
        unique_bounties = self._deduplicate_bounties(all_bounties)
        
        return unique_bounties
    
    def _deduplicate_bounties(self, bounties: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []
        
        for bounty in bounties:
            key = f"{bounty['repo_full_name']}#{bounty['number']}"
            if key not in seen:
                seen.add(key)
                unique.append(bounty)
        
        return unique
    
    def filter_by_criteria(self, bounties: List[Dict], **criteria) -> List[Dict]:
        """根据条件筛选赏金任务"""
        filtered = bounties
        
        # 最小赏金金额
        if 'min_bounty' in criteria:
            filtered = [b for b in filtered if b.get('bounty_amount', 0) >= criteria['min_bounty']]
        
        # 编程语言
        if 'languages' in criteria:
            languages = [lang.lower() for lang in criteria['languages']]
            filtered = [b for b in filtered if any(lang in b.get('labels', []) for lang in languages)]
        
        # 最小评论数
        if 'min_comments' in criteria:
            filtered = [b for b in filtered if b.get('comments', 0) >= criteria['min_comments']]
        
        # 日期范围
        if 'days_old' in criteria:
            cutoff_date = datetime.now() - timedelta(days=criteria['days_old'])
            filtered = [b for b in filtered if datetime.fromisoformat(b['created_at'].replace('Z', '+00:00')) >= cutoff_date]
        
        return filtered
    
    def rank_bounties(self, bounties: List[Dict]) -> List[Dict]:
        """对赏金任务进行排序"""
        def score(bounty):
            score = 0
            
            # 赏金金额
            if bounty.get('bounty_amount'):
                score += min(bounty['bounty_amount'] / 100, 10)
            
            # 评论数（活跃度）
            score += min(bounty.get('comments', 0), 5)
            
            # 反应数
            score += min(bounty.get('reactions', 0), 3)
            
            # 标签优先级
            labels = bounty.get('labels', [])
            if 'good first issue' in labels:
                score += 5
            if 'help wanted' in labels:
                score += 3
            
            # 平台优先级
            platform = bounty.get('platform', '')
            if 'Gitcoin' in platform:
                score += 2
            if 'Ethereum' in platform:
                score += 2
            
            return score
        
        return sorted(bounties, key=score, reverse=True)


def main():
    import sys
    
    print("=" * 70)
    print("🌐 主流赏金平台集成测试")
    print("=" * 70)
    
    # 获取token
    token = sys.argv[1] if len(sys.argv) > 1 else input("请输入GitHub Token: ").strip()
    
    if not token:
        print("❌ Token不能为空")
        return
    
    # 创建管理器
    manager = BountyPlatformManager(token)
    
    # 搜索所有平台
    print("\n🔍 搜索所有平台的赏金任务...")
    bounties = manager.search_all_platforms(limit_per_platform=5)
    
    print(f"\n✅ 共找到 {len(bounties)} 个赏金任务")
    
    # 排序
    ranked_bounties = manager.rank_bounties(bounties)
    
    # 显示前10个
    print("\n📊 排名前10的赏金任务:")
    print("=" * 100)
    
    for i, bounty in enumerate(ranked_bounties[:10], 1):
        print(f"\n{i}. {bounty['title']}")
        print(f"   平台: {bounty['platform']}")
        print(f"   仓库: {bounty['repo_full_name']}")
        print(f"   链接: {bounty['url']}")
        print(f"   标签: {', '.join(bounty['labels'])}")
        
        if bounty['bounty_amount']:
            print(f"   💰 赏金: ${bounty['bounty_amount']}")
        
        print(f"   📅 创建: {bounty['created_at'][:10]}")
        print(f"   💬 评论: {bounty['comments']}")
        print("-" * 100)


if __name__ == "__main__":
    main()
