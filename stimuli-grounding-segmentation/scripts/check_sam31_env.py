#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any


REQUIRED_MODULES = [
    "numpy",
    "PIL",
    "torch",
    "torchvision",
    "timm",
    "ftfy",
    "iopath",
    "huggingface_hub",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether the SAM3.1 runtime is ready.")
    parser.add_argument("--repo-dir", type=Path, default=None, help="Path to cloned facebookresearch/sam3 repo")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Path to sam3.1 checkpoint")
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda"],
        default="auto",
        help="Required runtime device",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Optional path to save JSON report",
    )
    return parser.parse_args()


def add_repo_to_path(repo_dir: Path | None) -> None:
    if repo_dir is None:
        return
    repo_dir = repo_dir.resolve()
    if repo_dir.is_dir():
        sys.path.insert(0, str(repo_dir))


def check_module(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def main() -> int:
    args = parse_args()
    add_repo_to_path(args.repo_dir)

    report: dict[str, Any] = {
        "python": {
            "version": sys.version.split()[0],
            "ok": sys.version_info >= (3, 12),
            "platform": platform.platform(),
        },
        "commands": {name: shutil.which(name) for name in ["git", "git-lfs", "nvidia-smi", "xvfb-run"]},
        "modules": {},
        "repo": None,
        "checkpoint": None,
        "device": None,
        "ready": False,
    }

    for name in REQUIRED_MODULES:
        report["modules"][name] = check_module(name)

    report["modules"]["sam3"] = check_module("sam3")

    torch_status = report["modules"].get("torch", {})
    cuda_available = False
    cuda_version = None
    device_count = None
    if torch_status.get("ok"):
        import torch

        cuda_available = bool(torch.cuda.is_available())
        cuda_version = torch.version.cuda
        device_count = torch.cuda.device_count() if cuda_available else 0

    requested_device = args.device
    if requested_device == "auto":
        requested_device = "cuda" if cuda_available else "cpu"

    report["device"] = {
        "requested": args.device,
        "resolved": requested_device,
        "cuda_available": cuda_available,
        "cuda_version": cuda_version,
        "cuda_device_count": device_count,
        "libcuda_visible": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }

    if args.repo_dir is not None:
        report["repo"] = {
            "path": str(args.repo_dir),
            "exists": args.repo_dir.exists(),
            "has_pyproject": (args.repo_dir / "pyproject.toml").exists(),
            "has_model_builder": (args.repo_dir / "sam3" / "model_builder.py").exists(),
        }

    if args.checkpoint is not None:
        exists = args.checkpoint.exists()
        report["checkpoint"] = {
            "path": str(args.checkpoint),
            "exists": exists,
            "size_bytes": args.checkpoint.stat().st_size if exists else None,
        }

    missing_modules = [name for name, status in report["modules"].items() if not status.get("ok")]
    missing_repo = args.repo_dir is not None and not report["repo"]["exists"]
    missing_checkpoint = args.checkpoint is not None and not report["checkpoint"]["exists"]
    cuda_blocked = requested_device == "cuda" and not cuda_available

    report["ready"] = not any(
        [
            not report["python"]["ok"],
            bool(missing_modules),
            missing_repo,
            missing_checkpoint,
            cuda_blocked,
        ]
    )
    report["missing_modules"] = missing_modules

    payload = json.dumps(report, ensure_ascii=False, indent=2)
    print(payload)
    if args.json_out is not None:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload + "\n", encoding="utf-8")

    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
