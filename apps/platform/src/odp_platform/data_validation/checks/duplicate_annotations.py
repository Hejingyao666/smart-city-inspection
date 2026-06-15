#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检测完全相同的重复标注行，以及空间上高度重叠（IoU≥0.95）的近似重复。"""
from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

def iou(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    a1 = w1 * h1
    a2 = w2 * h2
    inter_w = max(0, min(x1+w1/2, x2+w2/2) - max(x1-w1/2, x2-w2/2))
    inter_h = max(0, min(y1+h1/2, y2+h2/2) - max(y1-h1/2, y2-h2/2))
    inter = inter_w * inter_h
    return inter / (a1 + a2 - inter) if (a1 + a2 - inter) > 0 else 0.0

@check("duplicate_annotations")
def check_duplicate_annotations(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    exact_dups = 0
    near_dups = 0
    total_boxes = 0

    for split_name, label_paths in snap.labels_per_split.items():
        for label_path in label_paths:
            if not label_path.exists():
                continue
            try:
                lines = label_path.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            boxes = []  # (cls_id, x, y, w, h)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    continue
                try:
                    cls_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                except ValueError:
                    continue
                boxes.append((cls_id, x, y, w, h))
                total_boxes += 1
            # 精确重复
            seen = set()
            for cls_id, x, y, w, h in boxes:
                key = (cls_id, round(x, 6), round(y, 6), round(w, 6), round(h, 6))
                if key in seen:
                    exact_dups += 1
                seen.add(key)
            # 近似重复 IoU>=0.95 且类别相同
            for i in range(len(boxes)):
                for j in range(i+1, len(boxes)):
                    if boxes[i][0] == boxes[j][0]:
                        if iou(boxes[i][1:5], boxes[j][1:5]) >= 0.95:
                            near_dups += 1

    if exact_dups > 0 or near_dups > 0:
        summary = f"发现 {exact_dups} 个精确重复框, {near_dups} 对近似重复框 (IoU≥0.95)"
        severity = CheckSeverity.WARNING
    else:
        summary = f"无重复标注 (共检查 {total_boxes} 个框)"
        severity = CheckSeverity.PASS
    return CheckResult(name="duplicate_annotations", severity=severity, summary=summary,
                       details={"exact_duplicates": exact_dups, "near_duplicates": near_dups})
