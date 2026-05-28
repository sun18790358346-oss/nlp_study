"""玩家AI代理

每个玩家角色对应一个AI代理，用于在游戏中做决策
"""

from typing import Dict, Any, List

from agents import Agent, Runner
from agents import set_default_openai_api, set_tracing_disabled
from schema.system_config import load_system_config
from memory.experience import get_experience_prompt

set_default_openai_api("chat_completions")
set_tracing_disabled(True)

config = load_system_config("config/system_config.json")


# 决策风格定义
DECISION_STYLES = {
    "cautious": {
        "name": "谨慎型",
        "description": "宁可放过可疑玩家，也不轻易误杀好人",
        "speech_tendency": "保守分析，少说少错",
        "vote_tendency": "跟票，不首先提名",
        "night_tendency": "不轻易用药/查验",
    },
    "bold": {
        "name": "大胆型",
        "description": "敢于冒险，快速做出判断",
        "speech_tendency": "激进指控，主动带队",
        "vote_tendency": "果断投票，不怕误杀",
        "night_tendency": "冒险用药/深夜击杀",
    },
    "random": {
        "name": "随机型",
        "description": "不要过度分析，依靠直觉",
        "speech_tendency": "随机发言，看心情",
        "vote_tendency": "随机投票",
        "night_tendency": "随机目标",
    },
    "balanced": {
        "name": "平衡型",
        "description": "综合考虑各种因素",
        "speech_tendency": "客观分析",
        "vote_tendency": "理性分析后投票",
        "night_tendency": "合理使用能力",
    },
}


