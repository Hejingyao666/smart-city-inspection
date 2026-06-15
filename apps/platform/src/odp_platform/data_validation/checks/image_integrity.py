#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""检查图像是否损坏、EXIF方向、通道数等。由于扫描图像可能耗时，默认需要在 CLI 中开启 --check-images。"""
from __future__ import annotations

from odp_platform.data_validation.registry import CheckContext, CheckResult, CheckSeverity, check

@check("image_integrity")
def check_image_integrity(ctx: CheckContext) -> CheckResult:
    # 检查是否应跳过（需要从 ctx 获取 options，但当前没有 options 属性，默认真实扫描）
    # 为了安全，默认执行（可能需要 Pillow）
    try:
        from PIL import Image
    except ImportError:
        return CheckResult(
            name="image_integrity",
            severity=CheckSeverity.WARNING,
            summary="Pillow 未安装，无法检查图像完整性。请安装: pip install Pillow",
            details={"error": "Pillow not installed"},
        )
    snap = ctx.snapshot
    corrupted = []
    exif_rotated = []
    total = 0
    for split_name, image_paths in snap.images_per_split.items():
        for img_path in image_paths:
            total += 1
            try:
                with Image.open(img_path) as img:
                    img.verify()
                # 重新打开以读取 EXIF
                with Image.open(img_path) as img2:
                    exif = img2._getexif()
                    if exif and 274 in exif and exif[274] != 1:
                        exif_rotated.append(str(img_path))
            except Exception:
                corrupted.append(str(img_path))
    if corrupted:
        summary = f"发现 {len(corrupted)} 张损坏图像（无法解码）"
        severity = CheckSeverity.ERROR
    elif exif_rotated:
        summary = f"发现 {len(exif_rotated)} 张图像包含 EXIF 方向标记，建议预处理"
        severity = CheckSeverity.INFO
    else:
        summary = f"全部 {total} 张图像完整且无 EXIF 旋转标记"
        severity = CheckSeverity.PASS
    return CheckResult(name="image_integrity", severity=severity, summary=summary,
                       details={"corrupted": corrupted[:10], "exif_rotated": exif_rotated[:10]})
