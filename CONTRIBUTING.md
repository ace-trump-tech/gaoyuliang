# 🤝 贡献指南

感谢你有兴趣贡献到 **gaoyuliang**！下面是你需要知道的。

---

## 📋 行为准则

- 尊重他人，文明沟通
- PR 讨论聚焦技术与设计本身
- 不接受包含恶意代码、外挂、作弊工具的 PR

---

## 🛠️ 开发流程

### 1. Fork & Clone

```bash
git clone https://github.com/ace-trump-tech/gaoyuliang.git
cd gaoyuliang
```

### 2. 创建分支

```bash
git checkout -b feat/your-feature
# 或 fix/your-bug
```

### 3. 设置环境

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env       # 填入你的 API key
```

### 4. 写代码

**风格**：

- Python ≥ 3.11
- 用 `from __future__ import annotations`
- 类型注解：函数签名全标注，类属性用 `dataclass`
- 中文注释 OK，但 docstring 优先英文
- 单个文件不超过 400 行；超过请拆分

**导入顺序**：

```python
from __future__ import annotations

# 标准库
import asyncio
import logging

# 第三方
import yaml

# 本地
from src.audio import AudioConfig
```

### 5. 测试

```bash
# 至少跑通音频测试
python -m tests.test_audio

# 跑全部测试
python -m pytest tests/ -v
```

新增部委或功能时，**必须**附带：

- 测试用例（`tests/test_xxx.py`）
- `config/prompts.yaml` 的 system prompt
- `config/departments.yaml` 的部委定义
- README 角色表更新

### 6. Commit & Push

```bash
git commit -m "feat: 新增纪委部委"
git push origin feat/your-feature
```

**Commit 规范**（建议）：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 仅文档
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 杂项

### 7. Pull Request

PR 描述需包含：

1. **What** —— 这个 PR 做了什么
2. **Why** —— 为什么要做
3. **How** —— 怎么实现的（关键设计点）
4. **Test** —— 如何验证

---

## 🎯 推荐的贡献方向

### 新部委

最容易上手的方向：

1. 在 `src/departments/` 下新建 `discipline.py`（纪委）
2. 参考 `organization.py` 的薄封装模式
3. 在 `doubao_agent.py` 的 `DEPARTMENT_TOOLS` 注册
4. 在 `config/prompts.yaml` 加 system prompt
5. 在 `config/departments.yaml` 注册业务
6. 在 README 角色表加一行

### 新人设 Preset

把秘书人设抽成可切换 preset：

```python
# config/presets/
PRESETS = {
    "高育良": "你是高育良同志的贴身秘书...",
    "校长助理": "你是一所大学的校长助理...",
    "客户经理": "你是某公司的大客户经理...",
}
```

### 新 TTS 声音

在 `config/settings.yaml` 加预设：

```yaml
tts:
  voices:
    female_universal: BV001_streaming   # 豆包通用女声
    male_calm: BV002_streaming         # 男声
    female_news: BV003_streaming       # 新闻女声
```

### 真实硬件接线图

如果你做了不同款红色座机的接线记录，欢迎 PR 到 `hardware/case_studies/`。

---

## 🐛 Bug 报告

提 Issue 时请包含：

- OS 版本（Windows 10 / 11 / Linux）
- Python 版本
- 完整错误堆栈（不是只贴最后一行）
- 复现步骤
- 期望行为 vs 实际行为

---

## 💡 Feature Request

提 Issue 时请说明：

- 这个功能解决什么问题
- 期望的 API 或使用方式
- 是否愿意自己实现（PR）

---

## 📦 发布流程

（仅维护者）

1. 更新 `CHANGELOG.md`
2. 更新版本号（`src/__init__.py` 的 `__version__`）
3. 打 tag：`git tag v1.x.x`
4. `git push --tags`
5. GitHub Release 写 release notes

---

## ❓ 问题？

- 提 Issue
- 邮件：通过 GitHub Issues 公开讨论
- 微信公众号：（暂无）

---

再次感谢你的贡献！🎉
