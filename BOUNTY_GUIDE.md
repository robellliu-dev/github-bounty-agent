# GitHub 赏金任务查找助手

## 功能说明

这个工具帮助你找到GitHub上的赏金任务（bounty issues），并分析其可行性。

## 安装依赖

```bash
pip install -r bounty_requirements.txt
```

## 使用方法

### 1. 创建 GitHub Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 选择以下权限:
   - `public_repo` (访问公共仓库)
   - `read:org` (如果需要访问组织项目)
4. 复制生成的 token

### 2. 运行程序

```bash
python3 bounty_hunter.py
```

### 3. 使用流程

1. 输入你的 GitHub Personal Access Token
2. 选择要筛选的编程语言 (例如: Python, JavaScript, TypeScript)
3. 程序会搜索相关的赏金任务
4. 查看结果列表
5. 选择感兴趣的任务进行深入分析
6. 保存结果供后续参考

## 注意事项

⚠️ **重要提示:**

- 本工具仅用于查找和分析赏金任务
- 所有代码提交和PR需要**人工审核后**手动提交
- 不要自动提交代码，保持对代码质量的控制
- 遵守项目的贡献指南和行为准则

## 贡献流程建议

对于找到的任务，建议按以下流程操作:

1. **需求分析**: 仔细阅读issue描述和评论
2. **本地开发**: Fork仓库，在本地开发功能
3. **测试**: 编写并运行测试
4. **代码审查**: 自我审查代码质量
5. **提交PR**: 手动创建Pull Request
6. **响应反馈**: 根据maintainer反馈修改代码

## 下一步

成功完成一个PR后，可以考虑:
- 查看项目的赏金结算方式
- 注册相应的支付账户
- 建立与项目维护者的联系

## 文件说明

- `bounty_hunter.py`: 主要的赏金查找工具
- `bounty_finder.py`: 简化版的查找工具
- `bounty_requirements.txt`: Python依赖包
- `BOUNTY_GUIDE.md`: 本使用指南
