#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""路径 SSoT."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

# 项目根目录发现（向上查找 .odp-workspace）
def _find_root(start: Path = None) -> Path:
    if start is None:
        start = Path(__file__).resolve().parent
    for parent in [start] + list(start.parents):
        if (parent / ".odp-workspace").exists():
            return parent
    raise RuntimeError("未找到 .odp-workspace 标记文件，请确保在项目根目录运行")

ROOT_DIR: Path = _find_root()
APP_DIR: Path = ROOT_DIR / "apps" / "platform"
SRC_DIR: Path = APP_DIR / "src" / "odp_platform"

# 数据目录
DATA_DIR: Path = ROOT_DIR / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
TRAIN_DIR: Path = DATA_DIR / "train"
VAL_DIR: Path = DATA_DIR / "val"
TEST_DIR: Path = DATA_DIR / "test"

# 训练/验证/测试集的图像和标签目录
TRAIN_IMAGES_DIR: Path = TRAIN_DIR / "images"
TRAIN_LABELS_DIR: Path = TRAIN_DIR / "labels"
VAL_IMAGES_DIR: Path = VAL_DIR / "images"
VAL_LABELS_DIR: Path = VAL_DIR / "labels"
TEST_IMAGES_DIR: Path = TEST_DIR / "images"
TEST_LABELS_DIR: Path = TEST_DIR / "labels"

# 模型目录
MODELS_DIR: Path = ROOT_DIR / "models"
PRETRAINED_MODELS_DIR: Path = MODELS_DIR / "pretrained"
CHECKPOINTS_DIR: Path = MODELS_DIR / "checkpoints"

# 运行输出目录
RUNS_DIR: Path = ROOT_DIR / "runs"
VALIDATION_RUNS_DIR: Path = RUNS_DIR / "data_validation"

# 配置目录
CONFIGS_DIR: Path = APP_DIR / "configs"
DATASET_CONFIGS_DIR: Path = CONFIGS_DIR / "datasets"
RUNTIME_CONFIGS_DIR: Path = CONFIGS_DIR / "runtime"

# 日志目录
LOGGING_DIR: Path = APP_DIR / "logging"

# 测试目录
TESTS_DIR: Path = APP_DIR / "tests"

# 脚本目录
SCRIPTS_DIR: Path = ROOT_DIR / "scripts"

# 文档目录
DOCS_DIR: Path = ROOT_DIR / "docs"

# 内部元数据目录
ODP_META_DIR: Path = ROOT_DIR / ".odp-meta"
ODP_META_LOGS_DIR: Path = ODP_META_DIR / "logs"


def get_dirs_to_initialize() -> List[Path]:
    """返回需要在项目初始化时创建的目录列表."""
    return [
        DATA_DIR,
        RAW_DATA_DIR,
        TRAIN_DIR / "images",
        TRAIN_DIR / "labels",
        VAL_DIR / "images",
        VAL_DIR / "labels",
        TEST_DIR / "images",
        TEST_DIR / "labels",
        MODELS_DIR,
        PRETRAINED_MODELS_DIR,
        CHECKPOINTS_DIR,
        RUNS_DIR,
        VALIDATION_RUNS_DIR,
        CONFIGS_DIR,
        DATASET_CONFIGS_DIR,
        RUNTIME_CONFIGS_DIR,
        LOGGING_DIR,
        TESTS_DIR,
        SCRIPTS_DIR,
        DOCS_DIR,
        ODP_META_DIR,
        ODP_META_LOGS_DIR,
    ]


def get_dirs_to_reset() -> List[Path]:
    """返回 odp-reset 可以删除的运行时目录（不包含配置和数据）. """
    return [
        RUNS_DIR,
        VALIDATION_RUNS_DIR,
        LOGGING_DIR,
        ODP_META_LOGS_DIR,
        CHECKPOINTS_DIR,
    ]


def is_protected(path: Path) -> bool:
    """判断路径是否为受保护路径（odp-reset 不能删除）. """
    protected = {
        ROOT_DIR,
        APP_DIR,
        SRC_DIR,
        DATA_DIR,
        RAW_DATA_DIR,
        CONFIGS_DIR,
        DATASET_CONFIGS_DIR,
        RUNTIME_CONFIGS_DIR,
        MODELS_DIR,
        PRETRAINED_MODELS_DIR,
        TESTS_DIR,
        SCRIPTS_DIR,
        DOCS_DIR,
        ODP_META_DIR,
    }
    # 检查 path 或其任何祖先是否在 protected 集合中
    for p in [path] + list(path.parents):
        if p in protected:
            return True
    return False


def raw_dataset_root(name: str) -> Path:
    """返回原始数据集的根目录路径: <RAW_DATA_DIR>/<name>"""
    return RAW_DATA_DIR / name


def dataset_yaml_path(name: str) -> Path:
    """返回数据集配置文件的路径: <CONFIGS_DIR>/datasets/<name>.yaml"""
    return DATASET_CONFIGS_DIR / f"{name}.yaml"


def runtime_config_path(name: str) -> Path:
    """返回运行配置文件的路径: <CONFIGS_DIR>/runtime/<name>.yaml"""
    return RUNTIME_CONFIGS_DIR / f"{name}.yaml"


def validation_run_dir(run_id: str) -> Path:
    """返回数据验证运行的输出目录: runs/data_validation/<run_id>/"""
    return VALIDATION_RUNS_DIR / run_id


# ============================================================
# 路径解析工具（模型、数据集）
# ============================================================

def resolve_model_path(model: str | Path, *, search_dirs: Optional[List[Path]] = None) -> Path:
    """解析模型权重文件路径。

    Args:
        model: 模型名称或路径（如 "yolo11n.pt" 或绝对路径）
        search_dirs: 额外搜索目录列表，默认使用 PRETRAINED_MODELS_DIR

    Returns:
        解析后的绝对路径（若找不到则返回原路径，让 ultralytics 自动下载）
    """
    model_path = Path(model)

    if model_path.is_absolute():
        return model_path

    if search_dirs is None:
        dirs = [PRETRAINED_MODELS_DIR]
    else:
        dirs = list(search_dirs)

    for d in dirs:
        candidate = d / model_path.name
        if candidate.exists():
            return candidate

    # fallback：返回原路径
    return model_path


def resolve_dataset_path(data: str | Path) -> Path:
    """解析数据集配置文件（data.yaml）路径。

    Args:
        data: 数据集名称（如 "plantdoc"）或路径

    Returns:
        解析后的绝对路径（若找不到则返回原路径）
    """
    data_path = Path(data)

    if data_path.is_absolute():
        return data_path

    config_candidate = DATASET_CONFIGS_DIR / data_path.name
    if config_candidate.exists():
        return config_candidate

    return data_path
