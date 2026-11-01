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

要求：Python 3.12，无第三方依赖。
