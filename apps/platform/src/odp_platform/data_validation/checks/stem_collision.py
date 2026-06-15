#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查同一 split 内是否存在同名但不同扩展名的图像文件（如 a.jpg 和 a.png），会导致标签归属歧义。"""
from __future__ import annotations

from collections import defaultdict
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

@check("stem_collision")
def check_stem_collision(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    collisions = []
    for split_name, image_paths in snap.images_per_split.items():
        stems = defaultdict(set)
        for img_path in image_paths:
            stems[img_path.stem.lower()].add(img_path.suffix.lower())
        for stem, exts in stems.items():
            if len(exts) > 1:
                collisions.append(f"{split_name}: {stem} 有多个扩展名 {exts}")
                if len(collisions) >= 10:
                    break
    if collisions:
        summary = f"发现 {len(collisions)} 组同名不同扩展名冲突，标签可能归属错误"
        severity = CheckSeverity.WARNING
    else:
        summary = "无同名异扩展冲突"
        severity = CheckSeverity.PASS
    return CheckResult(name="stem_collision", severity=severity, summary=summary, details={"conflicts": collisions})
