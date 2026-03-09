# GitHub Bounty Agent

**An intelligent, automated system for finding and fixing open source bounty issues.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/robellliu-dev/github-bounty-agent.svg?style=social)](https://github.com/robellliu-dev/github-bounty-agent)

## 🎯 Overview

GitHub Bounty Agent automatically:
- 🔍 **Finds** suitable bounty issues from popular platforms (Gitcoin, GitHub, Algorand, etc.)
- 🧠 **Analyzes** issue requirements and project structure
- 🔧 **Fixes** code using OpenCode CLI integration
- ✅ **Validates** changes with tests and CI checks
- 📝 **Creates** high-quality Pull Requests following project conventions
- 🚀 **Runs 24/7** processing 10+ bounty projects per day

## 📊 Bounty Platforms Supported

| Platform | Average Bounty | Max Bounty | Total Paid |
|----------|---------------|------------|------------|
| Gitcoin | $50 - $5,000 | $50,000+ | $50M+ |
| Ethereum Foundation | $500 - $250,000 | $250,000 | $1M+ |
| Solana Foundation | $100 - $50,000 | $2M | $200K+ |
| Algorand Foundation | $100 - $50,000 | $1M | $150K+ |
| Mozilla | $100 - $15,000 | $15,000 | $1M+ |
| Linux Kernel | $200 - $10,000 | $100,000 | Ongoing |

**Realistic Monthly Earnings:**
- Part-time (10-20 hrs/week): $500 - $3,000
- Full-time (40 hrs/week): $2,000 - $10,000
- Expert level: $5,000 - $50,000+

## 🏗️ Architecture

```
github-bounty-agent/
├── intelligent_bounty_agent.py   # Main intelligent agent
├── opencode_bounty_agent.py      # OpenCode CLI integration
├── opencode_integration.py       # OpenCode client wrapper
├── simple_bounty_agent.py        # Simplified agent
├── run_agent.py                  # Entry point script
├── run_continuous.py             # 24/7 runner
├── bounty_projects_config.yaml   # Bounty platforms config
├── requirements.txt              # Python dependencies
└── .github/
    └── workflows/
        └── auto-bounty.yml       # GitHub Actions workflow
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Git
- GitHub Personal Access Token (with `repo` scope)
- OpenCode CLI (optional, for advanced code analysis)

### Installation

```bash
# Clone the repository
git clone https://github.com/robellliu-dev/github-bounty-agent.git
cd github-bounty-agent

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GITHUB_TOKEN="your_github_token_here"
export GITHUB_USERNAME="your_github_username"
```

### Run Once (Single Issue)

```bash
python3 intelligent_bounty_agent.py
```

### Run Continuously (24/7)

```bash
nohup python3 run_continuous.py > continuous.log 2>&1 &
```

## 📖 Usage Examples

### Example 1: Fix a Specific Issue

```python
from intelligent_bounty_agent import IntelligentBountyAgent
from pathlib import Path

agent = IntelligentBountyAgent(
    token="your_github_token",
    username="your_username",
    work_dir=Path("./workspace")
)

# Find and process one issue
issue = agent.find_issue()
result = agent.process_issue(issue)

if result["success"]:
    print(f"PR created: {result['pr_info']['pr_url']}")
```

### Example 2: Batch Processing

```python
# Process 10 issues
for i in range(10):
    issue = agent.find_issue()
    if issue:
        result = agent.process_issue(issue)
        print(f"Issue {i+1}: {'Success' if result['success'] else 'Failed'}")
```

### Example 3: Custom Configuration

Edit `bounty_projects_config.yaml`:

```yaml
defaults:
  max_projects_per_run: 10
  target_pr_count_per_day: 10
  
  filters:
    min_stars: 100
    max_size_kb: 50000
    preferred_labels:
      - "good first issue"
      - "help wanted"
      - "bounty"
```

## 🔧 How It Works

### 1. Issue Discovery

The agent searches GitHub for issues with:
- `good first issue` label
- `help wanted` label
- `bounty` label
- Low comment count (< 10)
- Recent activity

### 2. Intelligent Analysis

For each issue, the agent:
- Analyzes project structure (language, build system, tests)
- Extracts requirements from issue title and description
- Identifies relevant source files
- Classifies issue type (bug, feature, enhancement)

### 3. Code Fix Implementation

Using OpenCode CLI integration:
- Analyzes codebase context
- Generates fix plan
- Implements changes
- Validates with tests

### 4. PR Generation

Creates Pull Request with:
- Proper title format (following project conventions)
- Detailed description
- Issue linkage (Closes #123)
- Test results
- Checklist items

## 📋 PR Log Format

Each processed issue generates a detailed log:

```
pr_logs/pr_<owner>_<repo>_<issue_number>.log
```

Example log content:
```
======================================================================
ISSUE PROCESSING: Add Hindi and Tamil nutrient name aliases
Repository: Medinz01/nutrition-label-ocr
Issue: #2
URL: https://github.com/Medinz01/nutrition-label-ocr/issues/2
======================================================================

[1/7] Forking repository...
✅ Fork successful

[2/7] Cloning repository...
✅ Cloned to workspace/nutrition-label-ocr

[3/7] Analyzing project structure...
Language: Python
Build: pip
Key files: 15

[4/7] Understanding issue requirements...
Type: feature
Complexity: easy
Keywords: ['level', 'autocomplete', 'keyword']

[5/7] Finding relevant files...
Found 3 relevant files:
  - semantic_parser.py
  - iw4_builtins.json
  - GscCompletionHandler.cs

[6/7] Creating feature branch...
✅ Branch: fix/issue-2-20260309120000

[7/7] Fixing the code...
✅ Code fixed successfully

Changes:
Added 'level' keyword to iw4_builtins.json
Added autocomplete support for level fields

[8/9] Committing and pushing...
✅ Committed and pushed

[9/9] Generating PR information...
======================================================================
PR INFORMATION
======================================================================

Title:
feat(aliases): add Hindi and Tamil nutrient name variants

Description:
...

PR Link:
https://github.com/Medinz01/nutrition-label-ocr/compare/main...
```

## 🎓 Learning Resources

### Bounty Platforms

- [Gitcoin Guide](https://gitcoin.co/explorer) - Web3 bounties
- [GitHub Sponsors](https://github.com/sponsors) - Direct sponsorships
- [IssueHunt](https://issuehunt.io) - Japanese bounty platform

### Best Practices

1. **Start Small**: Begin with `good first issue` labeled items
2. **Read Guidelines**: Always check CONTRIBUTING.md
3. **Test Locally**: Run tests before submitting PR
4. **Clear Communication**: Write detailed PR descriptions
5. **Be Patient**: Wait for maintainer reviews

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenCode AI for intelligent code analysis
- GitHub API for issue discovery
- All open source bounty platforms

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/robellliu-dev/github-bounty-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/robellliu-dev/github-bounty-agent/discussions)
- **Email**: robellliu.dev@gmail.com

## 🗺️ Roadmap

- [ ] Support for more bounty platforms
- [ ] Enhanced code analysis with AI models
- [ ] Multi-language support
- [ ] Web dashboard for monitoring
- [ ] Slack/Discord notifications
- [ ] Bounty tracking and analytics

---

**Made with ❤️ by [robellliu-dev](https://github.com/robellliu-dev)**

**⭐ If this project helps you earn bounties, please give it a star! ⭐**