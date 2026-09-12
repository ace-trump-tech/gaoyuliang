"""
方案 B —— 全云端流式入口

流程：
1. 待机：监听 mic RMS，拿起话筒（> 阈值 100ms）→ 进入通话
2. 启动火山 ASR 流式 + 豆包秘书
3. 收集用户一段话（基于火山 ASR endpoint 判定）
4. 送豆包 → 回复 → TTS → 播放
5. 火山 ASR 5s 静默 → 挂断
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# 让 src 包可导入
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.audio import AudioConfig, AudioInput, AudioOutput  # noqa: E402
from src.asr_volc_stream import VolcASRStream, VolcASRStreamConfig  # noqa: E402
from src.conversation import Conversation  # noqa: E402
from src.doubao_agent import DoubaoAgent, DoubaoConfig  # noqa: E402
from src.notifier import PhoneNotifier  # noqa: E402
from src.tts_volc import VolcTTS, VolcTTSConfig  # noqa: E402

logger = logging.getLogger(__name__)


def _load_yaml(name: str) -> dict:
    with open(ROOT / "config" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


async def _run_call(
    audio_in: AudioInput,
    audio_out: AudioOutput,
    tts: VolcTTS,
    asr_cfg: VolcASRStreamConfig,
    agent: DoubaoAgent,
    conv: Conversation,
    rms_threshold: int,
    notifier: PhoneNotifier,
) -> None:
    """单轮通话循环：拿起 → 多次对话 → 挂断"""
    conv.reset()

    # 1) 等拿起话筒：连续 N 块能量 > 阈值
    logger.info("待机：等拿起话筒...")
    pick_up_chunks = 0
    while True:
        chunk = await audio_in.read_chunk()
        rms = AudioInput.rms_energy(chunk)
        if rms > rms_threshold:
            pick_up_chunks += 1
            if pick_up_chunks >= 3:  # 60ms 持续有能量
                break
        else:
            pick_up_chunks = 0

    logger.info("检测到拿起话筒")

    # 2) 启动 ASR 流式
    asr = VolcASRStream(asr_cfg)
    await asr.start()

    try:
        # 启动音频泵：mic → ASR
        pump = asyncio.create_task(_pump_mic_to_asr(audio_in, asr))

        # 启动 ASR 结果消费
        while True:
            logger.info("秘书候命中...")
            try:
                user_text = await asyncio.wait_for(asr.wait_final(), timeout=60)
            except asyncio.TimeoutError:
                logger.info("超时，自动挂断")
                break

            if not user_text:
                logger.info("ASR 无文本，挂断")
                break

            # 把这一段送秘书
            reply = await agent.handle(user_text, conv)
            pcm = await tts.synthesize(reply)
            if pcm:
                await audio_out.play_pcm_async(pcm)

            # 5s 内没新 ASR final → 挂断（火山 ASR 自己判定 endpoint）
            # 这里简单用 conv 不再增长作为信号
            await asyncio.sleep(0.2)

        # 停泵
        pump.cancel()
        try:
            await pump
        except asyncio.CancelledError:
            pass
    finally:
        await asr.finish()


async def _pump_mic_to_asr(audio_in: AudioInput, asr: VolcASRStream) -> None:
    """把 mic 音频持续送进 ASR"""
    while True:
        chunk = await audio_in.read_chunk()
        await asr.feed(chunk)


async def main_async() -> None:
    load_dotenv(ROOT / ".env")
    settings = _load_yaml("settings.yaml")
    prompts = _load_yaml("prompts.yaml")

    # ---- 配置 ----
    audio_cfg = AudioConfig(
        sample_rate=settings["audio"]["sample_rate"],
        channels=settings["audio"]["channels"],
        block_size=settings["audio"]["block_size"],
        mic_rms_threshold=settings["audio"]["mic_rms_threshold"],
    )

    asr_cfg = VolcASRStreamConfig(
        appid=os.environ["VOLC_APPID"],
        token=os.environ["VOLC_TOKEN"],
        cluster=settings["asr"]["cluster"],
        language=settings["asr"]["language"],
        sample_rate=settings["audio"]["sample_rate"],
        domain=settings["asr"]["domain"],
        endpoint_silence_ms=5000,
    )

    tts_cfg = VolcTTSConfig(
        appid=os.environ["VOLC_APPID"],
        token=os.environ["VOLC_TOKEN"],
        cluster=settings["tts"]["cluster"],
        voice=settings["tts"]["voice"],
        sample_rate=settings["tts"]["sample_rate"],
    )

    doubao_cfg = DoubaoConfig(
        api_key=os.environ["DOUBAO_API_KEY"],
        base_url=os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        model=os.environ.get("DOUBAO_MODEL", settings["doubao"]["model"]),
        temperature=settings["doubao"]["temperature"],
        max_history=settings["doubao"]["max_history"],
    )

    # ---- 启动硬件 ----
    audio_in = AudioInput(audio_cfg)
    audio_out = AudioOutput(audio_cfg)
    audio_out.start()
    await audio_in.start()

    # ---- TTS + 秘书 ----
    tts = VolcTTS(tts_cfg)
    notifier = PhoneNotifier(tts, audio_out)

    agent = DoubaoAgent(
        doubao_cfg,
        secretary_system_prompt=prompts["secretary"],
        on_response=notifier.notify,
    )

    # ---- 主循环：拿起 → 通话 → 挂断 → 循环 ----
    stop = asyncio.Event()

    def _sig(*_):
        stop.set()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    try:
        while not stop.is_set():
            conv = Conversation()
            try:
                await _run_call(
                    audio_in,
                    audio_out,
                    tts,
                    asr_cfg,
                    agent,
                    conv,
                    audio_cfg.mic_rms_threshold,
                    notifier,
                )
            except Exception as e:  # noqa: BLE001
                logger.exception("通话异常: %s", e)
                await asyncio.sleep(1.0)
    finally:
        await agent.aclose()
        await tts.aclose()
        await audio_in.stop()
        audio_out.stop()


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
