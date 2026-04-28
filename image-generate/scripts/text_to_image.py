#!/usr/bin/env python3
import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_KEY_ENV = "MINIMAX_API_KEY"
API_URL = os.environ.get("MINIMAX_API_URL", "https://api.minimaxi.com/v1/image_generation")
DEFAULT_MODEL = "image-01"
DEFAULT_RESPONSE_FORMAT = "url"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "image"


def post_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {API_KEY_ENV}")

    request = Request(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "curl/8.0",
        },
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        raise RuntimeError(f"文生图 API 请求失败: HTTP {e.code} {e.reason}; {body}") from e


def save_url_images(image_urls: List[str], output_dir: Path, prefix: str) -> List[Dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for idx, image_url in enumerate(image_urls, start=1):
        file_path = output_dir / f"{prefix}_{idx:03d}.png"
        req = Request(
            image_url,
            headers={
                "User-Agent": "curl/8.0",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            },
            method="GET",
        )
        with urlopen(req, timeout=120) as response:
            file_path.write_bytes(response.read())
        records.append({"file": str(file_path), "image_url": image_url})
    return records


def save_base64_images(image_base64: List[str], output_dir: Path, prefix: str) -> List[Dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for idx, encoded in enumerate(image_base64, start=1):
        file_path = output_dir / f"{prefix}_{idx:03d}.png"
        file_path.write_bytes(base64.b64decode(encoded))
        records.append({"file": str(file_path), "image_base64": "<omitted>"})
    return records


def build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "response_format": args.response_format,
        "n": args.n,
        "prompt_optimizer": args.prompt_optimizer,
        "aigc_watermark": args.aigc_watermark,
    }
    if args.aspect_ratio:
        payload["aspect_ratio"] = args.aspect_ratio
    if args.width is not None and args.height is not None:
        payload["width"] = args.width
        payload["height"] = args.height
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.style_type:
        payload["style"] = {"style_type": args.style_type}
        if args.style_weight is not None:
            payload["style"]["style_weight"] = args.style_weight
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate images with text-to-image API.")
    parser.add_argument("--prompt", required=True, help="Text prompt for image generation")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated images")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=["image-01", "image-01-live"])
    parser.add_argument("--aspect-ratio", choices=["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"])
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--response-format", default=DEFAULT_RESPONSE_FORMAT, choices=["url", "base64"])
    parser.add_argument("--seed", type=int)
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--prompt-optimizer", action="store_true")
    parser.add_argument("--aigc-watermark", action="store_true")
    parser.add_argument("--style-type", choices=["漫画", "元气", "中世纪", "水彩"])
    parser.add_argument("--style-weight", type=float)
    parser.add_argument("--prefix", default=None, help="Output filename prefix")
    parser.add_argument("--metadata-file", default=None, help="Optional metadata json path")
    parser.add_argument("--print-each", action="store_true", help="Print one JSON line per image")
    args = parser.parse_args()

    if args.n < 1 or args.n > 9:
        print("n 必须在 1 到 9 之间", file=sys.stderr)
        return 2
    if (args.width is None) ^ (args.height is None):
        print("width 和 height 必须同时提供", file=sys.stderr)
        return 2

    prefix = args.prefix or slugify(args.prompt)[:80]
    output_dir = Path(args.output_dir)
    payload = build_payload(args)
    response = post_json(payload)

    base_resp = response.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        print(
            json.dumps(
                {
                    "status_code": base_resp.get("status_code"),
                    "status_msg": base_resp.get("status_msg"),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 3

    data = response.get("data", {})
    records: List[Dict[str, str]]
    if args.response_format == "url":
        image_urls = data.get("image_urls", [])
        if not image_urls:
            print("接口未返回 image_urls", file=sys.stderr)
            return 4
        records = save_url_images(image_urls, output_dir, prefix)
    else:
        image_base64 = data.get("image_base64", [])
        if not image_base64:
            print("接口未返回 image_base64", file=sys.stderr)
            return 4
        records = save_base64_images(image_base64, output_dir, prefix)

    result = {
        "task_id": response.get("id"),
        "model": args.model,
        "prompt": args.prompt,
        "output_dir": str(output_dir),
        "response_format": args.response_format,
        "success_count": response.get("metadata", {}).get("success_count"),
        "failed_count": response.get("metadata", {}).get("failed_count"),
        "images": records,
    }

    if args.metadata_file:
        metadata_path = Path(args.metadata_file)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.print_each:
        for record in records:
            print(json.dumps(record, ensure_ascii=False))

    summary = {
        "task_id": result["task_id"],
        "model": result["model"],
        "saved": len(records),
        "output_dir": result["output_dir"],
        "metadata_file": args.metadata_file,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
