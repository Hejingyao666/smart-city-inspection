#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查类别在训练/验证/测试集中是否都有出现，发现只在 val/test 中出现而未在 train 中出现的类别。"""
from __future__ import annotations

from collections import Counter
from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

@check("class_presence")
def check_class_presence(ctx: CheckContext) -> CheckResult:
    snap = ctx.snapshot
    class_names = snap.class_names
    class_ids = set(range(len(class_names)))

    def get_classes_for_split(split_name):
        classes = set()
        label_paths = snap.labels_per_split.get(split_name, [])
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
                    classes.add(cls_id)
                except ValueError:
                    continue
        return classes

    present = {}
    for split_name in snap.images_per_split.keys():
        present[split_name] = get_classes_for_split(split_name)

    missing_in_train = []
    for split_name in ["val", "test"]:
        if split_name in present:
            missing = present[split_name] - present.get("train", set())
            if missing:
                missing_in_train.extend([class_names[i] for i in missing])

    dead_classes = present.get("train", set()) - (present.get("val", set()) | present.get("test", set()))
    dead_names = [class_names[i] for i in dead_classes]

    issues = []
    if missing_in_train:
        issues.append(f"验证/测试集中出现但训练集缺失的类别: {list(set(missing_in_train))}")
    if dead_names:
        issues.append(f"仅在训练集出现（无验证/测试）的类别: {dead_names}")

    if issues:
        summary = "; ".join(issues)
        severity = CheckSeverity.WARNING
    else:
        summary = "类别在 train/val/test 中分布一致，无缺失或死类"
        severity = CheckSeverity.PASS
    return CheckResult(name="class_presence", severity=severity, summary=summary, details={"issues": issues})
