"""
silero-vad 封装（仅方案 C 使用）

判断一段 PCM 是 speech / silence，给 main_c.py 用来：
1. 截断一句话
2. 5 秒无 speech → 自动挂断
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VADConfig:
    speech_threshold: float = 0.5
    min_silence_ms: int = 500
    hangup_silence_sec: float = 5.0
    sample_rate: int = 16000


class SileroVAD:
    """
    包装 silero-vad 模型

    用法：
        vad = SileroVAD(VADConfig())
        vad.reset()
        for chunk in mic:
            prob = vad.feed(chunk)
            if prob > 0.5:
                # 当前是 speech
            ...
    """

    def __init__(self, cfg: VADConfig):
        self._cfg = cfg
        self._model = None
        self._state = None
        self._ctx = None
        # 滑动窗口：每个块一个 prob
        self._window_ms = 100  # silero 要求每块 ≥30ms；用 100ms 一块
        self._samples_per_window = int(self._cfg.sample_rate * self._window_ms / 1000)
        self._buffer = bytearray()
        # 连续静音累计秒数
        self._silence_acc = 0.0
        self._chunk_duration_ms = 0.0

    def load(self) -> None:
        """懒加载 silero 模型"""
        if self._model is not None:
            return
        try:
            from silero_vad import load_silero_vad

            self._model, self._state = load_silero_vad(onnx=True)
            logger.info("silero-vad loaded (onnx)")
        except Exception as e:  # noqa: BLE001
            logger.warning("silero ONNX load failed, fallback to torch: %s", e)
            try:
                import torch  # noqa: F401

                from silero_vad import load_silero_vad  # type: ignore

                self._model, self._state = load_silero_vad(onnx=False)
                logger.info("silero-vad loaded (torch)")
            except Exception as e2:  # noqa: BLE001
                logger.error("silero-vad load failed: %s", e2)
                raise

    def reset(self) -> None:
        """重置内部状态（一轮通话开始）"""
        self._state = None  # silero state 重置
        self._buffer = bytearray()
        self._silence_acc = 0.0

    def feed(self, pcm_chunk: bytes) -> Optional[float]:
        """
        喂一块 PCM，返回当前 100ms 块的 speech_prob；
        如果还没攒够一个 window，返回 None
        """
        self.load()
        if self._model is None:
            return None

        self._buffer.extend(pcm_chunk)
        if len(self._buffer) < self._samples_per_window * 2:
            return None

        # 切 100ms
        n = self._samples_per_window * 2
        block = bytes(self._buffer[:n])
        del self._buffer[:n]

        audio = np.frombuffer(block, dtype=np.int16).astype(np.float32) / 32768.0
        prob = float(self._model.audio_forward(audio, self._state))
        self._chunk_duration_ms = self._window_ms

        if prob >= self._cfg.speech_threshold:
            self._silence_acc = 0.0
        else:
            self._silence_acc += self._chunk_duration_ms / 1000.0

        return prob

    @property
    def silence_seconds(self) -> float:
        """累计连续静音秒数"""
        return self._silence_acc

    @property
    def should_hangup(self) -> bool:
        """是否已达到挂断阈值"""
        return self._silence_acc >= self._cfg.hangup_silence_sec

    @property
    def current_utt_complete(self) -> bool:
        """一句话是否已结束（≥ min_silence_ms 静音）"""
        return self._silence_acc * 1000.0 >= self._cfg.min_silence_ms
