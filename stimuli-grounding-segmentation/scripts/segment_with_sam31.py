#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

# Threshold sweep sequence for --retry-sweep mode (descending)
RETRY_SCORE_THRESHOLDS = [0.2, 0.1, 0.05, 0.01, 0.0]


def scan_disk_artifacts(output_root: Path, grounding_id: str, base_display: Path) -> dict[str, list[str]]:
    """Scan masks/, overlays/, examples/ for files matching *grounding_id* prefix.

    Returns dict with keys mask_paths, overlay_paths, example_paths — each a list
    of display-relative paths for files that already exist on disk.  Matches files
    whose stem starts with ``slugify(grounding_id)`` followed by ``__`` (the
    separator used by this script) or any version suffix like ``_v1__``, ``_v2__``.
    """
    slug = slugify(grounding_id)
    result: dict[str, list[str]] = {"mask_paths": [], "overlay_paths": [], "example_paths": []}
    dir_map = {
        "mask_paths": output_root / "masks",
        "overlay_paths": output_root / "overlays",
        "example_paths": output_root / "examples",
    }
    for key, directory in dir_map.items():
        if not directory.is_dir():
            continue
        for p in sorted(directory.iterdir()):
            stem = p.stem
            # Match exact id prefix (e.g. "exp1_foo__01") or versioned
            # variants (e.g. "exp1_foo_v2__01", "exp1_foo_scene__01").
            if stem.startswith(slug) and "__" in stem:
                result[key].append(rel_or_abs_display(p, base_display))
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SAM3.1 grounding over stimulus family requests.")
    parser.add_argument("--requests-file", type=Path, required=True, help="grounding_requests.json path")
    parser.add_argument("--output-root", type=Path, required=True, help="paper/grounding output dir")
    parser.add_argument("--repo-dir", type=Path, required=True, help="Cloned facebookresearch/sam3 repo")
    parser.add_argument("--checkpoint", type=Path, required=True, help="Local SAM3.1 checkpoint path")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--confidence-threshold", type=float, default=0.2)
    parser.add_argument("--score-threshold", type=float, default=0.2)
    parser.add_argument("--max-masks-per-family", type=int, default=8)
    parser.add_argument("--min-mask-area", type=int, default=256)
    parser.add_argument("--max-mask-area-ratio", type=float, default=0.92)
    parser.add_argument(
        "--ambiguity-mask-count",
        type=int,
        default=6,
        help="If accepted masks reach this count, mark the family as ambiguous",
    )
    parser.add_argument(
        "--retry-sweep",
        action="store_true",
        help="Auto-sweep thresholds and fallback prompts for no_match families. "
             "Forces confidence-threshold to 0.0 to maximise candidate retrieval.",
    )
    return parser.parse_args()


def add_repo_to_path(repo_dir: Path) -> None:
    repo_dir = repo_dir.resolve()
    if not repo_dir.exists():
        raise FileNotFoundError(f"repo dir does not exist: {repo_dir}")
    sys.path.insert(0, str(repo_dir))


