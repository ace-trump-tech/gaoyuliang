"""
音频 I/O 封装

- AudioInput：mic → async.Queue（PCM bytes）
- AudioOutput：async.Queue → 听筒（PCM bytes）
- rms_energy：给方案 B 用来检测"拿起话筒"和"挂断"
"""
from __future__ import annotations

import asyncio
import logging
import queue
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
except OSError as e:
    raise RuntimeError(
        "sounddevice 加载失败，请先安装 PortAudio 或在 Windows 上确认 "
        "Microsoft C++ Redistributable 已安装"
    ) from e

logger = logging.getLogger(__name__)


class AudioConfig:
    """音频参数（由 config/settings.yaml 注入）"""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        block_size: int = 320,
        mic_rms_threshold: int = 100,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size
        self.mic_rms_threshold = mic_rms_threshold


class AudioInput:
    """
    把 USB 声卡 mic 的流式 PCM 灌进 asyncio.Queue

    启动后从 self._queue 拿 bytes；每块 20ms (320 采样) int16 LE 单声道
    """

    def __init__(self, cfg: AudioConfig, device: Optional[str] = None):
        self._cfg = cfg
        self._device = device
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)
        self._stream: Optional[sd.InputStream] = None

    def _callback(self, indata, frames, time_info, status):
        if status:
            logger.warning("AudioInput status: %s", status)
        # sounddevice 给的 indata 是 np.ndarray（int16）—— 直接拿 bytes
        chunk = bytes(indata)
        if self._loop is None:
            return
        # 从 mic 线程跨到 asyncio 线程
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, chunk)
        except asyncio.QueueFull:
            # 队列满 = 消费跟不上 = 直接丢，避免阻塞 mic 线程
            logger.warning("AudioInput queue full, dropping chunk")

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._stream = sd.InputStream(
            samplerate=self._cfg.sample_rate,
            channels=self._cfg.channels,
            dtype=self._cfg.dtype,
            blocksize=self._cfg.block_size,
            device=self._device,
            callback=self._callback,
        )
        self._stream.start()
        logger.info(
            "AudioInput started: rate=%d ch=%d block=%d",
            self._cfg.sample_rate,
            self._cfg.channels,
            self._cfg.block_size,
        )

    async def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("AudioInput stopped")

    async def read_chunk(self) -> bytes:
        """阻塞读一块 20ms PCM"""
        return await self._queue.get()

    @staticmethod
    def rms_energy(audio: bytes) -> float:
        """int16 PCM 的 RMS（方案 B 用来判断"是否在说话"）"""
        if not audio:
            return 0.0
        arr = np.frombuffer(audio, dtype=np.int16)
        return float(np.sqrt(np.mean(arr.astype(np.float32) ** 2)))


class AudioOutput:
    """
    把 TTS 输出的 PCM bytes 灌到听筒

    阻塞播放；可由 OutputStream 异步写入
    """

    def __init__(self, cfg: AudioConfig, device: Optional[str] = None):
        self._cfg = cfg
        self._device = device
        self._stream: Optional[sd.OutputStream] = None

    def start(self) -> None:
        self._stream = sd.OutputStream(
            samplerate=self._cfg.sample_rate,
            channels=self._cfg.channels,
            dtype=self._cfg.dtype,
            blocksize=self._cfg.block_size,
            device=self._device,
        )
        self._stream.start()
        logger.info("AudioOutput started")

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("AudioOutput stopped")

    def play_pcm(self, pcm: bytes) -> None:
        """同步播放一段完整 PCM（int16 LE mono）"""
        if self._stream is None:
            self.start()
        arr = np.frombuffer(pcm, dtype=np.int16)
        if arr.size == 0:
            return
        # sounddevice 自动按 block_size 切，write 阻塞直到播完
        self._stream.write(arr)

    async def play_pcm_async(self, pcm: bytes) -> None:
        await asyncio.to_thread(self.play_pcm, pcm)


def list_input_devices() -> list[dict]:
    """列出所有可用的输入设备（调试用）"""
    devs = sd.query_devices()
    return [
        {"index": i, "name": d["name"], "max_input_channels": d["max_input_channels"]}
        for i, d in enumerate(devs)
        if d["max_input_channels"] > 0
    ]


def list_output_devices() -> list[dict]:
    """列出所有可用的输出设备（调试用）"""
    devs = sd.query_devices()
    return [
        {"index": i, "name": d["name"], "max_output_channels": d["max_output_channels"]}
        for i, d in enumerate(devs)
        if d["max_output_channels"] > 0
    ]
