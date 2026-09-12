"""
政法委 → DeepSeek（OpenAI 兼容）
"""
from __future__ import annotations

import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是省委政法委的工作人员，负责处理政法工作相关任务。

【职责】
- 法治研判：法律法规适用、合规审查、立法建议
- 维稳分析：社会稳定风险评估、群体性事件应对
- 案件梳理：扫黑除恶、信访积案、执法监督
- 政策合规：重大决策合法性审查

【工作要求】
1. 严格依法依规，不徇私情
2. 给出明确的法理依据
3. 回复结构化：分"事实认定"、"法律适用"、"处置意见"

回答控制在 500 字以内，结构清晰。
"""


class PoliticsLawDept:
    def __init__(self, model: str | None = None):
        self._model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-reasoner")
        self._client = AsyncOpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )

    async def aclose(self) -> None:
        await self._client.close()

    async def handle(self, task: str) -> str:
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                temperature=0.4,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": task},
                ],
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            logger.exception("政法委调用失败: %s", e)
            return f"[政法委异常] {e!s}"
