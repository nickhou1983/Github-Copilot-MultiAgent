---
name: azure-video-gen
description: "使用 Azure OpenAI Sora 模型生成视频。当需要根据文本描述创建短视频时使用此技能。支持自定义视频尺寸和时长。触发条件：用户要求生成视频、创建动画、AI视频生成。"
---

# Azure OpenAI 视频生成 Skill

使用 Azure OpenAI 的 **Sora** 模型，根据文本描述生成短视频。

## 前置要求

1. 已部署 Azure OpenAI `sora` 模型
2. 在 Skill 目录下配置 `.env` 文件（参考 [.env.example](./.env.example)）
3. 已安装 Python 3.10+ 和 `requests` 包

## 环境配置

在 `.github/skills/azure-video-gen/.env` 中配置以下变量：

```text
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_SORA_DEPLOYMENT=sora
```

脚本使用固定接口：`POST /openai/v1/videos`。鉴权默认发送 `Authorization: Bearer <api_key>`，并兼容 `api-key` 请求头。

## 使用方式

当需要生成视频时，运行 Skill 目录中的 [generate_video.py](./generate_video.py) 脚本：

```bash
cd .github/skills/azure-video-gen
python generate_video.py --prompt "描述文本" --output "../../../output/video.mp4"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompt` | 是 | - | 视频描述（支持中英文） |
| `--output` | 否 | `./output.mp4` | 输出文件路径 |
| `--size` | 否 | `1920x1080` | 视频尺寸，格式为 `宽x高`（例如 `854x480`、`1920x1080`） |
| `--seconds` | 否 | `5` | 视频时长/秒（`4`、`5`、`10`、`15`、`20`） |
| `--n-seconds` | 否 | - | 兼容旧参数，等价于 `--seconds` |
| `--poll-interval` | 否 | `10` | 轮询间隔/秒 |
| `--max-wait` | 否 | `600` | 最大等待时间/秒 |

### 示例

```bash
python .github/skills/azure-video-gen/generate_video.py \
  --prompt "春日江南水乡，柳树随风摇曳，燕子掠过水面，桃花花瓣飘落" \
  --output "./output/spring.mp4" \
  --size "1920x1080" \
  --seconds 10
```

## 注意事项

- 视频生成是异步过程，可能需要等待数分钟
- 生成视频需要消耗 Azure OpenAI 的配额
- 确保 `.env` 文件已添加到 `.gitignore`，避免泄露密钥
- 推荐在 prompt 中加入场景、动作和风格描述以获得更好效果
- 接口路径固定为 `/openai/v1/videos`，请确保 `AZURE_OPENAI_ENDPOINT` 仅填写资源根域名（不要包含 `/openai`）

## 常见故障排查

- 若出现 `HTTP 404 Resource not found`，请核对 endpoint 与路径是否组合为 `https://<resource>.openai.azure.com/openai/v1/videos`
- 请优先在 Azure AI Foundry / Azure OpenAI 门户中打开 `sora` 部署，复制官方“调用示例”中的 endpoint 与路径对照 `.env`
- 若返回 `401/403`，请检查 `AZURE_OPENAI_API_KEY` 是否有效、订阅/资源访问权限是否正确
