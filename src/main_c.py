"""
方案 C —— 本地 VAD + 一次性 ASR 入口

流程：
1. mic → silero-vad 实时判断 speech / silence
2. VAD 检测到 speech → 进入"累积一句话"状态
3. min_silence_ms 静音后 → 整段 POST 给火山 ASR
4. 送豆包 → 回复 → TTS → 播放
5. hangup_silence_sec 连续静音 → 挂断
"""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.audio import AudioConfig, AudioInput, AudioOutput  # noqa: E402
from src.asr_volc_oneshot import VolcASROneshot, VolcASROneshotConfig  # noqa: E402
from src.conversation import Conversation  # noqa: E402
from src.doubao_agent import DoubaoAgent, DoubaoConfig  # noqa: E402
from src.notifier import PhoneNotifier  # noqa: E402
from src.tts_volc import VolcTTS, VolcTTSConfig  # noqa: E402
from src.vad import SileroVAD, VADConfig  # noqa: E402

logger = logging.getLogger(__name__)


def _load_yaml(name: str) -> dict:
    with open(ROOT / "config" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


async def _run_call(
    audio_in: AudioInput,
    audio_out: AudioOutput,
    tts: VolcTTS,
    asr: VolcASROneshot,
    vad: SileroVAD,
    agent: DoubaoAgent,
    conv: Conversation,
    notifier: PhoneNotifier,
) -> None:
    """单轮通话：拿起 → 多轮对话 → 挂断"""
    conv.reset()
    vad.reset()

    # 1) 待机：等说话
    logger.info("待机：等你说话...")
    while True:
        chunk = await audio_in.read_chunk()
        prob = vad.feed(chunk)
        if prob is not None and prob >= vad._cfg.speech_threshold:  # noqa: SLF001
            break

    logger.info("检测到 speech")

    # 2) 累积一句话（直到一句完整）
    while True:
        chunk = await audio_in.read_chunk()
        prob = vad.feed(chunk)

        # VAD: 已挂断阈值（hangup）
        if vad.should_hangup:
            logger.info("VAD: %ds 静音，挂断", vad._cfg.hangup_silence_sec)  # noqa: SLF001
            return

        # VAD: 一句话结束
        if prob is not None and prob < vad._cfg.speech_threshold and vad.current_utt_complete:  # noqa: SLF001
            # 把这一段送 ASR
            # 注意：vad 在内部维护了 buffer，但我们其实可以在下面重新累积
            # 简化：再开一个 buffer 从这一刻开始到 sentence_end
            sentence = await _accumulate_one_sentence(audio_in, vad)
            if not sentence:
                continue
            text = await asr.recognize(sentence)
            if not text:
                continue
            logger.info("用户: %s", text)
            reply = await agent.handle(text, conv)
            pcm = await tts.synthesize(reply)
            if pcm:
                await audio_out.play_pcm_async(pcm)
            # 播完后重置 VAD sentence-end 计数
            vad.reset()
            # 重新进入"等下一句"状态
            await _wait_for_speech(audio_in, vad)


async def _wait_for_speech(audio_in: AudioInput, vad: SileroVAD) -> None:
    """等下一次说话开始"""
    while True:
        chunk = await audio_in.read_chunk()
        if vad.should_hangup:
            return
        prob = vad.feed(chunk)
        if prob is not None and prob >= vad._cfg.speech_threshold:  # noqa: SLF001
            return


async def _accumulate_one_sentence(audio_in: AudioInput, vad: SileroVAD) -> bytes:
    """
    累积直到一句话结束（≥ min_silence_ms 静音）
    返回完整 PCM
    """
    buf = bytearray()
    while True:
        chunk = await audio_in.read_chunk()
        buf.extend(chunk)
        vad.feed(chunk)
        if vad.should_hangup:
            return bytes(buf)
        if vad.current_utt_complete and vad.feed(b"\x00" * len(chunk)) is not None:
            # 再吃一块确认 sentence end
            pass
        # 简化：一旦静音 ≥ min_silence_ms，认为本句结束
        if vad.silence_seconds * 1000 >= vad._cfg.min_silence_ms:  # noqa: SLF001
            return bytes(buf)


async def main_async() -> None:
    load_dotenv(ROOT / ".env")
    settings = _load_yaml("settings.yaml")
    prompts = _load_yaml("prompts.yaml")

    # ---- 配置 ----
    audio_cfg = AudioConfig(
        sample_rate=settings["audio"]["sample_rate"],
        channels=settings["audio"]["channels"],
        block_size=settings["audio"]["block_size"],
    )

    vad_cfg = VADConfig(
        speech_threshold=settings["vad"]["speech_threshold"],
        min_silence_ms=settings["vad"]["min_silence_ms"],
        hangup_silence_sec=settings["vad"]["hangup_silence_sec"],
        sample_rate=settings["audio"]["sample_rate"],
    )

    asr_cfg = VolcASROneshotConfig(
        appid=os.environ["VOLC_APPID"],
        token=os.environ["VOLC_TOKEN"],
        cluster=settings["asr"]["cluster"],
        language=settings["asr"]["language"],
        sample_rate=settings["audio"]["sample_rate"],
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

    vad = SileroVAD(vad_cfg)
    vad.load()

    tts = VolcTTS(tts_cfg)
    asr = VolcASROneshot(asr_cfg)
    notifier = PhoneNotifier(tts, audio_out)

    agent = DoubaoAgent(
        doubao_cfg,
        secretary_system_prompt=prompts["secretary"],
        on_response=notifier.notify,
    )

    stop = asyncio.Event()

    def _sig(*_):
        stop.set()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    try:
        while not stop.is_set():
            conv = Conversation()
            try:
                await _run_call(audio_in, audio_out, tts, asr, vad, agent, conv, notifier)
            except Exception as e:  # noqa: BLE001
                logger.exception("通话异常: %s", e)
                await asyncio.sleep(1.0)
    finally:
        await agent.aclose()
        await tts.aclose()
        await asr.aclose()
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
