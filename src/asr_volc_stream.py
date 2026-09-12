"""
火山 ASR —— WebSocket 流式识别（方案 B 使用）

API 文档：https://www.volcengine.com/docs/6561/79817
鉴权：Bearer token (VOLC_TOKEN)
endpoint：wss://openspeech.bytedance.com/api/v2/asr
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import numpy as np

try:
    import websockets
except ImportError:
    websockets = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class VolcASRStreamConfig:
    appid: str
    token: str
    cluster: str = "volcano_tts"
    language: str = "zh-CN"
    sample_rate: int = 16000
    domain: str = "bigmodel"        # bigmodel / general / education
    format: str = "pcm"
    endpoint_silence_ms: int = 5000  # 句尾静音 5s 视为本句结束


class VolcASRStream:
    """
    流式 ASR 客户端

    用法：
        asr = VolcASRStream(cfg)
        await asr.start()
        async for text in asr.feed(pcm_chunk): ...
        final = await asr.finish()
    """

    def __init__(self, cfg: VolcASRStreamConfig):
        self._cfg = cfg
        self._ws = None
        self._seq = 1
        self._final_text = ""
        self._result_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

    async def start(self) -> None:
        if websockets is None:
            raise RuntimeError("请先 pip install websockets")

        url = "wss://openspeech.bytedance.com/api/v2/asr"
        headers = {
            "Authorization": f"Bearer; {self._cfg.token}",
        }

        # 第一帧是 full client request（配置）
        req = {
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
                "domain": self._cfg.domain,
            },
            "request": {
                "reqid": str(int(time.time() * 1000)),
                "nbest": 1,
                "endpoint_silence_ms": self._cfg.endpoint_silence_ms,
                "show_utterances": True,
            },
        }

        self._ws = await websockets.connect(
            url,
            extra_headers=headers,
            max_size=10 * 1024 * 1024,
        )
        await self._ws.send(json.dumps(req))
        # 启动后台任务，循环读取 server response
        self._reader_task = asyncio.create_task(self._reader())
        logger.info("VolcASRStream connected, reqid=%s", req["request"]["reqid"])

    async def _reader(self) -> None:
        assert self._ws is not None
        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="ignore")
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("ASR non-json payload: %s", raw)
                    continue

                # 1 = intermediate, 2 = final
                if payload.get("type") == "result":
                    utterances = payload.get("utterances") or []
                    if utterances:
                        text = utterances[0].get("text", "")
                        is_final = utterances[0].get("definite", False)
                        if text:
                            await self._result_queue.put(text)
                            if is_final:
                                self._final_text = text
                                await self._result_queue.put(None)  # 哨兵
                elif payload.get("type") == "error":
                    logger.error("ASR error: %s", payload)
                    await self._result_queue.put(None)
                    break
        except Exception as e:  # noqa: BLE001
            logger.exception("ASR reader crashed: %s", e)
            await self._result_queue.put(None)

    async def feed(self, pcm_chunk: bytes) -> None:
        """送一块 20ms PCM 上去"""
        assert self._ws is not None
        await self._ws.send(pcm_chunk)

    async def stream_text(self) -> AsyncIterator[str]:
        """
        持续产出识别文本（中间结果实时增量更新）
        收尾时抛 StopIteration（通过 None 哨兵结束）
        """
        while True:
            text = await self._result_queue.get()
            if text is None:
                return
            yield text

    async def wait_final(self) -> str:
        """阻塞直到收到最终结果"""
        async for t in self.stream_text():
            if t:
                pass
        return self._final_text

    async def finish(self) -> str:
        """发结束帧，等最终结果"""
        assert self._ws is not None
        await self._ws.send(b"")  # 火山用空二进制帧表示音频结束
        final = await self.wait_final()
        try:
            await self._ws.close()
        except Exception:  # noqa: BLE001
            pass
        logger.info("ASR final: %s", final)
        return final
