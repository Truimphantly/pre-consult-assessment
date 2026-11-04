"""健康检查。

作用：汇总版本号、已实现量表、硬性规则扫描结果与检查时间，
     供本地自检、CI 门禁与运维探活使用；不依赖任何外部文件与网络。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app import __version__
from app.scales import SCALE_REGISTRY
from app.selfcheck import run_all


@dataclass(frozen=True)
class HealthReport:
    """一次健康检查的结果。"""

    version: str
    scale_count: int
    scale_codes: tuple[str, ...]
    rule_total: int
    rule_passed: int
    checked_at: str

    @property
    def ok(self) -> bool:
        """规则全部通过时视为健康。"""
        return self.rule_passed == self.rule_total


def collect() -> HealthReport:
    """执行一次健康检查
    作用：跑一遍规则扫描，汇总版本、量表与检查时间;
    Args:
        - 无;
    Return:
        - HealthReport: 不可变健康检查结果;
    """
    results = run_all()
    passed = sum(1 for item in results if item.ok)
    return HealthReport(
        version=__version__,
        scale_count=len(SCALE_REGISTRY),
        scale_codes=tuple(sorted(SCALE_REGISTRY)),
        rule_total=len(results),
        rule_passed=passed,
        checked_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def render_text(report: HealthReport) -> str:
    """渲染中文健康检查文本
    作用：输出版本、量表清单、规则扫描结论与检查时间;
    Args:
        - report: 健康检查结果;
    Return:
        - str: 多行中文文本;
    """
    scale_text = "、".join(report.scale_codes)
    conclusion = "健康" if report.ok else "存在规则违规，请先修复"
    return "\n".join(
        [
            "【系统健康检查】",
            f"版本：{report.version}",
            f"已实现量表：{report.scale_count} 张（{scale_text}）",
            f"规则扫描：{report.rule_passed}/{report.rule_total} 通过",
            f"检查时间：{report.checked_at}",
            f"结论：{conclusion}",
        ]
    )


def to_payload(report: HealthReport) -> dict:
    """转换为对外 JSON 结构
    作用：供 --json 分支与其他程序消费;
    Args:
        - report: 健康检查结果;
    Return:
        - dict: 可序列化字典;
    """
    return {
        "version": report.version,
        "scale_count": report.scale_count,
        "scale_codes": list(report.scale_codes),
        "rule_total": report.rule_total,
        "rule_passed": report.rule_passed,
        "ok": report.ok,
        "checked_at": report.checked_at,
    }
