import logging
from pathlib import Path
from odp_platform.data_validation import CheckContext, run_all_checks, list_check_names
from odp_platform.data_validation.snapshot import build_snapshot

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

print('已注册的 check:', list_check_names())

yaml_path = Path(r'C:\Users\14041\Desktop\ODPlatform\apps\platform\configs\datasets\plantdoc.yaml')
snap = build_snapshot(yaml_path)          # 一次扫描，供所有 check 使用
ctx = CheckContext(yaml_path=yaml_path, snapshot=snap)
results = run_all_checks(ctx)

for r in results:
    print(f"{r.severity} {r.name} — {r.summary}")
    if r.details.get('problems'):
        for p in r.details['problems']:
            print('  ', p)
