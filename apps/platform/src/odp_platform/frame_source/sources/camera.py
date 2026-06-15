#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : camera.py
# @Author    : 雨霓同学
# @Project   : ODPlatform / frame_source
# @Function  : 摄像头输入源 — 跨平台 + 后端协商 + 参数验证
"""
摄像头输入源。

工程要点(均为撞墙记录,改动前请先理解):
    1. MSMF 后端必须在 cv2.VideoCapture 创建之前设置环境变量
       OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS=0,否则帧率下降 20-30%
    2. 参数设置顺序必须是: 宽高 → FOURCC → FPS,
       否则 MSMF 下高帧率请求会被驱动重新协商时覆盖,完全失效
    3. set() 是请求不是命令,必须 read 一帧触发驱动协商,再 get 读回真实值
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import cv2

from odp_platform.frame_source.core.base   import FrameSource
from odp_platform.frame_source.core.config import CameraConfig
from odp_platform.frame_source.core.types  import Frame, FrameInfo, SourceType


logger = logging.getLogger(__name__)


class CameraSource(FrameSource):
    """
    摄像头输入源,支持指定分辨率/帧率/后端/编码。

    示例:
        # 默认配置
        config = CameraConfig()
        with CameraSource(config) as cam:
            for frame in cam:
                process(frame.image)

        # 高帧率(Windows MSMF + MJPG)
        config = CameraConfig(width=1280, height=720, fps=90, backend="msmf")
        with CameraSource(config) as cam:
            for frame in cam:
                process(frame.image)
    """

    def __init__(self, config: CameraConfig):
        super().__init__(str(config.camera_id))
        self.config = config
        self._cap: Optional[cv2.VideoCapture] = None
        self._width  = 0
        self._height = 0
        self._fps    = 0.0

    def open(self) -> bool:
        # ── 撞墙记录 ①: MSMF 必须在 VideoCapture 之前设置环境变量 ──
        # 该环境变量关闭 MSMF 自动插入的硬件色彩转换滤镜(HW Transforms),
        # 否则会导致帧率下降 20~30%。必须在初始化前设置才生效。
        if self.config.backend == "msmf":
            os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

        self._cap = cv2.VideoCapture(self.config.camera_id, self._get_backend())

        if not self._cap.isOpened():
            logger.error(f"无法打开摄像头 {self.config.camera_id}")
            return False

        # ── 撞墙记录 ②: 参数设置顺序 宽高 → FOURCC → FPS ──
        # 正确顺序:
        #   1. 先设分辨率:驱动据此筛选可用的媒体类型列表
        #   2. 再设 FOURCC:从上一步的列表中选择编码格式(MJPG)
        #   3. 最后设 FPS:格式锁定后才约束帧率
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.config.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.config.codec))
        self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)

        # ── 曝光控制: 在协商读帧之前下发 auto_exposure / exposure (两者都没配则一个字节都不碰) ──
        self._apply_exposure()

        # ── 撞墙记录 ③: MSMF/DSHOW 懒初始化,必须 read 一帧触发协商 ──
        # set() 只是登记意图,驱动在第一次 read() 时才真正与摄像头硬件
        # 协商并锁定格式。没有这次 read(),下面的 get() 读回的是"请求值"
        # 而非"实际值"。
        ret, _ = self._cap.read()
        if not ret:
            logger.warning("格式协商触发帧读取失败,实际参数可能不准确")

        # 读回实际生效的参数
        self._width  = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps    = self._cap.get(cv2.CAP_PROP_FPS)

        # ── "我设了" ≠ "它生效了":验证差异并 warning ──
        if self._width != self.config.width or self._height != self.config.height:
            logger.warning(
                f"分辨率未完全生效:期望 {self.config.width}x{self.config.height},"
                f"实际 {self._width}x{self._height}"
            )
        if self._fps < self.config.fps * 0.9:    # 允许 10% 误差
            logger.warning(
                f"帧率未完全生效:期望 {self.config.fps}fps,"
                f"实际标称 {self._fps:.1f}fps"
            )

        logger.info(
            f"摄像头已打开 (backend={self.config.backend}, codec={self.config.codec})"
        )
        logger.info(
            f"  目标: {self.config.width}x{self.config.height} @ {self.config.fps}fps"
        )
        logger.info(
            f"  实际: {self._width}x{self._height} @ {self._fps:.1f}fps"
        )
        return True

    def _get_backend(self) -> int:
        """将配置字符串映射为 OpenCV 后端常量(Pydantic 已保证不会传非法值)"""
        backends = {
            "auto":  cv2.CAP_ANY,
            "msmf":  cv2.CAP_MSMF,
            "dshow": cv2.CAP_DSHOW,
            "v4l2":  cv2.CAP_V4L2,
        }
        return backends[self.config.backend]

    def _apply_exposure(self) -> None:
        """按 config 下发 auto_exposure / exposure 并读回校验.

        两个字段都默认 None = 一个字节都不碰, 100% 等价旧行为.
        顺序铁律: 先关自动曝光(切手动), 再写手动曝光值 —— 反了的话手动值会被自动逻辑覆盖.

        撞墙记录: AUTO_EXPOSURE 取值在不同后端语义不统一, 不能假设一定生效:
            dshow / v4l2 / auto : 0.25=手动, 0.75=自动 (OpenCV 沿用 V4L2 历史约定, 较可靠)
            msmf                : 0.0 =手动, 0.75=自动 (Media Foundation; 实测因驱动/版本而异, 最不稳)
        所以设完一律 get() 读回 + 比对 + warning. Windows 上锁曝光不灵时优先改 backend='dshow',
        或直接在罗技 Logi Tune 里关掉自动曝光(RightLight).
        """
        cfg = self.config
        if cfg.auto_exposure is None and cfg.exposure is None:
            return  # 都没配 → 不干预, 等价旧行为

        manual_v, auto_v = {
            "auto":  (0.25, 0.75),
            "dshow": (0.25, 0.75),
            "v4l2":  (0.25, 0.75),
            "msmf":  (0.0,  0.75),
        }.get(cfg.backend, (0.25, 0.75))

        # 1) 自动 / 手动模式 (必须先设, 后面手动曝光值才压得住)
        if cfg.auto_exposure is not None:
            want = auto_v if cfg.auto_exposure else manual_v
            self._cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, want)
            got = self._cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            logger.info("  曝光模式: 请求%s (AUTO_EXPOSURE=%.2f), 读回=%.3f",
                        "自动" if cfg.auto_exposure else "手动", want, got)
            if abs(got - want) > 1e-3:
                logger.warning(
                    "AUTO_EXPOSURE 疑似未生效 (请求 %.2f, 读回 %.3f). 曝光控制各后端差异大: "
                    "msmf 最不稳, Windows 上建议改 backend='dshow' 重试, 或在 Logi Tune 里关自动曝光.",
                    want, got,
                )

        # 2) 手动曝光值 (仅手动模式有意义)
        if cfg.exposure is not None:
            if cfg.auto_exposure is not False:
                logger.warning(
                    "exposure=%s 但 auto_exposure 不是 False —— 自动曝光开着时手动值不会生效. "
                    "锁曝光请同时设 auto_exposure=false.", cfg.exposure,
                )
            self._cap.set(cv2.CAP_PROP_EXPOSURE, float(cfg.exposure))
            got = self._cap.get(cv2.CAP_PROP_EXPOSURE)
            logger.info("  曝光值: 请求=%s, 读回=%s (Windows 后端 log2 秒: -7≈7.8ms, -6≈15.6ms)",
                        cfg.exposure, got)
            if abs(got - float(cfg.exposure)) > 1e-3:
                logger.warning(
                    "EXPOSURE 疑似未生效 (请求 %s, 读回 %s); 同样建议试 dshow 后端或相机厂商工具.",
                    cfg.exposure, got,
                )

    def read(self) -> Optional[Frame]:
        if self._cap is None:
            return None

        ret, image = self._cap.read()
        if not ret:
            return None

        info = FrameInfo(
            width=self._width,
            height=self._height,
            source_type=SourceType.CAMERA,
            source_path=self.source_path,
            frame_index=self._frame_index,
            timestamp=time.time() - self._start_time,
            fps=self._fps,
            filename=f"camera:{self.config.camera_id}",
        )
        self._frame_index += 1
        return Frame(image=image, info=info)

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("摄像头已关闭")

    def get_source_type(self) -> SourceType:
        return SourceType.CAMERA
