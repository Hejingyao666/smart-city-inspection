#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查无标注图像占比。"""
from __future__ import annotations

from pathlib import Path
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

@check("annotation_coverage")
def check_annotation_coverage(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    total_images = 0
    images_without_ann = 0

    for split_name, image_paths in snap.images_per_split.items():
        label_paths = snap.labels_per_split.get(split_name, [])
        label_stems = {p.stem for p in label_paths}
        for img_path in image_paths:
            total_images += 1
            if img_path.stem not in label_stems:
                images_without_ann += 1

    ratio = images_without_ann / total_images if total_images else 0
    if ratio >= 0.30:
        severity = CheckSeverity.WARNING
        summary = f"无标注图像占比 {ratio:.2%} (>=30%)，建议检查数据完整性"
    elif ratio >= 0.05:
        severity = CheckSeverity.INFO
        summary = f"无标注图像占比 {ratio:.2%} (>=5%)，可接受但需留意"
    else:
        severity = CheckSeverity.PASS
        summary = f"无标注图像占比 {ratio:.2%}，标注覆盖良好"

    return CheckResult(
        name="annotation_coverage",
        severity=severity,
        summary=summary,
        details={"ratio": ratio, "without_ann": images_without_ann, "total": total_images},
    )
