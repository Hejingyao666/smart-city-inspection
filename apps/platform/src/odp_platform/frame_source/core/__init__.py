#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""core 子包: 核心类型与抽象基类。

本模块为 frame_source 子系统的内部子包，定义所有输入源共享的协议和数据类型。
"""
from odp_platform.frame_source.core.types import (
    SourceType,
    FrameInfo,
    Frame,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)
from odp_platform.frame_source.core.config import (
    CameraConfig,
    CameraBackend,
    CameraCodec,
)
from odp_platform.frame_source.core.base import FrameSource

__all__ = [
    "SourceType",
    "FrameInfo",
    "Frame",
    "IMAGE_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "CameraConfig",
    "CameraBackend",
    "CameraCodec",
    "FrameSource",
]
