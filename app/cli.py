"""命令行入口。

命令契约见 docs/命令接口约定.md；本文件是全项目唯一允许退出进程的地方（AGENT.md R8）。
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import unittest
from pathlib import Path

from app import __version__
from app.engine import load_answers, score
from app.errors import InputError, ScoreError
from app.health import collect, render_text, to_payload
from app.models import Answer, ScoreResult
from app.report import render_report
from app.scales import DEMO_ANSWERS, SCALE_REGISTRY, get_scale
from app.selfcheck import format_report, run_all

ROOT = Path(__file__).resolve().parent.parent

# 子命令登记表：help 文本集中在此，rules 检查 R9 会核对它与两份文档是否一致
COMMANDS: dict[str, str] = {
    "self-check": "冒烟检查：版本、量表、命令",
    "list-scales": "列出已实现量表",
    "rule-check": "扫描硬性规则 R1～R9",
    "score": "计分并输出 JSON",
    "report": "计分并输出中文报告",
    "health": "健康检查：版本、量表、规则扫描结果",
    "verify": "一键验收：规则扫描 + 单元测试",
}


def main(argv: list[str] | None = None) -> int:
    """命令行主入口
    作用：解析子命令并分发，统一处理业务异常与退出码;
    Args:
        - argv: 参数列表，缺省取 sys.argv[1:];
    Return:
        - int: 退出码（0 成功，1 业务/输入错误，2 用法错误由 argparse 产生）;
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return _dispatch(args)
    except (ScoreError, InputError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """构建参数解析器（子命令清单取自 COMMANDS，供 R9 自动核对）"""
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="老年人预问诊量表评估系统 · 命令行入口",
    )
    parser.add_argument("--version", action="version", version=f"量表评估系统 {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in COMMANDS.items():
        sub = subparsers.add_parser(name, help=help_text)
        if name in ("score", "report"):
            sub.add_argument("--scale", default="adl", help="量表编码，默认 adl")
            sub.add_argument("--answers", default="", help="答案 JSON 文件路径")
            sub.add_argument("--demo", action="store_true", help="使用内置演示数据")
        if name == "health":
            sub.add_argument("--json", action="store_true", help="以 JSON 输出")
    return parser


def _dispatch(args: argparse.Namespace) -> int:
    """按子命令分发"""
    if args.command == "self-check":
        return _self_check()
    if args.command == "list-scales":
        return _list_scales()
    if args.command == "rule-check":
        return _rule_check()
    if args.command == "health":
        return _health(args.json)
    if args.command == "verify":
        return _verify()
    if args.command in ("score", "report"):
        return _score_or_report(args)
    raise InputError(f"未知命令：{args.command}")


def _self_check() -> int:
    """冒烟检查：不依赖外部文件与参数"""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"量表评估系统 {__version__}")
    print(f"运行环境：Python {version}")
    print(f"已实现量表：{len(SCALE_REGISTRY)} 张（{'、'.join(sorted(SCALE_REGISTRY))}）")
    print(f"可用命令：{'、'.join(COMMANDS)}")
    print(f"演示数据：{len(DEMO_ANSWERS)} 张量表可直接试用")
    print("下一步：python -m app.cli report --scale adl --demo")
    return 0


def _list_scales() -> int:
    """列出已实现量表的题库概况"""
    for scale in SCALE_REGISTRY.values():
        print(f"[{scale.code}] {scale.name}")
        print(f"  标准来源：{scale.standard_ref}")
        print(f"  条目数：{len(scale.items)}，分值区间：{scale.min_total}～{scale.max_total} 分")
        levels = "，".join(f"{level.label}（{level.min_score}～{level.max_score}）" for level in scale.levels)
        print(f"  分级：{levels}")
        has_demo = "有，可加 --demo 试用" if scale.code in _demo_scales() else "无，需用 --answers 提供答案文件"
        print(f"  演示数据：{has_demo}")
    return 0


def _rule_check() -> int:
    """执行硬性规则扫描"""
    results = run_all()
    print(format_report(results))
    return 0 if all(item.ok for item in results) else 1


def _health(use_json: bool) -> int:
    """健康检查：汇总版本、量表与规则扫描结果

    文本模式输出中文摘要；--json 模式只输出可解析的 JSON，不混入任何提示行。
    """
    report = collect()
    if use_json:
        print(json.dumps(to_payload(report), ensure_ascii=False, indent=2))
    else:
        print(render_text(report))
    return 0 if report.ok else 1


def _verify() -> int:
    """一键验收：规则扫描 + 全部单元测试"""
    results = run_all()
    print(format_report(results))
    rules_ok = all(item.ok for item in results)
    total, failed, output = _run_tests()
    print(f"[单元测试] 运行 {total} 项，失败 {failed} 项")
    if failed:
        print(output.strip())
    ok = rules_ok and failed == 0
    print("验收结果：通过" if ok else "验收结果：失败")
    return 0 if ok else 1


def _run_tests() -> tuple[int, int, str]:
    """以编程方式运行 tests 目录下的单元测试"""
    suite = unittest.TestLoader().discover(str(ROOT / "tests"), top_level_dir=str(ROOT))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    failed = len(result.failures) + len(result.errors)
    return result.testsRun, failed, stream.getvalue()


def _score_or_report(args: argparse.Namespace) -> int:
    """计分并按子命令渲染 JSON 或中文报告"""
    answers = _load_answers(args.scale, args.answers, args.demo)
    result = score(args.scale, answers)
    if args.command == "score":
        print(json.dumps(_to_payload(result), ensure_ascii=False, indent=2))
    else:
        print(render_report(result))
    return 0


def _load_answers(scale_code: str, answers_path: str, use_demo: bool) -> list[Answer]:
    """取得作答列表：优先读文件，其次使用内置演示数据"""
    if answers_path:
        path = Path(answers_path)
        if not path.exists():
            raise InputError(f"答案文件不存在：{path}")
        text = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InputError(f"答案文件不是合法 JSON：第 {exc.lineno} 行第 {exc.colno} 列") from exc
        payload_scale, answers = load_answers(payload)
        if payload_scale != scale_code:
            raise InputError(f"答案文件中的量表编码 {payload_scale} 与 --scale {scale_code} 不一致")
        return answers
    if not use_demo and scale_code not in SCALE_REGISTRY:
        raise InputError("请通过 --answers 指定答案文件，或对已内置演示数据的量表使用 --demo")
    scale = get_scale(scale_code)
    if scale.code not in _demo_scales():
        raise InputError(f"量表 {scale_code} 暂无内置演示数据，请使用 --answers 指定答案文件")
    demo = DEMO_ANSWERS[scale.code]
    return [Answer(item_code=item, option_code=option) for item, option in demo.items()]


def _demo_scales() -> set[str]:
    """内置演示数据覆盖的量表编码"""
    return set(DEMO_ANSWERS)


def _to_payload(result: ScoreResult) -> dict:
    """把计分结果转为对外 JSON 结构"""
    return {
        "scale_code": result.scale_code,
        "scale_name": result.scale_name,
        "standard_ref": result.standard_ref,
        "total": result.total,
        "max_total": result.max_total,
        "item_scores": result.item_scores,
        "item_labels": result.item_labels,
        "level_label": result.level_label,
        "advice": result.advice,
        "missing": list(result.missing),
    }


if __name__ == "__main__":
    raise SystemExit(main())
