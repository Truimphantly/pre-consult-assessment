"""命令行契约测试：退出码、输出格式、错误提示。"""

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from app.cli import main


class CommandResult:
    """一次命令调用的捕获结果"""

    def __init__(self, code: int, out: str, err: str):
        self.code = code
        self.out = out
        self.err = err


def run_cli(*argv: str) -> CommandResult:
    """在捕获上下文中调用 main"""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return CommandResult(code, out.getvalue(), err.getvalue())


class TestSmokeCommands(unittest.TestCase):
    """冒烟与列举命令"""

    def test_self_check(self):
        result = run_cli("self-check")
        self.assertEqual(result.code, 0)
        self.assertIn("量表评估系统", result.out)
        self.assertIn("已实现量表", result.out)

    def test_list_scales(self):
        result = run_cli("list-scales")
        self.assertEqual(result.code, 0)
        self.assertIn("[adl]", result.out)
        self.assertIn("条目数：10", result.out)

    def test_rule_check_passes(self):
        result = run_cli("rule-check")
        self.assertEqual(result.code, 0, result.out)
        self.assertIn("规则扫描：8/8 通过", result.out)


class TestScoreAndReport(unittest.TestCase):
    """计分与报告命令"""

    def test_score_demo_json(self):
        result = run_cli("score", "--scale", "adl", "--demo")
        self.assertEqual(result.code, 0)
        payload = json.loads(result.out)
        self.assertEqual(payload["scale_code"], "adl")
        self.assertEqual(payload["total"], 85)
        self.assertEqual(payload["level_label"], "轻度依赖")
        self.assertEqual(payload["missing"], [])

    def test_report_demo_text(self):
        result = run_cli("report", "--scale", "adl", "--demo")
        self.assertEqual(result.code, 0)
        self.assertIn("轻度依赖", result.out)
        self.assertIn("请医师结合临床确认", result.out)

    def test_default_command_uses_demo(self):
        result = run_cli("score")
        self.assertEqual(result.code, 0)
        self.assertEqual(json.loads(result.out)["total"], 85)


class TestErrorHandling(unittest.TestCase):
    """错误路径：中文提示 + 退出码 1"""

    def test_unknown_scale_exits_1(self):
        result = run_cli("score", "--scale", "nrs2002", "--demo")
        self.assertEqual(result.code, 1)
        self.assertIn("错误：", result.err)
        self.assertIn("未注册的量表", result.err)

    def test_missing_file_exits_1(self):
        result = run_cli("score", "--scale", "adl", "--answers", "不存在的答案.json")
        self.assertEqual(result.code, 1)
        self.assertIn("答案文件不存在", result.err)

    def test_answer_scale_mismatch_exits_1(self):
        result = run_cli("score", "--scale", "adl", "--answers", "tests/fixtures/scale_mismatch.json")
        self.assertEqual(result.code, 1)
        self.assertIn("不一致", result.err)


if __name__ == "__main__":
    unittest.main()
