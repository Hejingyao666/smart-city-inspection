#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查是否存在标签文件但无对应图像（孤儿标签）。"""
from __future__ import annotations

from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

@check("orphan_labels")
def check_orphan_labels(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    orphan_count = 0
    total_label_files = 0
    samples = []

    for split_name, label_paths in snap.labels_per_split.items():
        image_stems = {p.stem for p in snap.images_per_split.get(split_name, [])}
        for label_path in label_paths:
            total_label_files += 1
            if label_path.stem not in image_stems:
                orphan_count += 1
                if len(samples) < 10:
                    samples.append(str(label_path))

    if orphan_count > 0:
        ratio = orphan_count / total_label_files if total_label_files else 0
        severity = CheckSeverity.WARNING if ratio >= 0.10 else CheckSeverity.INFO
        summary = f"发现 {orphan_count}/{total_label_files} ({ratio:.2%}) 个孤儿标签文件（无对应图像）"
    else:
        severity = CheckSeverity.PASS
        summary = "所有标签文件都有对应的图像文件"

    return CheckResult(
        name="orphan_labels",
        severity=severity,
        summary=summary,
        details={"orphan_count": orphan_count, "total_label_files": total_label_files, "samples": samples},
    )
