#!/usr/bin/env python3
"""
Azure OpenAI 图片生成脚本
使用 gpt-image-1 模型根据文本描述生成图片
"""

import argparse
import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import AzureOpenAI


def load_config() -> dict:
    """加载 .env 配置文件"""
    # 优先加载 skill 目录下的 .env
    skill_dir = Path(__file__).parent
    env_path = skill_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    config = {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "deployment": os.getenv("AZURE_OPENAI_DALLE_DEPLOYMENT", "gpt-image-1"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
    }

    if not config["endpoint"] or not config["api_key"]:
        print("错误: 请配置 AZURE_OPENAI_ENDPOINT 和 AZURE_OPENAI_API_KEY")
        print(f"可以在 {skill_dir / '.env'} 文件中设置，参考 .env.example")
        sys.exit(1)

    return config


def generate_image(
    prompt: str,
    output_path: str = "./output.png",
    size: str = "1024x1024",
    quality: str = "high",
) -> str:
    """
    调用 Azure OpenAI gpt-image-1 生成图片

    Args:
        prompt: 图片描述文本
        output_path: 输出文件路径
        size: 图片尺寸 (1024x1024, 1024x1536, 1536x1024)
        quality: 图片质量 (low, medium, high)

    Returns:
        保存的文件路径
    """
    config = load_config()

    client = AzureOpenAI(
        azure_endpoint=config["endpoint"],
        api_key=config["api_key"],
        api_version=config["api_version"],
    )

    print(f"正在生成图片...")
    print(f"  描述: {prompt}")
    print(f"  尺寸: {size}")
    print(f"  质量: {quality}")
    print(f"  模型: {config['deployment']}")

    result = client.images.generate(
        model=config["deployment"],
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )

    # gpt-image-1 返回 base64 编码的图片数据
    image_data = result.data[0]

    # 确保输出目录存在
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(image_data, "b64_json") and image_data.b64_json:
        # base64 格式
        image_bytes = base64.b64decode(image_data.b64_json)
        output_file.write_bytes(image_bytes)
    elif hasattr(image_data, "url") and image_data.url:
        # URL 格式 (fallback)
        import urllib.request
        urllib.request.urlretrieve(image_data.url, str(output_file))
    else:
        print("错误: 未能从 API 响应中获取图片数据")
        sys.exit(1)

    print(f"图片已保存到: {output_file.resolve()}")
    return str(output_file.resolve())


def main():
    parser = argparse.ArgumentParser(
        description="使用 Azure OpenAI gpt-image-1 生成图片"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="图片描述文本（支持中英文）",
    )
    parser.add_argument(
        "--output",
        default="./output.png",
        help="输出文件路径（默认: ./output.png）",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=["1024x1024", "1024x1536", "1536x1024"],
        help="图片尺寸（默认: 1024x1024）",
    )
    parser.add_argument(
        "--quality",
        default="high",
        choices=["low", "medium", "high"],
        help="图片质量（默认: high）",
    )

    args = parser.parse_args()

    generate_image(
        prompt=args.prompt,
        output_path=args.output,
        size=args.size,
        quality=args.quality,
    )


if __name__ == "__main__":
    main()
