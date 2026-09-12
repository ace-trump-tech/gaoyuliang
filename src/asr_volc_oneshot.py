"""
火山 ASR —— HTTP 一次性识别（方案 C 使用）

接收完整 PCM 字节数组，调用火山 ASR REST API，返回识别文本
比流式简单很多：等用户说完一句话后整段 POST
"""
from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

VOLC_ASR_HTTP_URL = "https://openspeech.bytedance.com/api/v1/asr"


@dataclass
class VolcASROneshotConfig:
    appid: str
    token: str
    cluster: str = "volcano_tts"
    language: str = "zh-CN"
    sample_rate: int = 16000
    format: str = "pcm"


class VolcASROneshot:
    """一次性 ASR：等一段完整音频 → POST → 收文本"""

    def __init__(self, cfg: VolcASROneshotConfig):
        self._cfg = cfg
        self._client = httpx.AsyncClient(timeout=30.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def recognize(self, pcm_bytes: bytes) -> str:
        """
        把一段完整 PCM 16k mono 送 ASR

        返回识别文本；空音频或失败返回 ""
        """
        if not pcm_bytes:
            return ""

        # 火山 ASR v1 接口要求把音频作为 base64 字符串放进 JSON body
        audio_b64 = base64.b64encode(pcm_bytes).decode("ascii")

        body = {
            "app": {
                "appid": self._cfg.appid,
                "cluster": self._cfg.cluster,
                "token": self._cfg.token,
            },
            "user": {"uid": "gaoyuliang"},
            "audio": {
                "format": self._cfg.format,
                "rate": self._cfg.sample_rate,
                "language": self._cfg.language,
            },
            "request": {
                "reqid": str(int(time.time() * 1000)),
                "nbest": 1,
            },
        }
        body["audio"]["data"] = audio_b64

        headers = {
            "Authorization": f"Bearer; {self._cfg.token}",
            "Content-Type": "application/json",
        }

        try:
            r = await self._client.post(VOLC_ASR_HTTP_URL, json=body, headers=headers)
            r.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("ASR HTTP failed: %s", e)
            return ""

        payload = r.json()
        if "error" in payload and payload.get("error_code", 0) != 0:
            logger.error("ASR error: %s", payload)
            return ""

        # 解析 result
        result_text = ""
        if isinstance(payload.get("result"), list) and payload["result"]:
            first = payload["result"][0]
            if isinstance(first, dict):
                result_text = first.get("text", "")
            elif isinstance(first, str):
                # 部分老接口直接返回字符串
                result_text = first

        logger.info("ASR oneshot: %s", result_text)
        return result_text
