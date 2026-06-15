#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""runtime_config — YOLO 训练 / 验证配置子系统.

公共 API:

  配置类:
      BaseConfig, YOLOTrainConfig, YOLOValConfig

  加载器(外部数据 → dict):
      YAMLLoader, CLILoader, load_all_sources

  合并器(三源合并 + 溯源):
      ConfigMerger, ConfigSource, ConfigMetadata

  生成器(Pydantic → YAML 模板):
      ConfigGenerator

  一键 build:
      build_train_config, build_val_config

不公开:
  - _drop_none / _CONFIG_REGISTRY 等内部工具
  - 不在 __all__ 里的所有符号都是内部细节, 可能在小版本变化

典型用法 (在 D6 service 层):

    from odp_platform.runtime_config import build_train_config

    config, merger = build_train_config(
        yaml_path = "train.yaml",
        cli_args  = args,         # argparse.Namespace
    )

    # 主线: 用 config 跑训练
    model.train(**config.to_ultralytics_kwargs())

    # 副线: 打来源报告 / 查单字段溯源
    print(merger.get_source_report())
    print(merger.get_metadata("lr0").chain_str())
"""
from __future__ import annotations

from argparse import Namespace
from pathlib  import Path
from typing   import Any, Dict, List, Mapping, Optional, Tuple, Union

from odp_platform.runtime_config.base   import BaseConfig
from odp_platform.runtime_config.train  import YOLOTrainConfig
from odp_platform.runtime_config.val    import YOLOValConfig
from odp_platform.runtime_config.infer  import YOLOInferConfig

from odp_platform.runtime_config.loaders import (
    YAMLLoader,
    CLILoader,
    load_all_sources,
)

from odp_platform.runtime_config.merger import (
    ConfigMerger,
    ConfigSource,
    ConfigMetadata,
)

from odp_platform.runtime_config.generator import ConfigGenerator


def build_train_config(
    yaml_path: Optional[Union[str, Path]] = "train.yaml",
    cli_args:  Optional[Union[Namespace, Dict[str, Any]]] = None,
    *,
    yaml_dir:      Optional[Union[str, Path]] = None,
    cli_exclude:   Optional[List[str]]        = None,
    cli_mapping:   Optional[Dict[str, str]]   = None,
    extra_sources: Optional[List[Tuple[Union[ConfigSource, str], Mapping[str, Any]]]] = None,
    track_sources: bool = True,
    dry_run:       bool = False,
) -> Tuple[Optional[YOLOTrainConfig], ConfigMerger]:
    from odp_platform.common.paths import RUNTIME_CONFIGS_DIR

    sources = load_all_sources(
        yaml_path   = yaml_path,
        yaml_dir    = yaml_dir or RUNTIME_CONFIGS_DIR,
        cli_args    = cli_args,
        cli_exclude = cli_exclude,
        cli_mapping = cli_mapping,
    )

    sources_list: List[Tuple[Union[ConfigSource, str], Mapping[str, Any]]] = []
    if sources["yaml"]:
        sources_list.append((ConfigSource.YAML, sources["yaml"]))
    if extra_sources:
        sources_list.extend(extra_sources)
    if sources["cli"]:
        sources_list.append((ConfigSource.CLI, sources["cli"]))

    merger = ConfigMerger(track_sources=track_sources)
    if dry_run:
        merger.preview(YOLOTrainConfig, sources=sources_list)
        return None, merger
    config = merger.merge(YOLOTrainConfig, sources=sources_list)
    return config, merger


def build_val_config(
    yaml_path: Optional[Union[str, Path]] = "val.yaml",
    cli_args:  Optional[Union[Namespace, Dict[str, Any]]] = None,
    *,
    yaml_dir:      Optional[Union[str, Path]] = None,
    cli_exclude:   Optional[List[str]]        = None,
    cli_mapping:   Optional[Dict[str, str]]   = None,
    extra_sources: Optional[List[Tuple[Union[ConfigSource, str], Mapping[str, Any]]]] = None,
    track_sources: bool = True,
    dry_run:       bool = False,
) -> Tuple[Optional[YOLOValConfig], ConfigMerger]:
    from odp_platform.common.paths import RUNTIME_CONFIGS_DIR

    sources = load_all_sources(
        yaml_path   = yaml_path,
        yaml_dir    = yaml_dir or RUNTIME_CONFIGS_DIR,
        cli_args    = cli_args,
        cli_exclude = cli_exclude,
        cli_mapping = cli_mapping,
    )

    sources_list: List[Tuple[Union[ConfigSource, str], Mapping[str, Any]]] = []
    if sources["yaml"]:
        sources_list.append((ConfigSource.YAML, sources["yaml"]))
    if extra_sources:
        sources_list.extend(extra_sources)
    if sources["cli"]:
        sources_list.append((ConfigSource.CLI, sources["cli"]))

    merger = ConfigMerger(track_sources=track_sources)
    if dry_run:
        merger.preview(YOLOValConfig, sources=sources_list)
        return None, merger
    config = merger.merge(YOLOValConfig, sources=sources_list)
    return config, merger


def build_infer_config(
    yaml_path: Optional[Union[str, Path]] = "infer.yaml",
    cli_args:  Optional[Union[Namespace, Dict[str, Any]]] = None,
    *,
    yaml_dir:      Optional[Union[str, Path]] = None,
    cli_exclude:   Optional[List[str]]        = None,
    cli_mapping:   Optional[Dict[str, str]]   = None,
    extra_sources: Optional[List[Tuple[Union[ConfigSource, str], Mapping[str, Any]]]] = None,
    track_sources: bool = True,
    dry_run:       bool = False,
) -> Tuple[Optional[YOLOInferConfig], ConfigMerger]:
    from odp_platform.common.paths import RUNTIME_CONFIGS_DIR

    sources = load_all_sources(
        yaml_path   = yaml_path,
        yaml_dir    = yaml_dir or RUNTIME_CONFIGS_DIR,
        cli_args    = cli_args,
        cli_exclude = cli_exclude,
        cli_mapping = cli_mapping,
    )

    sources_list: List[Tuple[Union[ConfigSource, str], Mapping[str, Any]]] = []
    if sources["yaml"]:
        sources_list.append((ConfigSource.YAML, sources["yaml"]))
    if extra_sources:
        sources_list.extend(extra_sources)
    if sources["cli"]:
        sources_list.append((ConfigSource.CLI, sources["cli"]))

    merger = ConfigMerger(track_sources=track_sources)
    if dry_run:
        merger.preview(YOLOInferConfig, sources=sources_list)
        return None, merger
    config = merger.merge(YOLOInferConfig, sources=sources_list)
    return config, merger


__all__ = [
    "BaseConfig",
    "YOLOTrainConfig",
    "YOLOValConfig",
    "YOLOInferConfig",
    "YAMLLoader",
    "CLILoader",
    "load_all_sources",
    "ConfigMerger",
    "ConfigSource",
    "ConfigMetadata",
    "ConfigGenerator",
    "build_train_config",
    "build_val_config",
    "build_infer_config",
]
