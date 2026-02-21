#!/usr/bin/env python3
"""
Azure OpenAI Sora 图片转视频脚本
基于输入图片和文本描述生成视频（Image-to-Video）
"""

import argparse
import base64
import mimetypes
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


def load_config() -> dict:
    """加载 .env 配置文件"""
    # 优先加载 skill 目录下的 .env
    skill_dir = Path(__file__).parent
    env_path = skill_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # 也尝试加载 azure-video-gen skill 的 .env 作为 fallback
    video_gen_env = skill_dir.parent.parent / ".github" / "skills" / "azure-video-gen" / ".env"
    if video_gen_env.exists():
        load_dotenv(video_gen_env, override=False)

    config = {
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "deployment": os.getenv("AZURE_OPENAI_SORA_DEPLOYMENT", "sora"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "preview"),
        "video_api_mode": os.getenv("AZURE_OPENAI_VIDEO_API_MODE", "jobs").lower(),
    }

    if not config["endpoint"] or not config["api_key"]:
        print("错误: 请配置 AZURE_OPENAI_ENDPOINT 和 AZURE_OPENAI_API_KEY")
        print(f"可以在 {skill_dir / '.env'} 文件中设置，参考 .env.example")
        sys.exit(1)

    if config["video_api_mode"] not in ("auto", "legacy", "jobs"):
        print("错误: AZURE_OPENAI_VIDEO_API_MODE 仅支持 auto / legacy / jobs")
        sys.exit(1)

    return config


def encode_image_to_base64(image_path: str) -> tuple[str, str]:
    """
    将图片文件编码为 base64 字符串

    Returns:
        (base64_string, mime_type) 元组
    """
    path = Path(image_path)
    if not path.exists():
        print(f"错误: 图片文件不存在: {path.resolve()}")
        sys.exit(1)

    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None:
        # 根据扩展名推断
        ext = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext)
        if mime_type is None:
            print(f"错误: 不支持的图片格式: {ext}")
            print("支持的格式: PNG, JPG, JPEG, WEBP")
            sys.exit(1)

    image_bytes = path.read_bytes()
    base64_str = base64.b64encode(image_bytes).decode("utf-8")

    file_size_mb = len(image_bytes) / (1024 * 1024)
    print(f"  图片大小: {file_size_mb:.2f} MB")

    return base64_str, mime_type


def get_video_submit_url(config: dict, mode: str) -> str:
    """构建视频生成提交 URL"""
    if mode == "jobs":
        return (
            f"{config['endpoint'].rstrip('/')}/openai/v1/video/generations/jobs"
            f"?api-version={config['api_version']}"
        )

    return (
        f"{config['endpoint'].rstrip('/')}/openai/deployments/{config['deployment']}"
        f"/videos/generations?api-version={config['api_version']}"
    )


def get_video_status_url(config: dict, mode: str, job_id: str) -> str:
    """构建视频生成状态查询 URL"""
    if mode == "jobs":
        return (
            f"{config['endpoint'].rstrip('/')}/openai/v1/video/generations/jobs/{job_id}"
            f"?api-version={config['api_version']}"
        )

    return (
        f"{config['endpoint'].rstrip('/')}/openai/deployments/{config['deployment']}"
        f"/videos/generations/{job_id}?api-version={config['api_version']}"
    )


def get_video_content_url(config: dict, route_mode: str, generation_id: str) -> str:
    """构建视频内容下载 URL"""
    if route_mode == "jobs":
        return (
            f"{config['endpoint'].rstrip('/')}/openai/v1/video/generations/{generation_id}"
            f"/content/video?api-version={config['api_version']}"
        )

    return ""


def resolve_probe_modes(config: dict) -> list[str]:
    """根据配置解析需要探测的路由模式"""
    if config["video_api_mode"] == "auto":
        return ["jobs", "legacy"]
    return [config["video_api_mode"]]


def is_resource_not_found(response: requests.Response) -> bool:
    """判断是否为典型的 Azure 404 资源不可用错误"""
    return response.status_code == 404


