#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查边界框几何合法性：退化框（w<=0或h<=0）和极端宽高比（>20或<0.05）。"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import List, Dict, Any

from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check
from odp_platform.common.constants import STATS_MAX_ASPECT_RATIO

@check("box_geometry")
def check_box_geometry(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    degenerate = 0
    extreme_aspect = 0
    total_boxes = 0
    details: List[Dict] = []

    for split_name, label_paths in snap.labels_per_split.items():
        for label_path in label_paths:
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
                if len(parts) != 5:  # detect 格式
                    continue
                try:
                    cls_id = int(parts[0])
                    x, y, w, h = map(float, parts[1:5])
                except ValueError:
                    continue
                total_boxes += 1
                if w <= 0 or h <= 0:
                    degenerate += 1
                    if len(details) < 20:
                        details.append({"label": str(label_path), "line": line_no, "type": "degenerate", "w": w, "h": h})
                else:
                    aspect = max(w, h) / min(w, h)
                    if aspect > STATS_MAX_ASPECT_RATIO:
                        extreme_aspect += 1
                        if len(details) < 20:
                            details.append({"label": str(label_path), "line": line_no, "type": "extreme_aspect", "aspect": aspect})

    if degenerate > 0 or extreme_aspect > 0:
        summary = f"发现 {degenerate} 个退化框, {extreme_aspect} 个极端宽高比框（阈值>{STATS_MAX_ASPECT_RATIO}）"
        severity = CheckSeverity.WARNING
    else:
        summary = f"全部 {total_boxes} 个边界框几何正常"
        severity = CheckSeverity.PASS

    return CheckResult(
        name="box_geometry",
        severity=severity,
        summary=summary,
        details={"degenerate": degenerate, "extreme_aspect": extreme_aspect, "samples": details[:10]},
    )
