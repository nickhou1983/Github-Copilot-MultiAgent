---
name: azure-image-to-video
description: "使用 Azure OpenAI Sora 模型将图片转换为视频（Image-to-Video）。当需要基于已有图片生成动态视频时使用此技能。支持自定义视频尺寸和时长。触发条件：用户要求从图片生成视频、图片转视频、将图片动画化、image to video、基于图片创建视频。"
---

# Azure OpenAI 图片转视频 Skill

使用 Azure OpenAI 的 **Sora** 模型，基于输入图片和文本描述生成短视频（Image-to-Video）。

## 前置要求

1. 已部署 Azure OpenAI `sora` 模型
2. 在 Skill 目录下配置 `.env` 文件（参考 [.env.example](./.env.example)）
3. 已安装 Python 3.10+、`requests` 和 `python-dotenv` 包

## 环境配置

在 `.github/skills/azure-image-to-video/.env` 中配置以下变量：

```text
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_SORA_DEPLOYMENT=sora
AZURE_OPENAI_API_VERSION=preview
AZURE_OPENAI_VIDEO_API_MODE=jobs
```

也可以复用 `azure-video-gen` skill 中已有的 `.env` 配置。

## 使用方式

运行 Skill 目录中的 [generate_video_from_image.py](./generate_video_from_image.py) 脚本：

```bash
python .github/skills/azure-image-to-video/generate_video_from_image.py \
  --image "./output/spring.png" \
  --prompt "让画面中的柳树随风摇曳，燕子掠过水面，桃花花瓣缓缓飘落" \
  --output "./output/spring_animated.mp4"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--image` | 是 | - | 输入图片路径（支持 PNG、JPG、WEBP） |
| `--prompt` | 否 | `""` | 动画描述（描述图片应如何动起来） |
| `--output` | 否 | `./output.mp4` | 输出视频文件路径 |
| `--size` | 否 | `1920x1080` | 视频尺寸，格式为 `宽x高` |
| `--n-seconds` | 否 | `5` | 视频时长/秒（`5`、`10`、`15`、`20`） |
| `--poll-interval` | 否 | `10` | 轮询间隔/秒 |
| `--max-wait` | 否 | `600` | 最大等待时间/秒 |

### 典型工作流：图片生成 → 图片转视频

1. 先用 `azure-image-gen` 技能生成静态图片
2. 再用本技能将图片转为动态视频

```bash
# 第一步：生成图片
python .github/skills/azure-image-gen/generate_image.py \
  --prompt "春日江南水乡，柳树依依，桃花盛开" \
  --output "./output/spring.png"

# 第二步：基于图片生成视频
python .github/skills/azure-image-to-video/generate_video_from_image.py \
  --image "./output/spring.png" \
  --prompt "柳树随风摇曳，燕子掠过水面，桃花花瓣飘落，水面泛起涟漪" \
  --output "./output/spring_video.mp4" \
  --n-seconds 10
```

## 注意事项

- 视频生成是异步过程，可能需要等待数分钟
- 输入图片会被自动转为 base64 编码上传
- 推荐使用 1024x1024 或更大尺寸的输入图片以获得更好效果
- prompt 描述应聚焦在「运动和变化」上，而非图片已有的静态内容
- 确保 `.env` 文件已添加到 `.gitignore`，避免泄露密钥
