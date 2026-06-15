#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import annotations

import logging
from pathlib import Path

from odp_platform.common.paths import DATASET_CONFIGS_DIR

logger = logging.getLogger(__name__)


def resolve_dataset_path(data: str | Path) -> Path:
    data_path = Path(data)

    if data_path.is_absolute():
        return data_path

    config_candidate = DATASET_CONFIGS_DIR / data_path.name
    if config_candidate.exists():
        logger.info(f"数据集配置文件已找到: {config_candidate}")
        return config_candidate

    logger.warning(f"数据集配置文件未找到: {data_path} DATASET_CONFIG_DIR: {DATASET_CONFIGS_DIR}")
    return data_path
