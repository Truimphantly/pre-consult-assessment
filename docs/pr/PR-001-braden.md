# PR #1　新增 Braden 压力性损伤风险评估量表（B.16）

- 来源分支：`feat/braden-scale` → 目标分支：`main`
- 作者：项目组　提交：`79133e1`
- 关联标准：WS/T 888—2026 附录 B 表 B.16

## 1. 背景

现有主线只支持 ADL 一张量表，`项目构想总需求.md` 第 7 节把 Braden 列在二期。
本轮把 ADL 计分链路作为主线，另开分支补上第二张量表，用来验证"新增量表只加数据、不改引擎"这条约定是否成立。

## 2. 变更内容

| 文件 | 变更 |
| --- | --- |
| `app/scales.py` | 新增 `BRADEN`：6 个条目（感知、潮湿、活动、移动、营养、摩擦与剪切力），总分 6～23，5 档分级；注册进 `SCALE_REGISTRY` |
| `app/scales.py` | `DEMO_ANSWERS` 由扁平字典改为按量表编码分组，为 `adl` 和 `braden` 各备一份演示数据 |
| `app/cli.py` | `--demo` 改为读取对应量表的演示数据；`_demo_scales()` 由 `DEMO_ANSWERS` 推导，避免两处名单不一致 |
| `tests/test_braden.py` | 新增 13 项用例：题库结构、6/9/10/13/14/18/19/23 分边界、缺项校验、报告输出 |
| `tests/test_engine.py`、`tests/test_report.py` | 跟随 `DEMO_ANSWERS` 结构变更调整取值 |
| `tests/test_scales.py` | 原"未知量表"用例用的是 `braden`，注册后失效，改为 `nrs2002` |

计分引擎 `app/engine.py` **没有改动**。

## 3. 影响面

- 对外命令不变（`score`、`report`、`list-scales`），只多了一张可选量表编码 `braden`。
- `DEMO_ANSWERS` 是公共常量，结构变化会影响所有引用方；本 PR 已同步 3 处测试，`app/cli.py` 1 处。
- 不涉及数据库、网络与第三方依赖。

## 4. 验证方式

```powershell
python -m app.cli verify                     # 规则扫描 + 全部单元测试
python -m app.cli list-scales                # 应列出 adl 与 braden
python -m app.cli score --scale braden --demo   # 15 分，轻度风险
python -m app.cli report --scale braden --demo  # 中文报告片段
```

实际结果：规则扫描 9/9 通过；单元测试 69 项全部通过；`braden --demo` 总分 15 分，分级为轻度风险。

## 5. 风险与回滚

- 风险：分级档位（5 档）与部分机构使用的 4 档口径不一致，可能需要在配置里调整。
- 回滚：`git revert` 合并提交即可；`braden` 未被写入任何持久化数据，回滚无迁移成本。

## 6. 评审关注点

1. 5 档分级的依据是否需要在代码中注明，允许机构调整到什么程度。
2. `DEMO_ANSWERS` 结构调整是否值得，能否用新增键代替重构。
3. 文档（AGENT.md 实现范围、项目构想实现状态表）是否必须同 PR 更新。

## 7. 评审后修订（2026-11-15）

第一轮评审结论为"需要修改后合并"，两条必须修改的处理如下：

| 评审意见 | 修订内容 | 状态 |
| --- | --- | --- |
| 文档没有同步 | `AGENT.md` 第 1 节登记 Braden（B.16），第 3 节补 `tests/test_braden.py`，修订记录新增 v0.3.2；`项目构想总需求.md` 第 7 节把 Braden 移到"已实现"，同步 M3 与范围风险；`README.md` 改为两张量表并补 Braden 演示命令 | 已关闭 |
| 分级依据没有写清楚 | `app/scales.py` 注明 WS/T 888—2026 附录 B 表 B.16、5 档区间、连续覆盖 6～23 的约束，以及机构口径不同时只改 `levels`、不改引擎 | 已关闭 |

修订提交：`63130df`。复验：规则扫描 9/9 通过，单元测试 69 项全部通过，退出码 0；`braden --demo` 总分 15/23，分级"轻度风险"。第二轮复审结论为"通过，可以合并"。

## 8. 自查清单

- [x] 只加数据，没有改计分引擎
- [x] 阈值只写在 `app/scales.py`
- [x] 新增用例覆盖分级边界与缺项
- [x] `python -m app.cli verify` 通过
- [x] 文档同步（`AGENT.md`、`项目构想总需求.md`、`README.md` 已在评审后补齐）
