# AGENT.md

> 本文件是本仓库**唯一的 AI 编码契约**。任何 AI 编码工具（DeepSeek Harness / Trae Work / Claude Code / Copilot 等）在改动代码前必须先读本文件，并遵守第 6、7 节的硬性规则与禁止清单。
> 需求与业务流程见 [项目构想总需求.md](项目构想总需求.md)；命令行契约见 [docs/命令接口约定.md](docs/命令接口约定.md)。

## 0. 怎么用这份文件

| 顺序 | 先读什么 | 目的 |
| --- | --- | --- |
| 1 | 第 1 节 当前实现范围 | 知道哪些功能**已经存在**、哪些**还没写**，不要凭空造模块 |
| 2 | 第 3 节 仓库结构 | 知道代码该放哪个目录、import 前缀是什么 |
| 3 | 第 5 节 验证命令 | 改完代码必须自己跑一遍，绿了才算完成 |
| 4 | 第 6、7 节 硬性规则与禁止清单 | 违反即视为任务失败，必须重写 |
| 5 | 第 8、9 节 项目特有的坑与接口位置 | 避免"看起来对、跑起来错" |

优先级：**用户当轮指令 > 本文件 > 代码中的历史写法**。若用户指令与本文件冲突，先指出冲突并请用户确认，不得默默违反。

---

## 1. 项目是什么，现在做到哪一步

老年人预问诊量表评估系统：把 WS/T 888—2026 附录 B 的 21 张量表做成"可采集、可计分、可出报告"的软件能力。

**当前实现范围（v0.1.0，代码事实）**

| 能力 | 状态 | 位置 |
| --- | --- | --- |
| ADL（Barthel 指数，10 项 0～100 分）题库与分级 | 已实现 | `app/scales.py` |
| 通用计分引擎（校验、求和、分级） | 已实现 | `app/engine.py` |
| 中文报告片段生成 | 已实现 | `app/report.py` |
| 命令行入口（self-check / score / report / verify / list-scales） | 已实现 | `app/cli.py` |
| 规则自检（把硬性规则变成可执行检查） | 已实现 | `app/selfcheck.py` |
| Braden、NRS2002、FRAIL、MMSE 等其余 20 张量表 | **未实现**，不要假装已存在 | — |
| 语音/对话采集、数据库、Web 接口、前端 | **未实现** | — |

新增功能前先确认自己在"未实现"清单里，不要引用不存在的模块、函数或数据表。

---

## 2. 技术栈与版本（精确，不许模糊）

| 项 | 值 | 说明 |
| --- | --- | --- |
| 语言 | Python **3.12.14** | 已验证版本；禁止使用 3.13+ 语法（如 PEP 695 `type` 别名） |
| 运行时依赖 | **无**（仅标准库） | 不得引入 requests/pydantic/fastapi 等第三方包 |
| 开发依赖 | **无**（标准库 `unittest`） | 用 `python -m unittest`，不要用 pytest |
| 操作系统 | Windows 11（PowerShell 5.1/7） | 命令示例均为 PowerShell 可执行形式 |
| 文本编码 | UTF-8（无 BOM） | 所有源码、JSON、Markdown 统一 UTF-8 |
| 入口方式 | `python -m app.cli ...` | 不使用 `./cli.py`、不依赖 `python cli.py` |
| 数据存储 | 内存对象（dataclass） | 一期不接数据库 |

版本冲突时以此表为准，不得"顺手升级"。

---

## 3. 仓库结构（单仓库，无前后端拆分）

