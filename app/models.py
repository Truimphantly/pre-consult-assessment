"""数据结构定义。

作用：用不可变 dataclass 描述"量表—条目—选项—分级"与"作答—计分结果"，
供 scales / engine / report / cli 共用，避免各层各自定义字典结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Option:
    """选项：一个可选答案及其对应分值。"""

    code: str
    label: str
    score: int


@dataclass(frozen=True)
class Item:
    """条目：量表中的一个问句，包含若干互斥选项。"""

    code: str
    label: str
    options: tuple[Option, ...]
    required: bool = True


@dataclass(frozen=True)
class Level:
    """分级：总分区间对应的依赖程度与建议。"""

    label: str
    min_score: int
    max_score: int
    advice: str


@dataclass(frozen=True)
class Scale:
    """量表：条目集合 + 分级规则 + 标准来源。"""

    code: str
    name: str
    standard_ref: str
    items: tuple[Item, ...]
    levels: tuple[Level, ...]

    @property
    def max_total(self) -> int:
        """满分：各条目最大可选分值之和。"""
        return sum(max(option.score for option in item.options) for item in self.items)

    @property
    def min_total(self) -> int:
        """最低分：各条目最小可选分值之和。"""
        return sum(min(option.score for option in item.options) for item in self.items)


@dataclass(frozen=True)
class Answer:
    """一次作答：条目编码 + 所选选项编码。"""

    item_code: str
    option_code: str


@dataclass(frozen=True)
class ScoreResult:
    """计分结果：下游（报告、接口、数据库）唯一依赖的结构。"""

    scale_code: str
    scale_name: str
    standard_ref: str
    total: int
    max_total: int
    item_scores: dict[str, int] = field(default_factory=dict)
    item_labels: dict[str, str] = field(default_factory=dict)
    level_label: str = ""
    advice: str = ""
    missing: tuple[str, ...] = ()
