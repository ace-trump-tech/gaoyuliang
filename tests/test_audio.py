"""
音频设备测试

用法：
    python -m tests.test_audio
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import sounddevice as sd

from src.audio import (
    AudioConfig,
    AudioInput,
    AudioOutput,
    list_input_devices,
    list_output_devices,
)


def main() -> None:
    print("=== 输入设备 ===")
    for d in list_input_devices():
        print(f"  [{d['index']}] {d['name']} (ch={d['max_input_channels']})")

    print("\n=== 输出设备 ===")
    for d in list_output_devices():
        print(f"  [{d['index']}] {d['name']} (ch={d['max_output_channels']})")

    print("\n=== 默认设备 ===")
    print(f"  default input:  {sd.query_devices(kind='input')['name']}")
    print(f"  default output: {sd.query_devices(kind='output')['name']}")

    print("\n=== 录音 3 秒 ===")
    sr = 16000
    rec = sd.rec(int(3 * sr), samplerate=sr, channels=1, dtype="int16")
    sd.wait()
    rms = float(np.sqrt(np.mean(rec.astype(np.float32) ** 2)))
    peak = int(np.max(np.abs(rec)))
    print(f"  RMS = {rms:.1f}, Peak = {peak}")
    if rms < 50:
        print("  ⚠️  能量过低，可能是话筒没接好")
    elif rms > 5000:
        print("  ⚠️  能量过高，可能是 gain 太大或 MIC 偏置异常")

    print("\n=== 回放 ===")
    sd.play(rec, samplerate=sr)
    sd.wait()
    print("  ✓ 播放完成")

    print("\n=== RMS 函数单元测试 ===")
    cfg = AudioConfig()
    ai = AudioInput(cfg)
    silence = bytes(320 * 2)  # 320 samples int16 = 640 bytes
    loud = np.random.randint(-1000, 1000, 320, dtype=np.int16).tobytes()
    s_rms = ai.rms_energy(silence)
    l_rms = ai.rms_energy(loud)
    print(f"  silence RMS = {s_rms:.1f} (期望接近 0)")
    print(f"  loud RMS    = {l_rms:.1f} (期望 > 100)")
    assert s_rms < 5, "静音 RMS 应接近 0"
    assert l_rms > 100, "响亮 RMS 应 > 100"
    print("  ✓ RMS 函数正常")


if __name__ == "__main__":
    main()
