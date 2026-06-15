#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : camera.py
# @Author    : 雨霓同学
# @Project   : ODPlatform / frame_source
# @Function  : 摄像头输入源 (实时流, 不支持 seek)
"""摄像头输入源。

支持:
    - 本地摄像头 (索引或设备路径)
    - RTSP 网络流
    - HTTP 视频流

示例:
    # 本地摄像头
    with CameraSource(0) as camera:
        for frame in camera:
            process(frame.image)

    # RTSP 流
    with CameraSource("rtsp://admin:pass@192.168.1.100:554/stream") as camera:
        for frame in camera:
            process(frame.image)
"""
from __future__ import annotations

import logging
import time
from typing import Optional, Union

import cv2
import numpy as np

from odp_platform.frame_source.core.base import FrameSource
from odp_platform.frame_source.core.types import Frame, FrameInfo, SourceType


logger = logging.getLogger(__name__)


class CameraSource(FrameSource):
    """
    摄像头/实时流输入源。

    特性:
        - 支持本地摄像头索引 (0, 1, 2, ...)
        - 支持 RTSP / HTTP 流
        - 不支持 seek (实时流)
        - 自动重连机制

    Args:
        source: 摄像头索引(int)或流地址(str)
        fps: 目标帧率(用于限制读取速度, None 表示不限制)
        buffer_size: OpenCV 内部缓冲区大小(1 表示不缓冲)
    """

    def __init__(
        self,
        source: Union[int, str],
        fps: Optional[float] = None,
        buffer_size: int = 1,
    ):
        # 统一转为字符串路径
        source_path = str(source) if isinstance(source, int) else source
        super().__init__(source_path)

        self._source = source
        self._cap: Optional[cv2.VideoCapture] = None
        self._fps_limit = fps
        self._buffer_size = buffer_size
        self._width: int = 0
        self._height: int = 0
        self._actual_fps: float = 0.0
        self._last_read_time: float = 0.0

        # 帧率控制
        self._frame_interval: float = 1.0 / fps if fps else 0.0

    def open(self) -> bool:
        """打开摄像头/流."""
        self._cap = cv2.VideoCapture(self._source)
        if not self._cap.isOpened():
            logger.error(f"无法打开摄像头/流: {self._source}")
            return False

        # 设置缓冲区大小(减少延迟)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, self._buffer_size)

        # 获取分辨率
        self._width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        self._height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        self._actual_fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0

        # 判断源类型
        source_type = "摄像头" if isinstance(self._source, int) else "流"
        logger.info(
            f"{source_type}已打开: {self.source_path} "
            f"({self._width}x{self._height}, {self._actual_fps:.2f}fps)"
        )
        return True

    def read(self) -> Optional[Frame]:
        """读取一帧."""
        if self._cap is None or not self._cap.isOpened():
            return None

        # 帧率控制
        if self._fps_limit:
            elapsed = time.time() - self._last_read_time
            if elapsed < self._frame_interval:
                time.sleep(self._frame_interval - elapsed)

        ret, image = self._cap.read()
        if not ret:
            logger.warning(f"读取帧失败: {self.source_path}")
            return None

        self._last_read_time = time.time()
        timestamp = time.time() - self._start_time

        info = FrameInfo(
            width=self._width,
            height=self._height,
            source_type=SourceType.CAMERA,
            source_path=self.source_path,
            frame_index=self._frame_index,
            total_frames=None,  # 摄像头无总帧数
            timestamp=timestamp,
            fps=self._actual_fps,
            filename=f"camera:{self.source_path}",
        )
        self._frame_index += 1
        return Frame(image=image, info=info)

    def close(self) -> None:
        """释放摄像头资源."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info(f"摄像头已关闭: {self.source_path}")

    def get_source_type(self) -> SourceType:
        return SourceType.CAMERA

    @property
    def seekable(self) -> bool:
        """摄像头不支持 seek."""
        return False

    @property
    def width(self) -> int:
        """视频宽度."""
        return self._width

    @property
    def height(self) -> int:
        """视频高度."""
        return self._height

    @property
    def actual_fps(self) -> float:
        """实际帧率."""
        return self._actual_fps

    def set_resolution(self, width: int, height: int) -> bool:
        """
        设置分辨率。

        Args:
            width:  目标宽度
            height: 目标高度

        Returns:
            是否成功
        """
        if self._cap is None or not self._cap.isOpened():
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # 验证是否设置成功
        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if actual_w == width and actual_h == height:
            self._width = width
            self._height = height
            logger.info(f"分辨率已设置: {width}x{height}")
            return True
        else:
            logger.warning(
                f"分辨率设置失败, 请求 {width}x{height}, "
                f"实际 {actual_w}x{actual_h}"
            )
            self._width = actual_w
            self._height = actual_h
            return False

    def set_fps(self, fps: float) -> bool:
        """
        设置帧率。

        Args:
            fps: 目标帧率

        Returns:
            是否成功
        """
        if self._cap is None or not self._cap.isOpened():
            return False

        self._cap.set(cv2.CAP_PROP_FPS, fps)
        actual_fps = self._cap.get(cv2.CAP_PROP_FPS)

        if abs(actual_fps - fps) < 1.0:
            self._actual_fps = fps
            logger.info(f"帧率已设置: {fps}fps")
            return True
        else:
            logger.warning(f"帧率设置失败, 请求 {fps}fps, 实际 {actual_fps}fps")
            self._actual_fps = actual_fps
            return False