```text
pre-consult-assessment/
├─ AGENT.md                     # 本文件：AI 编码契约（唯一事实来源）
├─ 项目构想总需求.md             # 需求事实来源（做不做、做到什么程度）
├─ README.md                    # 三行起步说明，指向 AGENT.md
├─ .gitignore                   # 忽略 __pycache__、*.pyc、.venv、本地答案文件
├─ docs/
│  ├─ 命令接口约定.md            # ★ 前后端/人机接口契约：命令、参数、输出、退出码
│  └─ 实验记录.md                # AI 编码实验的步骤、命令与输出留档
├─ app/                         # 源码（import 前缀 app.*）
│  ├─ __init__.py               # 版本号 __version__
│  ├─ errors.py                 # 统一异常：ScoreError / InputError
│  ├─ models.py                 # 数据结构：Option/Item/Scale/Level/Answer/ScoreResult
│  ├─ scales.py                 # ★ 量表题库与分级阈值（唯一允许出现阈值的地方）
│  ├─ engine.py                 # 计分引擎（只做流程与校验，不写阈值）
│  ├─ report.py                 # 中文报告片段（只做文案，不写阈值）
│  ├─ selfcheck.py              # 硬性规则扫描器
│  └─ cli.py                    # 命令行入口（唯一允许 sys.exit 的地方）
└─ tests/                       # 单元测试（标准库 unittest）
   ├─ test_scales.py            # 题库一致性：条目数、分值区间、选项唯一
   ├─ test_engine.py            # 计分与校验：满分/分级/缺失/重复/未知编码
   ├─ test_report.py            # 报告：必备字段、合规措辞、禁用词
   └─ test_cli.py               # CLI：退出码、输出、verify 汇总
```

约定：

- 单仓库、单语言，不引入 `backend/`、`frontend/` 拆分；需要 Web 时再加 `app/api/` 并在本文件登记。
- `app/` 内部只允许 `app.*` 相对导入（`from app.models import ...`），禁止 `sys.path.append` 之类黑魔法。
- 测试与被测代码的对应关系保持 1:1（`app/x.py` ↔ `tests/test_x.py`）。

---

## 4. 构建与启动命令（一条命令能跑起来）

本项目**没有构建步骤**（纯源码）。三条命令覆盖全部日常操作：

```powershell
# 1) 启动/冒烟：打印版本、可用量表、命令帮助（不依赖任何参数与文件）
python -m app.cli self-check

# 2) 用内置演示数据跑一次完整链路（题库 → 计分 → 中文报告）
python -m app.cli report --scale adl --demo

# 3) 查看全部命令
python -m app.cli --help
```

要求：在干净环境（仅安装 Python 3.12）下，上述命令必须一次成功，不得要求设置环境变量、不得要求先建目录或先放文件。

---

## 5. 验证命令（改完必须自己跑）

```powershell
# 一键验收：规则扫描 + 全部单元测试；退出码 0 才算通过
python -m app.cli verify

# 只跑单元测试（需要看细节时用）
python -m unittest discover -s tests -v

# 只跑规则扫描（检查硬性规则是否被违反）
python -m app.cli rule-check
```

判定标准：

- `verify` 输出最后一行必须是 `验收结果：通过`，退出码 0；任何 `失败` 都不得提交。
- 新增/修改计分逻辑必须新增对应测试用例；只改实现不补测试视为未完成。
- 报告类改动必须跑 `tests/test_report.py`，确认禁用词检查仍通过。

---

## 6. 硬性规则（违反即出错，必须重写）

每条规则都**可被 `python -m app.cli rule-check` 自动检查**，不靠人盯。

| 编号 | 规则 | 反例（禁止） | 正例（必须） | 检查方式 |
| --- | --- | --- | --- | --- |
| R1 | 计分相关函数必须返回 `ScoreResult`，不得返回 `None`、裸数字或 `dict` | `def score(...): ... return None` | `return ScoreResult(scale_code=..., total=85, ...)` | 扫描 `app/engine.py`、`app/report.py` 中的 `return None` |
| R2 | 业务错误统一抛 `app.errors.ScoreError`（输入类用 `InputError`），禁止 `ValueError`/`KeyError`/`assert` 做业务校验，禁止 `except Exception: pass` | `raise ValueError("missing answer")` | `raise ScoreError("缺少必填条目：adl_eat")` | 扫描项目源码中的 `raise ValueError`、`raise KeyError`、`except Exception:` |
| R3 | 所有面向人的文本（CLI 输出、异常 message、报告）必须是简体中文；英文只允许出现在代码标识符与命令名中 | `print("score ok")` | `print("计分完成，总分 85 分")` | 扫描 `print(...)`、`ScoreError(...)`、`InputError(...)` 中的纯英文字面量 |
| R4 | 量表条目、分值与分级阈值只能写在 `app/scales.py`；`engine.py`、`report.py` 不得出现两位以上的数字常量 | `if total >= 60:` | `level = pick_level(scale.levels, total)` | 扫描 `engine.py`、`report.py` 中的 `\b\d{2,}\b` |
| R5 | 改计分逻辑前先写/改 `tests/` 用例；`verify` 未通过不得提交 | 先改 `engine.py` 再补测试 | 先加 `test_engine.py` 用例，再改实现 | 由 `verify` 兜底（测试必须全绿） |
| R6 | 只允许标准库；新增第三方依赖必须先修改本节并在提交信息中说明理由、获人工确认 | `import requests` | `import json` | 扫描非标准库 import 白名单 |
| R7 | 读写文件必须显式 `encoding="utf-8"`；禁止依赖系统默认编码 | `open(path)` | `open(path, encoding="utf-8")` | 扫描 `open(` 调用是否带 `encoding=` |
| R8 | 只有 `app/cli.py` 的 `__main__` 块允许 `sys.exit(...)`；库模块禁止退出进程 | `sys.exit(1)` 写在 `engine.py` | `if __name__ == "__main__": raise SystemExit(main())` | 扫描 `app/` 下非 `cli.py` 文件的 `sys.exit` |

