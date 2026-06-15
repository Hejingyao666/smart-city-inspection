#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查 train/val/test 划分是否存在，且规模符合最低要求。"""
from __future__ import annotations

from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

@check("split_presence")
def check_split_presence(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    expected = ["train", "val", "test"]
    present = [s for s in expected if s in snap.images_per_split]
    missing = [s for s in expected if s not in present]
    if missing:
        return CheckResult(
            name="split_presence",
            severity=CheckSeverity.ERROR,
            summary=f"缺少必要划分: {missing}",
            details={"missing": missing},
        )
    issues = []
    for split_name in expected:
        img_count = len(snap.images_per_split.get(split_name, []))
        if split_name == "train" and img_count < 10:
            issues.append(f"train 图像数 {img_count} < 10")
        elif split_name in ("val", "test") and img_count < 30 and img_count > 0:
            issues.append(f"{split_name} 图像数 {img_count} < 30（建议增加）")
        elif img_count == 0:
            issues.append(f"{split_name} 无图像")
    if issues:
        summary = "划分规模问题: " + "; ".join(issues)
        severity = CheckSeverity.WARNING
    else:
        summary = "train/val/test 划分齐全且规模达标"
        severity = CheckSeverity.PASS
    return CheckResult(name="split_presence", severity=severity, summary=summary, details={"issues": issues})
