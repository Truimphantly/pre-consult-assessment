"""硬性规则扫描器。

作用：把 AGENT.md 第 6 节的 R1～R8 从"文字约定"变成"可执行检查"，
`python -m app.cli rule-check` 与 `verify` 均调用本模块。
说明：扫描器自身不参与字符串扫描，避免规则文本自我命中。
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
TESTS_DIR = ROOT / "tests"

RULE_TITLES = {
    "R1": "计分返回类型",
    "R2": "统一异常",
    "R3": "中文输出",
    "R4": "阈值集中",
    "R5": "测试同步",
    "R6": "零第三方依赖",
    "R7": "显式 UTF-8",
    "R8": "退出码归属",
    "R9": "接口三同步",
}


@dataclass(frozen=True)
class RuleResult:
    """单条规则的检查结果。"""

    code: str
    title: str
    ok: bool
    detail: str


def _app_files() -> list[Path]:
    """列出 app 目录下的源码文件"""
    return sorted(path for path in APP_DIR.glob("*.py"))


def _read(path: Path) -> str:
    """按 UTF-8 读取源码"""
    return path.read_text(encoding="utf-8")


def _scannable_files() -> list[Path]:
    """参与文本扫描的文件（排除扫描器自身）"""
    return [path for path in _app_files() if path.name != "selfcheck.py"]


def _result(code: str, hits: list[str], ok_detail: str, bad_title: str) -> RuleResult:
    """组装规则结果"""
    if hits:
        return RuleResult(code, RULE_TITLES[code], False, bad_title + " → " + "；".join(hits))
    return RuleResult(code, RULE_TITLES[code], True, ok_detail)


def check_r1() -> RuleResult:
    """R1：计分相关文件不得出现 return None"""
    hits: list[str] = []
    for name in ("engine.py", "report.py"):
        path = APP_DIR / name
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if re.search(r"return\s+None\b", line):
                hits.append(f"{name}:{lineno}")
    return _result("R1", hits, "未发现 return None", "发现 return None")


def check_r2() -> RuleResult:
    """R2：禁止用 ValueError/KeyError/assert 做业务校验，禁止静默吞异常"""
    hits: list[str] = []
    for path in _scannable_files():
        text = _read(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if re.search(r"raise\s+(ValueError|KeyError|TypeError|RuntimeError)\b", line):
                hits.append(f"{path.name}:{lineno} 使用了内置异常")
            if re.search(r"except\s+Exception\s*:\s*$", line):
                hits.append(f"{path.name}:{lineno} 捕获裸 Exception")
    return _result("R2", hits, "业务错误统一使用 ScoreError / InputError", "异常用法不合规")


def check_r3() -> RuleResult:
    """R3：print / 异常消息中的字面量必须是中文"""
    hits: list[str] = []
    targets = {"print", "ScoreError", "InputError"}
    cjk = re.compile(r"[\u4e00-\u9fff]")
    ascii_word = re.compile(r"[A-Za-z]{3,}")
    for path in _scannable_files():
        tree = ast.parse(_read(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id not in targets:
                continue
            for arg in node.args:
                # 遍历参数子树：既要抓纯字面量，也要抓 "..."+变量 这类拼接
                for sub in ast.walk(arg):
                    if not isinstance(sub, ast.Constant) or not isinstance(sub.value, str):
                        continue
                    text = sub.value
                    if ascii_word.search(text) and not cjk.search(text):
                        hits.append(f"{path.name}:{node.lineno} 英文提示「{text[:18]}」")
    return _result("R3", hits, "面向人的文本均为中文", "发现纯英文提示")


def check_r4() -> RuleResult:
    """R4：engine / report 中不得出现两位以上的数字常量"""
    hits: list[str] = []
    pattern = re.compile(r"(?<![\w.])\d{2,}(?![\w.])")
    for name in ("engine.py", "report.py"):
        path = APP_DIR / name
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if pattern.search(line):
                hits.append(f"{name}:{lineno} 出现数字常量")
    return _result("R4", hits, "阈值只出现在 scales.py", "阈值写进了业务代码")


def check_r5() -> RuleResult:
    """R5：核心模块必须有对应测试文件"""
    required = ("engine", "scales", "report", "cli")
    missing = [name for name in required if not (TESTS_DIR / f"test_{name}.py").exists()]
    return _result("R5", missing, "四个核心模块均有测试", "缺少测试文件")


def check_r6() -> RuleResult:
    """R6：只允许标准库与 app 内部导入"""
    allowed = set(sys.stdlib_module_names) | {"app", "__future__"}
    hits: list[str] = []
    for path in _app_files():
        tree = ast.parse(_read(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in allowed:
                        hits.append(f"{path.name}:{node.lineno} 引入 {top}")
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                top = node.module.split(".")[0]
                if top not in allowed:
                    hits.append(f"{path.name}:{node.lineno} 引入 {top}")
    return _result("R6", hits, "未引入第三方依赖", "引入了第三方依赖")


def check_r7() -> RuleResult:
    """R7：open() 必须显式声明 encoding"""
    hits: list[str] = []
    for path in _app_files():
        tree = ast.parse(_read(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "open":
                continue
            keywords = {keyword.arg for keyword in node.keywords}
            if "encoding" not in keywords and "b" not in ast.dump(node):
                hits.append(f"{path.name}:{node.lineno} open 缺少 encoding")
    return _result("R7", hits, "文件读写均声明 UTF-8", "缺少 encoding")


def check_r8() -> RuleResult:
    """R8：只有 cli.py 允许退出进程"""
    hits: list[str] = []
    for path in _scannable_files():
        if path.name == "cli.py":
            continue
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if re.search(r"\bsys\.exit\b|raise\s+SystemExit", line):
                hits.append(f"{path.name}:{lineno}")
    return _result("R8", hits, "库模块不退出进程", "库模块中退出进程")


def check_r9() -> RuleResult:
    """R9：接口三同步——每个 CLI 子命令必须写进命令契约与 README"""
    hits: list[str] = []
    cli_text = _read(APP_DIR / "cli.py")
    match = re.search(r"COMMANDS\s*[:=][^=]*=\s*\{(.*?)\}", cli_text, re.S)
    if match is None:
        return RuleResult("R9", RULE_TITLES["R9"], False, "未找到 COMMANDS 登记表，无法核对子命令清单")
    names = re.findall(r'"([a-z][a-z\-]*)"\s*:', match.group(1))
    docs_text = _read(ROOT / "docs" / "命令接口约定.md")
    readme_text = _read(ROOT / "README.md")
    for name in names:
        token = f"python -m app.cli {name}"
        if token not in docs_text:
            hits.append(f"{name} 未写入 docs/命令接口约定.md")
        if token not in readme_text:
            hits.append(f"{name} 未写入 README.md")
    return _result("R9", hits, "命令清单与两份文档一致", "接口未三同步")


def run_all() -> list[RuleResult]:
    """依次执行全部规则检查"""
    return [
        check_r1(),
        check_r2(),
        check_r3(),
        check_r4(),
        check_r5(),
        check_r6(),
        check_r7(),
        check_r8(),
        check_r9(),
    ]


def _display_width(text: str) -> int:
    """按终端显示宽度计算（中日韩字符占两列）"""
    return sum(2 if ord(char) > 127 else 1 for char in text)


def format_report(results: list[RuleResult]) -> str:
    """把规则结果格式化为中文报告"""
    lines: list[str] = []
    for item in results:
        padding = "." * max(2, 26 - _display_width(item.title))
        status = "通过" if item.ok else "失败"
        lines.append(f"[规则扫描] {item.code} {item.title}{padding} {status}")
        if not item.ok:
            lines.append(f"            {item.detail}")
    passed = sum(1 for item in results if item.ok)
    lines.append(f"规则扫描：{passed}/{len(results)} 通过")
    return "\n".join(lines)
