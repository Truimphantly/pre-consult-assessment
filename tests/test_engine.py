"""计分引擎测试：满分、分级边界、缺项、重复、未知编码、输入解析。"""

import unittest

from app.engine import load_answers, score
from app.errors import InputError, ScoreError
from app.models import Answer
from app.scales import DEMO_ANSWERS

ALL_FULL = {
    "adl_eat": "full",
    "adl_bath": "full",
    "adl_groom": "full",
    "adl_dress": "full",
    "adl_bowel": "full",
    "adl_bladder": "full",
    "adl_toilet": "full",
    "adl_transfer": "full",
    "adl_walk": "full",
    "adl_stairs": "full",
}


def make_answers(mapping: dict[str, str]) -> list[Answer]:
    """把"条目→选项"字典转成作答列表"""
    return [Answer(item_code=item, option_code=option) for item, option in mapping.items()]


class TestScoreBasics(unittest.TestCase):
    """正常计分"""

    def test_full_score_is_independent(self):
        result = score("adl", make_answers(ALL_FULL))
        self.assertEqual(result.total, 100)
        self.assertEqual(result.max_total, 100)
        self.assertEqual(result.level_label, "自理")

    def test_demo_data_scores_85(self):
        result = score("adl", make_answers(DEMO_ANSWERS))
        self.assertEqual(result.total, 85)
        self.assertEqual(result.level_label, "轻度依赖")
        self.assertIn("3 个月后复评", result.advice)

    def test_zero_score_is_severe(self):
        mapping = {item: "none" for item in ALL_FULL}
        result = score("adl", make_answers(mapping))
        self.assertEqual(result.total, 0)
        self.assertEqual(result.level_label, "重度依赖")

    def test_item_scores_and_labels(self):
        result = score("adl", make_answers(ALL_FULL))
        self.assertEqual(result.item_scores["adl_walk"], 15)
        self.assertEqual(result.item_labels["adl_eat"], "独立进食")
        self.assertEqual(len(result.item_scores), 10)

    def test_result_has_no_missing_when_complete(self):
        result = score("adl", make_answers(ALL_FULL))
        self.assertEqual(result.missing, ())
        self.assertEqual(result.standard_ref, "WS/T 888—2026 附录B 表B.1")


class TestLevelBoundaries(unittest.TestCase):
    """分级边界：Barthel 分值是 5 的倍数，测可达取值"""

    def test_65_is_mild(self):
        mapping = dict(ALL_FULL)
        mapping.update(
            {"adl_walk": "none", "adl_toilet": "partial", "adl_transfer": "partial", "adl_stairs": "none"}
        )
        result = score("adl", make_answers(mapping))
        self.assertEqual(result.total, 65)
        self.assertEqual(result.level_label, "轻度依赖")

    def test_60_is_moderate(self):
        mapping = dict(ALL_FULL)
        mapping.update(
            {
                "adl_dress": "partial",
                "adl_transfer": "minimal",
                "adl_walk": "none",
                "adl_stairs": "none",
            }
        )
        result = score("adl", make_answers(mapping))
        self.assertEqual(result.total, 60)
        self.assertEqual(result.level_label, "中度依赖")


class TestScoreValidation(unittest.TestCase):
    """异常与校验"""

    def test_unknown_scale(self):
        with self.assertRaises(ScoreError):
            score("nrs2002", make_answers(ALL_FULL))

    def test_unknown_item(self):
        mapping = dict(ALL_FULL)
        mapping["adl_unknown"] = "full"
        with self.assertRaises(ScoreError) as ctx:
            score("adl", make_answers(mapping))
        self.assertIn("未知条目", str(ctx.exception))

    def test_unknown_option(self):
        mapping = dict(ALL_FULL)
        mapping["adl_eat"] = "huge"
        with self.assertRaises(ScoreError) as ctx:
            score("adl", make_answers(mapping))
        self.assertIn("未知选项", str(ctx.exception))

    def test_duplicate_item(self):
        answers = make_answers(ALL_FULL) + [Answer(item_code="adl_eat", option_code="none")]
        with self.assertRaises(ScoreError) as ctx:
            score("adl", answers)
        self.assertIn("重复作答", str(ctx.exception))

    def test_missing_item_lists_code(self):
        mapping = dict(ALL_FULL)
        del mapping["adl_bath"]
        with self.assertRaises(ScoreError) as ctx:
            score("adl", make_answers(mapping))
        self.assertIn("缺少必填条目", str(ctx.exception))
        self.assertIn("adl_bath", str(ctx.exception))

    def test_empty_answers(self):
        with self.assertRaises(ScoreError):
            score("adl", [])


class TestLoadAnswers(unittest.TestCase):
    """外部 JSON 解析"""

    def test_valid_payload(self):
        payload = {
            "scale_code": "adl",
            "answers": [
                {"item_code": "adl_eat", "option_code": "full"},
                {"item_code": "adl_bath", "option_code": "none"},
            ],
        }
        scale_code, answers = load_answers(payload)
        self.assertEqual(scale_code, "adl")
        self.assertEqual(len(answers), 2)
        self.assertEqual(answers[0].item_code, "adl_eat")

    def test_not_a_dict(self):
        with self.assertRaises(InputError):
            load_answers([1, 2, 3])

    def test_missing_answers(self):
        with self.assertRaises(InputError):
            load_answers({"scale_code": "adl"})

    def test_row_missing_item_code(self):
        with self.assertRaises(InputError):
            load_answers({"scale_code": "adl", "answers": [{"option_code": "full"}]})

    def test_row_missing_option_code(self):
        with self.assertRaises(InputError):
            load_answers({"scale_code": "adl", "answers": [{"item_code": "adl_eat"}]})


if __name__ == "__main__":
    unittest.main()
