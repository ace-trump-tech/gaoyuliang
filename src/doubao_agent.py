"""
豆包秘书（doubao-pro）—— 上层贴身秘书

职责：
1. 接到一句话，先判断：闲聊 / 单部门任务 / 多部门协同
2. 若是任务，调用对应部门（src/departments/*）
3. 把部门结果综合回复给用户
4. 支持 tool calling（function_call）以触发部门调用

使用 volcengine Python SDK（OpenAI 兼容接口）调用豆包
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from openai import AsyncOpenAI  # 豆包 OpenAI 兼容

from .conversation import Conversation
from .departments.organization import OrganizationDept
from .departments.politics_law import PoliticsLawDept
from .departments.propaganda import PropagandaDept
from .departments.social import SocialDept

logger = logging.getLogger(__name__)


@dataclass
class DoubaoConfig:
    api_key: str
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model: str = "doubao-pro"
    temperature: float = 0.7
    max_history: int = 20


# 4 部委的工具定义（豆包 function call schema）
DEPARTMENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "dispatch_organization",
            "description": "派单给组织部（Claude）。处理干部考察、人才选拔、班子调配、组织架构等组织工作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "具体任务描述，例如'考察 XXX 同志的任职资格'",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_propaganda",
            "description": "派单给宣传部（Gemini）。处理舆论引导、新闻稿、形象塑造、宣传策略等宣传工作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "具体任务描述，例如'起草 XXX 事件通稿'",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_social",
            "description": "派单给社工部（Codex）。处理民生调研、信访处理、社工项目、数据分析等群众工作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "具体任务描述，例如'分析近期群众信访数据'",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "dispatch_politics_law",
            "description": "派单给政法委（DeepSeek）。处理法治研判、维稳分析、案件梳理、政策合规等政法工作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "具体任务描述，例如'评估 XXX 决策的合规性'",
                    }
                },
                "required": ["task"],
            },
        },
    },
]


class DoubaoAgent:
    """豆包秘书：单轮接听、派单、汇报"""

    def __init__(
        self,
        cfg: DoubaoConfig,
        secretary_system_prompt: str,
        on_response: Optional[Callable[[str], Awaitable[None]]] = None,
    ):
        self._cfg = cfg
        self._sys_prompt = secretary_system_prompt
        self._client = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        self._on_response = on_response  # 用于异步任务完成时回拨

        # 4 部委
        self._org = OrganizationDept()
        self._prop = PropagandaDept()
        self._soc = SocialDept()
        self._pl = PoliticsLawDept()

    async def aclose(self) -> None:
        await self._client.close()
        await asyncio.gather(
            self._org.aclose(),
            self._prop.aclose(),
            self._soc.aclose(),
            self._pl.aclose(),
            return_exceptions=True,
        )

    async def handle(self, user_text: str, conv: Conversation) -> str:
        """
        处理一条来自话筒的指令，返回秘书的回复文本

        如果是长任务，会先在后台 fire-and-forget 派单，再返回一句"安排中"
        """
        conv.add_user(user_text)

        # 调用豆包
        try:
            resp = await self._client.chat.completions.create(
                model=self._cfg.model,
                temperature=self._cfg.temperature,
                messages=[
                    {"role": "system", "content": self._sys_prompt},
                    *conv.to_messages(max_pairs=self._cfg.max_history),
                ],
                tools=DEPARTMENT_TOOLS,
                tool_choice="auto",
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("豆包调用失败: %s", e)
            return "领导，电话线路出了点问题，您稍等，我处理一下再回您。"

        msg = resp.choices[0].message
        text = (msg.content or "").strip()
        tool_calls = msg.tool_calls or []

        # 没有 tool call → 直接回复
        if not tool_calls:
            if not text:
                text = "好的领导。"
            conv.add_assistant(text)
            logger.info("秘书回复: %s", text)
            return text

        # 有 tool call → 派单（如果标注"加急"则同步等结果，否则后台 fire-and-forget）
        urgent = "加急" in user_text or "赶紧" in user_text

        if urgent:
            return await self._run_tools_sync(tool_calls, conv)
        else:
            # 异步：先给用户回"安排中"，后台跑完回拨
            asyncio.create_task(self._run_tools_async(tool_calls, conv))
            ack = "好的领导，我这就去安排相关部门处理，有结果我第一时间回您电话。"
            conv.add_assistant(ack)
            return ack

    async def _run_tools_sync(self, tool_calls, conv: Conversation) -> str:
        """加急：同步等所有部门结果，综合回复"""
        results = await asyncio.gather(
            *(self._call_dept(tc) for tc in tool_calls),
            return_exceptions=True,
        )
        tool_msgs = self._build_tool_msgs(tool_calls, results)
        # 第二次调豆包，让它综合结果
        try:
            resp = await self._client.chat.completions.create(
                model=self._cfg.model,
                temperature=self._cfg.temperature,
                messages=[
                    {"role": "system", "content": self._sys_prompt},
                    *conv.to_messages(max_pairs=self._cfg.max_history),
                    {"role": "assistant", "content": None, "tool_calls": tool_calls},
                    *tool_msgs,
                ],
            )
            text = (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            logger.exception("豆包综合失败: %s", e)
            text = self._fallback_summarize(results)

        conv.add_assistant(text)
        return text

    async def _run_tools_async(self, tool_calls, conv: Conversation) -> None:
        """异步：跑完自动回拨"""
        try:
            results = await asyncio.gather(
                *(self._call_dept(tc) for tc in tool_calls),
                return_exceptions=True,
            )
            text = self._fallback_summarize(results)
            conv.add_assistant(text)
            logger.info("异步任务完成: %s", text)
            if self._on_response is not None:
                await self._on_response(text)
        except Exception as e:  # noqa: BLE001
            logger.exception("异步派单失败: %s", e)
            if self._on_response is not None:
                await self._on_response("领导，事情没办成，我再催一下。")

    async def _call_dept(self, tc) -> Any:
        name = tc.function.name
        args = json.loads(tc.function.arguments or "{}")
        task = args.get("task", "")
        logger.info("派单 %s: %s", name, task)

        if name == "dispatch_organization":
            return await self._org.handle(task)
        if name == "dispatch_propaganda":
            return await self._prop.handle(task)
        if name == "dispatch_social":
            return await self._soc.handle(task)
        if name == "dispatch_politics_law":
            return await self._pl.handle(task)
        return f"[未识别部门 {name}]"

    @staticmethod
    def _build_tool_msgs(tool_calls, results):
        msgs = []
        for tc, r in zip(tool_calls, results):
            content = r if isinstance(r, str) else f"[异常] {r!r}"
            msgs.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": content,
                }
            )
        return msgs

    @staticmethod
    def _fallback_summarize(results) -> str:
        """豆包综合失败时，简单拼接"""
        parts = []
        for r in results:
            if isinstance(r, str) and r:
                parts.append(r)
        if not parts:
            return "领导，事情没办成，我再催一下。"
        return "领导，事情办妥了。\n" + "\n".join(parts)
