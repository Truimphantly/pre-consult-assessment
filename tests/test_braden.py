"""Braden 量表测试：条目结构、分级边界、演示数据与报告输出。"""

import unittest

from app.engine import score
from app.errors import ScoreError
from app.models import Answer
from app.report import render_report
from app.scales import BRADEN, DEMO_ANSWERS, SCALE_REGISTRY

ALL_MIN = {
    "braden_sensory": "none",
    "braden_moisture": "constantly",
    "braden_activity": "bedfast",
    "braden_mobility": "immobile",
    "braden_nutrition": "very_poor",
    "braden_friction": "problem",
}

ALL_MAX = {
    "braden_sensory": "intact",
    "braden_moisture": "rarely",
    "braden_activity": "walks_frequently",
    "braden_mobility": "unlimited",
    "braden_nutrition": "excellent",
    "braden_friction": "no_problem",
}


def make_answers(mapping: dict[str, str]) -> list[Answer]:
    """把条目到选项的字典转成作答列表"""
    return [Answer(item_code=item, option_code=option) for item, option in mapping.items()]


class TestBradenStructure(unittest.TestCase):
    """题库结构"""

    def test_registered(self):
        self.assertIn("braden", SCALE_REGISTRY)
        self.assertIs(SCALE_REGISTRY["braden"], BRADEN)

    def test_item_count_and_range(self):
        self.assertEqual(len(BRADEN.items), 6)
        self.assertEqual(BRADEN.min_total, 6)
        self.assertEqual(BRADEN.max_total, 23)

    def test_standard_reference(self):
        self.assertIn("WS/T 888", BRADEN.standard_ref)
        self.assertIn("B.16", BRADEN.standard_ref)

    def test_levels_cover_every_score(self):
        for total in range(BRADEN.min_total, BRADEN.max_total + 1):
            hits = [level for level in BRADEN.levels if level.min_score <= total <= level.max_score]
            self.assertEqual(len(hits), 1, f"总分 {total} 命中 {len(hits)} 个分级")


class TestBradenLevels(unittest.TestCase):
    """分级边界（阈值来自 WS/T 888—2026 附录 B 表 B.16）"""

    def test_all_min_is_extreme(self):
        result = score("braden", make_answers(ALL_MIN))
        self.assertEqual(result.total, 6)
        self.assertEqual(result.level_label, "极高度风险")

    def test_all_max_is_no_risk(self):
        result = score("braden", make_answers(ALL_MAX))
        self.assertEqual(result.total, 23)
        self.assertEqual(result.level_label, "无风险")

    def test_demo_is_mild(self):
        result = score("braden", make_answers(DEMO_ANSWERS["braden"]))
        self.assertEqual(result.total, 15)
        self.assertEqual(result.level_label, "轻度风险")

    def test_boundary_9(self):
        mapping = {
            "braden_sensory": "very_limited",
            "braden_moisture": "often",
            "braden_activity": "bedfast",
            "braden_mobility": "very_limited",
            "braden_nutrition": "very_poor",
            "braden_friction": "problem",
        }
        result = score("braden", make_answers(mapping))
        self.assertEqual(result.total, 9)
        self.assertEqual(result.level_label, "极高度风险")

    def test_boundary_10(self):
        mapping = {
            "braden_sensory": "very_limited",
            "braden_moisture": "often",
            "braden_activity": "chairfast",
            "braden_mobility": "very_limited",
            "braden_nutrition": "very_poor",
            "braden_friction": "problem",
        }
        result = score("braden", make_answers(mapping))
        self.assertEqual(result.total, 10)
        self.assertEqual(result.level_label, "高度风险")

    def test_boundary_13(self):
        mapping = {
            "braden_sensory": "very_limited",
            "braden_moisture": "often",
            "braden_activity": "chairfast",
            "braden_mobility": "slightly_limited",
            "braden_nutrition": "probably_inadequate",
            "braden_friction": "potential_problem",
        }
        result = score("braden", make_answers(mapping))
        self.assertEqual(result.total, 13)
        self.assertEqual(result.level_label, "中度风险")

    def test_boundary_14(self):
        mapping = {
            "braden_sensory": "very_limited",
            "braden_moisture": "often",
            "braden_activity": "walks_occasionally",
            "braden_mobility": "slightly_limited",
            "braden_nutrition": "probably_inadequate",
            "braden_friction": "potential_problem",
        }
        result = score("braden", make_answers(mapping))
        self.assertEqual(result.total, 14)
        self.assertEqual(result.level_label, "中度风险")

    def test_boundary_18(self):
        mapping = {
            "braden_sensory": "slightly_limited",
            "braden_moisture": "occasionally",
            "braden_activity": "walks_occasionally",
            "braden_mobility": "slightly_limited",
            "braden_nutrition": "adequate",
            "braden_friction": "no_problem",
        }
        result = score("braden", make_answers(mapping))
        self.assertEqual(result.total, 18)
        self.assertEqual(result.level_label, "轻度风险")

    def test_boundary_19(self):
        mapping = {
            "braden_sensory": "intact",
            "braden_moisture": "rarely",
            "braden_activity": "walks_frequently",
            "braden_mobility": "slightly_limited",
            "braden_nutrition": "adequate",
            "braden_friction": "problem",
        }
        result = score("braden", make_answers(mapping))
        self.assertEqual(result.total, 19)
        self.assertEqual(result.level_label, "无风险")


class TestBradenValidation(unittest.TestCase):
    """校验与报告"""

    def test_missing_item(self):
        mapping = dict(ALL_MAX)
        del mapping["braden_friction"]
        with self.assertRaises(ScoreError) as ctx:
            score("braden", make_answers(mapping))
        self.assertIn("braden_friction", str(ctx.exception))

    def test_report_contains_scale_and_level(self):
        result = score("braden", make_answers(DEMO_ANSWERS["braden"]))
        text = render_report(result)
        self.assertIn("Braden", text)
        self.assertIn("15 / 23", text)
        self.assertIn("轻度风险", text)
        self.assertIn("摩擦与剪切力", text)


if __name__ == "__main__":
    unittest.main()
