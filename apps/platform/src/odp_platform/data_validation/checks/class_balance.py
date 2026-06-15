#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查每个 split 中的类别实例数失衡比例，超过阈值触发 INFO/WARNING。"""
from __future__ import annotations

from collections import Counter
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check
from odp_platform.common.constants import STATS_MAX_IMBALANCE_RATIO

@check("class_balance")
def check_class_balance(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    issues = []
    for split_name, label_paths in snap.labels_per_split.items():
        counter = Counter()
        for label_path in label_paths:
            if not label_path.exists():
                continue
            try:
                lines = label_path.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) == 0:
                    continue
                try:
                    cls_id = int(parts[0])
                    counter[cls_id] += 1
                except ValueError:
                    continue
        if not counter:
            continue
        max_count = max(counter.values())
        min_count = min(counter.values())
        imbalance = max_count / min_count if min_count > 0 else float('inf')
        if imbalance >= STATS_MAX_IMBALANCE_RATIO:
            issues.append(f"{split_name} 失衡比 {imbalance:.1f}x (≥{STATS_MAX_IMBALANCE_RATIO}x)")
    if issues:
        summary = "; ".join(issues) + "，建议使用 class_weight 或重采样"
        severity = CheckSeverity.INFO
    else:
        summary = "各 split 类别分布相对均衡"
        severity = CheckSeverity.PASS
    return CheckResult(name="class_balance", severity=severity, summary=summary, details={"issues": issues})
