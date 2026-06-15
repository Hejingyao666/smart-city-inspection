#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : __init__.py
# @Author    : 雨霓同学
# @Project   : ODPlatform / visualization
# @Function  : visualization 模块导出
"""美化可视化模块导出。

提供 YOLO 检测结果美化绘制:
    from odp_platform.visualization import BeautifyVisualizer, Detection, DrawStyle

    viz = BeautifyVisualizer(labels=["person", "car"])
    annotated = viz.draw(image, detections)
"""
from .visualizer import BeautifyVisualizer
from .core.data_types import Detection, DrawStyle, LabelLayout, LabelPosition

__all__ = [
    "BeautifyVisualizer",
    "Detection",
    "DrawStyle",
    "LabelLayout",
    "LabelPosition",
]