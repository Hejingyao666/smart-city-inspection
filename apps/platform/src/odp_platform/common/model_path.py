#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from odp_platform.common.paths import PRETRAINED_MODELS_DIR

logger = logging.getLogger(__name__)


def resolve_model_path(model: str | Path, *, search_dirs: Sequence[Path] | None = None) -> Path:
    model_path = Path(model)

    if model_path.is_absolute():
        return model_path

    dirs: Sequence[Path] = search_dirs if search_dirs is not None else [PRETRAINED_MODELS_DIR]
    for d in dirs:
        candidate = d / model_path.name
        if candidate.exists():
            logger.info(f"模型文件已找到: {candidate}")
            return candidate

    logger.warning(f"模型文件未找到: {model_path}\n搜索过目录：{[str(d) for d in dirs]}\nUltralytics将会自动下载模型或从其他位置加载")
    return model_path
