#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""日志文件重命名."""
from __future__ import annotations

import logging
import re
from pathlib import Path

ROOT_LOGGER_NAME: str = "odp_platform"
logger = logging.getLogger(__name__)
_TIMESTAMP_RE = re.compile(r"(\d{8}-\d{6}(?:-\d+)?)")


def rename_log_to_save_dir(
    save_dir: Path,
    model_stem: str,
) -> Path | None:
    root = logging.getLogger(ROOT_LOGGER_NAME)
    file_handler = next((h for h in root.handlers if isinstance(h, logging.FileHandler)), None)
    if file_handler is None:
        logger.warning(f"'{ROOT_LOGGER_NAME}' 根 logger 上没有 FileHandler, 跳过日志改名")
        return None

    old_path = Path(file_handler.baseFilename)
    match = _TIMESTAMP_RE.search(old_path.stem)
    timestamp = match.group(1) if match else "unknown-time"
    new_name = f"{save_dir.name}_{timestamp}_{model_stem}.log"
    new_path = old_path.parent / new_name
    if new_path == old_path:
        return old_path

    formatter = file_handler.formatter
    level = file_handler.level
    encoding = getattr(file_handler, "encoding", None) or "utf-8"

    file_handler.close()
    root.removeHandler(file_handler)

    if not old_path.exists():
        logger.warning(f"旧日志文件不存在, 无法改名: {old_path}")
        return None

    try:
        old_path.rename(new_path)
    except OSError as e:
        logger.warning(f"日志 rename 失败 ({e}), 尝试恢复旧 handler...")
        try:
            restored = logging.FileHandler(old_path, encoding=encoding)
            if formatter:
                restored.setFormatter(formatter)
            restored.setLevel(level)
            root.addHandler(restored)
        except OSError as e2:
            logger.error(f"回滚 handler 也失败 ({e2}) — 后续日志可能丢失")
        return None

    try:
        new_handler = logging.FileHandler(new_path, encoding=encoding)
        if formatter:
            new_handler.setFormatter(formatter)
        new_handler.setLevel(level)
        root.addHandler(new_handler)
    except OSError as e:
        logger.error(f"创建新 FileHandler 失败 ({e}) — 文件已改名, 但后续日志写不进新文件")
        return new_path

    logger.info(f"日志文件已重命名: {new_path.name}")
    return new_path
