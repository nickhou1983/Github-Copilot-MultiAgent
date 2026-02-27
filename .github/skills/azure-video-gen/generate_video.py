#!/usr/bin/env python3
"""
Azure OpenAI Sora 视频生成脚本
使用 Sora 模型根据文本描述生成视频
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


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
        "deployment": os.getenv("AZURE_OPENAI_SORA_DEPLOYMENT", "sora"),
    }

    if not config["endpoint"] or not config["api_key"]:
        print("错误: 请配置 AZURE_OPENAI_ENDPOINT 和 AZURE_OPENAI_API_KEY")
        print(f"可以在 {skill_dir / '.env'} 文件中设置，参考 .env.example")
        sys.exit(1)

    return config


def build_headers(api_key: str, include_content_type: bool = True) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "api-key": api_key,
    }
    if include_content_type:
        headers["Content-Type"] = "application/json"
    return headers


def get_video_submit_url(config: dict) -> str:
    return f"{config['endpoint'].rstrip('/')}/openai/v1/videos"


def get_video_status_url(config: dict, video_id: str) -> str:
    return f"{config['endpoint'].rstrip('/')}/openai/v1/videos/{video_id}"


def parse_video_size(size: str) -> tuple[int, int]:
    try:
        width_str, height_str = size.lower().split("x")
        width = int(width_str)
        height = int(height_str)
    except ValueError:
        raise ValueError("size 格式必须为 宽x高，例如 854x480")

    if width <= 0 or height <= 0:
        raise ValueError("size 的宽和高必须为正整数")

    return width, height


def get_video_content_url(config: dict, video_id: str) -> str:
    return f"{config['endpoint'].rstrip('/')}/openai/v1/videos/{video_id}/content"


def submit_video_generation(config: dict, prompt: str, size: str, seconds: int) -> str:
    """提交视频生成任务，返回任务 ID"""
    url = get_video_submit_url(config)
    headers = build_headers(config["api_key"], include_content_type=True)

    try:
        parse_video_size(size)
    except ValueError as exc:
        print(f"错误: {exc}")
        sys.exit(1)

    payload = {
        "prompt": prompt,
        "size": size,
        "seconds": str(seconds),
        "model": config["deployment"],
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        print("错误: 无法连接到 Azure OpenAI 端点")
        print(f"详情: {exc}")
        sys.exit(1)

    if response.status_code not in (200, 201, 202):
        print(f"错误: 提交视频生成任务失败 (HTTP {response.status_code})")
        print(f"请求 URL: {url}")
        print(f"响应: {response.text}")
        sys.exit(1)

    data = response.json()
    video_id = data.get("id") or data.get("video_id") or data.get("job_id") or data.get("jobId")
    if not video_id:
        print("错误: 未能从 API 响应中获取任务 ID")
        print(f"响应: {data}")
        sys.exit(1)

    return video_id


def poll_video_status(config: dict, video_id: str, poll_interval: int = 10, max_wait: int = 600) -> dict:
    """轮询视频生成任务状态，直到完成或超时"""
    url = get_video_status_url(config, video_id)
    headers = build_headers(config["api_key"], include_content_type=False)

    elapsed = 0
    while elapsed < max_wait:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"警告: 查询状态失败 (HTTP {response.status_code})，将重试...")
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        data = response.json()
        status = (data.get("status") or data.get("state") or "unknown").lower()

        if status in ("succeeded", "completed", "done"):
            print("视频生成完成！")
            return data
        elif status in ("failed", "error", "cancelled"):
            error = data.get("error", {})
            if isinstance(error, dict):
                error_msg = error.get("message", "未知错误")
            else:
                error_msg = str(error)
            print(f"错误: 视频生成失败 - {error_msg}")
            sys.exit(1)
        else:
            print(f"  状态: {status}，已等待 {elapsed}s，继续轮询...")
            time.sleep(poll_interval)
            elapsed += poll_interval

    print(f"错误: 视频生成超时（已等待 {max_wait} 秒）")
    sys.exit(1)


def download_video(video_url: str, output_path: str) -> str:
    """下载视频文件并保存到本地"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("正在下载视频...")
    response = requests.get(video_url, stream=True, timeout=120)
    if response.status_code != 200:
        print(f"错误: 下载视频失败 (HTTP {response.status_code})")
        sys.exit(1)

    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"视频已保存到: {output_file.resolve()}")
    return str(output_file.resolve())


