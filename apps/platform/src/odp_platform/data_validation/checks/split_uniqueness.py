#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :split_uniqueness.py
# @Time      :2026/6/10
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :检查 train/val/test 之间是否有图像名重复（数据泄露）
from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, List

from odp_platform.data_validation.registry import (
    check, CheckContext, CheckResult, CheckSeverity,
)

PREVIEW_LIMIT = 20


@check("split_uniqueness")
def validate_split_uniqueness(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot

    if len(snap.images_per_split) < 2:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.PASS,
            summary=f"少于 2 个 split，跳过判重 (当前 splits: {list(snap.splits)})",
            details={"reason": "fewer_than_2_splits"},
        )

    stems_by_split = {
        split: {img.stem for img in images}
        for split, images in snap.images_per_split.items()
    }

    overlaps: List[Dict[str, Any]] = []
    for s1, s2 in combinations(stems_by_split.keys(), 2):
        common = stems_by_split[s1] & stems_by_split[s2]
        if common:
            stems_sorted = sorted(common)
            overlaps.append({
                "split_a": s1,
                "split_b": s2,
                "count": len(common),
                "preview": stems_sorted[:PREVIEW_LIMIT],
            })

    if not overlaps:
        return CheckResult(
            name="split_uniqueness",
            severity=CheckSeverity.PASS,
            summary=f"{len(snap.splits)} 个 split ({' / '.join(snap.splits)}) 之间无图像名重复",
            details={"splits": list(snap.splits)},
        )

    total_dup = sum(o["count"] for o in overlaps)
    pairs_str = ", ".join(f"{o['split_a']}↔{o['split_b']}({o['count']})" for o in overlaps)
    return CheckResult(
        name="split_uniqueness",
        severity=CheckSeverity.ERROR,
        summary=f"split 间有 {total_dup} 张图像名重复 — 数据泄露! [{pairs_str}]",
        details={
            "reason": "splits_overlap",
            "splits": list(snap.splits),
            "total_duplicates": total_dup,
            "overlaps": overlaps,
        },
    )
