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

# ---------------------------------------------------------------- B.16 Braden
# 6 个条目，每项 1～4 分，摩擦与剪切力最高 3 分，总分 6～23 分。
# 分值越低风险越高；分级采用国内临床通用的 5 档划分。
BRADEN = Scale(
    code="braden",
    name="压力性损伤风险评估量表（Braden）",
    standard_ref="WS/T 888—2026 附录B 表B.16",
    items=(
        Item(
            code="braden_sensory",
            label="感知能力",
            options=(
                Option("none", "完全丧失", 1),
                Option("very_limited", "严重损害", 2),
                Option("slightly_limited", "轻度损害", 3),
                Option("intact", "完全无损害", 4),
            ),
        ),
        Item(
            code="braden_moisture",
            label="潮湿程度",
            options=(
                Option("constantly", "持续潮湿", 1),
                Option("often", "经常潮湿", 2),
                Option("occasionally", "偶尔潮湿", 3),
                Option("rarely", "很少潮湿", 4),
            ),
        ),
        Item(
            code="braden_activity",
            label="活动能力",
            options=(
                Option("bedfast", "卧床不起", 1),
                Option("chairfast", "轮椅行走", 2),
                Option("walks_occasionally", "偶尔行走", 3),
                Option("walks_frequently", "可独立活动", 4),
            ),
        ),
        Item(
            code="braden_mobility",
            label="移动能力",
            options=(
                Option("immobile", "完全不能移动", 1),
                Option("very_limited", "严重受限", 2),
                Option("slightly_limited", "轻度受限", 3),
                Option("unlimited", "完全自主", 4),
            ),
        ),
        Item(
            code="braden_nutrition",
            label="营养摄取",
            options=(
                Option("very_poor", "极差", 1),
                Option("probably_inadequate", "尚可", 2),
                Option("adequate", "良好", 3),
                Option("excellent", "极好", 4),
            ),
        ),
        Item(
            code="braden_friction",
            label="摩擦与剪切力",
            options=(
                Option("problem", "存在问题", 1),
                Option("potential_problem", "有潜在问题", 2),
                Option("no_problem", "无明显问题", 3),
            ),
        ),
    ),
    levels=(
        Level("无风险", 19, 23, "压力性损伤风险低，维持现有护理措施并按周复评。"),
        Level("轻度风险", 15, 18, "存在轻度压力性损伤风险，建议落实定时翻身与皮肤观察。"),
        Level("中度风险", 13, 14, "存在中度风险，建议使用减压装置并缩短翻身间隔。"),
        Level("高度风险", 10, 12, "存在高度风险，建议启动压力性损伤预防方案并每日评估皮肤。"),
        Level("极高度风险", 6, 9, "存在极高度风险，建议多学科会诊并做好交接班记录。"),
    ),
)

SCALE_REGISTRY[BRADEN.code] = BRADEN

# 演示数据：按量表编码分组，保证 --demo 能覆盖已实现的多张量表
DEMO_ANSWERS: dict[str, dict[str, str]] = {
    "adl": {
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
    },
    # 15 分：感知轻度损害、偶尔潮湿、轮椅行走、轻度受限、营养良好、潜在摩擦
    "braden": {
        "braden_sensory": "slightly_limited",
        "braden_moisture": "often",
        "braden_activity": "chairfast",
        "braden_mobility": "slightly_limited",
        "braden_nutrition": "adequate",
        "braden_friction": "potential_problem",
    },
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
