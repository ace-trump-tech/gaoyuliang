# Windows 环境配置

## 1. 安装 Python

建议 Python 3.11+（3.12 兼容性最稳）。

下载：https://www.python.org/downloads/windows/

⚠️ **安装时勾选 "Add Python to PATH"**

验证：
```powershell
python --version
pip --version
```

## 2. 安装 Microsoft C++ Redistributable

sounddevice 依赖 PortAudio，需要 Visual C++ 运行库。

下载：https://aka.ms/vs/17/release/vc_redist.x64.exe

## 3. 克隆/拷贝项目

```powershell
cd C:\Users\tuozhongyao\Downloads
git clone <repo> gaoyuliang
# 或从 U 盘拷过来
cd gaoyuliang
```

## 4. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 若提示"无法加载脚本，因为在此系统上禁止运行脚本"
# 用管理员打开 PowerShell 执行：
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# 然后再激活
```

## 5. 安装依赖

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 常见安装报错

| 报错 | 解决 |
|---|---|
| `Microsoft Visual C++ 14.0 or greater is required` | 安装 Visual Studio Build Tools 2022：https://visualstudio.microsoft.com/visual-cpp-build-tools/ |
| `ERROR: Failed building wheel for pyaudio` | 用 `pipwin install pyaudio`，或先装 `portaudio` |
| `silero-vad` 装不上 | 确认 PyTorch 已装：`pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu`（CPU 版即可） |
| `onnxruntime` 装不上 | 选对应 Python 版本的 wheel：https://pypi.org/project/onnxruntime/#files |

## 6. 配置 API Key

```powershell
copy .env.example .env
notepad .env
```

填入：
- `VOLC_APPID` / `VOLC_TOKEN` —— 火山引擎控制台 https://console.volcengine.com/
- `DOUBAO_API_KEY` —— 火山引擎 → 豆包大模型 → 在线推理
- `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` / `OPENAI_API_KEY` / `DEEPSEEK_API_KEY`

## 7. 验证音频设备

```powershell
python -m tests.test_audio
```

应该列出 "USB Audio Device" 或类似名字的设备。

如果想指定设备，可以在 `main_b.py` / `main_c.py` 启动前设置：

```python
import os
os.environ["AUDIO_DEVICE_NAME"] = "USB Audio Device"
```

或者直接修改 `src/audio.py` 的 `AudioInput(device=...)`。

## 8. 验证 ASR / TTS

```powershell
python -m tests.test_asr
```

应能看到 "测试 ASR 成功" 字样（调用真实 API 会消耗额度）。

## 9. 启动

**方案 B**：
```powershell
python -m src.main_b
```

**方案 C**：
```powershell
python -m src.main_c
```

启动后：
- 控制台打印 "待机：等拿起话筒..."
- 拿起话筒，说"高书记，帮我看看近期宣传工作的舆论风险"
- 秘书处回应 → 调度宣传部 → TTS 播报

---

## 🔧 性能调优

### 减少 TTS 延迟
火山 TTS 第一次合成有 1-2s 冷启动；可以在程序启动时先合成一句"您好"热身。

### 减少 ASR 延迟
- 方案 B：火山 ASR WebSocket 是流式，首字延迟 ~300ms
- 方案 C：等用户说完才送 ASR，单次延迟 ~800ms

### 减少豆包延迟
- `temperature` 调到 0.5 → 更快
- `max_history` 调到 10 → 更快

### 防止 TTS 卡顿
火山 TTS 默认流式响应，可以修改 `tts_volc.py` 改为 streaming 模式，播放分段播放。
