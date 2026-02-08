---
name: azure-image-gen
description: "使用 Azure OpenAI gpt-image-1 模型生成图片。当需要为诗歌、文章或任何内容创建配图时使用此技能。支持根据文本描述生成高质量图片并保存为本地文件。触发条件：用户要求生成图片、需要配图、创建插图、AI绘画。"
---

# Azure OpenAI 图片生成 Skill

使用 Azure OpenAI 的 **gpt-image-1** 模型，根据文本描述生成高质量图片。

## 前置要求

1. 已部署 Azure OpenAI `gpt-image-1` 模型
2. 在 Skill 目录下配置 `.env` 文件（参考 [.env.example](./.env.example)）
3. 已安装 Python 3.10+ 和 `openai` 包

## 环境配置

在 `.github/skills/azure-image-gen/.env` 中配置以下变量：

```text
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_DALLE_DEPLOYMENT=gpt-image-1
AZURE_OPENAI_API_VERSION=2025-04-01-preview
```

## 使用方式

当需要生成图片时，运行 Skill 目录中的 [generate_image.py](./generate_image.py) 脚本：

```bash
cd .github/skills/azure-image-gen
python generate_image.py --prompt "描述文本" --output "../../../output/image.png"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompt` | 是 | - | 图片描述（支持中英文） |
| `--output` | 否 | `./output.png` | 输出文件路径 |
| `--size` | 否 | `1024x1024` | 图片尺寸（`1024x1024`、`1024x1536`、`1536x1024`） |
| `--quality` | 否 | `high` | 图片质量（`low`、`medium`、`high`） |

### 与诗人Agent配合使用

当诗人Agent判断需要配图时，按以下步骤操作：

1. 从诗人Agent的输出中获取「配图描述」
2. 将描述作为 `--prompt` 参数传入脚本
3. 对于中文描述，脚本会自动处理

示例：

```bash
python .github/skills/azure-image-gen/generate_image.py \
  --prompt "春日江南水乡，柳树依依，桃花盛开，燕子飞舞，池塘碧波荡漾，中国水墨画风格" \
  --output "./output/spring.png" \
  --size "1024x1024" \
  --quality "high"
```

## 注意事项

- 生成图片需要消耗 Azure OpenAI 的配额
- 确保 `.env` 文件已添加到 `.gitignore`，避免泄露密钥
- 推荐在 prompt 中加入画风描述（如"中国水墨画风格"、"水彩风格"）以获得更好效果
