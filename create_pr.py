import requests
import json

token = "YOUR_GITHUB_TOKEN_HERE"
owner = "Medinz01"
repo = "nutrition-label-ocr"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

pr_data = {
    "title": "feat(aliases): add Hindi and Tamil nutrient name variants",
    "body": """## 变更说明

修复了 issue #2: Add Hindi and Tamil nutrient name aliases

## Issue 链接

https://github.com/Medinz01/nutrition-label-ocr/issues/2

## 修改内容

在 `semantic_parser.py` 的 `NUTRIENT_ALIASES` 字典中添加了印地语和泰米尔语的营养素名称变体，包括：

### 印地语（Hindi）
- Energy: ऊर्जा (urja), कैलोरी (calorie)
- Protein: प्रोटीन
- Carbohydrates: कार्बोहाइड्रेट
- Sugar: चीनी (cheeni), शक्कर (shakkar)
- Fiber: फाइबर, रेशा (resha)
- Fat: वसा (vasa), फैट
- Saturated Fat: संतृप्त वसा (santrupt vasa)
- Trans Fat: ट्रांस फैट
- Sodium: सोडियम
- Cholesterol: कोलेस्ट्रॉल

### 泰米尔语（Tamil）
- Energy: ஆற்றல் (arul)
- Protein: புரதம் (puratham)
- Carbohydrates: கார்போஹைட்ரேட் (karbohidrate)
- Sugar: சர்க்கரை (sarkkarai)
- Fiber: நார்ச்சத்து (narchatru), இழைச்சத்து (izhaichatru)
- Fat: கொழுப்பு (koluppu)
- Saturated Fat: நிறைவுற்ற கொழுப்பு (niraivurra koluppu)
- Trans Fat: டிரான்ஸ் கொழுப்பு (trans koluppu)
- Sodium: சோடியம்
- Cholesterol: கொலஸ்ட்ரால் (kolastral)

## 技术细节

- 添加了印地语和泰米尔语的原始脚本形式
- 添加了音译（transliteration）形式，便于 OCR 识别
- 保持了现有的英文别名和 OCR 常见错误变体

## 测试

可以通过以下方式测试：
1. 使用包含印地语或泰米尔语营养标签的图片
2. 运行 OCR 服务
3. 验证能够正确识别这些语言的营养素名称

## 符合规范

- ✅ 遵循 CONTRIBUTING.md 中的 commit 格式
- ✅ 使用 PEP 8 代码风格
- ✅ 保持代码简洁，无多余修改

Closes #2""",
    "head": "robellliu-dev:fix/issue-2-20260309094452",
    "base": "main"
}

response = requests.post(
    f"https://api.github.com/repos/{owner}/{repo}/pulls",
    headers=headers,
    json=pr_data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 201:
    pr = response.json()
    print(f"\n✅ PR created successfully!")
    print(f"PR URL: {pr['html_url']}")
else:
    print(f"\n❌ Failed to create PR")
    print(f"Error: {response.text}")