def parse_video_size(size: str) -> tuple[int, int]:
    """解析视频尺寸字符串"""
    try:
        width_str, height_str = size.lower().split("x")
        width = int(width_str)
        height = int(height_str)
    except ValueError:
        raise ValueError("size 格式必须为 宽x高，例如 854x480")

    if width <= 0 or height <= 0:
        raise ValueError("size 的宽和高必须为正整数")

    return width, height


def preflight_video_generation_route(config: dict) -> str:
    """
    提交正式任务前，先探测视频路由是否可用。
    返回可用的路由模式。
    """
    headers = {
        "api-key": config["api_key"],
        "Content-Type": "application/json",
    }

    not_found_urls = []
    for mode in resolve_probe_modes(config):
        url = get_video_submit_url(config, mode)

        try:
            response = requests.post(url, headers=headers, json={}, timeout=20)
        except requests.RequestException as exc:
            print("错误: 无法连接到 Azure OpenAI 端点")
            print(f"详情: {exc}")
            sys.exit(1)

        if is_resource_not_found(response):
            not_found_urls.append(url)
            continue

        if response.status_code in (401, 403):
            print(f"错误: 预检查失败 (HTTP {response.status_code})，请检查 API Key 或访问权限")
            print(f"响应: {response.text}")
            sys.exit(1)

        return mode

    print("错误: 当前资源未暴露可用的 Sora 视频生成数据面路由（HTTP 404 Resource not found）")
    print("请检查以下配置是否与 Azure Portal 中的视频调用示例完全一致：")
    print(f"  endpoint: {config['endpoint']}")
    print(f"  deployment: {config['deployment']}")
    print(f"  api-version: {config['api_version']}")
    print(f"  video_api_mode: {config['video_api_mode']}")
    if not_found_urls:
        print("已探测路由:")
        for probe_url in not_found_urls:
            print(f"  - {probe_url}")
    print("建议：在 Azure AI Foundry / Azure OpenAI Portal 中复制该部署的最新视频生成调用示例进行对照。")
    sys.exit(1)


def submit_image_to_video(
    config: dict,
    route_mode: str,
    image_base64: str,
    mime_type: str,
    prompt: str,
    size: str,
    n_seconds: int,
) -> str:
    """
    提交图片转视频任务，返回任务 ID。

    图片以 data URI 形式嵌入请求。
    """
    url = get_video_submit_url(config, route_mode)
    headers = {
        "api-key": config["api_key"],
        "Content-Type": "application/json",
    }

    # 构建 data URI
    data_uri = f"data:{mime_type};base64,{image_base64}"

    if route_mode == "jobs":
        try:
            width, height = parse_video_size(size)
        except ValueError as exc:
            print(f"错误: {exc}")
            sys.exit(1)

        payload = {
            "prompt": prompt or "",
            "image": data_uri,
            "n_variants": "1",
            "n_seconds": str(n_seconds),
            "height": str(height),
            "width": str(width),
            "model": config["deployment"],
        }
    else:
        payload = {
            "prompt": prompt or "",
            "image": data_uri,
            "size": size,
            "n_seconds": n_seconds,
        }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code not in (200, 201, 202):
        print(f"错误: 提交图片转视频任务失败 (HTTP {response.status_code})")
        print(f"响应: {response.text}")
        sys.exit(1)

    data = response.json()
    job_id = data.get("id") or data.get("job_id") or data.get("jobId")
    if not job_id:
        print("错误: 未能从 API 响应中获取任务 ID")
        print(f"响应: {data}")
        sys.exit(1)

    return job_id


def poll_video_status(
    config: dict, route_mode: str, job_id: str, poll_interval: int = 10, max_wait: int = 600
) -> dict:
    """轮询视频生成任务状态，直到完成或超时"""
    url = get_video_status_url(config, route_mode, job_id)
    headers = {
        "api-key": config["api_key"],
    }

    elapsed = 0
    while elapsed < max_wait:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"警告: 查询状态失败 (HTTP {response.status_code})，将重试...")
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        data = response.json()
        status = data.get("status", "unknown")

        if status == "succeeded":
            print("视频生成完成！")
            return data
        elif status == "failed":
            error_msg = data.get("error", {}).get("message", "未知错误")
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


