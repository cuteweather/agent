#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from contextlib import nullcontext
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test local SAM3.1 runtime.")
    parser.add_argument("--repo-dir", type=Path, required=True, help="Cloned facebookresearch/sam3 repo")
    parser.add_argument("--checkpoint", type=Path, required=True, help="Local checkpoint path")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for smoke-test artifacts")
    parser.add_argument("--input-image", type=Path, default=None, help="Optional image to test on")
    parser.add_argument("--prompt", default="object", help="Text prompt for smoke test")
    parser.add_argument("--confidence-threshold", type=float, default=0.2)
    parser.add_argument("--require-mask", action="store_true", help="Fail if the prompt returns no masks")
    return parser.parse_args()


def add_repo_to_path(repo_dir: Path) -> None:
    repo_dir = repo_dir.resolve()
    if not repo_dir.exists():
        raise FileNotFoundError(f"repo dir does not exist: {repo_dir}")
    sys.path.insert(0, str(repo_dir))


def make_synthetic_image(path: Path) -> Image.Image:
    image = Image.new("RGB", (960, 720), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    draw.rectangle((120, 160, 360, 520), fill=(220, 30, 30), outline=(20, 20, 20), width=6)
    draw.ellipse((520, 180, 820, 500), fill=(40, 120, 240), outline=(20, 20, 20), width=6)
    draw.text((120, 80), "SAM3.1 smoke test", fill=(20, 20, 20))
    image.save(path)
    return image


def build_overlay(image: Image.Image, masks: np.ndarray, boxes: np.ndarray, output_path: Path) -> None:
    canvas = image.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    mask_colors = [(255, 0, 255, 120), (0, 255, 255, 120), (0, 255, 120, 120), (255, 255, 0, 120)]
    box_colors = [(255, 255, 0, 255), (255, 0, 255, 255), (0, 255, 255, 255), (255, 128, 0, 255)]
    for idx, mask in enumerate(masks):
        mask_color = mask_colors[idx % len(mask_colors)]
        box_color = box_colors[idx % len(box_colors)]
        mask_2d = np.squeeze(mask)
        mask_alpha = Image.fromarray((mask_2d > 0).astype(np.uint8) * mask_color[3], mode="L")
        tint = Image.new("RGBA", canvas.size, mask_color)
        overlay = Image.composite(tint, overlay, mask_alpha)
        x0, y0, x1, y1 = [float(v) for v in boxes[idx]]
        draw.rectangle((x0, y0, x1, y1), outline=box_color[:3], width=6)
        draw.text((x0 + 8, max(0, y0 - 28)), f"top-{idx + 1}", fill=box_color[:3])
    Image.alpha_composite(canvas, overlay).save(output_path)


def save_box_crop(image: Image.Image, box: np.ndarray, output_path: Path) -> None:
    x0, y0, x1, y1 = [int(round(float(v))) for v in box]
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(image.width, x1)
    y1 = min(image.height, y1)
    if x1 <= x0 or y1 <= y0:
        return
    image.crop((x0, y0, x1, y1)).save(output_path)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    add_repo_to_path(args.repo_dir)

    import torch
    from sam3.model_builder import build_sam3_image_model
    from sam3.model.sam3_image_processor import Sam3Processor

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")

    input_path = args.input_image
    if input_path is None:
        input_path = args.output_dir / "synthetic_input.png"
        image = make_synthetic_image(input_path)
    else:
        image = Image.open(input_path).convert("RGB")

    model = build_sam3_image_model(
        checkpoint_path=str(args.checkpoint),
        load_from_HF=False,
        device=device,
        eval_mode=True,
        enable_segmentation=True,
    )
    processor = Sam3Processor(model, device=device, confidence_threshold=args.confidence_threshold)
    autocast_dtype = torch.bfloat16 if device == "cuda" and torch.cuda.is_bf16_supported() else torch.float16
    inference_context = (
        torch.autocast(device_type="cuda", dtype=autocast_dtype)
        if device == "cuda"
        else nullcontext()
    )
    with inference_context:
        state = processor.set_image(image)
        output = processor.set_text_prompt(prompt=args.prompt, state=state)

    # Some GPU paths return bfloat16; cast to float32 before numpy.
    masks = (output["masks"].float().detach().cpu().numpy() > 0).astype(np.uint8)
    boxes = output["boxes"].float().detach().cpu().numpy()
    scores = output["scores"].float().detach().cpu().numpy()

    # Always show the single highest-scoring match for the overlay.
    if len(scores) > 0:
        top_idx = int(np.argmax(scores))
        kept_masks = masks[[top_idx]]
        kept_boxes = boxes[[top_idx]]
        kept_scores = scores[[top_idx]]
    else:
        kept_masks = masks
        kept_boxes = boxes
        kept_scores = scores

    summary = {
        "device": device,
        "input_image": str(input_path),
        "prompt": args.prompt,
        "mask_count": int(len(kept_masks)),
        "scores": [float(v) for v in kept_scores.tolist()],
        "boxes": [[float(x) for x in row] for row in kept_boxes.tolist()],
    }
    (args.output_dir / "verify_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if len(kept_masks) > 0:
        build_overlay(image, kept_masks, kept_boxes, args.output_dir / "verify_overlay.png")
        save_box_crop(image, kept_boxes[0], args.output_dir / "verify_top1_crop.png")

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.require_mask and len(kept_masks) == 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
