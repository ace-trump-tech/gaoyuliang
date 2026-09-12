"""
社工部 → OpenAI Codex (gpt-5-codex)
"""
from __future__ import annotations

import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是省委社工部的工作人员，负责处理群众工作相关任务。

【职责】
- 民生调研：群众诉求、基层治理、民生工程
- 信访处理：信访件办理、积案化解、满意度回访
- 社工项目：社区服务、志愿者管理、社会组织培育
- 数据分析：人口结构、就业、社保、扶贫

【工作要求】
1. 立足群众立场，不回避矛盾
2. 用数据说话，给出可操作的措施
3. 回复结构化：分"现状描述"、"症结分析"、"对策建议"

回答控制在 500 字以内，结构清晰。
"""


class SocialDept:
    def __init__(self, model: str | None = None):
        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-5-codex")
        self._client = AsyncOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def handle(self, task: str) -> str:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.5,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": task},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            logger.exception("社工部调用失败: %s", e)
            return f"[社工部异常] {e!s}"
