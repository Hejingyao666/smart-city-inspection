#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查边界框是否完全在图像内部（允许极小浮点误差）。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check
from PIL import Image

@check("bbox_within_image")
def check_bbox_within_image(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    out_of_bounds = 0
    total_boxes = 0
    samples: List[Dict] = []
    eps = 1e-6

    for split_name, image_paths in snap.images_per_split.items():
        label_paths = snap.labels_per_split.get(split_name, [])
        # 建立 stem -> image_path 映射
        img_by_stem = {p.stem: p for p in image_paths}
        for label_path in label_paths:
            stem = label_path.stem
            if stem not in img_by_stem:
                continue
            img_path = img_by_stem[stem]
            try:
                with Image.open(img_path) as img:
                    w_px, h_px = img.size
            except Exception:
                continue
            if not label_path.exists():
                continue
            try:
                lines = label_path.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for line_no, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    continue
                try:
                    x, y, w, h = map(float, parts[1:5])
                except ValueError:
                    continue
                total_boxes += 1
                # 将归一化坐标转为像素坐标
                x1_px = (x - w/2) * w_px
                y1_px = (y - h/2) * h_px
                x2_px = (x + w/2) * w_px
                y2_px = (y + h/2) * h_px
                if x1_px < -eps or y1_px < -eps or x2_px > w_px+eps or y2_px > h_px+eps:
                    out_of_bounds += 1
                    if len(samples) < 10:
                        samples.append({
                            "image": str(img_path),
                            "line": line_no,
                            "box": (x1_px, y1_px, x2_px, y2_px),
                            "img_size": (w_px, h_px),
                        })

    if out_of_bounds > 0:
        ratio = out_of_bounds / total_boxes if total_boxes else 0
        severity = CheckSeverity.ERROR if ratio >= 0.10 else CheckSeverity.WARNING
        summary = f"发现 {out_of_bounds}/{total_boxes} ({ratio:.2%}) 个框超出图像边界"
    else:
        severity = CheckSeverity.PASS
        summary = f"全部 {total_boxes} 个框均在图像内部"

    return CheckResult(
        name="bbox_within_image",
        severity=severity,
        summary=summary,
        details={"out_of_bounds": out_of_bounds, "total": total_boxes, "samples": samples},
    )
