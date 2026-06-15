from odp_platform.runtime_config import build_train_config
import argparse
args = argparse.Namespace()
args.epochs = 50
args.batch = 32
config, merger = build_train_config(yaml_path='train.yaml', cli_args=args)
print('最终 epochs:', config.epochs)
print('批次:', config.batch)
print('配置来源报告:')
print(merger.get_source_report())
print('epochs 覆盖链:', merger.get_metadata('epochs').chain_str())
