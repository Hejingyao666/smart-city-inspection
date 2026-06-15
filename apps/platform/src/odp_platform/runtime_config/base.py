#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : base.py
# @Author    : 雨霓同学 (ODPlatform team)
# @Project   : ODPlatform
# @Function  : runtime_config 子系统基础模型——BaseConfig
"""运行配置子系统基础模块."""
from __future__ import annotations

import warnings
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BaseConfig(BaseModel):
    """所有模式共享的基础配置"""
    model_config = ConfigDict(extra="forbid")
    FRAMEWORK_ONLY_FIELDS: ClassVar[set[str]] = {"verbose"}
    SENSITIVE_MASK: ClassVar[str] = "***"

    model: Optional[str] = Field(default=None, description="模型文件路径", json_schema_extra={"group": "核心参数", "examples": ["yolo11n.pt"], "tips": ["官方模型"], "yaml_comment": "模型文件路径"})
    data: Optional[str] = Field(default=None, description="数据集配置文件路径", json_schema_extra={"group": "核心参数", "examples": ["data.yaml"], "tips": ["数据集配置"], "yaml_comment": "数据集配置"})
    batch: Union[int, float] = Field(default=16, description="批次大小", json_schema_extra={"group": "输入配置", "examples": [8,16,32,-1,0.7], "tips": ["批次大小"], "yaml_comment": "批次大小"})
    imgsz: int = Field(default=640, ge=32, description="输入图像尺寸", json_schema_extra={"group": "输入配置", "examples": [640,1280], "tips": ["尺寸"], "yaml_comment": "图像尺寸"})
    workers: int = Field(default=8, ge=0, description="数据加载工作线程数", json_schema_extra={"group": "输入配置", "examples": [4,8,16], "tips": ["线程数"], "yaml_comment": "工作线程"})
    cache: Union[bool, str] = Field(default=False, description="数据缓存策略", json_schema_extra={"group": "输入配置", "examples": [False,True,"ram","disk"], "tips": ["缓存"], "yaml_comment": "缓存策略"})
    rect: bool = Field(default=False, description="矩形训练", json_schema_extra={"group": "输入配置", "examples": [False,True], "tips": ["矩形训练"], "yaml_comment": "矩形训练"})
    device: Optional[Union[int, str, List[Union[int, str]]]] = Field(default=None, description="训练设备", json_schema_extra={"group": "设备配置", "examples": [0,"cpu","0,1"], "tips": ["设备"], "yaml_comment": "设备"})
    amp: bool = Field(default=True, description="自动混合精度", json_schema_extra={"group": "设备配置", "examples": [True,False], "tips": ["AMP"], "yaml_comment": "AMP"})
    project: Optional[str] = Field(default=None, description="输出项目目录", json_schema_extra={"group": "输出配置", "examples": ["runs/detect"], "tips": ["项目目录"], "yaml_comment": "项目目录"})
    name: Optional[str] = Field(default=None, description="实验名称", json_schema_extra={"group": "输出配置", "examples": ["exp"], "tips": ["实验名"], "yaml_comment": "实验名"})
    exist_ok: bool = Field(default=False, description="允许覆盖已有实验", json_schema_extra={"group": "输出配置", "examples": [False,True], "tips": ["覆盖"], "yaml_comment": "覆盖"})
    save: bool = Field(default=True, description="保存训练检查点", json_schema_extra={"group": "输出配置", "examples": [True,False], "tips": ["保存"], "yaml_comment": "保存检查点"})
    verbose: bool = Field(default=True, description="详细输出模式", json_schema_extra={"group": "基础设置", "examples": [True,False], "tips": ["详细日志"], "yaml_comment": "详细输出"})
    seed: int = Field(default=0, ge=0, description="随机种子", json_schema_extra={"group": "基础设置", "examples": [0,42], "tips": ["种子"], "yaml_comment": "随机种子"})
    deterministic: bool = Field(default=True, description="确定性算法", json_schema_extra={"group": "基础设置", "examples": [True,False], "tips": ["确定性"], "yaml_comment": "确定性算法"})

    @field_validator("imgsz")
    @classmethod
    def _validate_imgsz(cls, v: int) -> int:
        if v % 32 != 0:
            warnings.warn(f"imgsz={v} 不是32的倍数", UserWarning)
        return v

    @field_validator("batch", mode="before")
    @classmethod
    def _validate_batch(cls, v: Any) -> Union[int, float]:
        if isinstance(v, bool):
            raise TypeError("batch不能是bool")
        if isinstance(v, int):
            if v == -1:
                return v
            if v <= 0:
                raise ValueError("batch必须>=1或-1")
            return v
        v_float = float(v)
        if not (0.0 < v_float <= 1.0):
            raise ValueError("batch float必须在(0,1]")
        return v_float

    @field_validator("device")
    @classmethod
    def _validate_device(cls, v: Any) -> Any:
        if v is None or isinstance(v, (str, int, list)):
            return v
        raise TypeError("device类型错误")

    @field_validator("cache")
    @classmethod
    def _validate_cache(cls, v: Union[bool, str]) -> Union[bool, str]:
        if isinstance(v, bool):
            return v
        if v.lower() in ("ram", "disk"):
            return v.lower()
        raise ValueError("cache必须是False/True/'ram'/'disk'")

    @model_validator(mode="after")
    def _cross_field_validation(self) -> "BaseConfig":
        if isinstance(self.batch, int) and self.batch > 0:
            if self.workers > self.batch * 2:
                warnings.warn(f"workers={self.workers}远大于batch={self.batch}", UserWarning)
        return self

    def to_ultralytics_kwargs(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True)
        for f in self.FRAMEWORK_ONLY_FIELDS:
            d.pop(f, None)
        return d

    def get_field_groups(self) -> Dict[str, List[str]]:
        groups = {}
        for name, info in self.__class__.model_fields.items():
            extra = info.json_schema_extra or {}
            group = extra.get("group", "其他") if isinstance(extra, dict) else "其他"
            groups.setdefault(group, []).append(name)
        return groups

    def get_field_metadata(self, field_name: str) -> Dict[str, Any]:
        if field_name not in self.__class__.model_fields:
            raise ValueError(f"字段不存在: {field_name}")
        info = self.__class__.model_fields[field_name]
        meta = {"description": info.description, "default": info.default, "examples": [], "tips": [], "yaml_comment": info.description, "group": "其他", "sensitive": False}
        if isinstance(info.json_schema_extra, dict):
            meta.update(info.json_schema_extra)
        return meta

    def to_audit_snapshot(self) -> Dict[str, Any]:
        return {"config_class": self.__class__.__name__, "config_module": self.__class__.__module__, "frozen_at": datetime.now().isoformat(timespec="seconds"), "values": self.model_dump()}

    @classmethod
    def from_audit_snapshot(cls, snapshot: Dict[str, Any]) -> "BaseConfig":
        if snapshot.get("config_class") != cls.__name__:
            raise ValueError("快照类名不匹配")
        return cls(**snapshot.get("values", {}))

    def mask_sensitive_dump(self) -> Dict[str, Any]:
        dump = self.model_dump()
        for name, info in self.__class__.model_fields.items():
            extra = info.json_schema_extra or {}
            if isinstance(extra, dict) and extra.get("sensitive") and dump.get(name) is not None:
                dump[name] = self.SENSITIVE_MASK
        return dump

    @classmethod
    def sensitive_field_names(cls) -> set[str]:
        result = set()
        for name, info in cls.model_fields.items():
            extra = info.json_schema_extra or {}
            if isinstance(extra, dict) and extra.get("sensitive"):
                result.add(name)
        return result
