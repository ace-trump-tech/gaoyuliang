# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- 回声消除（AEC）模块
- pytest CI 集成
- 秘书人设 preset 系统
- 座机拨号盘识别

## [1.0.0] - 2025-XX-XX

### Added
- 红色座机 + CM108 USB 声卡接线文档
- 豆包 doubao-pro 秘书系统（带 4 部委 function call）
- 方案 B（全云端流式）+ 方案 C（本地 VAD + 一次性）双方案
- 火山 ASR WebSocket 流式 / HTTP 一次性双接口
- 火山 TTS（豆包通用女声 BV001_streaming）
- 4 部委：
  - 组织部 → Claude（Anthropic）
  - 宣传部 → Gemini（Google）
  - 社工部 → Codex（OpenAI）
  - 政法委 → DeepSeek
- 异步回拨通知机制（长任务完成后秘书主动回拨）
- 对话历史管理（`Conversation` 类）
- silero-vad 本地端点检测
- 完整测试套件（音频、ASR、豆包）
- Windows 环境配置文档
- 角色化 Prompt 模板

### Documentation
- README（中英双语，徽章，架构图，FAQ）
- CONTRIBUTING.md
- hardware/wiring.md（接线图）
- hardware/windows_setup.md（Windows 配置）

[Unreleased]: https://github.com/your-username/gaoyuliang/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-username/gaoyuliang/releases/tag/v1.0.0
