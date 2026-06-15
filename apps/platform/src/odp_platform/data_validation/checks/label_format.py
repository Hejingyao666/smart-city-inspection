#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :label_format.py
# @Time      :2026/6/10
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :验证每行标签格式是否正确
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from odp_platform.common.constants import Task
from odp_platform.data_validation.registry import (
    check, CheckContext, CheckResult, CheckSeverity,
)

PREVIEW_LIMIT = 20


@check("label_format")
def validate_label_format(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot

    if snap.nc is None or snap.nc <= 0:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.INFO,
            summary="缺少合法 nc，跳过 label_format",
            details={"reason": "nc_unavailable"},
        )

    task_type = snap.task_type
    errors: List[Dict[str, Any]] = []
    error_kinds = Counter()
    total_lines = 0

    for split, labels in snap.labels_per_split.items():
        for lbl in labels:
            if not lbl.exists():
                continue
            try:
                content = lbl.read_text(encoding="utf-8")
            except OSError:
                continue
            for line_no, line in enumerate(content.splitlines(), 1):
                line = line.strip()
                if not line:
                    continue
                total_lines += 1
                err = _validate_one_line(line, task_type, snap.nc)
                if err is not None:
                    kind, detail = err
                    error_kinds[kind] += 1
                    if len(errors) < PREVIEW_LIMIT:
                        errors.append({
                            "label": str(lbl),
                            "line_no": line_no,
                            "kind": kind,
                            "detail": detail,
                        })

    if not error_kinds:
        return CheckResult(
            name="label_format",
            severity=CheckSeverity.PASS,
            summary=f"全部 {total_lines} 行标签格式正确 (task={task_type})",
            details={"task_type": task_type, "total_lines": total_lines},
        )

    total_errors = sum(error_kinds.values())
    return CheckResult(
        name="label_format",
        severity=CheckSeverity.ERROR,
        summary=f"{total_errors}/{total_lines} 行标签格式错误 (task={task_type})",
        details={
            "task_type": task_type,
            "total_lines": total_lines,
            "total_errors": total_errors,
            "error_kinds": dict(error_kinds),
            "errors_preview": errors,
        },
    )


def _validate_one_line(line: str, task_type: str, nc: int):
    parts = line.split()

    if task_type == Task.DETECT:
        if len(parts) != 5:
            return "field_count_mismatch", f"detect 需要 5 字段，实际 {len(parts)}"
        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:5]]
        except ValueError as e:
            return "parse_error", f"字段类型错误: {e}"
        if not (0 <= cls_id < nc):
            return "class_id_out_of_range", f"cls_id={cls_id} 不在 [0,{nc})"
        if not all(0.0 <= c <= 1.0 for c in coords):
            return "coord_out_of_range", f"坐标越界 [0,1]: {coords}"
        return None

    if task_type == Task.SEGMENT:
        if len(parts) < 7 or (len(parts) - 1) % 2 != 0:
            if len(parts) < 7:
                return "polygon_too_few", f"segment 需要至少 3 个点 (7 字段)，实际 {len(parts)}"
            return "field_count_mismatch", f"segment 字段数应为 1+2N，实际 {len(parts)}"
        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:]]
        except ValueError as e:
            return "parse_error", f"字段类型错误: {e}"
        if not (0 <= cls_id < nc):
            return "class_id_out_of_range", f"cls_id={cls_id} 不在 [0,{nc})"
        if not all(0.0 <= c <= 1.0 for c in coords):
            return "coord_out_of_range", f"坐标越界 [0,1]"
        return None

    return "unknown_task", f"未知 task_type: {task_type}"
