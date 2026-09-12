"""
对话历史管理

每条 user / assistant 文本按调用顺序记录，
to_messages() 转成 OpenAI/豆包 格式 messages
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, List


@dataclass
class Turn:
    role: str  # 'user' | 'assistant'
    content: str


class Conversation:
    """一轮通话的对话历史（拿起话筒到挂断）"""

    def __init__(self, max_turns: int = 50):
        self._turns: Deque[Turn] = deque(maxlen=max_turns)

    def reset(self) -> None:
        self._turns.clear()

    def add_user(self, text: str) -> None:
        if text:
            self._turns.append(Turn("user", text))

    def add_assistant(self, text: str) -> None:
        if text:
            self._turns.append(Turn("assistant", text))

    def to_messages(self, max_pairs: int = 20) -> List[dict]:
        """转成豆包 messages 格式，按 pair 截断（保持 user/assistant 交替）"""
        turns = list(self._turns)[-2 * max_pairs :]
        return [{"role": t.role, "content": t.content} for t in turns]
