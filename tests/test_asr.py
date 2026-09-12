"""
火山 ASR + TTS 测试

需要 .env 里的 VOLC_APPID / VOLC_TOKEN 有效
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.asr_volc_oneshot import VolcASROneshot, VolcASROneshotConfig
from src.tts_volc import VolcTTS, VolcTTSConfig


async def main() -> None:
    load_dotenv(ROOT / ".env")
    if not os.environ.get("VOLC_APPID") or os.environ["VOLC_APPID"] == "your_volc_appid":
        print("⚠️  请先在 .env 填入 VOLC_APPID / VOLC_TOKEN")
        return

    # ---- TTS 测试 ----
    print("=== TTS 测试 ===")
    tts = VolcTTS(
        VolcTTSConfig(
            appid=os.environ["VOLC_APPID"],
            token=os.environ["VOLC_TOKEN"],
        )
    )
    try:
        pcm = await tts.synthesize("您好高书记，我是您的秘书。")
        print(f"  TTS 输出 {len(pcm)} bytes PCM")
        assert len(pcm) > 1000, "TTS 输出 PCM 太短，可能失败"
        print("  ✓ TTS 正常")
    finally:
        await tts.aclose()

    # ---- ASR 测试（用 TTS 输出做回路）----
    print("\n=== ASR 测试 ===")
    asr = VolcASROneshot(
        VolcASROneshotConfig(
            appid=os.environ["VOLC_APPID"],
            token=os.environ["VOLC_TOKEN"],
        )
    )
    try:
        # 用 TTS 的 PCM 喂给 ASR
        tts2 = VolcTTS(
            VolcTTSConfig(
                appid=os.environ["VOLC_APPID"],
                token=os.environ["VOLC_TOKEN"],
            )
        )
        try:
            test_pcm = await tts2.synthesize("北京今天天气晴朗，最高温度二十五度。")
            text = await asr.recognize(test_pcm)
            print(f"  ASR 识别: {text}")
            if "北京" in text or "天气" in text:
                print("  ✓ ASR 正常")
            else:
                print("  ⚠️  ASR 识别偏差较大，但接口是通的")
        finally:
            await tts2.aclose()
    finally:
        await asr.aclose()


if __name__ == "__main__":
    asyncio.run(main())
