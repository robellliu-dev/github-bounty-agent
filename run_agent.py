#!/usr/bin/env python3
"""
主入口脚本 - 运行 Bounty Agent
支持本地运行和 CI/CD 环境
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def check_environment():
    """检查环境"""
    print("=" * 70)
    print("环境检查")
    print("=" * 70)
    
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")
    
    if not token:
        print("❌ 错误: 未设置 GITHUB_TOKEN 环境变量")
        return False, None, None
    
    print(f"✅ GITHUB_TOKEN 已设置 ({len(token)} 字符)")
    print(f"✅ GITHUB_USERNAME: {username or '未设置'}")
    
    opencode_path = subprocess.run(
        ["which", "opencode"],
        capture_output=True,
        text=True
    )
    
    if opencode_path.returncode == 0:
        print(f"✅ OpenCode CLI: {opencode_path.stdout.strip()}")
    else:
        print("⚠️  OpenCode CLI 未安装，将使用 fallback 模式")
    
    return True, token, username


def setup_workspace(work_dir: Path):
    """设置工作目录"""
    work_dir.mkdir(parents=True, exist_ok=True)
    
    (work_dir / "results").mkdir(exist_ok=True)
    (work_dir / "logs").mkdir(exist_ok=True)
    
    print(f"✅ 工作目录: {work_dir.absolute()}")


def run_agent(token: str, username: str, work_dir: Path, target_pr_count: int = 10):
    """运行 Agent"""
    print("\n" + "=" * 70)
    print("启动 Bounty Agent")
    print("=" * 70)
    
    from opencode_bounty_agent import EnhancedBountyAgent
    
    agent = EnhancedBountyAgent(
        token=token,
        username=username or "robellliu-dev",
        work_dir=work_dir
    )
    
    results = agent.run_batch(
        target_pr_count=target_pr_count,
        max_parallel=3
    )
    
    return results


def main():
    print("\n" + "=" * 70)
    print("🤖 GitHub Bounty Agent - 自动化赏金任务处理")
    print("=" * 70)
    print(f"启动时间: {datetime.now().isoformat()}")
    print()
    
    ok, token, username = check_environment()
    if not ok:
        sys.exit(1)
    
    work_dir = Path(os.getenv("WORK_DIR", "./workspace"))
    setup_workspace(work_dir)
    
    target_pr_count = int(os.getenv("TARGET_PR_COUNT", "10"))
    
    try:
        results = run_agent(token or "", username or "robellliu-dev", work_dir, target_pr_count)
        
        print("\n" + "=" * 70)
        print("📊 执行结果")
        print("=" * 70)
        print(f"目标 PR 数: {results.get('target_pr_count', 0)}")
        print(f"找到任务数: {results.get('tasks_found', 0)}")
        print(f"处理任务数: {results.get('tasks_processed', 0)}")
        print(f"创建 PR 数: {results.get('prs_created', 0)}")
        print(f"成功率: {results.get('success_rate', 0) * 100:.1f}%")
        
        if results.get("pr_urls"):
            print("\n创建的 PR:")
            for url in results["pr_urls"]:
                print(f"  ✅ {url}")
        
        if results.get("errors"):
            print("\n错误列表:")
            for error in results["errors"][:5]:
                print(f"  ❌ {error}")
        
        result_file = work_dir / "results" / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n结果已保存到: {result_file}")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()