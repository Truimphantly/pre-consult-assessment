"""量表题库：条目、选项、分值与分级阈值。

本文件是**唯一允许出现量表分值与阈值的地方**（见 AGENT.md R4）。
阈值来源：WS/T 888—2026《医疗机构老年综合评估技术操作标准》附录 B，表 B.1。
一期实现：ADL（Barthel 指数，10 项，0～100 分）。
"""

from __future__ import annotations

from app.errors import ScoreError
from app.models import Item, Level, Option, Scale

# ---------------------------------------------------------------- B.1 ADL
ADL = Scale(
    code="adl",
    name="日常生活活动能力评定量表（Barthel 指数）",
    standard_ref="WS/T 888—2026 附录B 表B.1",
    items=(
        Item(
            code="adl_eat",
            label="进食",
            options=(
                Option("full", "独立进食", 10),
                Option("partial", "需部分帮助", 5),
                Option("none", "需极大帮助或完全依赖", 0),
            ),
        ),
        Item(
            code="adl_bath",
            label="洗澡",
            options=(
                Option("full", "可独立完成", 5),
                Option("none", "需他人帮助", 0),
            ),
        ),
        Item(
            code="adl_groom",
            label="修饰（洗脸、刷牙、梳头）",
            options=(
                Option("full", "可独立完成", 5),
                Option("none", "需他人帮助", 0),
            ),
        ),
        Item(
            code="adl_dress",
            label="穿衣",
            options=(
                Option("full", "独立完成", 10),
                Option("partial", "需部分帮助", 5),
                Option("none", "完全依赖", 0),
            ),
        ),
        Item(
            code="adl_bowel",
            label="大便控制",
            options=(
                Option("full", "能控制", 10),
                Option("partial", "偶有失禁", 5),
                Option("none", "失禁或需灌肠", 0),
            ),
        ),
        Item(
            code="adl_bladder",
            label="小便控制",
            options=(
                Option("full", "能控制", 10),
                Option("partial", "偶有失禁", 5),
                Option("none", "失禁或留置导尿", 0),
            ),
        ),
        Item(
            code="adl_toilet",
            label="如厕",
            options=(
                Option("full", "独立完成", 10),
                Option("partial", "需部分帮助", 5),
                Option("none", "完全依赖", 0),
            ),
        ),
        Item(
            code="adl_transfer",
            label="床椅转移",
            options=(
                Option("full", "独立完成", 15),
                Option("partial", "需少量帮助", 10),
                Option("minimal", "能坐但需大量帮助", 5),
                Option("none", "完全依赖", 0),
            ),
        ),
        Item(
            code="adl_walk",
            label="平地行走",
            options=(
                Option("full", "独立行走", 15),
                Option("partial", "需一人帮助", 10),
                Option("wheelchair", "能自行使用轮椅", 5),
                Option("none", "卧床或完全依赖", 0),
            ),
        ),
        Item(
            code="adl_stairs",
            label="上下楼梯",
            options=(
                Option("full", "独立完成", 10),
                Option("partial", "需帮助", 5),
                Option("none", "不能完成", 0),
            ),
        ),
    ),
    levels=(
        Level("自理", 100, 100, "生活基本自理，建议保持规律活动并按年度复评。"),
        Level("轻度依赖", 61, 99, "存在轻度依赖，建议关注跌倒风险与工具性日常生活能力，3 个月后复评。"),
        Level("中度依赖", 41, 60, "存在中度依赖，建议评估照护者支持与辅具适配，1 个月内复评。"),
        Level("重度依赖", 0, 40, "存在重度依赖，建议安排专人照护，并排查吞咽、压力性损伤与营养风险。"),
    ),
)

SCALE_REGISTRY: dict[str, Scale] = {ADL.code: ADL}

# 演示数据：10 项均有作答，总分 85（平地行走需一人帮助、上下楼梯不能完成）
DEMO_ANSWERS: dict[str, str] = {
    "adl_eat": "full",
    "adl_bath": "full",
    "adl_groom": "full",
    "adl_dress": "full",
    "adl_bowel": "full",
    "adl_bladder": "full",
    "adl_toilet": "full",
    "adl_transfer": "full",
    "adl_walk": "partial",
    "adl_stairs": "none",
}


def get_scale(scale_code: str) -> Scale:
    """按编码取量表
    作用：统一量表查找入口，未注册编码抛 ScoreError;
    Args:
        - scale_code: 量表编码，例如 "adl";
    Return:
        - Scale: 已注册的量表对象;
    """
    scale = SCALE_REGISTRY.get(scale_code)
    if scale is None:
        registered = "、".join(sorted(SCALE_REGISTRY))
        raise ScoreError(f"未注册的量表：{scale_code}（当前可用：{registered}）")
    return scale
