#!/bin/bash
# 快速测试脚本 - 使用测试环境变量

export GITHUB_TOKEN="test_token_for_testing"
export GITHUB_USERNAME="test_user"
export WORK_DIR="./workspace"

echo "🧪 运行测试..."
python3 test_agent.py

echo ""
echo "🔍 测试查找功能..."
python3 opencode_agent.py --action find --languages python

echo ""
echo "✅ 测试完成"
