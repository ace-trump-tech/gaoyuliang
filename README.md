<div align="center">

# 📞 高育良同志的红色座机

### 一台真实的复古座机 × 豆包贴身秘书 × 四大 AI 部委 × Windows

[English](#english) · [简体中文](#简体中文) · [演示](#演示) · [快速开始](#快速开始) · [架构](#架构) · [贡献](#贡献)

</div>

---

<div align="center">

![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue?logo=windows)
![ASR](https://img.shields.io/badge/ASR-火山引擎-orange)
![TTS](https://img.shields.io/badge/TTS-豆包通用女声-ff69b4)
![Secretary](https://img.shields.io/badge/Secretary-豆包%20doubao--pro-9cf)
![Status](https://img.shields.io/badge/status-active--development-yellow)

**一个角色扮演式的语音 AI 助理系统：你扮演省委副书记，通过真实的红色座机给"豆包秘书处"打电话，调度 Claude / Gemini / Codex / DeepSeek 四路 AI 部委完成工作。**

</div>

---

## 🎬 演示场景

> *"沙沙的电话铃声响起。你拿起那台红色老式座机的话筒，听到秘书熟悉的声音——'领导，您好，我是您的秘书。' 你说：'帮我看看近期宣传工作的舆论风险。' 秘书：'好的领导，我这就去安排宣传部处理。' 片刻之后，电话再次响起：'领导，宣传工作研判完成，结论是这样……'"*

你不再是打字敲键盘，而是**用声音指挥一个由 4 个 AI 部委组成的虚拟机关**。

---

## 🏛️ 角色分工

| 角色 | 实现 | 职责 |
|---|---|---|
| **高育良同志** 👤 | 真人 | 拿起话筒、说话、下指示 |
| **贴身秘书** 🎙️ | 豆包 doubao-pro（女声）| 接电话、理解意图、调度各部委、汇报结果 |
| **组织部** 🧠 | Claude（Opus 4）| 干部考察、人才选拔、班子调配、组织架构 |
| **宣传部** 🧠 | Gemini 2.5 Pro | 舆论引导、新闻稿、形象塑造、宣传策略 |
| **社工部** 🧠 | OpenAI GPT-5 Codex | 群众工作、民生调研、信访处理、社工项目 |
| **政法委** 🧠 | DeepSeek R1 | 法治研判、维稳分析、案件梳理、政策合规 |

> 💡 **为什么选这个组合？** 豆包对中文老干部腔和长 prompt 指令遵循度最高，适合做秘书调度；4 部委各自选最擅长的模型——Claude 的逻辑推理、Gemini 的长文生成、Codex 的数据分析、DeepSeek 的法律合规推理。

---

## ✨ 核心特性

- 📞 **真实硬件交互**：用淘宝买的红色老式固定座机 + CM108 USB 声卡（总成本 ~¥200）
- 🗣️ **豆包通用女声**：TTS 直接调火山引擎，沉浸式秘书腔
- 🔁 **双方案可选**：
  - **方案 B** —— 全云端流式（低延迟首字 ~300ms）
  - **方案 C** —— 本地 silero-vad + 一次性 ASR（隐私敏感场景）
- 🤖 **多 Agent 编排**：豆包作为贴身秘书，4 部委作为子 Agent，支持 function calling
- ⚡ **异步回拨机制**：长任务后台执行，秘书主动回拨电话汇报（不让你举着话筒等）
- 🎚️ **角色化 Prompt**：所有 Prompt 用 YAML 管理，方便 fork 后改人设
- 🪟 **Windows 一键运行**：完整依赖、接线图、故障排查文档齐全

---

## 📑 目录

- [演示场景](#演示场景)
- [角色分工](#角色分工)
- [核心特性](#核心特性)
- [快速开始](#快速开始)
- [架构](#架构)
- [方案对比](#方案对比)
- [配置说明](#配置说明)
- [硬件组装](#硬件组装)
- [开发与扩展](#开发与扩展)
- [测试](#测试)
- [常见问题](#常见问题)
- [路线图](#路线图)
- [贡献](#贡献)
- [License](#license)
- [致谢](#致谢)
- [English](#english)

---

## 🚀 快速开始

### 1. 硬件准备（约 ¥200）

| 物料 | 价格 | 购买 |
|---|---|---|
| 复古红色固定座机（80年代款）| ¥150-300 | 淘宝搜"复古红色座机 80年代" |
| CM108 USB 声卡模块 | ¥25-40 | 淘宝搜"CM108 USB 声卡" |
| 3.5mm 插头 + 屏蔽线 | ¥10 | 五金店 |

按 [hardware/wiring.md](hardware/wiring.md) 把话筒/听筒焊到 USB 声卡。

> 💡 **不想买硬件？** 跳过接线，直接用普通 USB 耳机或笔记本自带麦即可，API 完全兼容。

### 2. 软件安装

```powershell
# Windows PowerShell
git clone https://github.com/ace-trump-tech/gaoyuliang.git
cd gaoyuliang

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

> 🐧 **Linux/macOS 用户** 也可以跑，把 `sounddevice` 换成你系统的音频驱动即可，主流程一致。

### 3. 配置 API Key

```bash
cp .env.example .env
```

编辑 `.env`，填入以下 key：

| Key | 来源 |
|---|---|
| `VOLC_APPID` / `VOLC_TOKEN` | [火山引擎控制台](https://console.volcengine.com/) |
| `DOUBAO_API_KEY` | 火山引擎 → 豆包大模型 → 在线推理 |
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) |
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `DEEPSEEK_API_KEY` | [DeepSeek Platform](https://platform.deepseek.com/api_keys) |

### 4. 验证音频设备

```bash
python -m tests.test_audio
```

应该列出 "USB Audio Device" 或类似设备。

### 5. 启动

**方案 B**（全云端流式，低延迟）：
```bash
python -m src.main_b
```

**方案 C**（本地 VAD + 一次性 ASR，更隐私）：
```bash
python -m src.main_c
```

启动后控制台输出：
```
[INFO] AudioInput started: rate=16000 ch=1 block=320
[INFO] AudioOutput started
[INFO] 待机：等拿起话筒...
```

拿起话筒，说"**高书记，帮我看看近期宣传工作的舆论风险**"，等待秘书回应。

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────┐
│                     🎤 红色座机硬件                       │
│              (话筒 MIC + 听筒 EAR)                        │
└────────────────────┬────────────────────────────────────┘
                     │ 4 芯线
                     ▼
┌─────────────────────────────────────────────────────────┐
│              🔌 CM108 USB 声卡 (¥30)                     │
└────────────────────┬────────────────────────────────────┘
                     │ USB
                     ▼
┌─────────────────────────────────────────────────────────┐
│  🪟 Windows + Python 3.11                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ src/audio.py  ── sounddevice 输入/输出流          │  │
│  │ src/vad.py    ── silero-vad（仅方案 C）          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
   方案 B：火山 ASR            方案 C：火山 ASR
   WebSocket 流式              HTTP 一次性
        │                         │
        └────────────┬────────────┘
                     ▼ 文本
┌─────────────────────────────────────────────────────────┐
│  🎙️ 豆包秘书 (doubao-pro)                                 │
│     ┌────────────────────────────────────────────────┐  │
│     │  system prompt: "你是高育良同志的贴身秘书..."  │  │
│     │  tools: 4 个 function_call（部委派单）          │  │
│     └────────────────────────────────────────────────┘  │
└──────┬─────────┬─────────┬─────────┬───────────────────┘
       │         │         │         │
       ▼         ▼         ▼         ▼
   组织部    宣传部    社工部    政法委
   Claude    Gemini    Codex    DeepSeek
       │         │         │         │
       └─────────┴─────────┴─────────┘
                     ▼
              综合汇报文本
                     ▼
┌─────────────────────────────────────────────────────────┐
│  🔊 火山 TTS (豆包通用女声 BV001_streaming)                │
└────────────────────┬────────────────────────────────────┘
                     ▼
              🔊 听筒播放
```

---

## ⚖️ 方案对比

| 维度 | 方案 B（全云端流式）| 方案 C（本地 VAD + 一次性）|
|---|---|---|
| **挂断检测** | 火山 ASR 云端 endpoint（5s）| 本地 silero-vad（5s 静音）|
| **ASR 模式** | WebSocket 流式 | HTTP 一次性（整段）|
| **首字延迟** | ~300ms | ~800ms（要等用户说完）|
| **网络要求** | 高（持续 WebSocket）| 低（短连接）|
| **隐私** | 音频持续上行 | 句子级上行 |
| **功耗** | 高（持续推流）| 低 |
| **适用场景** | 演示、家庭 | 隐私敏感、低带宽 |

**建议**：先跑方案 B 验证链路，再按需切方案 C。

---

## ⚙️ 配置说明

所有配置集中在 `config/*.yaml`：

| 文件 | 内容 |
|---|---|
| `config/settings.yaml` | 采样率、VAD 阈值、ASR/TTS 模型、4 部委模型映射 |
| `config/prompts.yaml` | 豆包秘书 + 4 部委 system prompt |
| `config/departments.yaml` | 部委业务定位、工具能力、并发数 |

### 调整灵敏度

```yaml
# config/settings.yaml
audio:
  mic_rms_threshold: 100   # 越小越敏感（拿起话筒的能量阈值）
vad:
  speech_threshold: 0.5    # VAD 检测阈值（0.3-0.7）
  hangup_silence_sec: 5    # 静音多久挂断
```

### 修改秘书人设

```yaml
# config/prompts.yaml
secretary: |
  你是高育良同志的贴身秘书...
```

改成你自己想要的角色（比如改成"皇帝身边的太监"、"校长助理"、"客户经理"），Prompt 完全可定制。

### 替换部委模型

```yaml
# config/settings.yaml
departments:
  organization: claude-sonnet-4-20250514   # 换便宜模型
  propaganda: gemini-2.5-flash             # 换快速模型
  social: gpt-5                            # Codex 换标准 GPT
  politics_law: deepseek-chat              # 换非推理模型
```

---

## 🔧 硬件组装

详见 [hardware/wiring.md](hardware/wiring.md) 和 [hardware/windows_setup.md](hardware/windows_setup.md)，包含：

- 红色座机内部结构图
- 4 芯话筒线颜色定义
- CM108 USB 声卡接线针脚图
- 电烙铁焊接步骤
- 常见问题排查（mic bias、串扰、底噪等）

---

## 🛠️ 开发与扩展

### 项目结构

```
gaoyuliang/
├── src/
│   ├── audio.py              # sounddevice 封装（async.Queue）
│   ├── vad.py                # silero-vad 封装
│   ├── asr_volc_stream.py    # 火山 ASR WebSocket
│   ├── asr_volc_oneshot.py   # 火山 ASR HTTP
│   ├── tts_volc.py           # 火山 TTS
│   ├── doubao_agent.py       # 豆包秘书（function calling 编排）
│   ├── conversation.py       # 对话历史
│   ├── notifier.py           # 异步回拨
│   ├── main_b.py             # 方案 B 入口
│   ├── main_c.py             # 方案 C 入口
│   └── departments/          # 4 部委
│       ├── organization.py   # Claude
│       ├── propaganda.py     # Gemini
│       ├── social.py         # OpenAI
│       └── politics_law.py   # DeepSeek
├── config/                   # YAML 配置
├── hardware/                 # 接线文档
├── tests/                    # pytest 用例
└── logs/                     # 运行日志
```

### 添加新部委

1. 在 `src/departments/` 下新建 `xxx.py`，继承类似 `OrganizationDept` 的模式
2. 在 `doubao_agent.py` 的 `DEPARTMENT_TOOLS` 注册新的 tool
3. 在 `config/prompts.yaml` 加 prompt
4. 在 `config/departments.yaml` 注册业务定位

### 替换底层模型

4 部委都是薄封装，直接改 `__init__` 里的 `model` 参数即可换模型。

---

## 🧪 测试

```bash
# 音频设备
python -m tests.test_audio

# 火山 ASR + TTS（消耗额度）
python -m tests.test_asr

# 豆包秘书 + 派单
python -m tests.test_doubao
```

未来计划用 `pytest` 框架组织（见路线图）。

---

## ❓ 常见问题

<details>
<summary><b>Q: 不想买硬件，能跑吗？</b></summary>

A: 可以。直接用普通 USB 耳机或笔记本自带麦即可，API 完全兼容。也可以用 VB-Cable 等虚拟音频设备做开发调试。
</details>

<details>
<summary><b>Q: 火山 ASR 流式接口报 401？</b></summary>

A: 检查 `.env` 里 `VOLC_TOKEN` 是否正确。火山控制台 → 访问控制 → API Access Key → 复制 token。Token 不是 AppKey，注意区分。
</details>

<details>
<summary><b>Q: 豆包 function calling 不触发？</b></summary>

A: 检查 prompt 里是否清晰描述了 4 部委的职责分工。如果发现豆包总是闲聊，把 `config/prompts.yaml` 里 `secretary` 段中的【调度规则】改得更明确。
</details>

<details>
<summary><b>Q: 话筒声音很小？</b></summary>

A: 见 [hardware/wiring.md](hardware/wiring.md) 的"常见坑"章节——CM108 mic bias 默认 2.5V，可在 mic 线和地之间串 1kΩ 电阻衰减。
</details>

<details>
<summary><b>Q: 听筒里有自己的回声？</b></summary>

A: 这是真实电话的特性（mic/ear 在同一手柄上）。如果太严重，物理上把话筒和喇叭拉远，或在软件里加 echo cancellation（未来 feature）。
</details>

<details>
<summary><b>Q: 4 个部委 API 调用太贵？</b></summary>

A: 全部换成便宜模型：
```yaml
departments:
  organization: claude-haiku-4
  propaganda: gemini-2.5-flash
  social: gpt-5-mini
  politics_law: deepseek-chat
```
实测每次通话成本可压到 ¥0.1 以内。
</details>

---

## 🗺️ 路线图

- [ ] 真实硬件接线视频教程（B 站）
- [ ] 加入回声消除（AEC）模块
- [ ] 用 pytest 改造测试，支持 CI
- [ ] 加入"座机拨号盘"识别（用 WebRTC VAD）
- [ ] 把秘书人设做成可切换 preset（书记 / 校长 / 客户经理）
- [ ] 支持更多 TTS 声音（男声 / 方言 / 英文）
- [ ] 加入来电显示（OLED 小屏 + Arduino）

---

## 🤝 贡献

欢迎 PR！特别是：

- 新的部委（纪委 / 统战部 / 教育部……）
- 新的人设 preset
- 多语言支持（英文秘书腔）
- 真实硬件测试反馈

提交前请：

1. `python -m tests.test_audio` 通过
2. 新增部委的话更新 `config/departments.yaml` 和 README 角色表
3. 在 `## 致谢` 加上你的 GitHub 链接

---

## 📜 License

[MIT](LICENSE) © 2025 gaoyuliang contributors

---

## 🙏 致谢

- [火山引擎](https://www.volcengine.com/) —— ASR / TTS / 豆包推理服务
- [Anthropic](https://www.anthropic.com/) —— Claude
- [Google](https://ai.google.dev/) —— Gemini
- [OpenAI](https://openai.com/) —— GPT / Codex
- [DeepSeek](https://www.deepseek.com/) —— DeepSeek-R1
- [silero-vad](https://github.com/snakers4/silero-vad) —— 开源 VAD 模型
- [sounddevice](https://python-sounddevice.readthedocs.io/) —— Python 音频 I/O

贡献者：[ace-trump-tech](https://github.com/ace-trump-tech)

---

## English

**"Comrade Gao Yuliang's Red Landline"** is a voice AI assistant system with a retro roleplay twist: you play a provincial party secretary who calls a real red landline phone to dispatch tasks to a "secretarial office" powered by Doubao (豆包) doubao-pro, which in turn orchestrates four AI departments (Claude / Gemini / Codex / DeepSeek).

- **Hardware**: A ¥200 setup — vintage red landline + CM108 USB sound card + Windows PC
- **ASR/TTS**: Volcengine (火山引擎), with Doubao's universal female voice
- **Two modes**:
  - Plan B — Full cloud streaming (lower latency)
  - Plan C — Local silero-vad + one-shot ASR (more private)
- **Async callback**: Long tasks run in background; the secretary calls you back when done

See [Quick Start](#快速开始) above for setup. Hardware wiring in [hardware/wiring.md](hardware/wiring.md).

---

<div align="center">

如果这个项目对你有帮助，欢迎 ⭐ Star！

Made with 🎙️ in China

</div>