def load_requests(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        families = raw
    elif isinstance(raw, dict) and isinstance(raw.get("families"), list):
        families = raw["families"]
    else:
        raise ValueError("requests file must be a list or an object with a 'families' list")
    return [dict(item) for item in families]


def slugify(text: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z._-]+", "_", text.strip()).strip("_")
    return slug or "grounding"


def rel_or_abs_display(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path.resolve())


def resolve_source_path(source_path: Any, base_dir: Path) -> Path | None:
    if source_path in (None, "", False):
        return None
    candidate = Path(str(source_path))
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()
    return candidate


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def build_prompt_text(record: dict[str, Any]) -> str:
    description = " ".join(str(record.get("description", "")).split())
    must_preserve = [str(item).strip() for item in ensure_list(record.get("must_preserve")) if str(item).strip()]
    if not description:
        return ""
    if not must_preserve:
        return description[:240]
    preserve_text = "; ".join(must_preserve[:3])
    prompt = f"{description} Must preserve: {preserve_text}."
    return prompt[:320]


def to_numpy_mask(mask_tensor: Any) -> np.ndarray:
    # Some GPU paths return bfloat16; cast to float32 before numpy.
    mask = mask_tensor.float().detach().cpu().numpy()
    mask = np.asarray(mask)
    if mask.ndim == 3:
        mask = mask[0]
    return (mask > 0).astype(np.uint8)


def box_to_list(box_tensor: Any) -> list[float]:
    # Some GPU paths return bfloat16; cast to float32 before numpy.
    box = box_tensor.float().detach().cpu().numpy().tolist()
    return [float(v) for v in box]


def save_mask(mask: np.ndarray, path: Path) -> None:
    Image.fromarray(mask.astype(np.uint8) * 255, mode="L").save(path)


def compute_crop_bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("mask is empty")
    x0 = int(xs.min())
    y0 = int(ys.min())
    x1 = int(xs.max()) + 1
    y1 = int(ys.max()) + 1
    return x0, y0, x1, y1


def save_example(image: Image.Image, mask: np.ndarray, path: Path) -> None:
    x0, y0, x1, y1 = compute_crop_bbox(mask)
    image_rgba = image.convert("RGBA")
    alpha = Image.fromarray(mask.astype(np.uint8) * 255, mode="L")
    image_rgba.putalpha(alpha)
    cropped = image_rgba.crop((x0, y0, x1, y1))
    cropped.save(path)


def save_overlay(image: Image.Image, mask: np.ndarray, box_xyxy: list[float], path: Path) -> None:
    canvas = image.convert("RGBA")
    alpha = Image.fromarray(mask.astype(np.uint8) * 120, mode="L")
    tint = Image.new("RGBA", canvas.size, (255, 60, 60, 120))
    overlay = Image.composite(tint, Image.new("RGBA", canvas.size, (0, 0, 0, 0)), alpha)
    merged = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(merged)
    x0, y0, x1, y1 = box_xyxy
    draw.rectangle((x0, y0, x1, y1), outline=(255, 220, 40, 255), width=3)
    merged.save(path)


@dataclass
class Candidate:
    score: float
    box_xyxy: list[float]
    mask: np.ndarray
    mask_area: int


def select_candidates(
    output: dict[str, Any],
    score_threshold: float,
    min_mask_area: int,
    max_mask_area_ratio: float,
    max_masks_per_family: int,
) -> tuple[list[Candidate], list[dict[str, Any]], str | None]:
    masks = output["masks"]
    boxes = output["boxes"]
    scores = output["scores"]
    selected: list[Candidate] = []
    searched_regions: list[dict[str, Any]] = []
    image_area = int(masks.shape[-2] * masks.shape[-1])
    rejected_reason = None

    ranked = sorted(
        range(int(scores.shape[0])),
        key=lambda idx: float(scores[idx].float().detach().cpu().item()),
        reverse=True,
    )

    for idx in ranked:
        score = float(scores[idx].float().detach().cpu().item())
        mask = to_numpy_mask(masks[idx])
        mask_area = int(mask.sum())
        box_xyxy = box_to_list(boxes[idx])
        searched_regions.append(
            {
                "kind": "predicted_box",
                "box_xyxy": box_xyxy,
                "score": score,
                "mask_area": mask_area,
            }
        )
        if score < score_threshold:
            rejected_reason = "no_mask_above_threshold"
            continue
        if mask_area < min_mask_area:
            rejected_reason = "all_masks_filtered_by_area"
            continue
        if mask_area > int(image_area * max_mask_area_ratio):
            rejected_reason = "all_masks_filtered_by_area"
            continue
        selected.append(Candidate(score=score, box_xyxy=box_xyxy, mask=mask, mask_area=mask_area))
        if len(selected) >= max_masks_per_family:
            break

    return selected, searched_regions, rejected_reason


def main() -> int:
    args = parse_args()
    # When retry-sweep is on, force confidence_threshold to 0.0 so the model
    # returns ALL candidates; filtering happens solely via score_threshold.
    if args.retry_sweep:
        args.confidence_threshold = 0.0

    args.output_root.mkdir(parents=True, exist_ok=True)
    masks_dir = args.output_root / "masks"
    overlays_dir = args.output_root / "overlays"
    examples_dir = args.output_root / "examples"
    masks_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    families = load_requests(args.requests_file)
    request_base = args.requests_file.parent

    processor = None

    def get_processor():
        nonlocal processor
        if processor is not None:
            return processor

        add_repo_to_path(args.repo_dir)
        import torch
        from sam3.model_builder import build_sam3_image_model
        from sam3.model.sam3_image_processor import Sam3Processor

        device = args.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")

        model = build_sam3_image_model(
            checkpoint_path=str(args.checkpoint),
            load_from_HF=False,
            device=device,
            eval_mode=True,
            enable_segmentation=True,
        )
        processor = Sam3Processor(model, device=device, confidence_threshold=args.confidence_threshold)
        return processor

    base_display = args.output_root.parent.parent if len(args.output_root.parts) >= 2 else Path.cwd()
    grounding_index: list[dict[str, Any]] = []

    for record in families:
        grounding_id = str(record.get("grounding_id") or slugify(str(record.get("stimulus_family", "grounding"))))
        stimulus_family = str(record.get("stimulus_family", ""))
        prompt_text = build_prompt_text(record)
        source_path_value = record.get("source_path")
        source_path = resolve_source_path(source_path_value, request_base)
        source_exists = bool(source_path and source_path.exists())

        reference_priority = "figure_then_text" if source_path_value else "text_only"
        missing_fields = [
            field
            for field in ["description", "must_preserve"]
            if not record.get(field)
        ]
        if source_path_value and not record.get("figure_locator"):
            missing_fields.append("figure_locator")

        mask_paths: list[str] = []
        overlay_paths: list[str] = []
        example_paths: list[str] = []
        searched_regions: list[dict[str, Any]] = []
        no_match_reason: str | None = None
        match_status = "no_match"
        retry_attempts_log: list[dict[str, Any]] = []

        if missing_fields:
            no_match_reason = f"missing_required_fields:{','.join(missing_fields)}"
        elif not prompt_text:
            no_match_reason = "missing_required_fields:description,must_preserve"
        elif not source_path_value:
            no_match_reason = "missing_source_image"
        elif not source_exists:
            no_match_reason = "missing_source_image"
        else:
            image = Image.open(source_path).convert("RGB")
            try:
                processor_instance = get_processor()
                import torch

                autocast_dtype = (
                    torch.bfloat16
                    if processor_instance.device == "cuda" and torch.cuda.is_bf16_supported()
                    else torch.float16
                )
                inference_context = (
                    torch.autocast(device_type="cuda", dtype=autocast_dtype)
                    if processor_instance.device == "cuda"
                    else nullcontext()
                )
                with inference_context:
                    state = processor_instance.set_image(image)
                    output = processor_instance.set_text_prompt(prompt=prompt_text, state=state)
                selected, searched_regions, rejected_reason = select_candidates(
                    output=output,
                    score_threshold=args.score_threshold,
                    min_mask_area=args.min_mask_area,
                    max_mask_area_ratio=args.max_mask_area_ratio,
                    max_masks_per_family=args.max_masks_per_family,
                )

                # ── retry-sweep: threshold sweep + fallback prompts ──
                if not selected and args.retry_sweep:
                    # Phase 1: sweep score_threshold with the original prompt
                    for st in RETRY_SCORE_THRESHOLDS:
                        if st >= args.score_threshold:
                            continue  # already tried at this or higher threshold
                        re_selected, re_searched, re_reason = select_candidates(
                            output=output,
                            score_threshold=st,
                            min_mask_area=args.min_mask_area,
                            max_mask_area_ratio=args.max_mask_area_ratio,
                            max_masks_per_family=args.max_masks_per_family,
                        )
                        retry_attempts_log.append({
                            "phase": "threshold_sweep",
                            "prompt": prompt_text,
                            "score_threshold": st,
                            "candidates_found": len(re_selected),
                            "searched_count": len(re_searched),
                        })
                        if re_selected:
                            selected = re_selected
                            searched_regions = re_searched
                            rejected_reason = None
                            break

                    # Phase 2: try fallback_prompts with full threshold sweep
                    if not selected:
                        fallback_prompts = ensure_list(record.get("fallback_prompts"))
                        for fp in fallback_prompts:
                            if not fp or not str(fp).strip():
                                continue
                            fp_str = str(fp).strip()
                            with inference_context:
                                fb_output = processor_instance.set_text_prompt(prompt=fp_str, state=state)
                            for st in RETRY_SCORE_THRESHOLDS:
                                re_selected, re_searched, re_reason = select_candidates(
                                    output=fb_output,
                                    score_threshold=st,
                                    min_mask_area=args.min_mask_area,
                                    max_mask_area_ratio=args.max_mask_area_ratio,
                                    max_masks_per_family=args.max_masks_per_family,
                                )
                                retry_attempts_log.append({
                                    "phase": "fallback_prompt",
                                    "prompt": fp_str,
                                    "score_threshold": st,
                                    "candidates_found": len(re_selected),
                                    "searched_count": len(re_searched),
                                })
                                if re_selected:
                                    selected = re_selected
                                    searched_regions = re_searched
                                    rejected_reason = None
                                    prompt_text = fp_str
                                    break
                            if selected:
                                break

                if selected:
                    for idx, candidate in enumerate(selected, start=1):
                        stem = f"{slugify(grounding_id)}__{idx:02d}"
                        mask_path = masks_dir / f"{stem}.png"
                        overlay_path = overlays_dir / f"{stem}.png"
                        example_path = examples_dir / f"{stem}.png"
                        save_mask(candidate.mask, mask_path)
                        save_overlay(image, candidate.mask, candidate.box_xyxy, overlay_path)
                        save_example(image, candidate.mask, example_path)
                        mask_paths.append(rel_or_abs_display(mask_path, base_display))
                        overlay_paths.append(rel_or_abs_display(overlay_path, base_display))
                        example_paths.append(rel_or_abs_display(example_path, base_display))
                    match_status = "matched"
                    if len(selected) >= args.ambiguity_mask_count:
                        match_status = "ambiguous"
                else:
                    no_match_reason = rejected_reason or "no_mask_above_threshold"
            except Exception as exc:
                no_match_reason = f"model_runtime_error:{exc}"

        if match_status in {"matched", "ambiguous"} and mask_paths:
            effective_reference_basis = "crop_and_text"
        elif source_path_value:
            effective_reference_basis = "figure_and_text"
        else:
            effective_reference_basis = "text_only"

        grounding_index.append(
            {
                "grounding_id": grounding_id,
                "stimulus_family": stimulus_family,
                "source_path": str(source_path_value) if source_path_value is not None else None,
                "figure_locator": record.get("figure_locator"),
                "experiment_ids": ensure_list(record.get("experiment_ids")),
                "phase_ids": ensure_list(record.get("phase_ids")),
                "condition_scope": record.get("condition_scope", []),
                "prompt_text": prompt_text,
                "description": record.get("description", ""),
                "must_preserve": ensure_list(record.get("must_preserve")),
                "allowed_variation": ensure_list(record.get("allowed_variation")),
                "reference_priority": reference_priority,
                "effective_reference_basis": effective_reference_basis,
                "reference_role": record.get("reference_role"),
                "non_exhaustive": bool(record.get("non_exhaustive", True)),
                "match_status": match_status,
                "mask_paths": mask_paths,
                "example_paths": example_paths,
                "overlay_paths": overlay_paths,
                "searched_regions": searched_regions,
                "no_match_reason": no_match_reason,
                "retry_attempts": retry_attempts_log if source_exists else [],
            }
        )

    index_path = args.output_root / "grounding_index.json"

    # ── Merge with existing index: preserve families not in current request set ──
    existing_index: list[dict[str, Any]] = []
    if index_path.exists():
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                existing_index = raw
            elif isinstance(raw, dict) and isinstance(raw.get("families"), list):
                existing_index = raw["families"]
        except Exception:
            pass  # corrupt file — will be overwritten

    current_ids = {r["grounding_id"] for r in grounding_index}
    for old_record in existing_index:
        old_id = old_record.get("grounding_id")
        if old_id and old_id not in current_ids:
            grounding_index.append(old_record)

    # ── Disk artifact reconciliation ──
    # For every family that ended up as no_match, check if there are files on
    # disk that belong to it (from a prior run).  If so, upgrade the record so
    # the index reflects reality.
    for record in grounding_index:
        if record["match_status"] != "no_match":
            continue
        gid = record["grounding_id"]
        disk = scan_disk_artifacts(args.output_root, gid, base_display)
        if disk["mask_paths"] or disk["example_paths"] or disk["overlay_paths"]:
            # Merge: keep existing + add newly discovered
            existing_masks = set(record.get("mask_paths") or [])
            existing_examples = set(record.get("example_paths") or [])
            existing_overlays = set(record.get("overlay_paths") or [])
            merged_masks = sorted(existing_masks | set(disk["mask_paths"]))
            merged_examples = sorted(existing_examples | set(disk["example_paths"]))
            merged_overlays = sorted(existing_overlays | set(disk["overlay_paths"]))
            if merged_masks or merged_examples or merged_overlays:
                record["mask_paths"] = merged_masks
                record["example_paths"] = merged_examples
                record["overlay_paths"] = merged_overlays
                record["match_status"] = "matched"
                record["effective_reference_basis"] = "crop_and_text"
                record["no_match_reason"] = None
                if not record.get("_disk_reconciled"):
                    record["_disk_reconciled"] = True

    index_path.write_text(json.dumps(grounding_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"grounding_index": str(index_path), "families": len(grounding_index)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
