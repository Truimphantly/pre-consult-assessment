"""计分引擎。

作用：把"作答"变成"计分结果"，只负责校验与流程；分值、分级阈值全部来自
app/scales.py（见 AGENT.md R4）。
"""

from __future__ import annotations

from app.errors import InputError, ScoreError
from app.models import Answer, Level, Scale, ScoreResult

import app.scales as scale_module


def load_answers(payload: object) -> tuple[str, list[Answer]]:
    """解析答案 JSON 结构
    作用：把外部 JSON 转成内部 Answer 列表，结构不合法时抛 InputError;
    Args:
        - payload: 已 json.loads 的对象，形如 {"scale_code": "adl", "answers": [...]};
    Return:
        - 元组（量表编码, 作答列表）;
    """
    if not isinstance(payload, dict):
        raise InputError("答案数据必须是 JSON 对象")
    scale_code = payload.get("scale_code")
    if not isinstance(scale_code, str) or not scale_code.strip():
        raise InputError("答案数据缺少 scale_code 字段")
    rows = payload.get("answers")
    if not isinstance(rows, list) or not rows:
        raise InputError("答案数据缺少非空的 answers 列表")
    answers: list[Answer] = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise InputError(f"第 {index} 条作答不是对象")
        item_code = row.get("item_code")
        option_code = row.get("option_code")
        if not isinstance(item_code, str) or not item_code.strip():
            raise InputError(f"第 {index} 条作答缺少 item_code")
        if not isinstance(option_code, str) or not option_code.strip():
            raise InputError(f"第 {index} 条作答缺少 option_code")
        answers.append(Answer(item_code=item_code, option_code=option_code))
    return scale_code, answers


def score(scale_code: str, answers: list[Answer]) -> ScoreResult:
    """计算一张量表的得分与分级
    作用：校验作答合法性后累加分项得分，并按分级区间给出分级与建议;
    Args:
        - scale_code: 量表编码，必须在 SCALE_REGISTRY 中注册;
        - answers: 作答列表，每个条目最多出现一次;
    Return:
        - ScoreResult: 统一计分结果;
    """
    if not answers:
        raise ScoreError("作答为空，无法计分")
    scale = scale_module.get_scale(scale_code)
    answer_map = _index_answers(scale, answers)
    missing = _missing_items(scale, answer_map)
    if missing:
        raise ScoreError("缺少必填条目：" + "、".join(missing))
    item_scores, item_labels, total = _accumulate(scale, answer_map)
    level = _pick_level(scale, total)
    return ScoreResult(
        scale_code=scale.code,
        scale_name=scale.name,
        standard_ref=scale.standard_ref,
        total=total,
        max_total=scale.max_total,
        item_scores=item_scores,
        item_labels=item_labels,
        level_label=level.label,
        advice=level.advice,
        missing=(),
    )


def _index_answers(scale: Scale, answers: list[Answer]) -> dict[str, str]:
    """把作答列表转成"条目编码 → 选项编码"映射
    作用：拦截未知条目与重复作答，保证后续累加只做一次遍历;
    Args:
        - scale: 目标量表;
        - answers: 作答列表;
    Return:
        - dict[str, str]: 条目编码到选项编码的映射;
    """
    item_codes = {item.code for item in scale.items}
    answer_map: dict[str, str] = {}
    for answer in answers:
        if answer.item_code not in item_codes:
            raise ScoreError(f"未知条目：{answer.item_code}（不属于量表 {scale.code}）")
        if answer.item_code in answer_map:
            raise ScoreError(f"条目重复作答：{answer.item_code}")
        answer_map[answer.item_code] = answer.option_code
    return answer_map


def _missing_items(scale: Scale, answer_map: dict[str, str]) -> list[str]:
    """找出缺失的必填条目
    作用：缺项必须整体报错，不允许用 0 分补齐（见 AGENT.md 禁止清单）;
    Args:
        - scale: 目标量表;
        - answer_map: 条目编码到选项编码的映射;
    Return:
        - list[str]: 缺失的条目编码列表;
    """
    return [item.code for item in scale.items if item.required and item.code not in answer_map]


def _accumulate(
    scale: Scale, answer_map: dict[str, str]
) -> tuple[dict[str, int], dict[str, str], int]:
    """累加各条目得分
    作用：按条目顺序取选项分值，返回分项分、选项标签与总分;
    Args:
        - scale: 目标量表;
        - answer_map: 条目编码到选项编码的映射;
    Return:
        - 元组（分项分, 选项标签, 总分）;
    """
    item_scores: dict[str, int] = {}
    item_labels: dict[str, str] = {}
    total = 0
    for item in scale.items:
        option_code = answer_map[item.code]
        option = _find_option(item, option_code)
        item_scores[item.code] = option.score
        item_labels[item.code] = option.label
        total += option.score
    return item_scores, item_labels, total


def _find_option(item, option_code: str):
    """在条目内查找选项
    作用：未知选项编码抛 ScoreError，禁止返回空值;
    Args:
        - item: 目标条目;
        - option_code: 选项编码;
    Return:
        - Option: 命中的选项;
    """
    for option in item.options:
        if option.code == option_code:
            return option
    allowed = "、".join(option.code for option in item.options)
    raise ScoreError(f"未知选项：{option_code}（条目 {item.code} 可用：{allowed}）")


def _pick_level(scale: Scale, total: int) -> Level:
    """按总分匹配分级
    作用：在量表分级区间中查找命中的等级;
    Args:
        - scale: 目标量表;
        - total: 总分;
    Return:
        - Level: 命中的分级;
    """
    for level in scale.levels:
        if level.min_score <= total <= level.max_score:
            return level
    raise ScoreError(f"总分 {total} 未命中任何分级区间，请检查 scales.py 的分级配置")
