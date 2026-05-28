"""测试玩家AI代理"""

import pytest
from unittest.mock import patch
from agent.player_agent import (
    PlayerAgent,
    JudgeAgent,
    create_player_agent,
    create_judge_agent,
    DECISION_STYLES,
)
from unittest.mock import patch, MagicMock


class TestDecisionStyles:
    """测试决策风格定义"""

    def test_all_styles_defined(self):
        """测试所有决策风格都已定义"""
        assert "cautious" in DECISION_STYLES
        assert "bold" in DECISION_STYLES
        assert "random" in DECISION_STYLES
        assert "balanced" in DECISION_STYLES

    def test_style_has_required_fields(self):
        """测试每个风格都有必需字段"""
        required_fields = ["name", "description", "speech_tendency",
                          "vote_tendency", "night_tendency"]
        for style_name, style_info in DECISION_STYLES.items():
            for field in required_fields:
                assert field in style_info, f"Style {style_name} missing {field}"

    def test_style_name_non_empty(self):
        """测试每个风格都有非空名称"""
        for style_name, style_info in DECISION_STYLES.items():
            assert style_info["name"]
            assert len(style_info["name"]) > 0


class TestPlayerAgent:
    """测试 PlayerAgent 类"""

    @pytest.fixture
    def mock_agent_config(self):
        """模拟 agent 配置"""
        with patch('agent.player_agent.config') as mock_config:
            mock_config.default_model = "gpt-4"
            yield mock_config

    @pytest.fixture
    def sample_private_context(self):
        """样例私有上下文"""
        return {"role": "Werewolf", "player_id": 0, "camp": "evil"}

    def test_init_basic(self, mock_agent_config, sample_private_context):
        """测试基本初始化"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        assert agent.player_id == 0
        assert agent.role_name == "Werewolf"
        assert agent.camp == "evil"
        assert agent.decision_style == "balanced"

    def test_init_with_decision_style(self, mock_agent_config, sample_private_context):
        """测试带决策风格的初始化"""
        agent = PlayerAgent(
            player_id=1,
            role_name="Seer",
            private_context=sample_private_context,
            camp="good",
            decision_style="cautious"
        )
        assert agent.decision_style == "cautious"

    def test_build_instructions_contains_role(self, mock_agent_config, sample_private_context):
        """测试指令包含角色信息"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        instructions = agent._build_instructions()
        assert "Werewolf" in instructions
        assert "邪恶阵营" in instructions

    def test_build_instructions_contains_private_context(self, mock_agent_config, sample_private_context):
        """测试指令包含私有上下文"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        instructions = agent._build_instructions()
        assert "Werewolf" in instructions
        assert "player_id" in instructions

    def test_build_instructions_contains_style(self, mock_agent_config, sample_private_context):
        """测试指令包含决策风格"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil",
            decision_style="bold"
        )
        instructions = agent._build_instructions()
        assert "大胆型" in instructions
        assert "决策风格" in instructions

    def test_build_night_prompt(self, mock_agent_config, sample_private_context):
        """测试夜间决策提示"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        prompt = agent._build_night_prompt({"day": 1, "phase": "night"})
        assert "Werewolf" in prompt
        assert "夜晚" in prompt
        assert "击杀" in prompt

    def test_build_speech_prompt(self, mock_agent_config, sample_private_context):
        """测试白天发言提示"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Seer",
            private_context=sample_private_context,
            camp="good"
        )
        prompt = agent._build_speech_prompt({"day": 1, "phase": "speech"})
        assert "Seer" in prompt
        assert "发言" in prompt
        assert "JSON" in prompt

    def test_build_vote_prompt(self, mock_agent_config, sample_private_context):
        """测试投票提示"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Villager",
            private_context=sample_private_context,
            camp="good"
        )
        prompt = agent._build_vote_prompt({"day": 1, "phase": "vote"})
        assert "Villager" in prompt
        assert "投票" in prompt

    def test_parse_json_output_valid(self, mock_agent_config, sample_private_context):
        """测试解析有效 JSON"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        result = agent._parse_json_output('{"action": "vote", "target": 3}')
        assert result["action"] == "vote"
        assert result["target"] == 3

    def test_parse_json_output_with_extra_text(self, mock_agent_config, sample_private_context):
        """测试解析带额外文本的 JSON"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        result = agent._parse_json_output('好的，这是我的决策：{"action": "vote", "target": 3}谢谢')
        assert result["action"] == "vote"
        assert result["target"] == 3

    def test_parse_json_output_invalid(self, mock_agent_config, sample_private_context):
        """测试解析无效 JSON"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=sample_private_context,
            camp="evil"
        )
        result = agent._parse_json_output("这不是有效的 JSON 输出")
        assert result["action"] == "unknown"
        assert "raw_output" in result


