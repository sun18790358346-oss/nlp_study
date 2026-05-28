"""总结代理

在游戏结束后，为每个玩家生成表现总结，并保存为经验供后续游戏参考。
"""

from typing import Dict, Any, List, Optional

from agents import Agent, Runner
from agents import set_default_openai_api, set_tracing_disabled
from schema.system_config import load_system_config

set_default_openai_api("chat_completions")
set_tracing_disabled(True)

config = load_system_config("config/system_config.json")


SUMMARY_PROMPT_TEMPLATE = """你刚刚完成了一局狼人杀游戏。请以第一人称视角，回顾你这局游戏的表现，进行深度总结。

## 你的身份
- 角色：{role_name}
- 阵营：{camp_name}
- 玩家名称：{player_name}

## 游戏结果
- 胜利方：{winner_name}
- 你的阵营：{is_winner_text}

## 你的游戏经历
以下是你在整局游戏中经历的所有事件：
{personal_history}

## 要求
请反思你的表现，并以 **JSON 格式** 输出以下内容：

```json
{{
    "summary": "整体表现总结（2-3句话，回顾自己本局的表现和关键决策）",
    "strategies": "你使用了哪些策略？哪些有效、哪些无效？",
    "mistakes": "犯了哪些错误？有哪些地方可以做得更好？",
    "lessons": "对未来的自己有什么具体建议？（1-2条，面向同角色的后续游戏）"
}}
```

只输出 JSON，不要包含其他内容。
"""


class SummaryAgent:
    """总结代理

    用于在游戏结束后，根据每个玩家的视角生成结构化总结。
    """

    def __init__(self):
        self.agent = Agent(
            name="SummaryAgent",
            model=config.default_model,
            instructions="你是一个狼人杀游戏的复盘分析师。你会根据玩家的游戏经历生成深度反思总结。",
        )

    async def generate_summary(
        self,
        player_name: str,
        role_name: str,
        camp: str,
        winner: Optional[str],
        personal_history: str,
    ) -> Dict[str, str]:
        """为一个玩家生成总结

        Args:
            player_name: 玩家名称
            role_name: 角色名（如 "狼人", "预言家"）
            camp: 阵营（"good" 或 "evil"）
            winner: 胜利方（"good" 或 "evil"）
            personal_history: 该玩家视角的经历文本

        Returns:
            包含 summary, strategies, mistakes, lessons 的字典
        """
        camp_name = "善良阵营" if camp == "good" else "邪恶阵营"
        winner_name = "善良阵营（好人）" if winner == "good" else "邪恶阵营（狼人）" if winner == "evil" else (winner or "未知")
        is_winner_text = "胜利！" if camp == winner else "失败。"

        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            role_name=role_name,
            camp_name=camp_name,
            player_name=player_name,
            winner_name=winner_name,
            is_winner_text=is_winner_text,
            personal_history=personal_history,
        )

        try:
            result = await Runner.run(self.agent, prompt)
            return self._parse_json_output(result.final_output)
        except Exception as e:
            return {
                "summary": f"总结生成失败: {e}",
                "strategies": "",
                "mistakes": "",
                "lessons": "",
            }

    def _parse_json_output(self, output: str) -> Dict[str, str]:
        """解析 LLM 输出的 JSON"""
        import json
        import re

        json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            "summary": output[:200],
            "strategies": "",
            "mistakes": "",
            "lessons": "",
        }


__all__ = ["SummaryAgent"]