def try_download_video_content(config: dict, video_id: str, output_path: str) -> str | None:
    """尝试通过受保护的 content 端点下载视频"""
    content_url = get_video_content_url(config, video_id)
    headers = build_headers(config["api_key"], include_content_type=False)

    try:
        response = requests.get(content_url, headers=headers, stream=True, timeout=120)
    except requests.RequestException:
        return None

    if response.status_code != 200:
        return None

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"视频已保存到: {output_file.resolve()}")
    return str(output_file.resolve())


def extract_video_url(result: dict[str, Any]) -> str | None:
    direct_url = result.get("video_url") or result.get("videoUrl") or result.get("url")
    if isinstance(direct_url, str) and direct_url:
        return direct_url

    output = result.get("output")
    if isinstance(output, dict):
        nested_url = output.get("video_url") or output.get("videoUrl") or output.get("url")
        if isinstance(nested_url, str) and nested_url:
            return nested_url

    generations = result.get("generations")
    if isinstance(generations, list) and generations:
        first_generation = generations[0]
        if isinstance(first_generation, dict):
            video = first_generation.get("video")
            if isinstance(video, dict):
                generation_url = video.get("url")
                if isinstance(generation_url, str) and generation_url:
                    return generation_url

    return None


def generate_video(
    prompt: str,
    output_path: str = "./output.mp4",
    size: str = "1920x1080",
    seconds: int = 5,
    poll_interval: int = 10,
    max_wait: int = 600,
) -> str:
    """
    调用 Azure OpenAI Sora 生成视频

    Args:
        prompt: 视频描述文本
        output_path: 输出文件路径
        size: 视频尺寸 (1920x1080, 1080x1920, 480x480)
        seconds: 视频时长（秒）
        poll_interval: 轮询间隔（秒）
        max_wait: 最大等待时间（秒）

    Returns:
        保存的文件路径
    """
    config = load_config()

    print("正在生成视频...")
    print(f"  描述: {prompt}")
    print(f"  尺寸: {size}")
    print(f"  时长: {seconds} 秒")
    print(f"  模型: {config['deployment']}")
    print(f"  请求地址: {get_video_submit_url(config)}")

    # 第一步：提交生成任务
    print("正在提交视频生成任务...")
    video_id = submit_video_generation(config, prompt, size, seconds)
    print(f"任务已提交，ID: {video_id}")

    # 第二步：轮询等待完成
    print(f"等待视频生成（轮询间隔: {poll_interval}s，超时: {max_wait}s）...")
    result = poll_video_status(config, video_id, poll_interval, max_wait)

    # 第三步：下载视频
    video_url = extract_video_url(result)

    if not video_url:
        downloaded_file = try_download_video_content(config, video_id, output_path)
        if downloaded_file:
            return downloaded_file

    if not video_url:
        print("错误: 未能从 API 响应中获取视频 URL")
        print(f"响应: {result}")
        sys.exit(1)

    return download_video(video_url, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="使用 Azure OpenAI Sora 生成视频"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="视频描述文本（支持中英文）",
    )
    parser.add_argument(
        "--output",
        default="./output.mp4",
        help="输出文件路径（默认: ./output.mp4）",
    )
    parser.add_argument(
        "--size",
        default="1920x1080",
        help="视频尺寸，格式 宽x高（默认: 1920x1080，例如: 854x480）",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=5,
        choices=[4, 5, 10, 15, 20],
        help="视频时长/秒（默认: 5）",
    )
    parser.add_argument(
        "--n-seconds",
        type=int,
        choices=[4, 5, 10, 15, 20],
        help="兼容旧参数名，等价于 --seconds",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="轮询间隔/秒（默认: 10）",
    )
    parser.add_argument(
        "--max-wait",
        type=int,
        default=600,
        help="最大等待时间/秒（默认: 600）",
    )

    args = parser.parse_args()
    seconds = args.n_seconds if args.n_seconds is not None else args.seconds

    generate_video(
        prompt=args.prompt,
        output_path=args.output,
        size=args.size,
        seconds=seconds,
        poll_interval=args.poll_interval,
        max_wait=args.max_wait,
    )


if __name__ == "__main__":
    main()