违规处理：`rule-check` 报红 → 立即修代码，不许"先提交再说"，也不许改检查脚本放行（改检查脚本本身需要人工确认）。

---

## 7. 禁止清单（这些做法在本项目一律不被允许）

1. 禁止引入第三方依赖或新建虚拟环境（R6）。
2. 禁止在 `engine.py` / `report.py` 里写死量表分值、总分上限、分级阈值（R4）。
3. 禁止把"诊断/确诊/停药/调整用药"写进报告或提示语——系统只做评估提示。
4. 禁止在代码、测试、文档中出现真实姓名、身份证号、手机号；样例数据只用"张三"等虚构值。
5. 禁止返回"看起来正常"的空结果来掩盖错误（例如缺项时返回 0 分）。
6. 禁止删除或注释掉既有测试来让 `verify` 变绿。
7. 禁止在源码里使用 `print` 调试后遗留（CLI 层按契约输出，其他层用异常传错）。
8. 禁止把 `AGENT.md`、`项目构想总需求.md` 的描述改成与代码不符的"已完成"。
9. 禁止在 Windows 上写 `bash`/`sh` 命令示例（本仓库统一 PowerShell 形式）。
10. 禁止一次提交混合多个不相关改动（一次提交只做一件事）。

---

## 8. 项目特有的坑与易错点

| 易错点 | 为什么容易错 | 正确做法 |
| --- | --- | --- |
| PowerShell 下执行命令 | 直接 `./app/cli.py` 会被当成命令找不到 | 统一用 `python -m app.cli ...` |
| Windows 控制台编码 | 默认 GBK 会把中文输出成乱码 | 源码 UTF-8；`cli.py` 输出前 `sys.stdout.reconfigure(encoding="utf-8")` |
| 阈值散落 | Barthel 的 60/41/40 很容易被顺手写进 `engine.py` | 阈值只在 `scales.py` 的 `levels` 里，引擎只做区间匹配 |
| 缺项处理 | 缺项时返回 0 分会让报告"看起来正常" | 缺必填项直接抛 `ScoreError`，并在 message 里列出缺哪几项 |
| 报告合规 | "提示糖尿病"和"诊断糖尿病"在读者眼里差别很大 | 结论一律"提示/建议/请医师确认"，并附固定合规尾注 |
| 代答场景 | 家属代答会影响结果效度 | 一期先不做代答登记；接入时必须记录提供者并在报告标注 |
| Python 版本 | 用 3.13 的新语法在 3.12 上直接语法错误 | 只用 3.12 可用语法；`match` 可用，PEP 695 不可用 |
| 中英文混排 | 单位、量表名混排导致对齐错乱 | 数字与中文之间留空格；量表名首次出现写全称+简称 |
| PowerShell 写文件带 BOM | `Set-Content -Encoding UTF8` 会写入 BOM，`ast.parse` 直接报 `invalid non-printable character U+FEFF`，表现为"代码看着没问题却跑不起来" | 用编辑器或 `Path.write_text(text, encoding="utf-8")` 落盘；改完立刻跑 `rule-check`，BOM 会在第一步暴露 |

---

