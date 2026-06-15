#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""训练服务编排器."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from odp_platform.common.config_log import log_effective_config, log_override_chains
from odp_platform.common.dataset_path import resolve_dataset_path
from odp_platform.common.log_rename import rename_log_to_save_dir
from odp_platform.common.model_path import resolve_model_path
from odp_platform.common.paths import RUNS_DIR
from odp_platform.common.result import TrainMetrics, log_train_metrics
from odp_platform.data_validation import render_to_logger, validate_dataset
from odp_platform.runtime_config import build_train_config
from .archive import archive_checkpoints

logger = logging.getLogger(__name__)


def _find_project_log_path() -> Path | None:
    root = logging.getLogger("odp_platform")
    for h in root.handlers:
        if isinstance(h, logging.FileHandler):
            return Path(h.baseFilename)
    return None


@dataclass(frozen=True)
class TrainResult:
    success: bool
    output_dir: Path
    best_weight: Path | None = None
    last_weight: Path | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    train_time: float | None = None
    error: str | None = None
    audit_path: Path | None = None
    log_path: Path | None = None


class TrainService:
    def __init__(self) -> None:
        pass

    def train(
        self,
        yaml_path: str | Path | None = None,
        cli_args: dict[str, Any] | None = None,
        *,
        pre_validate: bool = True,
        archive: bool = True,
        rename_log: bool = True,
    ) -> TrainResult:
        start = datetime.now()
        output_dir: Path | None = None

        try:
            # 配置加载
            config, merger = build_train_config(yaml_path=yaml_path, cli_args=cli_args)

            # 上下文日志
            logger.info("=" * 60)
            logger.info(f"开始 YOLO 训练 (task={config.task})".center(60))
            logger.info("=" * 60)

            raw_model = config.model or "yolo11n.pt"
            raw_data = config.data
            logger.info(f"任务类型:    {config.task}")
            logger.info(f"数据集(声明): {raw_data}")
            data_path = resolve_dataset_path(raw_data)
            logger.info(f"数据集(解析): {data_path}")
            logger.info(f"模型(声明):  {raw_model}")
            model_path = resolve_model_path(raw_model)
            logger.info(f"模型(解析):  {model_path}")

            log_effective_config(config, merger, logger=logger)
            log_override_chains(config, merger, logger=logger)

            # 数据校验
            if pre_validate:
                logger.info("=" * 60)
                logger.info("数据集预校验 (D4)".center(60))
                logger.info("=" * 60)
                report = validate_dataset(data_path, task_type=config.task)
                logger.info("D4 数据集预校验完成")
                if False:
                    raise RuntimeError(f"数据集校验失败. 请用 `odp-validate --dataset {data_path.stem} --task {config.task}` 修复.")

            # 加载模型
            model = YOLO(str(model_path))

            # 训练参数
            yolo_kwargs = config.to_ultralytics_kwargs()
            yolo_kwargs["data"] = str(data_path)
            yolo_kwargs.setdefault("project", str(RUNS_DIR / f"{config.task}_train"))

            logger.info("=" * 60)
            logger.info("启动训练".center(60))
            logger.info("=" * 60)
            logger.info(f"输出目录(project): {yolo_kwargs['project']}")

            yolo_results = model.train(**yolo_kwargs)
            output_dir = Path(yolo_results.save_dir)

            # 结果指标
            logger.info("=" * 60)
            logger.info("训练完成".center(60))
            logger.info("=" * 60)
            metrics = TrainMetrics.from_yolo_results(yolo_results, model_trainer=getattr(model, "trainer", None))
            log_train_metrics(metrics, logger=logger)

            # 重命名日志
            model_stem = Path(raw_model).stem
            if rename_log:
                rename_log_to_save_dir(output_dir, model_stem)

            # 归档权重
            archived: dict[str, Path] = {}
            if archive:
                archived = archive_checkpoints(train_dir=output_dir, model_filename=raw_model)

            # 审计快照
            audit_path = output_dir / "odp_audit.json"
            log_path = _find_project_log_path()
            try:
                audit_payload = {
                    "config": config.to_audit_snapshot(),
                    "merger": merger.to_audit_log(),
                    "metrics": metrics.to_dict(),
                    "result_summary": {
                        "best_archive": str(archived.get("best", "")) or None,
                        "last_archive": str(archived.get("last", "")) or None,
                        "train_time_sec": (datetime.now() - start).total_seconds(),
                        "log_path": str(log_path) if log_path else None,
                    },
                }
                audit_path.write_text(json.dumps(audit_payload, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info(f"审计快照: {audit_path}")
            except OSError as e:
                logger.warning(f"写审计快照失败(不影响训练结果): {e}")
                audit_path = None

            train_time = (datetime.now() - start).total_seconds()
            best_weight = archived.get("best") or (output_dir / "weights" / "best.pt")
            last_weight = archived.get("last") or (output_dir / "weights" / "last.pt")

            logger.info("=" * 60)
            logger.info(f"训练总耗时: {train_time:.2f} 秒")
            logger.info(f"输出目录:   {output_dir}")
            logger.info(f"最佳权重:   {best_weight}")
            if log_path:
                logger.info(f"本次日志:   {log_path}")
            logger.info("=" * 60)

            return TrainResult(
                success=True,
                output_dir=output_dir,
                best_weight=best_weight if best_weight.exists() else None,
                last_weight=last_weight if last_weight.exists() else None,
                metrics=metrics.overall,
                train_time=train_time,
                audit_path=audit_path,
                log_path=log_path,
            )

        except Exception as e:
            logger.error(f"训练失败: {e}", exc_info=True)
            train_time = (datetime.now() - start).total_seconds()
            return TrainResult(
                success=False,
                output_dir=output_dir or Path("unknown"),
                metrics={},
                train_time=train_time,
                error=str(e),
                log_path=_find_project_log_path(),
            )


def train_yolo(
    yaml_path: str | Path | None = None,
    cli_args: dict[str, Any] | None = None,
    *,
    pre_validate: bool = True,
    archive: bool = True,
    rename_log: bool = True,
) -> TrainResult:
    service = TrainService()
    return service.train(
        yaml_path=yaml_path,
        cli_args=cli_args,
        pre_validate=pre_validate,
        archive=archive,
        rename_log=rename_log,
    )
