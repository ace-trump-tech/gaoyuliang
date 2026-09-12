"""
宣传部 → Gemini
"""
from __future__ import annotations

import logging
import os

import google.generativeai as genai

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """你是省委宣传部的工作人员，负责处理宣传工作相关任务。

【职责】
- 舆论引导：舆情分析、应对预案、媒体协调
- 新闻稿撰写：通稿、人物专访、事件报道
- 形象塑造：典型宣传、专题策划、对外推介
- 宣传策略：政策解读、理论宣讲、对外传播

【工作要求】
1. 严格政治站位，与中央保持一致
2. 用词规范，避免引起负面舆论
3. 回复结构化：分"舆情现状"、"研判意见"、"应对建议"

回答控制在 500 字以内，结构清晰。
"""


class PropagandaDept:
    def __init__(self, model: str | None = None):
        self._model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        self._gmodel = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=SYSTEM_PROMPT,
        )

    async def aclose(self) -> None:
        return None

    async def handle(self, task: str) -> str:
        try:
            resp = await self._gmodel.generate_content_async(task)
            return resp.text.strip()
        except Exception as e:  # noqa: BLE001
            logger.exception("宣传部调用失败: %s", e)
            return f"[宣传部异常] {e!s}"
