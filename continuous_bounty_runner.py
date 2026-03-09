#!/usr/bin/env python3
"""
Continuous Bounty Agent Runner
Runs 24/7, processes 10 bounty projects per day
"""

import os
import sys
import time
import yaml
import logging
import schedule
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bounty_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousBountyRunner:
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.load_config()
        self.setup_directories()
        
    def load_config(self):
        """Load bounty projects configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded config from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
    
    def setup_directories(self):
        """Setup workspace directories"""
        self.work_dir = Path("./workspace_continuous")
        self.work_dir.mkdir(exist_ok=True)
        
        self.results_dir = self.work_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.logs_dir = self.work_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
    
    def run_daily_bounty_hunt(self):
        """Run bounty hunt for the day"""
        logger.info("=" * 70)
        logger.info("STARTING DAILY BOUNTY HUNT")
        logger.info(f"Time: {datetime.now().isoformat()}")
        logger.info("=" * 70)
        
        try:
            # Import the agent
            sys.path.insert(0, str(Path(__file__).parent))
            from simple_bounty_agent import SimpleBountyAgent
            
            # Initialize agent
            token = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME", "robellliu-dev")
            
            if not token:
                logger.error("GITHUB_TOKEN not set")
                return
            
            agent = SimpleBountyAgent(token, username, self.work_dir)
            
            # Process bounties
            for i in range(10):  # 10 projects per day
                logger.info(f"\n{'='*70}")
                logger.info(f"Processing Project {i+1}/10")
                logger.info(f"{'='*70}")
                
                try:
                    issue = agent.find_simple_issue()
                    if issue:
                        success = agent.process_issue(issue)
                        if success:
                            logger.info(f"✅ Project {i+1} completed successfully")
                        else:
                            logger.warning(f"⚠️ Project {i+1} failed")
                    else:
                        logger.warning(f"No suitable issue found for project {i+1}")
                    
                    # Wait between projects
                    time.sleep(300)  # 5 minutes between projects
                    
                except Exception as e:
                    logger.error(f"Error processing project {i+1}: {e}")
                    time.sleep(60)
            
            logger.info("\n" + "=" * 70)
            logger.info("DAILY BOUNTY HUNT COMPLETED")
            logger.info(f"Time: {datetime.now().isoformat()}")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Daily bounty hunt failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start(self):
        """Start continuous runner"""
        logger.info("=" * 70)
        logger.info("CONTINUOUS BOUNTY RUNNER STARTED")
        logger.info("=" * 70)
        logger.info(f"Config: {self.config_file}")
        logger.info(f"Work dir: {self.work_dir}")
        logger.info(f"Schedule: Every day at 00:00 UTC")
        logger.info(f"Target: 10 projects per day")
        logger.info("=" * 70)
        
        # Schedule daily runs
        schedule.every().day.at("00:00").do(self.run_daily_bounty_hunt)
        
        # Run immediately on start
        logger.info("\nRunning first bounty hunt now...")
        self.run_daily_bounty_hunt()
        
        # Keep running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("\nShutting down by user request...")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)

def main():
    config_file = "/home/robell/github-bounty-agent/bounty_projects_config.yaml"
    
    runner = ContinuousBountyRunner(config_file)
    runner.start()

if __name__ == "__main__":
    main()