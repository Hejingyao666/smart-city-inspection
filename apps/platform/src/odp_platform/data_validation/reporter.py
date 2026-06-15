"""验证报告输出: 汇总打印数据集统计 + 各 check 结果。"""
from __future__ import annotations

import logging
from typing import Dict, Any

from odp_platform.data_validation.models import ValidationReport, Severity

logger = logging.getLogger(__name__)


def print_report(report: ValidationReport) -> None:
    """打印人类可读的验证报告。"""
    print("\n" + "=" * 60)
    print("  DATA VALIDATION REPORT")
    print("=" * 60)

    # 汇总数据集统计 (从各 check 的 details 中提取)
    all_details: Dict[str, Any] = {}
    for r in report.results:
        all_details.update(r.details)

    if all_details:
        print("\n[Dataset Info]")
        for key in ("nc", "names_count", "images_total", "images_train", "images_val", "images_test"):
            if key in all_details:
                print(f"  {key}: {all_details[key]}")

    # 各 check 结果
    print("\n[Check Results]")
    for r in report.results:
        icon = "PASS" if r.passed else "FAIL"
        sev = r.severity.value.upper()
        print(f"  [{icon}] {r.name} ({sev}): {r.message}")

    # 总结
    print("\n" + "-" * 60)
    if report.passed:
        print("  RESULT: ALL PASSED")
    else:
        print(f"  RESULT: FAILED ({len(report.errors)} errors, {len(report.warnings)} warnings)")
    print("=" * 60 + "\n")
