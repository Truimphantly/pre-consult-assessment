"""健康检查测试：结构、中文输出、退出码与 JSON 契约。"""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from app.cli import main
from app.health import collect, render_text, to_payload


def run_cli(*argv: str) -> tuple[int, str, str]:
    """在捕获上下文中调用 main，返回（退出码, 标准输出, 错误输出）"""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestHealthModel(unittest.TestCase):
    """健康检查数据模型"""

    def test_collect_counts_match_registry(self):
        report = collect()
        self.assertEqual(report.scale_count, len(report.scale_codes))
        self.assertIn("adl", report.scale_codes)

    def test_rule_total_matches_checks(self):
        report = collect()
        self.assertEqual(report.rule_total, 9)
        self.assertLessEqual(report.rule_passed, report.rule_total)

    def test_ok_is_true_when_all_rules_pass(self):
        report = collect()
        self.assertTrue(report.ok, "存在规则违规时健康检查必须报不健康")

    def test_checked_at_format(self):
        report = collect()
        self.assertRegex(report.checked_at, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


class TestHealthRender(unittest.TestCase):
    """中文文本与 JSON 契约"""

    def test_render_text_fields(self):
        text = render_text(collect())
        for keyword in ("【系统健康检查】", "版本：", "已实现量表：", "规则扫描：", "结论："):
            self.assertIn(keyword, text)

    def test_render_text_conclusion(self):
        text = render_text(collect())
        self.assertTrue("健康" in text)

    def test_payload_keys(self):
        payload = to_payload(collect())
        for key in ("version", "scale_count", "scale_codes", "rule_total",
                    "rule_passed", "ok", "checked_at"):
            self.assertIn(key, payload)
        self.assertIsInstance(payload["scale_codes"], list)


class TestHealthCommand(unittest.TestCase):
    """命令行入口"""

    def test_health_text_exit_0(self):
        code, out, _ = run_cli("health")
        self.assertEqual(code, 0, out)
        self.assertIn("【系统健康检查】", out)

    def test_health_json(self):
        code, out, _ = run_cli("health", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["rule_total"], 9)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
