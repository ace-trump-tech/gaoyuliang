"""
火山 TTS —— 调用豆包通用女声，把秘书文本转 PCM

API 文档：https://www.volcengine.com/docs/6561/79817
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

VOLC_TTS_HTTP_URL = "https://openspeech.bytedance.com/api/v1/tts"


@dataclass
class VolcTTSConfig:
    appid: str
    token: str
    cluster: str = "volcano_tts"
    voice: str = "BV001_streaming"  # 豆包通用女声
    sample_rate: int = 16000
    encoding: str = "pcm_s16le"    # 直接 PCM，免转码
    speed_ratio: float = 1.0


class VolcTTS:
    """同步调用一次 TTS，返回完整 PCM bytes"""

    def __init__(self, cfg: VolcTTSConfig):
        self._cfg = cfg
        self._client = httpx.AsyncClient(timeout=30.0)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def synthesize(self, text: str) -> bytes:
        """文本 → PCM bytes"""
        if not text:
            return b""

        req = {
            "app": {
                "appid": self._cfg.appid,
                "cluster": self._cfg.cluster,
                "token": self._cfg.token,
            },
            "user": {"uid": "gaoyuliang"},
            "audio": {
                "voice_type": self._cfg.voice,
                "encoding": self._cfg.encoding,
                "speed_ratio": self._cfg.speed_ratio,
                "rate": self._cfg.sample_rate,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson",
            },
        }

        headers = {
            "Authorization": f"Bearer; {self._cfg.token}",
            "Content-Type": "application/json",
        }

        try:
            r = await self._client.post(VOLC_TTS_HTTP_URL, json=req, headers=headers)
            r.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("TTS HTTP failed: %s", e)
            return b""

        payload = r.json()
        if "data" not in payload or not payload["data"]:
            logger.error("TTS no data: %s", payload)
            return b""

        import base64

        pcm = base64.b64decode(payload["data"])
        logger.debug("TTS %d chars → %d bytes PCM", len(text), len(pcm))
        return pcm
