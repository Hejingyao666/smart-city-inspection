#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import LOGGING_DIR, dataset_yaml_path, validation_run_dir
from odp_platform.data_validation import (
    build_snapshot, CheckContext, run_all_checks,
    ValidationReport, render_to_logger
)


def main() -> int:
    parser = argparse.ArgumentParser(prog="odp-validate")
    parser.add_argument("--dataset", required=True, help="数据集名称")
    parser.add_argument("--task", default="detect", choices=["detect", "segment"])
    args = parser.parse_args()

    logger = get_logger(base_path=LOGGING_DIR, log_type="odp_validate")

    yaml_path = dataset_yaml_path(args.dataset)
    start_time = time.perf_counter()
    started_at_iso = datetime.now(timezone.utc).isoformat()

    snap = build_snapshot(yaml_path, task_type=args.task)
    ctx = CheckContext(yaml_path=yaml_path, snapshot=snap)
    results = run_all_checks(ctx)

    duration = time.perf_counter() - start_time
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = validation_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    report = ValidationReport(
        run_id=run_id,
        yaml_path=yaml_path,
        snapshot=snap,
        results=results,
        duration_seconds=duration,
        started_at_iso=started_at_iso,
        run_dir=run_dir,
    )

    render_to_logger(report, logger, report_path=report.report_path)

    # 可选：写 JSON 报告
    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"JSON 报告已保存: {json_path}")

    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
