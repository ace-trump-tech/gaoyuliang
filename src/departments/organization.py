"""
组织部 → Claude Agent SDK

用 Claude 作为组织部的"头脑"，可以读写本地文件、查公开信息
注意：实际部署时应该给 Claude 接一套受限的工具（只读 + WebFetch）
"""
from __future__ import annotations

import logging
import os

import anthropic

from ..conversation import Conversation

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是省委组织部的工作人员，负责处理组织工作相关任务。

【职责】
- 干部考察：干部履历、任职资格、民主推荐
- 人才选拔：高层次人才引进、人才项目评审
- 班子调配：领导班子换届、岗位调整、挂职锻炼
- 组织架构：党组织设置、支部建设

【工作要求】
1. 严格遵守干部工作纪律，不泄露未公开的考察材料
2. 回复结构化：分"基本情况"、"分析研判"、"建议意见"
3. 涉及人事安排需明确"建议方案"，不直接下定论

回答控制在 500 字以内，结构清晰。
"""


class OrganizationDept:
    def __init__(self, model: str | None = None):
        self._model = model or os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-20250514")
        self._client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def handle(self, task: str) -> str:
        try:
            resp = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": task}],
            )
            parts = []
            for block in resp.content:
                if hasattr(block, "text"):
                    parts.append(block.text)
            return "\n".join(parts).strip()
        except Exception as e:  # noqa: BLE001
            logger.exception("组织部调用失败: %s", e)
            return f"[组织部异常] {e!s}"
