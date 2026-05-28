"""FastAPI Server 集成测试"""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

from httpx import AsyncClient, ASGITransport

from api.server import app, games
from agent.player_agent import PlayerAgent
from agent.summary_agent import SummaryAgent


# ── Mock LLM ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def mock_llm():
    """Mock PlayerAgent decision methods so tests don't call real LLM APIs."""
    original_night = PlayerAgent.decide_night_action
    original_speech = PlayerAgent.decide_speech
    original_vote = PlayerAgent.decide_vote
    original_summary = SummaryAgent.generate_summary

    async def mock_night(self, game_state):
        """Return sensible targets based on game state."""
        alive = game_state.get("alive_players", [])
        my_id = game_state.get("player_id", self.player_id)
        role = game_state.get("role", "")
        if role == "witch":
            return {"action": "skip", "reasoning": "test"}
        # Pick last alive player that is not self
        for p in reversed(alive):
            pid = p["player_id"] if isinstance(p, dict) else p
            if pid != my_id:
                return {"target": pid, "reasoning": "test"}
        return {"target": None, "reasoning": "no target"}

    async def mock_speech(self, game_state):
        return {"content": "我是好人，请大家相信我。"}

    async def mock_vote(self, game_state):
        """Vote for first alive player not self."""
        alive = game_state.get("alive_players", [])
        my_id = game_state.get("player_id", self.player_id)
        for p in alive:
            pid = p["player_id"] if isinstance(p, dict) else p
            if pid != my_id:
                return {"target": pid}
        return {"target": None}

    async def mock_summary(self, player_name, role_name, camp, winner, personal_history):
        return {
            "summary": "本局测试总结",
            "strategies": "测试策略",
            "mistakes": "测试错误",
            "lessons": "测试建议",
        }

    PlayerAgent.decide_night_action = mock_night
    PlayerAgent.decide_speech = mock_speech
    PlayerAgent.decide_vote = mock_vote
    SummaryAgent.generate_summary = mock_summary

    yield

    PlayerAgent.decide_night_action = original_night
    PlayerAgent.decide_speech = original_speech
    PlayerAgent.decide_vote = original_vote
    SummaryAgent.generate_summary = original_summary


# ── Helpers ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
def clear_games():
    """Clear games dict before each test."""
    games.clear()
    yield


async def create_default_game(client):
    """Helper: create a standard game and return game_id."""
    resp = await client.post("/games", json={"config_name": "standard_6"})
    assert resp.status_code == 200
    data = resp.json()
    assert "game_id" in data
    return data["game_id"]


# ── Tests ────────────────────────────────────────────────────────────

