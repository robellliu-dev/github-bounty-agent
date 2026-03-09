#!/usr/bin/env python3
"""
Continuous Bounty Agent Runner - No External Dependencies
Runs 24/7, processes 10 bounty projects per day
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def run_bounty_cycle():
    """Run one bounty hunting cycle"""
    print("\n" + "=" * 70)
    print(f"STARTING BOUNTY CYCLE - {datetime.now().isoformat()}")
    print("=" * 70)
    
    try:
        from simple_bounty_agent import SimpleBountyAgent
        
        token = os.getenv("GITHUB_TOKEN")
        username = os.getenv("GITHUB_USERNAME", "robellliu-dev")
        
        if not token:
            print("ERROR: GITHUB_TOKEN not set")
            return
        
        work_dir = Path("./workspace_continuous")
        work_dir.mkdir(exist_ok=True)
        
        agent = SimpleBountyAgent(token, username, work_dir)
        
        success_count = 0
        for i in range(10):
            print(f"\n{'='*70}")
            print(f"Project {i+1}/10")
            print(f"{'='*70}")
            
            try:
                issue = agent.find_simple_issue()
                if issue:
                    success = agent.process_issue(issue)
                    if success:
                        success_count += 1
                        print(f"✅ Project {i+1} SUCCESS")
                    else:
                        print(f"⚠️ Project {i+1} FAILED")
                else:
                    print(f"No suitable issue found for project {i+1}")
                
                # Wait between projects
                time.sleep(120)  # 2 minutes between projects
                
            except Exception as e:
                print(f"ERROR: Project {i+1} failed: {e}")
                time.sleep(60)
        
        print("\n" + "=" * 70)
        print(f"CYCLE COMPLETE - Success: {success_count}/10")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # Save results
        results_file = work_dir / "results" / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "success_count": success_count,
                "total_attempted": 10
            }, f, indent=2)
        
        return success_count
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    print("=" * 70)
    print("CONTINUOUS BOUNTY RUNNER")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Target: 10 projects per cycle")
    print(f"Schedule: Continuous (24/7)")
    print("=" * 70)
    
    cycle_count = 0
    total_success = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\n{'='*70}")
            print(f"CYCLE #{cycle_count}")
            print(f"{'='*70}")
            
            success = run_bounty_cycle()
            total_success += success
            
            print(f"\nTotal success: {total_success}/{cycle_count * 10}")
            
            # Wait 24 hours before next cycle
            print(f"\nNext cycle in 24 hours...")
            time.sleep(86400)  # 24 hours
            
        except KeyboardInterrupt:
            print("\n\nShutting down by user request...")
            print(f"Final stats: {total_success} successful PRs in {cycle_count} cycles")
            break
        except Exception as e:
            print(f"\nERROR in cycle: {e}")
            print("Retrying in 1 hour...")
            time.sleep(3600)  # 1 hour

if __name__ == "__main__":
    main()