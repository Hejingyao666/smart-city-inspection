"""调度层: 按注册表跑所有 check, 不内嵌任何业务逻辑。"""
from __future__ import annotations

import logging
from pathlib import Path

from odp_platform.data_validation.models import CheckResult, Severity, ValidationReport
from odp_platform.data_validation.registry import get_all_checks
from odp_platform.data_validation.registry import CheckSeverity

logger = logging.getLogger(__name__)


def run_all_checks(cfg: dict, data_root: Path) -> ValidationReport:
    """按 order 顺序跑所有已注册的 check, 失败也不停, 全部收集。"""
    report = ValidationReport()

    for entry in get_all_checks():
        logger.info(f"Running check: {entry.name}")
        try:
            result = entry.func(cfg, data_root)
        except Exception as e:
            result = CheckResult(
                name=entry.name,
                passed=False,
                severity=CheckSeverity.ERROR,
                message=f"check 内部异常: {e}",
            )
        
            logger.exception(f"check {entry.name} 抛出异常")

        report.results.append(result)

    return report
