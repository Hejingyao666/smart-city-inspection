#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :yaml_schema.py
# @Time      :2026/6/10
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :验证数据集 yaml 文件的字段完整性和一致性（使用 snapshot）
from __future__ import annotations

from typing import List

from odp_platform.data_validation.registry import (
    check, CheckContext, CheckResult, CheckSeverity,
)


@check("yaml_schema")
def validate_yaml_schema(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot

    if snap.yaml_load_error is not None:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=snap.yaml_load_error,
            details={"reason": "yaml_load_error", "yaml_path": str(snap.yaml_path)},
        )

    problems: List[str] = []
    nc = snap.nc
    if nc is None or nc <= 0:
        problems.append(f"nc 缺失或不是正整数: {snap.yaml_data.get('nc')!r}")

    class_names = snap.class_names
    if not class_names:
        raw = snap.yaml_data.get("names")
        problems.append(f"names 缺失或不是合法 list[str]/dict[int,str]: {type(raw).__name__}")

    if nc is not None and class_names and len(class_names) != nc:
        problems.append(f"nc ({nc}) 与 names 长度 ({len(class_names)}) 不一致")

    if problems:
        return CheckResult(
            name="yaml_schema",
            severity=CheckSeverity.ERROR,
            summary=f"yaml 字段不一致: {len(problems)} 处问题",
            details={"problems": problems, "nc": nc, "names_count": len(class_names)},
        )

    return CheckResult(
        name="yaml_schema",
        severity=CheckSeverity.PASS,
        summary=f"yaml 字段一致 (nc={nc}, names_count={len(class_names)})",
        details={"nc": nc, "names_count": len(class_names)},
    )
