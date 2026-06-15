#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""wrappers 子包:套在任何 FrameSource 外面的性能/接口扩展层。

不属于任何一种"输入源",而是"输入源的装饰器" —— 跟具体源正交。
"""
from __future__ import annotations

from odp_platform.frame_source.wrappers.threaded import ThreadedSource, BufferStrategy
from odp_platform.frame_source.wrappers.aio      import AsyncSource

__all__ = [
    "ThreadedSource",
    "BufferStrategy",
    "AsyncSource",
]
