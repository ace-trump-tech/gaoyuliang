"""
回拨通知器（异步任务完成后，通过座机主动回拨高育良）

原理：秘书处触发 on_response(text) → 这里把 text 灌进 TTS → 走 AudioOutput 播放
本质上复用 main 循环的音频输出通道
"""
from __future__ import annotations

import asyncio
import logging

from .tts_volc import VolcTTS

logger = logging.getLogger(__name__)


class PhoneNotifier:
    """异步回拨——把文本走 TTS 然后播放"""

    def __init__(self, tts: VolcTTS, audio_output):
        self._tts = tts
        self._out = audio_output
        self._lock = asyncio.Lock()  # 保证一次只播一段

    async def notify(self, text: str) -> None:
        """主动拨出"""
        async with self._lock:
            logger.info("回拨: %s", text)
            try:
                pcm = await self._tts.synthesize(text)
                if pcm:
                    await self._out.play_pcm_async(pcm)
            except Exception as e:  # noqa: BLE001
                logger.exception("回拨失败: %s", e)