class PlayerAgent:
    """玩家AI代理

    根据角色类型生成对应的LLM代理，进行游戏决策
    """

    def __init__(self, player_id: int, role_name: str, private_context: Dict[str, Any],
                 camp: str, decision_style: str = "balanced", role_type: str = ""):
        self.player_id = player_id
        self.role_name = role_name
        self.private_context = private_context
        self.camp = camp
        self.decision_style = decision_style
        self.role_type = role_type or ""  # 英文角色类型，如 "werewolf", 用于加载经验

        instructions = self._build_instructions()

        self.agent = Agent(
            name=f"Player_{player_id}",
            model=config.default_model,
            instructions=instructions,
        )

    def _build_instructions(self) -> str:
        """构建角色提示词"""
        camp_desc = "善良阵营" if self.camp == "good" else "邪恶阵营"
        style_info = DECISION_STYLES.get(self.decision_style, DECISION_STYLES["balanced"])

        instructions = f"""你是一个狼人杀游戏中的玩家。
你的角色是：{self.role_name}
你的阵营是：{camp_desc}
你的玩家ID是：{self.player_id}

## 游戏规则
1. 夜晚：狼人需要协调击杀目标，预言家查验玩家，女巫决定是否用药
2. 白天：公开辩论后投票选出嫌疑人处决
3. 胜利条件：
   - 善良阵营：消灭所有狼人
   - 邪恶阵营：消灭所有神职或所有村民

## 我的私有信息
{self.private_context}

## 决策风格
你的决策风格是：{style_info['name']}
特点：{style_info['description']}
- 发言倾向：{style_info['speech_tendency']}
- 投票倾向：{style_info['vote_tendency']}
- 夜间行动倾向：{style_info['night_tendency']}

请根据你的决策风格做出符合该风格的游戏决策。
{self._get_experience_section()}

## 输出要求
你必须输出JSON格式的决策，格式如下：
- 夜晚行动：{{"action": "night_action", "target": 玩家ID或null, "reasoning": "决策理由"}}
- 白天发言：{{"action": "speech", "content": "发言内容"}}
- 投票：{{"action": "vote", "target": 玩家ID或null}}

请根据当前游戏状态做出最优决策。
"""
        return instructions

    def _get_experience_section(self) -> str:
        """获取过往经验文本，用于注入到提示词中"""
        if not self.role_type:
            return ""
        return get_experience_prompt(self.role_type)

    async def decide_night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """夜晚行动决策

        Args:
            game_state: 当前游戏状态

        Returns:
            决策结果，包含 action, target, reasoning
        """
        prompt = self._build_night_prompt(game_state)
        result = await Runner.run(self.agent, prompt)
        return self._parse_json_output(result.final_output)

    async def decide_speech(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """白天发言决策

        Args:
            game_state: 当前游戏状态

        Returns:
            决策结果，包含 action, content
        """
        prompt = self._build_speech_prompt(game_state)
        result = await Runner.run(self.agent, prompt)
        return self._parse_json_output(result.final_output)

    async def decide_vote(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """投票决策

        Args:
            game_state: 当前游戏状态

        Returns:
            决策结果，包含 action, target
        """
        prompt = self._build_vote_prompt(game_state)
        result = await Runner.run(self.agent, prompt)
        return self._parse_json_output(result.final_output)

    def _build_night_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建夜间决策提示"""
        style_info = DECISION_STYLES.get(self.decision_style, DECISION_STYLES["balanced"])
        return f"""## 当前游戏状态
{game_state}

## 你的角色是 {self.role_name}
请决定今晚的行动。

夜晚行动选项：
- 狼人：选择要击杀的目标玩家ID
- 预言家：选择要查验的目标玩家ID
- 女巫：选择是否用药（heal/poison）和目标
- 猎人：如果死亡，选择要开枪带走的目标玩家ID
- 村民：无夜间行动

{style_info['night_tendency']}

请以JSON格式输出你的决策：
"""

    def _build_speech_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建白天发言提示"""
        style_info = DECISION_STYLES.get(self.decision_style, DECISION_STYLES["balanced"])
        return f"""## 当前游戏状态
{game_state}

## 你的角色是 {self.role_name}
现在是公开辩论时间，请发表你的发言。

{style_info['speech_tendency']}

发言要点：
1. 根据已有信息分析谁可能是狼人
2. 说明你的推理过程
3. 质疑你认为可疑的玩家
4. 保护队友（如你是神职）

请以JSON格式输出你的发言：
{{"action": "speech", "content": "发言内容"}}
"""

    def _build_vote_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建投票提示"""
        style_info = DECISION_STYLES.get(self.decision_style, DECISION_STYLES["balanced"])
        return f"""## 当前游戏状态
{game_state}

## 你的角色是 {self.role_name}
现在进入投票环节，请选择你要投票的目标。

{style_info['vote_tendency']}

规则：
- 你可以选择投某位玩家
- 也可以选择跳过（不投票）
- 票数最多的玩家将被处决

请以JSON格式输出你的投票：
{{"action": "vote", "target": 玩家ID或null}}
"""

    def _parse_json_output(self, output: str) -> Dict[str, Any]:
        """解析LLM输出的JSON

        Args:
            output: LLM输出的原始文本

        Returns:
            解析后的决策字典
        """
        import json
        import re

        # 尝试从输出中提取JSON
        json_match = re.search(r'\{[^{}]*\}', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 如果解析失败，返回默认值
        return {"action": "unknown", "raw_output": output}


class JudgeAgent:
    """主持人AI代理（裁判）

    负责判定游戏规则、计算结果、推进游戏流程
    """

    def __init__(self):
        instructions = """你是狼人杀游戏的主持人（裁判）。
你的职责是：
1. 按照游戏规则推进游戏流程
2. 收集并执行玩家的决策
3. 宣布每天的死亡结果
4. 判断游戏是否结束及胜利方

游戏流程：
1. 夜晚：依次执行狼人杀人、预言家查验、女巫用药
2. 白天：宣布死亡、公开辩论、投票处决

你必须输出JSON格式的游戏指令。
"""
        self.agent = Agent(
            name="Judge",
            model=config.default_model,
            instructions=instructions,
        )

    async def announce_death(self, deaths: List[int], cause: str, game_state: Dict[str, Any]) -> str:
        """宣布死亡结果

        Args:
            deaths: 死亡玩家ID列表
            cause: 死亡原因（night_kill, vote, shoot, poison）

        Returns:
            死亡公告文本
        """
        if not deaths:
            return "今晚无人死亡。"

        death_names = [f"玩家{p}" for p in deaths]
        cause_desc = {
            "night_kill": "昨夜",
            "vote": "投票",
            "shoot": "枪杀",
            "poison": "毒杀",
        }.get(cause, cause)

        announcement = f"{cause_desc}，以下玩家死亡：{', '.join(death_names)}"

        # 添加死亡玩家遗言
        for player_id in deaths:
            player = game_state.get("players", {}).get(player_id)
            if player:
                announcement += f"\n{player.get('name', f'玩家{player_id}')} 说："

        return announcement

    async def announce_phase(self, phase: str, day_number: int) -> str:
        """宣布游戏阶段

        Args:
            phase: 当前阶段
            day_number: 第几天

        Returns:
            阶段公告文本
        """
        if "night" in phase:
            return f"第{day_number}夜开始，请各位保持安静。"
        else:
            return f"第{day_number}天，阳光照耀，请各位玩家开始发言。"


def create_player_agent(player_id: int, role_name: str, private_context: Dict[str, Any],
                       camp: str, decision_style: str = "balanced",
                       role_type: str = "") -> PlayerAgent:
    """工厂函数：创建玩家代理"""
    return PlayerAgent(player_id, role_name, private_context, camp, decision_style, role_type)


def create_judge_agent() -> JudgeAgent:
    """工厂函数：创建主持人代理

    Returns:
        JudgeAgent实例
    """
    return JudgeAgent()