class TestCreatePlayerAgent:
    """测试 create_player_agent 工厂函数"""

    @pytest.fixture
    def mock_agent_config(self):
        with patch('agent.player_agent.config') as mock_config:
            mock_config.default_model = "gpt-4"
            yield mock_config

    def test_create_player_agent_default_style(self, mock_agent_config):
        """测试创建默认风格的玩家代理"""
        agent = create_player_agent(
            player_id=0,
            role_name="Werewolf",
            private_context={"role": "Werewolf"},
            camp="evil"
        )
        assert isinstance(agent, PlayerAgent)
        assert agent.decision_style == "balanced"

    def test_create_player_agent_custom_style(self, mock_agent_config):
        """测试创建自定义风格的玩家代理"""
        agent = create_player_agent(
            player_id=0,
            role_name="Werewolf",
            private_context={"role": "Werewolf"},
            camp="evil",
            decision_style="bold"
        )
        assert agent.decision_style == "bold"


class TestJudgeAgent:
    """测试 JudgeAgent 类"""

    @pytest.fixture
    def mock_agent_config(self):
        with patch('agent.player_agent.config') as mock_config:
            mock_config.default_model = "gpt-4"
            yield mock_config

    def test_init(self, mock_agent_config):
        """测试初始化"""
        judge = JudgeAgent()
        assert judge.agent is not None
        assert judge.agent.name == "Judge"

    @pytest.mark.asyncio
    async def test_announce_death_with_deaths(self, mock_agent_config):
        """测试宣布死亡"""
        judge = JudgeAgent()
        result = await judge.announce_death([0, 1], "night_kill", {})
        assert "死亡" in result
        assert "玩家0" in result
        assert "玩家1" in result

    @pytest.mark.asyncio
    async def test_announce_death_empty(self, mock_agent_config):
        """测试宣布无人死亡"""
        judge = JudgeAgent()
        result = await judge.announce_death([], "night_kill", {})
        assert "无人死亡" in result

    @pytest.mark.asyncio
    async def test_announce_phase_night(self, mock_agent_config):
        """测试宣布夜晚阶段"""
        judge = JudgeAgent()
        result = await judge.announce_phase("night", 1)
        assert "夜" in result
        assert "1" in result

    @pytest.mark.asyncio
    async def test_announce_phase_day(self, mock_agent_config):
        """测试宣布白天阶段"""
        judge = JudgeAgent()
        result = await judge.announce_phase("day", 1)
        assert "天" in result
        assert "1" in result


class TestCreateJudgeAgent:
    """测试 create_judge_agent 工厂函数"""

    @pytest.fixture
    def mock_agent_config(self):
        with patch('agent.player_agent.config') as mock_config:
            mock_config.default_model = "gpt-4"
            yield mock_config

    def test_create_judge_agent(self, mock_agent_config):
        """测试创建裁判代理"""
        judge = create_judge_agent()
        assert isinstance(judge, JudgeAgent)


