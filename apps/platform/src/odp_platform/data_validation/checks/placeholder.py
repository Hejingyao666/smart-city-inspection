#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :placeholder.py
# @Time      :2026/6/10 10:38:18
# @Author    :雨霓同学
# @Project   :ODPlatform
# @Function  :
from odp_platform.data_validation.registry import (check, CheckContext, CheckResult, CheckSeverity)

@check("placeholder")
def placeholder_check(ctx: CheckContext) -> CheckResult:
    """占位 check, 框架启动时自动注册, 供测试用。"""
    return CheckResult(
        name="placeholder",
        severity=CheckSeverity.INFO,
        summary="这是一个占位 check, 框架启动时自动注册, 供测试用",
        details={"message": "这是占位 check, 框架启动时自动注册, 供测试用"},
    )
