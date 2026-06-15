#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : __init__.py
# @Author    : 雨霓同学
# @Project   : ODPlatform / frame_source
# @Function  : sources 子包入口 — 具体输入源实现
"""
sources 子包:各种输入源的具体实现。

每个源都是 FrameSource 的子类,实现统一的 open/read/close 协议。
"""
from __future__ import annotations

from odp_platform.frame_source.sources.camera import CameraSource
from odp_platform.frame_source.sources.video  import VideoSource
from odp_platform.frame_source.sources.image  import ImageSource, ImageFolderSource

__all__ = [
    "CameraSource",
    "VideoSource",
    "ImageSource",
    "ImageFolderSource",
]
