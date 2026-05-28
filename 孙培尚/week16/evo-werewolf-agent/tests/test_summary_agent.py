"""总结代理测试"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestSummaryAgent:
    """测试 SummaryAgent 基础功能"""

    def test_init(self):
        """测试初始化"""
        from agent.summary_agent import SummaryAgent
        sa = SummaryAgent()
        assert sa.agent is not None
        assert sa.agent.name == "SummaryAgent"

    @pytest.mark.asyncio
    async def test_generate_summary_calls_llm(self):
        """测试 generate_summary 调用 LLM"""
        from agent.summary_agent import SummaryAgent

        with patch("agent.summary_agent.Runner.run") as mock_run:
            mock_run.return_value.final_output = (
                '{"summary": "本局表现不错", "strategies": "悍跳",'
                '"mistakes": "发言不够自信", "lessons": "要更坚定"}'
            )

            sa = SummaryAgent()
            result = await sa.generate_summary(
                player_name="玩家1",
                role_name="狼人",
                camp="evil",
                winner="evil",
                personal_history="你首夜击杀了预言家\n你白天伪装发言",
            )

            assert result["summary"] == "本局表现不错"
            assert result["strategies"] == "悍跳"
            assert result["mistakes"] == "发言不够自信"
            assert result["lessons"] == "要更坚定"
            assert mock_run.called

    @pytest.mark.asyncio
    async def test_generate_summary_good_team_lost(self):
        """测试好人在失败时的总结"""
        from agent.summary_agent import SummaryAgent

        with patch("agent.summary_agent.Runner.run") as mock_run:
            mock_run.return_value.final_output = (
                '{"summary": "没能认出狼人", "strategies": "跟票",'
                '"mistakes": "投票错误", "lessons": "仔细分析发言"}'
            )

            sa = SummaryAgent()
            result = await sa.generate_summary(
                player_name="玩家2",
                role_name="预言家",
                camp="good",
                winner="evil",
                personal_history="你查验了玩家0,结果是狼人\n你白天跳明身份",
            )

            assert result["summary"] == "没能认出狼人"
            assert mock_run.called

    @pytest.mark.asyncio
    async def test_generate_summary_llm_failure(self):
        """测试 LLM 调用失败时的降级处理"""
        from agent.summary_agent import SummaryAgent

        with patch("agent.summary_agent.Runner.run") as mock_run:
            mock_run.side_effect = Exception("API Error")

            sa = SummaryAgent()
            result = await sa.generate_summary(
                player_name="玩家3",
                role_name="村民",
                camp="good",
                winner="good",
                personal_history="你没有特殊能力\n你白天正常发言投票",
            )

            assert "总结生成失败" in result["summary"]
            assert result["strategies"] == ""

    @pytest.mark.asyncio
    async def test_generate_summary_parse_json_error(self):
        """测试 LLM 返回非 JSON 时的降级处理"""
        from agent.summary_agent import SummaryAgent

        with patch("agent.summary_agent.Runner.run") as mock_run:
            mock_run.return_value.final_output = "纯文本回复，不是JSON格式"

            sa = SummaryAgent()
            result = await sa.generate_summary(
                player_name="玩家4",
                role_name="女巫",
                camp="good",
                winner="good",
                personal_history="你用解药救活了玩家0",
            )

            # 应返回原始文本截断作为 summary
            assert "纯文本回复" in result["summary"]

    @pytest.mark.asyncio
    async def test_generate_summary_prompt_includes_history(self):
        """测试提示词中包含个人经历"""
        from agent.summary_agent import SummaryAgent

        with patch("agent.summary_agent.Runner.run") as mock_run:
            mock_run.return_value.final_output = '{"summary": "ok"}'

            sa = SummaryAgent()
            await sa.generate_summary(
                player_name="玩家1",
                role_name="狼人",
                camp="evil",
                winner="evil",
                personal_history="你首夜击杀了预言家",
            )

            # 验证 prompt 包含关键信息
            called_prompt = mock_run.call_args[0][1]
            assert "玩家1" in called_prompt
            assert "狼人" in called_prompt
            assert "evil" in called_prompt or "邪恶" in called_prompt
            assert "你首夜击杀了预言家" in called_prompt