def generate_video_from_image(
    image_path: str,
    prompt: str = "",
    output_path: str = "./output.mp4",
    size: str = "1920x1080",
    n_seconds: int = 5,
    poll_interval: int = 10,
    max_wait: int = 600,
) -> str:
    """
    基于输入图片调用 Azure OpenAI Sora 生成视频

    Args:
        image_path: 输入图片文件路径
        prompt: 动画描述文本（可选，描述图片应如何动起来）
        output_path: 输出视频文件路径
        size: 视频尺寸 (例如 1920x1080)
        n_seconds: 视频时长（秒）
        poll_interval: 轮询间隔（秒）
        max_wait: 最大等待时间（秒）

    Returns:
        保存的视频文件路径
    """
    config = load_config()

    print("正在准备图片转视频...")
    print(f"  输入图片: {Path(image_path).resolve()}")
    print(f"  动画描述: {prompt or '(无额外描述)'}")
    print(f"  视频尺寸: {size}")
    print(f"  视频时长: {n_seconds} 秒")
    print(f"  模型: {config['deployment']}")

    # 编码图片
    print("正在编码图片...")
    image_base64, mime_type = encode_image_to_base64(image_path)
    print(f"  图片格式: {mime_type}")

    # 预检查路由
    print("正在执行视频路由预检查...")
    route_mode = preflight_video_generation_route(config)
    print(f"预检查通过，使用路由模式: {route_mode}")

    # 第一步：提交生成任务
    print("正在提交图片转视频任务...")
    job_id = submit_image_to_video(
        config, route_mode, image_base64, mime_type, prompt, size, n_seconds
    )
    print(f"任务已提交，ID: {job_id}")

    # 第二步：轮询等待完成
    print(f"等待视频生成（轮询间隔: {poll_interval}s，超时: {max_wait}s）...")
    result = poll_video_status(config, route_mode, job_id, poll_interval, max_wait)

    # 第三步：提取视频 URL 并下载
    video_url = result.get("video_url") or result.get("videoUrl")
    if not video_url:
        output = result.get("output", {})
        if isinstance(output, dict):
            video_url = output.get("video_url") or output.get("videoUrl")

    generations = result.get("generations", [])
    if not video_url and generations:
        video_url = generations[0].get("video", {}).get("url")

    # jobs 模式特殊处理：通过 content API 下载
    if not video_url and route_mode == "jobs" and generations:
        generation_id = generations[0].get("id")
        if generation_id:
            content_url = get_video_content_url(config, route_mode, generation_id)
            headers = {"api-key": config["api_key"]}
            response = requests.get(content_url, headers=headers, timeout=120)
            if response.status_code == 200:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"视频已保存到: {output_file.resolve()}")
                return str(output_file.resolve())
            print(f"错误: 视频内容下载失败 (HTTP {response.status_code})")
            print(f"响应: {response.text}")
            sys.exit(1)

    if not video_url:
        print("错误: 未能从 API 响应中获取视频 URL")
        print(f"响应: {result}")
        sys.exit(1)

    return download_video(video_url, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="使用 Azure OpenAI Sora 将图片转换为视频（Image-to-Video）"
    )
    parser.add_argument(
        "--image",
        required=True,
        help="输入图片路径（支持 PNG、JPG、WEBP）",
    )
    parser.add_argument(
        "--prompt",
        default="",
        help="动画描述（描述图片应如何动起来，可选）",
    )
    parser.add_argument(
        "--output",
        default="./output.mp4",
        help="输出视频文件路径（默认: ./output.mp4）",
    )
    parser.add_argument(
        "--size",
        default="1920x1080",
        help="视频尺寸，格式 宽x高（默认: 1920x1080）",
    )
    parser.add_argument(
        "--n-seconds",
        type=int,
        default=5,
        choices=[5, 10, 15, 20],
        help="视频时长/秒（默认: 5）",
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

    generate_video_from_image(
        image_path=args.image,
        prompt=args.prompt,
        output_path=args.output,
        size=args.size,
        n_seconds=args.n_seconds,
        poll_interval=args.poll_interval,
        max_wait=args.max_wait,
    )


if __name__ == "__main__":
    main()
