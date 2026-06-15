#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :snapshot.py
# @Time      :2026/6/10
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :DatasetSnapshot — 一次扫描，多次复用
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from odp_platform.common.constants import IMAGE_EXTENSIONS, Task

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SplitStats:
    """单个 split 的轻量统计"""
    image_count: int
    annotated_count: int
    total_instances: int


@dataclass(frozen=True)
class DatasetSnapshot:
    """数据集快照，供所有 check 共享消费"""
    yaml_path: Path
    yaml_data: Dict[str, Any]
    yaml_load_error: Optional[str]
    data_root: Path
    nc: Optional[int]
    class_names: Tuple[str, ...]
    task_type: str
    images_per_split: Dict[str, Tuple[Path, ...]]
    labels_per_split: Dict[str, Tuple[Path, ...]]
    stats_per_split: Dict[str, SplitStats]
    scan_warnings: Tuple[str, ...]

    @property
    def splits(self) -> Tuple[str, ...]:
        order = ("train", "val", "test")
        return tuple(s for s in order if s in self.images_per_split)

    @property
    def total_images(self) -> int:
        return sum(len(imgs) for imgs in self.images_per_split.values())


def _load_yaml(yaml_path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    if not yaml_path.exists():
        return {}, f"yaml 文件不存在: {yaml_path}"
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {}, f"yaml 顶层不是 dict: {type(data).__name__}"
        return data, None
    except yaml.YAMLError as e:
        return {}, f"yaml 解析失败: {e}"
    except OSError as e:
        return {}, f"yaml 读取失败: {e}"


def _resolve_data_root(yaml_path: Path, yaml_data: Dict[str, Any]) -> Path:
    path_str = yaml_data.get("path")
    if not path_str:
        return yaml_path.parent.resolve()
    p = Path(path_str)
    return p.resolve() if p.is_absolute() else (yaml_path.parent / p).resolve()


def _list_images(split_dir: Path) -> List[Path]:
    if not split_dir.exists() or not split_dir.is_dir():
        return []
    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(split_dir.glob(f"*{ext}"))
        images.extend(split_dir.glob(f"*{ext.upper()}"))
    return sorted(set(images))


def _label_path_for_image(image_path: Path) -> Path:
    parts = list(image_path.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            parts[i] = "labels"
            break
    return Path(*parts[:-1]) / (image_path.stem + ".txt")


def _normalize_names(names_raw: Any) -> Tuple[str, ...]:
    if isinstance(names_raw, list):
        if all(isinstance(n, str) for n in names_raw):
            return tuple(names_raw)
        return ()
    if isinstance(names_raw, dict):
        if all(isinstance(k, int) for k in names_raw.keys()) and \
           all(isinstance(v, str) for v in names_raw.values()):
            return tuple(v for _, v in sorted(names_raw.items()))
        return ()
    return ()


def _build_split_stats(labels: List[Path]) -> SplitStats:
    image_count = len(labels)
    annotated_count = 0
    total_instances = 0
    for lbl in labels:
        if not lbl.exists():
            continue
        try:
            content = lbl.read_text(encoding="utf-8")
        except OSError:
            continue
        lines = [l for l in content.splitlines() if l.strip()]
        if not lines:
            continue
        annotated_count += 1
        total_instances += len(lines)
    return SplitStats(
        image_count=image_count,
        annotated_count=annotated_count,
        total_instances=total_instances,
    )


def build_snapshot(
    yaml_path: Path,
    task_type: Optional[str] = None,
) -> DatasetSnapshot:
    """构建数据集快照，永远不抛异常"""
    yaml_path = yaml_path.resolve()
    warnings = []

    yaml_data, yaml_err = _load_yaml(yaml_path)
    if yaml_err:
        warnings.append(yaml_err)

    data_root = _resolve_data_root(yaml_path, yaml_data)

    nc = yaml_data.get("nc") if isinstance(yaml_data.get("nc"), int) else None
    class_names = _normalize_names(yaml_data.get("names"))

    resolved_task = task_type or yaml_data.get("task") or Task.DETECT
    if resolved_task not in (Task.DETECT, Task.SEGMENT):
        warnings.append(f"未知 task_type '{resolved_task}', 回退到 '{Task.DETECT}'")
        resolved_task = Task.DETECT

    images_per_split = {}
    labels_per_split = {}
    stats_per_split = {}

    for split in ("train", "val", "test"):
        split_rel = yaml_data.get(split)
        if not isinstance(split_rel, str) or not split_rel.strip():
            continue
        split_dir = Path(split_rel)
        if not split_dir.is_absolute():
            split_dir = data_root / split_dir
        if not split_dir.exists():
            warnings.append(f"split '{split}' 目录不存在: {split_dir}")
            continue
        images = _list_images(split_dir)
        if not images:
            warnings.append(f"split '{split}' 目录下无图像: {split_dir}")
            continue
        labels = [_label_path_for_image(img) for img in images]
        images_per_split[split] = tuple(images)
        labels_per_split[split] = tuple(labels)
        stats_per_split[split] = _build_split_stats(labels)

    return DatasetSnapshot(
        yaml_path=yaml_path,
        yaml_data=yaml_data,
        yaml_load_error=yaml_err,
        data_root=data_root,
        nc=nc,
        class_names=class_names,
        task_type=resolved_task,
        images_per_split=images_per_split,
        labels_per_split=labels_per_split,
        stats_per_split=stats_per_split,
        scan_warnings=tuple(warnings),
    )
