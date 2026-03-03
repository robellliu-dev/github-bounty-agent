#!/bin/bash
# 快速设置GitHub Token的辅助脚本

echo "======================================================================"
echo "🔑 GitHub Token 设置助手"
echo "======================================================================"
echo ""

echo "📋 你的GitHub账号信息:"
echo "   用户名: robellliu-dev"
echo ""

echo "⚠️  GitHub已弃用密码认证，需要使用Personal Access Token"
echo ""

echo "📖 创建Token的步骤:"
echo ""
echo "1️⃣  打开浏览器访问:"
echo "   https://github.com/settings/tokens"
echo ""
echo "2️⃣  点击 'Generate new token' → 'Generate new token (classic)'"
echo ""
echo "3️⃣  勾选权限:"
echo "   ✅ repo (完整仓库访问)"
echo "   ✅ public_repo (访问公共仓库)"
echo "   ✅ workflow (操作Actions，可选)"
echo ""
echo "4️⃣  点击 'Generate token' 并复制Token"
echo ""
echo "5️⃣  在下面粘贴你的Token:"
echo ""

read -p "请粘贴你的GitHub Token (ghp_xxxx...): " github_token

if [ -z "$github_token" ]; then
    echo "❌ 未输入Token"
    exit 1
fi

# 验证Token格式
if [[ ! $github_token =~ ^ghp_[a-zA-Z0-9]{36}$ ]]; then
    echo "⚠️  Token格式看起来不正确（应该是 ghp_ 开头的36位字符）"
    echo "   但仍然会尝试使用..."
fi

# 设置环境变量
export GITHUB_TOKEN="$github_token"
export GITHUB_USERNAME="robellliu-dev"

echo ""
echo "✅ 环境变量已设置"
echo ""

# 测试Token
echo "🔍 测试Token是否有效..."
curl -s -H "Authorization: token $github_token" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Token有效！"
    echo ""
    echo "🚀 现在可以运行:"
    echo "   python3 real_search.py           # 查找真实赏金任务"
    echo "   python3 opencode_agent.py --action find"
    echo ""
    echo "💡 要永久保存Token，添加到 ~/.bashrc 或 ~/.zshrc:"
    echo "   export GITHUB_TOKEN='$github_token'"
    echo "   export GITHUB_USERNAME='robellliu-dev'"
else
    echo "❌ Token无效，请检查是否正确复制"
    exit 1
fi
