"""项目统一异常。

约定（见 AGENT.md R2）：
- 业务/输入不合法一律抛 ScoreError；
- 读取外部输入（文件、JSON）失败抛 InputError；
- 禁止用 ValueError / KeyError / assert 承担业务校验。
"""


class ScoreError(Exception):
    """评估业务错误：未知量表、未知条目、未知选项、缺项、重复作答等。"""


class InputError(Exception):
    """输入源错误：答案文件不存在、JSON 解析失败、结构不符合约定。"""
