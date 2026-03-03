import requests
import json
from datetime import datetime, timedelta
import sys

GITHUB_API_BASE = "https://api.github.com"

def search_bounty_issues(token, languages=None, min_bounty=100, limit=10):
    """
    Search GitHub for bounty issues
    
    Args:
        token: GitHub personal access token
        languages: List of programming languages to filter by
        min_bounty: Minimum bounty amount in USD
        limit: Number of results to return
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Search for issues with bounty-related labels
    bounty_keywords = ["bounty", "bounty-hunter", "bounty-program", "$"]
    
    results = []
    for keyword in bounty_keywords:
        query = f'label:"{keyword}" is:issue is:open'
        
        if languages:
            lang_query = " OR ".join([f'language:{lang}' for lang in languages])
            query += f" {lang_query}"
        
        params = {
            "q": query,
            "per_page": 50,
            "sort": "created",
            "order": "desc"
        }
        
        try:
            response = requests.get(f"{GITHUB_API_BASE}/search/issues", 
                                  headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "items" in data:
                for item in data["items"]:
                    issue_data = parse_issue(item)
                    if issue_data:
                        results.append(issue_data)
                        
        except Exception as e:
            print(f"Error searching with keyword '{keyword}': {e}")
    
    # Remove duplicates
    seen = set()
    unique_results = []
    for r in results:
        key = f"{r['repo_full_name']}#{r['number']}"
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    
    return unique_results[:limit]

def parse_issue(issue):
    """Parse issue data to extract relevant information"""
    if "pull_request" in issue:
        return None  # Skip PRs
    
    repo_name = issue["repository_url"].split("/")[-1]
    owner = issue["repository_url"].split("/")[-2]
    
    # Try to extract bounty amount from labels or title
    bounty_amount = extract_bounty_amount(issue)
    
    return {
        "title": issue["title"],
        "url": issue["html_url"],
        "number": issue["number"],
        "repo_full_name": f"{owner}/{repo_name}",
        "repo_url": f"https://github.com/{owner}/{repo_name}",
        "created_at": issue["created_at"],
        "updated_at": issue["updated_at"],
        "labels": [label["name"] for label in issue.get("labels", [])],
        "bounty_amount": bounty_amount,
        "comments": issue.get("comments", 0),
        "reactions": issue.get("reactions", {}).get("total_count", 0)
    }

def extract_bounty_amount(issue):
    """Try to extract bounty amount from issue data"""
    # Check labels for amounts
    for label in issue.get("labels", []):
        label_name = label["name"].lower()
        if "$" in label_name:
            try:
                amount_str = label_name.replace("$", "").replace("usd", "").strip()
                return float(amount_str)
            except:
                continue
    
    # Check title
    import re
    amount_pattern = r'\$(\d+(?:,\d+)*(?:\.\d+)?)'
    matches = re.findall(amount_pattern, issue["title"])
    if matches:
        try:
            return float(matches[0].replace(",", ""))
        except:
            pass
    
    return None

def display_results(results):
    """Display search results"""
    if not results:
        print("\nNo bounty issues found.")
        return
    
    print(f"\nFound {len(results)} bounty issues:\n")
    print("=" * 100)
    
    for i, issue in enumerate(results, 1):
        print(f"\n{i}. {issue['title']}")
        print(f"   Repository: {issue['repo_full_name']}")
        print(f"   URL: {issue['url']}")
        print(f"   Labels: {', '.join(issue['labels'])}")
        
        if issue['bounty_amount']:
            print(f"   💰 Estimated Bounty: ${issue['bounty_amount']}")
        
        print(f"   Created: {issue['created_at'][:10]}")
        print(f"   Comments: {issue['comments']} | Reactions: {issue['reactions']}")
        print("-" * 100)

def get_popular_bounty_programs(token):
    """Get known bounty programs"""
    popular_programs = [
        "gitcoin-co/grants-stack",
        "Algorand基金会/grants",
        "ethereum/ethereum-org-website",
    ]
    
    return popular_programs

def main():
    print("GitHub Bounty Issue Finder")
    print("=" * 50)
    
    # Get GitHub token
    token = input("Enter your GitHub personal access token: ").strip()
    if not token:
        print("Error: Token is required")
        return
    
    # Optional: Filter by programming languages
    languages_input = input("Filter by languages (comma-separated, e.g., python,javascript,typescript): ").strip()
    languages = [l.strip() for l in languages_input.split(",")] if languages_input else None
    
    # Search
    print("\nSearching for bounty issues...")
    results = search_bounty_issues(token, languages=languages)
    
    # Display results
    display_results(results)
    
    # Option to save results
    if results:
        save = input("\nSave results to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"bounty_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()