## 9. 接口约定的位置

| 接口 | 位置 | 说明 |
| --- | --- | --- |
| 命令行契约（命令/参数/退出码/输出格式） | `docs/命令接口约定.md` | 改 CLI 前必须先改这份文档，再改 `app/cli.py` |
| 计分结果结构（下游依赖的字段） | `app/models.py` 的 `ScoreResult` | 增删字段属于破坏性变更，需同步 `docs/命令接口约定.md` 与测试 |
| 量表题库结构 | `app/scales.py` 的 `SCALE_REGISTRY` | 新增量表只加数据，不改引擎 |
| 异常契约 | `app/errors.py` | `ScoreError` 表示业务/输入错误，CLI 统一映射为退出码 1 |

任何"新接口"都必须先落到上述文件，不允许只在代码里隐含约定。

---

## 10. 开发流程（做完才算完成）

1. **先计划**：非一行改动能解决的需求，先在 `docs/` 写计划（大步骤 1、2…，子步骤 1.1…，`- [ ]` 标记），完成一项改 `- [X]`。
2. **再动手**：从 `main` 新建 `feat|fix|docs|test/chore` 分支，例如 `feat/adl-scoring`。
3. **小步提交**：提交信息格式 `类型(范围): 中文摘要`，摘要要写清"改了什么 + 为什么"，例如：
   `feat(engine): 新增 ADL 计分与分级，缺项改抛 ScoreError`
4. **自验**：`python -m app.cli verify` 全绿。
5. **合并**：合回 `main` 并删除功能分支；`main` 上始终保持可运行。
6. **收尾**：更新受影响的文档（`AGENT.md` / `项目构想总需求.md` / `docs/命令接口约定.md`）。

完成定义（DoD）：`verify` 通过 + 文档同步 + 无调试残留 + 提交信息合规，四者缺一不算完成。

---

## 11. 给 AI 的标准提示词模板（可直接复制）

```text
你是本仓库的编码助手。开始前请先阅读仓库根目录 AGENT.md，并严格遵守其中的硬性规则（第 6 节）
与禁止清单（第 7 节）。

任务：<一句话说明要做什么>
范围：只改 app/ 与 tests/ 下的相关文件，不改其他模块。
约束：
1) 不得引入第三方依赖；只改标准库用法。
2) 计分函数必须返回 ScoreResult；错误一律 raise ScoreError("中文原因")。
3) 阈值只能写在 app/scales.py，禁止写进 engine.py / report.py。
4) 先补 tests/ 用例，再改实现。
完成标准：python -m app.cli verify 退出码为 0，并把关键输出贴给我。
如果我的要求与 AGENT.md 冲突，请先指出冲突点，不要默默照做。
```

---

## 12. 维护规则

- 修改代码导致"结构、命令、规则、范围"任一变化时，**同一次提交内**更新本文件。
- 新增一条硬性规则时，必须同时给出：规则、反例、正例、检查方式（否则视为不可执行，不予采纳）。
- 本文件的"当前实现范围"表是防止 AI 幻觉的关键，任何功能上线/下线都要改这张表。
- 本文件与代码冲突时，以代码 + 测试为准，并在当次提交中修正本文件。

---

## 13. 修订记录

| 版本 | 触发事件 | 改了什么 | 效果 |
| --- | --- | --- | --- |
| v0.1.0 | 首次撰写 | 建立技术栈版本表、仓库结构、启动/验证命令、硬性规则 R1～R8、禁止清单 | 首次让"规则"可被检查 |
| v0.2.0 | AI 编码实验：首版代码同时违反 R1、R2、R3、R4 | 第 6 节每条规则补"反例（禁止）/正例（必须）"两列；新增第 11 节提示词模板；第 7 节禁止清单补第 10 条；第 8 节补 PowerShell BOM 坑 | 规则从"断言"变成"可对照的写法"，第二次生成未再犯同类错误 |
| v0.2.1 | 自检器漏检 `"..." + 变量` 形式的英文提示 | R3 检查改为遍历参数子树，覆盖字符串拼接 | 规则与检查器一致，8 条规则全部可自动判定 |

修订原则：任何一次违规，不能只改代码，必须回答"AGENT.md 里缺了什么"，并在同一次提交内补上。
