import logging
from pathlib import Path
from datetime import datetime, timezone
import time
from odp_platform.data_validation import (
    build_snapshot, CheckContext, run_all_checks,
    ValidationReport, render_to_logger, list_check_names
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger()

print('已注册的 check:', list_check_names())

yaml_path = Path(r'C:\Users\14041\Desktop\ODPlatform\apps\platform\configs\datasets\plantdoc.yaml')
t0 = time.perf_counter()
started = datetime.now(timezone.utc).isoformat()

snap = build_snapshot(yaml_path)
ctx = CheckContext(yaml_path=yaml_path, snapshot=snap)
results = run_all_checks(ctx)

report = ValidationReport(
    run_id="test_run",
    yaml_path=yaml_path,
    snapshot=snap,
    results=results,
    duration_seconds=time.perf_counter() - t0,
    started_at_iso=started,
)

render_to_logger(report, logger)
