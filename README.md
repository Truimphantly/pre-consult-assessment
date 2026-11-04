# 老年人预问诊量表评估系统（pre-consult-assessment）

把 WS/T 888—2026 附录 B 的 21 张老年综合评估量表做成"可采集、可计分、可出报告"的软件能力。
当前版本 v0.1.0 只实现 ADL（Barthel 指数）量表的最小闭环。

| 想知道什么 | 看哪里 |
| --- | --- |
| 做什么、为谁做、做到什么程度 | [项目构想总需求.md](项目构想总需求.md) |
| 怎么写代码、怎么启动、有哪些硬性规则 | [AGENT.md](AGENT.md) |
| 命令行怎么调、输出什么格式 | [docs/命令接口约定.md](docs/命令接口约定.md) |

## 快速开始（PowerShell，仓库根目录）

```powershell
python -m app.cli self-check                 # 冒烟：版本 / 量表 / 命令
python -m app.cli report --scale adl --demo  # ADL 演示计分 + 中文报告
python -m app.cli verify                     # 一键验收：规则扫描 + 单元测试
```

## 命令清单

R9（接口三同步）要求本表与 `app/cli.py` 的 `COMMANDS`、`docs/命令接口约定.md` 三处一致。

| 命令 | 作用 |
| --- | --- |
| `python -m app.cli self-check` | 冒烟检查：版本、量表、可用命令 |
| `python -m app.cli list-scales` | 列出已实现量表与分级 |
| `python -m app.cli rule-check` | 扫描硬性规则 R1～R9 |
| `python -m app.cli score --scale adl --demo` | 计分并输出 JSON |
| `python -m app.cli report --scale adl --demo` | 输出中文报告片段 |
| `python -m app.cli health` | 健康检查：版本、量表、规则扫描结论（`--json` 输出 JSON） |
| `python -m app.cli verify` | 一键验收：规则扫描 + 单元测试 |

要求：Python 3.12，无第三方依赖。
