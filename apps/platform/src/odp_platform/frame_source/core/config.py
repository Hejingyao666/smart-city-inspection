#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  : config.py
# @Author    : 雨霓同学
# @Project   : ODPlatform / frame_source
# @Function  : 摄像头硬件配置 (Pydantic v2)
"""
摄像头配置类(基于 Pydantic v2 BaseModel,不继承宿主项目内部配置基类)。

设计原则:
    - 配置层不绑 logger:验证失败直接 raise ValidationError,
      由调用方决定记录方式
    - 字段封闭取值用 Literal,拼写错误第一时间被 Pydantic 拦下
    - 不可冻结:factory.py 需要 model_copy(update=...) 替换 camera_id
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# 封闭取值(IDE 自动补全 + 错拼立刻 raise)
CameraBackend = Literal["auto", "msmf", "dshow", "v4l2"]
CameraCodec   = Literal["MJPG", "YUYV", "H264", "MP4V"]


class CameraConfig(BaseModel):
    """
    摄像头配置(Pydantic v2)。

    示例:
        # 默认配置
        config = CameraConfig()

        # 高帧率(Windows 必须 MSMF 后端 + MJPG 编码)
        config = CameraConfig(width=1280, height=720, fps=90, backend="msmf")

    字段说明:
        camera_id : OpenCV 设备 ID(≥ 0)
        width     : 请求分辨率宽(实际生效以 set+get 协商结果为准)
        height    : 请求分辨率高
        fps       : 请求帧率(高帧率必须配 MJPG codec + msmf 后端)
        backend   : 摄像头后端
            "auto"  跨平台默认,系统自选
            "msmf"  Windows Media Foundation,支持高帧率
            "dshow" DirectShow,Windows 兼容性好
            "v4l2"  Linux Video4Linux2
        codec     : FOURCC 编码,高帧率必须 MJPG
    """

    model_config = ConfigDict(
        extra="forbid",              # 拼错字段名第一时间拦下
        validate_assignment=True,    # 后续赋值也走验证
    )

    camera_id: int = Field(default=0,    ge=0,            description="OpenCV 设备 ID")
    width:     int = Field(default=1280, gt=0, le=7680,   description="请求分辨率宽")
    height:    int = Field(default=720,  gt=0, le=4320,   description="请求分辨率高")
    fps:       int = Field(default=30,   gt=0, le=1000,   description="请求帧率")

    backend: CameraBackend = Field(default="auto", description="摄像头后端")
    codec:   CameraCodec   = Field(default="MJPG", description="FOURCC 编码")

    # ── 曝光控制(暗光下锁帧率用)──────────────────────────────
    # 两个都默认 None = 不干预驱动默认值, 100% 保持旧行为(老配置不受影响).
    # 暗光掉帧的根因是自动曝光把快门时间拉长(>1/fps): 90fps 要求曝光 ≤ 11ms,
    # 暗处自动曝光会拉到 ~14ms 去多收光 → 帧率被压到 ~72fps. 锁短曝光即可稳住帧率
    # (代价: 画面变暗). 详见 camera.py 的下发逻辑与撞墙记录.
    auto_exposure: Optional[bool] = Field(
        default=None,
        description="自动曝光开关: None=不干预(默认); True=自动; False=手动(配合 exposure 锁定帧率)",
    )
    exposure: Optional[float] = Field(
        default=None,
        description=(
            "手动曝光值: None=不干预(默认); 仅 auto_exposure=False 时生效. "
            "取值刻度【依后端而定】, 不做范围校验: "
            "Windows(msmf/dshow)是 log2(秒) —— -7≈1/128s≈7.8ms(够 90fps), -6≈1/64s≈15.6ms; "
            "Linux v4l2 多为正整数(单位 100µs 量级, 因驱动而异)."
        ),
    )

    def get_resolution(self) -> tuple[int, int, int]:
        """返回 (width, height, fps) 三元组"""
        return (self.width, self.height, self.fps)
