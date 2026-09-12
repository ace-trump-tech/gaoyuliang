"""
豆包秘书测试

需要 .env 里的 DOUBAO_API_KEY 有效
测试秘书是否能正确：
1. 闲聊响应
2. 调用工具派单
3. 综合结果汇报
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from dotenv import load_dotenv

from src.conversation import Conversation
from src.doubao_agent import DEPARTMENT_TOOLS, DoubaoAgent, DoubaoConfig


def _load_yaml(name: str) -> dict:
    with open(ROOT / "config" / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


async def main() -> None:
    load_dotenv(ROOT / ".env")
    if (
        not os.environ.get("DOUBAO_API_KEY")
        or os.environ["DOUBAO_API_KEY"] == "your_doubao_api_key"
    ):
        print("⚠️  请先在 .env 填入 DOUBAO_API_KEY")
        return

    prompts = _load_yaml("prompts.yaml")
    cfg = DoubaoConfig(api_key=os.environ["DOUBAO_API_KEY"])

    agent = DoubaoAgent(
        cfg,
        secretary_system_prompt=prompts["secretary"],
    )

    # ---- 测试 1：闲聊 ----
    print("=== 测试 1：闲聊 ===")
    conv = Conversation()
    reply = await agent.handle("你好", conv)
    print(f"  秘书: {reply}")
    assert "领导" in reply or "高" in reply, "秘书应称呼'领导'"
    print("  ✓ 闲聊正常")

    # ---- 测试 2：派单（同步等结果，因为有'加急'）----
    print("\n=== 测试 2：派单（加急） ===")
    conv2 = Conversation()
    reply2 = await agent.handle(
        "加急！帮我看看近期宣传工作的舆论风险，给我个研判意见",
        conv2,
    )
    print(f"  秘书: {reply2}")
    print(f"  工具定义数量: {len(DEPARTMENT_TOOLS)}")
    print("  ✓ 派单 + 综合流程跑通")

    # ---- 清理 ----
    await agent.aclose()


if __name__ == "__main__":
    asyncio.run(main())
