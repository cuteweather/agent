#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_KEY_ENV = "PEXELS_API_KEY"
BASE_URL = "https://api.pexels.com/v1/search"
BLOCKED_TOKENS = ("placeholder", "dummy", "via.placeholder.com", "placehold.co")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "query"


def fetch_photos(params: Dict[str, str]) -> List[Dict]:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Missing required environment variable: {API_KEY_ENV}")

    query = urlencode(params)
    req = Request(
        f"{BASE_URL}?{query}",
        headers={
            "Authorization": api_key,
            "Accept": "application/json",
            "User-Agent": "curl/8.0",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        raise RuntimeError(f"Pexels API 请求失败: HTTP {e.code} {e.reason}; {body}") from e
    return data.get("photos", [])


def pick_image_url(photo: Dict) -> Optional[str]:
    src = photo.get("src", {})
    image_url = src.get("large2x") or src.get("original")
    if not image_url:
        return None
    lower = image_url.lower()
    if any(token in lower for token in BLOCKED_TOKENS):
        return None
    return image_url


def download_image(image_url: str, file_path: Path) -> None:
    req = Request(
        image_url,
        headers={
            "User-Agent": "curl/8.0",
            "Referer": "https://www.pexels.com/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
        method="GET",
    )
    with urlopen(req, timeout=30) as resp:
        file_path.write_bytes(resp.read())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search and download real photos from Pexels (no placeholders)."
    )
    parser.add_argument("--query", required=True, help="Search query, e.g. landscape")
    parser.add_argument("--output-dir", required=True, help="Directory to save images")
    parser.add_argument("--limit", type=int, default=1, help="Number of images to download")
    parser.add_argument(
        "--per-page",
        type=int,
        default=80,
        help="Pexels page size per request (1-80). Script auto-paginates.",
    )
    parser.add_argument("--orientation", choices=["landscape", "portrait", "square"])
    parser.add_argument("--size", choices=["large", "medium", "small"])
    parser.add_argument("--color")
    parser.add_argument("--locale")
    parser.add_argument(
        "--prefix",
        default=None,
        help="Filename prefix (default: slugified query)",
    )
    parser.add_argument(
        "--metadata-file",
        default=None,
        help="Optional output metadata jsonl path",
    )
    parser.add_argument(
        "--print-each",
        action="store_true",
        help="Print one JSON line for each downloaded image (default: only summary).",
    )
    args = parser.parse_args()

    if args.limit <= 0:
        print("limit 必须大于 0", file=sys.stderr)
        return 2
    if args.per_page < 1 or args.per_page > 80:
        print("per-page 必须在 1 到 80 之间", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.prefix or slugify(args.query)

    per_page = int(args.per_page)
    current_page = 1
    seen = set()
    saved = 0
    records = []
    while saved < args.limit:
        params: Dict[str, str] = {
            "query": args.query,
            "per_page": str(per_page),
            "page": str(current_page),
        }
        if args.orientation:
            params["orientation"] = args.orientation
        if args.size:
            params["size"] = args.size
        if args.color:
            params["color"] = args.color
        if args.locale:
            params["locale"] = args.locale

        photos = fetch_photos(params)
        if not photos:
            break

        for photo in photos:
            pid = photo.get("id")
            if pid in seen:
                continue
            seen.add(pid)

            image_url = pick_image_url(photo)
            if not image_url:
                continue

            saved += 1
            file_name = f"{prefix}_{saved:03d}_{pid}.jpg"
            file_path = output_dir / file_name
            download_image(image_url, file_path)

            record = {
                "file": str(file_path),
                "id": pid,
                "photographer": photo.get("photographer"),
                "url": photo.get("url"),
                "image_url": image_url,
            }
            records.append(record)
            if args.print_each:
                print(json.dumps(record, ensure_ascii=False))

            if saved >= args.limit:
                break

        # Reached the last page returned by API.
        if len(photos) < per_page:
            break
        current_page += 1

    if saved == 0:
        print("未下载到任何合规真实图片（已过滤占位符链接）", file=sys.stderr)
        return 4

    if args.metadata_file:
        metadata_path = Path(args.metadata_file)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with metadata_path.open("w", encoding="utf-8") as f:
            for row in records:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "query": args.query,
        "saved": saved,
        "requested_limit": args.limit,
        "end_page": current_page,
        "output_dir": str(output_dir),
        "metadata_file": args.metadata_file,
    }
    print(json.dumps(summary, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
