"""数据验证的统一结果模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class Severity(Enum):
    """检查严重程度。"""
    INFO  = "info"
    WARN  = "warn"
    ERROR = "error"


@dataclass
class CheckResult:
    """单个 check 的返回值。"""
    name: str
    passed: bool
    severity: Severity
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """所有 check 的汇总。"""
    results: List[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(
            r.severity == Severity.ERROR and not r.passed
            for r in self.results
        )

    @property
    def errors(self) -> List[CheckResult]:
        return [r for r in self.results if r.severity == Severity.ERROR and not r.passed]

    @property
    def warnings(self) -> List[CheckResult]:
        return [r for r in self.results if r.severity == Severity.WARN and not r.passed]
