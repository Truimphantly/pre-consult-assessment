"""题库一致性测试：条目数、分值区间、分级覆盖。"""

import unittest

from app.models import Scale
from app.scales import ADL, SCALE_REGISTRY, get_scale
from app.errors import ScoreError


class TestScaleRegistry(unittest.TestCase):
    """量表注册表与题库结构"""

    def test_registry_contains_adl(self):
        self.assertIn("adl", SCALE_REGISTRY)

    def test_get_scale_unknown_raises(self):
        with self.assertRaises(ScoreError) as ctx:
            get_scale("braden")
        self.assertIn("未注册的量表", str(ctx.exception))

    def test_adl_item_count(self):
        self.assertEqual(len(ADL.items), 10)

    def test_each_item_has_unique_options(self):
        for item in ADL.items:
            self.assertGreaterEqual(len(item.options), 2, item.code)
            codes = [option.code for option in item.options]
            self.assertEqual(len(codes), len(set(codes)), item.code)

    def test_adl_total_range(self):
        self.assertEqual(ADL.min_total, 0)
        self.assertEqual(ADL.max_total, 100)

    def test_adl_standard_reference(self):
        self.assertIn("WS/T 888", ADL.standard_ref)
        self.assertIn("B.1", ADL.standard_ref)

    def test_levels_cover_every_score_once(self):
        for total in range(ADL.min_total, ADL.max_total + 1):
            hits = [level for level in ADL.levels if level.min_score <= total <= level.max_score]
            self.assertEqual(len(hits), 1, f"总分 {total} 命中 {len(hits)} 个分级")

    def test_levels_are_ordered(self):
        levels = sorted(ADL.levels, key=lambda level: level.min_score)
        for previous, current in zip(levels, levels[1:]):
            self.assertEqual(previous.max_score + 1, current.min_score)

    def test_scale_dataclass_is_frozen(self):
        with self.assertRaises(Exception):
            ADL.code = "other"  # type: ignore[misc]

    def test_all_scales_are_scale_instances(self):
        for scale in SCALE_REGISTRY.values():
            self.assertIsInstance(scale, Scale)


if __name__ == "__main__":
    unittest.main()