class TestDecisionStyleIntegration:
    """测试决策风格与提示词集成"""

    @pytest.fixture
    def mock_agent_config(self):
        with patch('agent.player_agent.config') as mock_config:
            mock_config.default_model = "gpt-4"
            yield mock_config

    @pytest.fixture
    def private_context(self):
        return {"role": "Werewolf", "player_id": 0, "camp": "evil"}

    def test_cautious_style_prompt(self, mock_agent_config, private_context):
        """测试谨慎风格的提示词"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=private_context,
            camp="evil",
            decision_style="cautious"
        )
        night_prompt = agent._build_night_prompt({})
        assert "不轻易" in night_prompt or "谨慎" in night_prompt

    def test_bold_style_prompt(self, mock_agent_config, private_context):
        """测试大胆风格的提示词"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=private_context,
            camp="evil",
            decision_style="bold"
        )
        night_prompt = agent._build_night_prompt({})
        assert "冒险" in night_prompt or "大胆" in night_prompt or "敢于" in night_prompt

    def test_random_style_prompt(self, mock_agent_config, private_context):
        """测试随机风格的提示词"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=private_context,
            camp="evil",
            decision_style="random"
        )
        vote_prompt = agent._build_vote_prompt({})
        assert "随机" in vote_prompt or "直觉" in vote_prompt or "心情" in vote_prompt

    def test_balanced_style_prompt(self, mock_agent_config, private_context):
        """测试平衡风格的提示词"""
        agent = PlayerAgent(
            player_id=0,
            role_name="Werewolf",
            private_context=private_context,
            camp="evil",
            decision_style="balanced"
        )
        speech_prompt = agent._build_speech_prompt({})
        assert "综合" in speech_prompt or "客观" in speech_prompt or "理性" in speech_prompt


class TestPlayerAgentRoleType:
    """测试 PlayerAgent 的 role_type 和经验功能"""

    @pytest.fixture
    def mock_agent_config(self):
        with patch('agent.player_agent.config') as mock_config:
            mock_config.default_model = "gpt-4"
            yield mock_config

    @pytest.fixture
    def private_context(self):
        return {"role": "Werewolf", "player_id": 0, "camp": "evil"}

    def test_init_with_role_type(self, mock_agent_config, private_context):
        """测试带 role_type 的初始化"""
        agent = PlayerAgent(
            player_id=0,
            role_name="狼人",
            private_context=private_context,
            camp="evil",
            role_type="werewolf",
        )
        assert agent.role_type == "werewolf"

    def test_init_without_role_type(self, mock_agent_config, private_context):
        """测试不传 role_type 时默认为空"""
        agent = PlayerAgent(
            player_id=0,
            role_name="狼人",
            private_context=private_context,
            camp="evil",
        )
        assert agent.role_type == ""

    def test_get_experience_section_no_role_type(self, mock_agent_config, private_context):
        """测试无 role_type 时返回空字符串"""
        agent = PlayerAgent(
            player_id=0,
            role_name="狼人",
            private_context=private_context,
            camp="evil",
        )
        assert agent._get_experience_section() == ""

    @patch('agent.player_agent.get_experience_prompt')
    def test_get_experience_section_with_role_type(self, mock_get_exp, mock_agent_config, private_context):
        """测试有 role_type 时调用 get_experience_prompt"""
        mock_get_exp.return_value = "\n## 你的过往游戏经验\n..."
        agent = PlayerAgent(
            player_id=0,
            role_name="狼人",
            private_context=private_context,
            camp="evil",
            role_type="werewolf",
        )
        result = agent._get_experience_section()
        assert "过往游戏经验" in result
        # __init__ 中 _build_instructions 已调用一次，这里又调用一次
        assert mock_get_exp.call_count >= 1
        mock_get_exp.assert_any_call("werewolf")

    @patch('agent.player_agent.get_experience_prompt')
    def test_build_instructions_includes_experience(self, mock_get_exp, mock_agent_config, private_context):
        """测试构建指令时包含经验"""
        mock_get_exp.return_value = "\n## 你的过往游戏经验\n上次悍跳成功"
        agent = PlayerAgent(
            player_id=0,
            role_name="狼人",
            private_context=private_context,
            camp="evil",
            role_type="werewolf",
        )
        instructions = agent._build_instructions()
        assert "过往游戏经验" in instructions
        assert "上次悍跳成功" in instructions

    @patch('agent.player_agent.get_experience_prompt')
    def test_create_player_agent_passes_role_type(self, mock_get_exp, mock_agent_config, private_context):
        """测试 create_player_agent 工厂函数传递 role_type"""
        mock_get_exp.return_value = ""
        agent = create_player_agent(
            player_id=0,
            role_name="狼人",
            private_context=private_context,
            camp="evil",
            decision_style="balanced",
            role_type="werewolf",
        )
        assert agent.role_type == "werewolf"
        # 验证在指令构建时使用了 role_type
        assert agent._get_experience_section() is not None