class TestCreateGame:
    """创建游戏测试"""

    @pytest.mark.asyncio
    async def test_create_game_default(self, client):
        """测试创建默认游戏"""
        resp = await client.post("/games", json={"config_name": "standard_6"})
        assert resp.status_code == 200
        data = resp.json()
        assert "game_id" in data
        assert data["day_number"] == 1
        assert data["alive_count"] == 6
        assert data["is_game_over"] is False
        assert data["phase"] == "白天开始"

    @pytest.mark.asyncio
    async def test_create_game_with_custom_names(self, client):
        """测试自定义玩家名称"""
        names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"]
        resp = await client.post("/games", json={
            "config_name": "standard_6",
            "player_names": names,
            "shuffle": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["alive_count"] == 6

    @pytest.mark.asyncio
    async def test_create_game_invalid_config(self, client):
        """测试无效配置"""
        resp = await client.post("/games", json={"config_name": "unknown"})
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_game_wrong_player_count(self, client):
        """测试玩家数量不匹配"""
        resp = await client.post("/games", json={
            "config_name": "standard_6",
            "player_names": ["A", "B"],
        })
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_simple_4_game(self, client):
        """测试创建4人局"""
        resp = await client.post("/games", json={"config_name": "simple_4"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["alive_count"] == 4


class TestStepGame:
    """逐步执行游戏测试"""

    @pytest.mark.asyncio
    async def test_step_phases(self, client):
        """测试各个阶段逐步执行"""
        game_id = await create_default_game(client)

        phases_expected = [
            "night_wolf", "night_seer", "night_witch", "night_result",
            "day_start", "speech", "vote", "day_end",
        ]

        for i, expected_phase in enumerate(phases_expected):
            resp = await client.post(f"/games/{game_id}/step")
            assert resp.status_code == 200, f"Failed at step {i}: {expected_phase}"
            data = resp.json()
            assert data["phase"] == expected_phase, (
                f"Step {i}: expected {expected_phase}, got {data['phase']}"
            )
            assert data["day_number"] >= 1
            assert "players" in data
            assert "dialogues" in data
            assert "deaths" in data
            assert "is_game_over" in data
            # 游戏可能在投票阶段提前结束（狼人被票出导致 game_over）
            if data["is_game_over"]:
                break

    @pytest.mark.asyncio
    async def test_step_game_completion(self, client):
        """测试完整游戏到结束"""
        game_id = await create_default_game(client)

        max_steps = 100
        for i in range(max_steps):
            resp = await client.post(f"/games/{game_id}/step")
            assert resp.status_code == 200
            data = resp.json()
            if data["is_game_over"]:
                assert data["phase"] in ("day_end", "summary", "game_over")
                assert data["winner"] in ("good", "evil")
                break
        else:
            pytest.fail("Game did not finish within 100 steps")

    @pytest.mark.asyncio
    async def test_step_after_game_over(self, client):
        """测试游戏结束后 step 返回 game_over"""
        game_id = await create_default_game(client)

        max_steps = 100
        for i in range(max_steps):
            resp = await client.post(f"/games/{game_id}/step")
            data = resp.json()
            if data["is_game_over"]:
                break

        # Step through summary phase if present
        resp = await client.post(f"/games/{game_id}/step")
        data = resp.json()
        if data["phase"] == "summary":
            resp = await client.post(f"/games/{game_id}/step")
            data = resp.json()

        # 再次 step 应该还是 game_over
        assert data["phase"] == "game_over"
        assert data["is_game_over"] is True

    @pytest.mark.asyncio
    async def test_step_game_not_found(self, client):
        """测试 step 不存在的游戏"""
        resp = await client.post("/games/nonexistent/step")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_step_night_wolf_data(self, client):
        """测试 night_wolf 阶段的 step_data"""
        game_id = await create_default_game(client)
        resp = await client.post(f"/games/{game_id}/step")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phase"] == "night_wolf"
        assert "step_data" in data
        assert "wolf_votes" in data["step_data"]
        assert "final_target" in data["step_data"]

    @pytest.mark.asyncio
    async def test_step_speech_data(self, client):
        """测试 speech 阶段包含发言数据"""
        game_id = await create_default_game(client)
        # 步进到 speech（index 0,1,2,3,4,5）
        for _ in range(5):
            await client.post(f"/games/{game_id}/step")
        resp = await client.post(f"/games/{game_id}/step")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phase"] == "speech"
        assert "speeches" in data["step_data"]
        assert len(data["step_data"]["speeches"]) > 0

    @pytest.mark.asyncio
    async def test_step_vote_data(self, client):
        """测试 vote 阶段包含投票数据"""
        game_id = await create_default_game(client)
        # 步进到 vote（index 0,1,2,3,4,5,6）
        for _ in range(6):
            await client.post(f"/games/{game_id}/step")
        resp = await client.post(f"/games/{game_id}/step")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phase"] == "vote"
        assert "votes" in data["step_data"]
        assert "eliminated" in data["step_data"]

    @pytest.mark.asyncio
    async def test_step_summary_phase(self, client):
        """测试游戏结束后的总结阶段"""
        game_id = await create_default_game(client)

        max_steps = 100
        for _ in range(max_steps):
            resp = await client.post(f"/games/{game_id}/step")
            data = resp.json()
            if data["is_game_over"]:
                break

        resp = await client.post(f"/games/{game_id}/step")
        data = resp.json()

        if data["phase"] == "summary":
            assert data["is_game_over"] is True
            assert data["winner"] in ("good", "evil")
        elif data["phase"] == "game_over":
            assert data["is_game_over"] is True


class TestGetGame:
    """获取游戏状态测试"""

    @pytest.mark.asyncio
    async def test_get_game_status(self, client):
        """测试获取游戏状态"""
        game_id = await create_default_game(client)
        resp = await client.get(f"/games/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["game_id"] == game_id
        assert "phase" in data
        assert "day_number" in data
        assert "players" in data
        assert len(data["players"]) == 6
        assert "dialogues" in data
        assert "death_records" in data
        assert "is_game_over" in data

    @pytest.mark.asyncio
    async def test_get_game_status_after_steps(self, client):
        """测试 step 后获取状态"""
        game_id = await create_default_game(client)
        for _ in range(4):
            await client.post(f"/games/{game_id}/step")

        resp = await client.get(f"/games/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["dialogues"]) > 0  # 应有对话记录

    @pytest.mark.asyncio
    async def test_get_game_not_found(self, client):
        """测试获取不存在的游戏"""
        resp = await client.get("/games/nonexistent")
        assert resp.status_code == 404


class TestListGames:
    """列出游戏测试"""

    @pytest.mark.asyncio
    async def test_list_games_empty(self, client):
        """测试空列表"""
        resp = await client.get("/games")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {}

    @pytest.mark.asyncio
    async def test_list_games_with_games(self, client):
        """测试有游戏时列出"""
        gid1 = await create_default_game(client)
        gid2 = await create_default_game(client)
        resp = await client.get("/games")
        assert resp.status_code == 200
        data = resp.json()
        assert gid1 in data
        assert gid2 in data
        assert len(data) == 2


class TestDeleteGame:
    """删除游戏测试"""

    @pytest.mark.asyncio
    async def test_delete_game(self, client):
        """测试删除游戏"""
        game_id = await create_default_game(client)
        resp = await client.delete(f"/games/{game_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "deleted" in data["message"]

        # 确认已删除
        resp = await client.get(f"/games/{game_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_game_not_found(self, client):
        """测试删除不存在的游戏"""
        resp = await client.delete("/games/nonexistent")
        assert resp.status_code == 404


class TestConfigs:
    """配置列表测试"""

    @pytest.mark.asyncio
    async def test_list_configs(self, client):
        """测试列出可用配置"""
        resp = await client.get("/configs")
        assert resp.status_code == 200
        data = resp.json()
        assert "standard_6" in data
        assert "simple_4" in data
        assert "big_9" in data
        assert data["standard_6"]["player_count"] == 6
        assert data["simple_4"]["player_count"] == 4
        assert data["big_9"]["player_count"] == 9
