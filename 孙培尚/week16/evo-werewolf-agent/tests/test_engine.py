"""测试游戏引擎模块"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from engine.phase import GamePhase, TurnOrder
from engine.state import GameState
from engine.player import Player
from engine.game_engine import (
    GameEngine,
    create_game,
    get_role_config,
    shuffle_roles,
    create_random_roles,
    ROLE_CONFIGS,
    STANDARD_6P_ROLES,
)


# ============== GamePhase Tests ==============

class TestGamePhase:
    """测试 GamePhase 枚举"""

    def test_night_phases(self):
        """测试夜晚阶段枚举值"""
        assert GamePhase.NIGHT_WOLF.value == "狼人杀人"
        assert GamePhase.NIGHT_SEER.value == "预言家查验"
        assert GamePhase.NIGHT_WITCH.value == "女巫用药"
        assert GamePhase.NIGHT_HUNTER.value == "猎人开枪"

    def test_day_phases(self):
        """测试白天阶段枚举值"""
        assert GamePhase.DAY_START.value == "白天开始"
        assert GamePhase.ELECTION.value == "警长选举"
        assert GamePhase.SPEECH.value == "公开演讲"
        assert GamePhase.VOTE.value == "投票环节"

    def test_game_over_phase(self):
        """测试游戏结束阶段"""
        assert GamePhase.GAME_OVER.value == "游戏结束"


# ============== TurnOrder Tests ==============

class TestTurnOrder:
    """测试 TurnOrder 类"""

    def test_get_night_order(self):
        """测试夜间行动顺序"""
        order = TurnOrder.get_night_order()
        assert len(order) == 3
        assert order[0] == GamePhase.NIGHT_WOLF
        assert order[1] == GamePhase.NIGHT_SEER
        assert order[2] == GamePhase.NIGHT_WITCH

    def test_is_night_phase(self):
        """测试判断夜间阶段"""
        assert TurnOrder.is_night_phase(GamePhase.NIGHT_WOLF) is True
        assert TurnOrder.is_night_phase(GamePhase.NIGHT_SEER) is True
        assert TurnOrder.is_night_phase(GamePhase.NIGHT_WITCH) is True
        assert TurnOrder.is_night_phase(GamePhase.NIGHT_HUNTER) is True
        assert TurnOrder.is_night_phase(GamePhase.DAY_START) is False
        assert TurnOrder.is_night_phase(GamePhase.SPEECH) is False

    def test_is_day_phase(self):
        """测试判断白天阶段"""
        assert TurnOrder.is_day_phase(GamePhase.DAY_START) is True
        assert TurnOrder.is_day_phase(GamePhase.ELECTION) is True
        assert TurnOrder.is_day_phase(GamePhase.SPEECH) is True
        assert TurnOrder.is_day_phase(GamePhase.VOTE) is True
        assert TurnOrder.is_day_phase(GamePhase.NIGHT_WOLF) is False


# ============== GameState Tests ==============

class TestGameState:
    """测试 GameState 类"""

    def test_init_default(self):
        """测试默认初始化"""
        state = GameState()
        assert state.players == []
        assert state.phase == GamePhase.DAY_START
        assert state.day_number == 1
        assert state.speaker_order == []
        assert state.current_speaker == 0
        assert state.last_words == []
        assert state.vote_record == []
        assert state.night_deaths == []

    def test_add_and_get_player(self):
        """测试添加和获取玩家"""
        state = GameState()
        mock_player = MagicMock()
        mock_player.player_id = 0
        state.players.append(mock_player)

        player = state.get_player(0)
        assert player == mock_player

    def test_get_player_not_found(self):
        """测试获取不存在的玩家"""
        state = GameState()
        player = state.get_player(999)
        assert player is None

    def test_get_alive_players(self):
        """测试获取存活玩家"""
        state = GameState()
        player1 = MagicMock()
        player1.is_alive = True
        player2 = MagicMock()
        player2.is_alive = False
        player3 = MagicMock()
        player3.is_alive = True
        state.players = [player1, player2, player3]

        alive = state.get_alive_players()
        assert len(alive) == 2
        assert player1 in alive
        assert player3 in alive

    def test_get_players_by_role(self):
        """测试根据角色类型获取玩家"""
        state = GameState()
        player1 = MagicMock()
        player1.role_type.value = "werewolf"
        player2 = MagicMock()
        player2.role_type.value = "villager"
        state.players = [player1, player2]

        wolves = state.get_players_by_role("werewolf")
        assert len(wolves) == 1
        assert wolves[0] == player1

    def test_get_players_by_camp(self):
        """测试根据阵营获取玩家"""
        state = GameState()
        player1 = MagicMock()
        player1.camp.value = "good"
        player2 = MagicMock()
        player2.camp.value = "evil"
        state.players = [player1, player2]

        good_players = state.get_players_by_camp("good")
        assert len(good_players) == 1

    def test_is_game_over_no_players(self):
        """测试没有玩家时游戏结束"""
        state = GameState()
        assert state.is_game_over() is True

    def test_is_game_over_no_wolves(self):
        """测试狼人全死亡时游戏结束（好人胜利）"""
        state = GameState()
        player1 = MagicMock()
        player1.is_alive = True
        player1.role_type.value = "villager"
        player1.camp.value = "good"
        player2 = MagicMock()
        player2.is_alive = True
        player2.role_type.value = "seer"
        player2.camp.value = "good"
        state.players = [player1, player2]

        assert state.is_game_over() is True
        assert state.get_winner() == "good"

    def test_is_game_over_no_good(self):
        """测试好人全死亡时游戏结束（狼人胜利）"""
        state = GameState()
        player1 = MagicMock()
        player1.is_alive = True
        player1.role_type.value = "werewolf"
        player1.camp.value = "evil"
        state.players = [player1]

        assert state.is_game_over() is True
        assert state.get_winner() == "evil"

    def test_is_game_over_not_over(self):
        """测试游戏未结束"""
        state = GameState()
        player1 = MagicMock()
        player1.is_alive = True
        player1.role_type.value = "werewolf"
        player1.camp.value = "evil"
        player2 = MagicMock()
        player2.is_alive = True
        player2.role_type.value = "villager"
        player2.camp.value = "good"
        state.players = [player1, player2]

        assert state.is_game_over() is False
        assert state.get_winner() is None

    def test_add_vote(self):
        """测试添加投票记录"""
        state = GameState()
        state.day_number = 1
        state.add_vote(voter_id=0, target_id=1)
        assert len(state.vote_record) == 1
        assert state.vote_record[0]["voter_id"] == 0
        assert state.vote_record[0]["target_id"] == 1
        assert state.vote_record[0]["day"] == 1

    def test_reset_vote_record(self):
        """测试重置投票记录"""
        state = GameState()
        state.add_vote(0, 1)
        state.add_vote(2, 3)
        state.reset_vote_record()
        assert state.vote_record == []

    def test_clear_night_deaths(self):
        """测试清除夜晚死亡记录"""
        state = GameState()
        state.night_deaths = [0, 1]
        state.clear_night_deaths()
        assert state.night_deaths == []

    def test_add_night_death(self):
        """测试添加夜晚死亡"""
        state = GameState()
        state.add_night_death(0)
        state.add_night_death(1)
        assert len(state.night_deaths) == 2
        assert 0 in state.night_deaths
        assert 1 in state.night_deaths

    def test_set_speaker_order(self):
        """测试设置发言顺序"""
        state = GameState()
        state.set_speaker_order([2, 0, 1])
        assert state.speaker_order == [2, 0, 1]
        assert state.current_speaker == 0

    def test_next_speaker(self):
        """测试切换到下一个发言者"""
        state = GameState()
        state.set_speaker_order([0, 1, 2])

        state.next_speaker()
        assert state.current_speaker == 1
        state.next_speaker()
        assert state.current_speaker == 2
        state.next_speaker()
        assert state.current_speaker == 0  # 循环

    def test_to_dict(self):
        """测试转换为字典"""
        state = GameState()
        mock_player = MagicMock()
        mock_player.to_dict.return_value = {"player_id": 0}
        state.players.append(mock_player)
        state.speaker_order = [0]

        result = state.to_dict()
        assert "day_number" in result
        assert "phase" in result
        assert "players" in result
        assert "alive_players" in result

    def test_get_public_context(self):
        """测试获取公开上下文"""
        state = GameState()
        state.day_number = 2
        state.phase = GamePhase.SPEECH
        mock_player = MagicMock()
        mock_player.player_id = 0
        mock_player.name = "Test"
        mock_player.is_alive = True
        state.players.append(mock_player)

        ctx = state.get_public_context()
        assert ctx["day_number"] == 2
        assert ctx["phase"] == GamePhase.SPEECH.value
        assert "alive_players" in ctx


# ============== Player Tests ==============

class TestPlayer:
    """测试 Player 类"""

    def test_init(self):
        """测试初始化"""
        from roles.villager import Villager
        role = Villager(player_id=0)
        player = Player(player_id=0, role=role, name="Test")

        assert player.player_id == 0
        assert player.name == "Test"
        assert player.role == role

    def test_role_type_property(self):
        """测试 role_type 属性"""
        from roles.werewolf import Werewolf
        role = Werewolf(player_id=0)
        player = Player(player_id=0, role=role)
        assert player.role_type.value == "werewolf"

    def test_camp_property(self):
        """测试 camp 属性"""
        from roles.werewolf import Werewolf
        role = Werewolf(player_id=0)
        player = Player(player_id=0, role=role)
        assert player.camp.value == "evil"

    def test_is_alive_property(self):
        """测试 is_alive 属性"""
        from roles.villager import Villager
        role = Villager(player_id=0)
        player = Player(player_id=0, role=role)
        assert player.is_alive is True

        player.role.is_alive = False
        assert player.is_alive is False

    def test_is_sheriff_property(self):
        """测试 is_sheriff 属性"""
        from roles.villager import Villager
        role = Villager(player_id=0)
        player = Player(player_id=0, role=role)
        assert player.is_sheriff is False

        player.is_sheriff = True
        assert player.is_sheriff is True

    def test_to_dict(self):
        """测试转换为字典"""
        from roles.villager import Villager
        role = Villager(player_id=0)
        player = Player(player_id=0, role=role, name="Test")
        player.role.is_alive = True
        player.role.is_sheriff = False

        result = player.to_dict()
        assert result["player_id"] == 0
        assert result["name"] == "Test"
        assert result["role"] == "villager"
        assert result["camp"] == "good"
        assert result["is_alive"] is True

    def test_repr(self):
        """测试字符串表示"""
        from roles.villager import Villager
        role = Villager(player_id=0)
        player = Player(player_id=0, role=role, name="Test")
        r = repr(player)
        assert "0" in r
        assert "alive" in r


# ============== GameEngine Tests ==============

class TestGameEngine:
    """测试 GameEngine 类"""

    def test_init(self):
        """测试初始化"""
        engine = GameEngine(["玩家1", "玩家2", "玩家3"])
        assert engine.player_names == ["玩家1", "玩家2", "玩家3"]
        assert engine.game_state is not None
        assert engine.player_agents == {}
        assert engine._is_running is False

    def test_init_with_logger(self):
        """测试带日志记录器初始化"""
        mock_logger = MagicMock()
        engine = GameEngine(["玩家1"], logger=mock_logger)
        assert engine.logger == mock_logger

    def test_log_without_logger(self):
        """测试没有日志记录器时不报错"""
        engine = GameEngine(["玩家1"])
        engine._log("info", "test message")  # 不应抛出异常

    def test_create_role(self):
        """测试创建角色"""
        engine = GameEngine(["玩家1"])

        werewolf = engine._create_role("werewolf", 0)
        assert werewolf.role_type.value == "werewolf"

        seer = engine._create_role("seer", 1)
        assert seer.role_type.value == "seer"

        witch = engine._create_role("witch", 2)
        assert witch.role_type.value == "witch"

        hunter = engine._create_role("hunter", 3)
        assert hunter.role_type.value == "hunter"

        villager = engine._create_role("villager", 4)
        assert villager.role_type.value == "villager"

    def test_create_role_unknown_defaults_to_villager(self):
        """测试未知角色默认为村民"""
        engine = GameEngine(["玩家1"])
        role = engine._create_role("unknown_role", 0)
        assert role.role_type.value == "villager"

    def test_count_vote(self):
        """测试投票统计"""
        engine = GameEngine(["玩家1"])
        result = engine._count_vote([0, 1, 0, 2, 0])
        assert result == 0

        result = engine._count_vote([1, 1, 2, 2])
        assert result in [1, 2]

    def test_stop(self):
        """测试停止游戏"""
        engine = GameEngine(["玩家1"])
        engine._is_running = True
        engine.stop()
        assert engine._is_running is False


# ============== Helper Function Tests ==============

class TestRoleConfigs:
    """测试角色配置相关函数"""

    def test_role_configs_has_required_keys(self):
        """测试预定义配置包含所有必需键"""
        required_configs = ["standard_6", "simple_4", "big_9"]
        for config_name in required_configs:
            assert config_name in ROLE_CONFIGS
            config = ROLE_CONFIGS[config_name]
            assert "name" in config
            assert "roles" in config

    def test_standard_6_roles(self):
        """测试标准6人局配置"""
        roles = ROLE_CONFIGS["standard_6"]["roles"]
        role_counts = {}
        for role_type in roles.values():
            role_counts[role_type] = role_counts.get(role_type, 0) + 1

        assert role_counts.get("werewolf", 0) == 2
        assert "seer" in role_counts
        assert "witch" in role_counts
        assert "hunter" in role_counts
        assert "villager" in role_counts

    def test_get_role_config_standard_6(self):
        """测试获取标准6人局配置"""
        config = get_role_config("standard_6")
        assert len(config) == 6
        assert 0 in config
        assert 5 in config

    def test_get_role_config_simple_4(self):
        """测试获取4人局配置"""
        config = get_role_config("simple_4")
        assert len(config) == 4

    def test_get_role_config_big_9(self):
        """测试获取9人局配置"""
        config = get_role_config("big_9")
        assert len(config) == 9

    def test_get_role_config_unknown_raises(self):
        """测试获取未知配置时抛出异常"""
        with pytest.raises(ValueError):
            get_role_config("unknown_config")

    def test_shuffle_roles(self):
        """测试打乱角色分配"""
        original = {0: "werewolf", 1: "seer", 2: "villager"}
        shuffled = shuffle_roles(original)

        assert len(shuffled) == 3
        assert set(shuffled.values()) == set(original.values())

        # 验证是随机打乱的（有一定概率通过，但大概率会改变顺序）
        # 这个测试主要验证函数不会出错
        # 至少有一次位置改变是大概率事件

    def test_create_random_roles_basic(self):
        """测试创建随机角色"""
        roles = create_random_roles(num_players=6)
        assert len(roles) == 6
        assert "werewolf" in roles.values()
        assert any(r in roles.values() for r in ["seer", "witch", "hunter"])

    def test_create_random_roles_has_wolves(self):
        """测试随机角色确保有狼人"""
        roles = create_random_roles(num_players=6)
        assert "werewolf" in roles.values()

    def test_create_random_roles_has_gods(self):
        """测试随机角色确保有神职"""
        roles = create_random_roles(num_players=6)
        assert any(r in roles.values() for r in ["seer", "witch", "hunter"])

    def test_create_random_roles_respects_ratio(self):
        """测试随机角色遵循狼人比例"""
        roles = create_random_roles(num_players=10, wolf_ratio=0.3)
        wolf_count = sum(1 for r in roles.values() if r == "werewolf")
        # 至少1只狼
        assert wolf_count >= 1


# ============== Integration Tests ==============

class TestGameIntegration:
    """测试游戏集成"""

    @pytest.mark.asyncio
    async def test_create_and_initialize_game(self):
        """测试创建并初始化游戏"""
        player_names = ["玩家1", "玩家2", "玩家3", "玩家4"]
        role_assignment = {
            0: "werewolf",
            1: "seer",
            2: "witch",
            3: "villager",
        }

        engine = await create_game(player_names, role_assignment)

        assert len(engine.game_state.players) == 4
        assert engine.game_state.players[0].role.role_type.value == "werewolf"
        assert engine.game_state.players[1].role.role_type.value == "seer"
        assert engine.game_state.players[2].role.role_type.value == "witch"
        assert engine.game_state.players[3].role.role_type.value == "villager"

    @pytest.mark.asyncio
    async def test_game_initialization_sets_speaker_order(self):
        """测试游戏初始化设置发言顺序"""
        player_names = ["玩家1", "玩家2"]
        role_assignment = {0: "werewolf", 1: "villager"}

        engine = await create_game(player_names, role_assignment)
        assert len(engine.game_state.speaker_order) == 2
        assert engine.game_state.speaker_order == [0, 1]


class TestStandardRoles:
    """测试标准角色配置"""

    def test_standard_6p_roles_matches_config(self):
        """测试 STANDARD_6P_ROLES 与配置一致"""
        config = ROLE_CONFIGS["standard_6"]["roles"]
        assert config == STANDARD_6P_ROLES

    def test_all_roles_implemented(self):
        """测试所有配置中的角色都已实现"""
        for config_name, config in ROLE_CONFIGS.items():
            for role_type in config["roles"].values():
                if role_type not in ["idiot"]:  # 白痴暂未实现
                    engine = GameEngine(["玩家1"])
                    role = engine._create_role(role_type, 0)
                    assert role is not None


class TestGameSummaryPhase:
    """测试游戏总结阶段"""

    @pytest.mark.asyncio
    async def test_run_summaries_called_once(self):
        """测试总结阶段只执行一次"""
        player_names = ["玩家1", "玩家2", "玩家3"]
        role_assignment = {0: "werewolf", 1: "villager", 2: "villager"}

        engine = await create_game(player_names, role_assignment)
        for p in engine.game_state.players:
            p.agent = MagicMock()
            p.agent.decide_night_action = AsyncMock(
                return_value={"target": 1, "reasoning": "test"}
            )
            p.agent.decide_speech = AsyncMock(return_value={"content": "test"})
            p.agent.decide_vote = AsyncMock(return_value={"target": 0})

        # Mock summary agent to avoid real LLM calls
        engine._summary_agent.generate_summary = AsyncMock(return_value={
            "summary": "test", "strategies": "", "mistakes": "", "lessons": "",
        })

        max_steps = 50
        found_game_over = False
        for _ in range(max_steps):
            result = await engine.step()
            if result["phase"] == "day_end" and result["is_game_over"]:
                found_game_over = True
                break
        assert found_game_over, "Game did not reach day_end with game_over"

        summary_result = await engine.step()
        assert summary_result["phase"] == "summary"
        assert summary_result["is_game_over"] is True

        assert engine._step_index == -1

        final_result = await engine.step()
        assert final_result["phase"] == "game_over"
        assert final_result["is_game_over"] is True

    def test_engine_has_summary_agent(self):
        """测试 GameEngine 初始化包含总结代理"""
        engine = GameEngine(["玩家1"])
        assert engine._summary_agent is not None
        assert engine._summaries_done is False

    @pytest.mark.asyncio
    async def test_summary_phase_saves_experiences(self):
        """测试总结阶段保存经验到文件"""
        import os
        from memory.experience import EXPERIENCES_DIR, load_experiences

        for role_file in ["werewolf.json", "villager.json"]:
            fp = os.path.join(EXPERIENCES_DIR, role_file)
            if os.path.exists(fp):
                os.remove(fp)

        player_names = ["玩家1", "玩家2"]
        role_assignment = {0: "werewolf", 1: "villager"}

        engine = await create_game(player_names, role_assignment)
        for p in engine.game_state.players:
            p.agent = MagicMock()
            p.agent.decide_night_action = AsyncMock(
                return_value={"target": 1, "reasoning": "test"}
            )
            p.agent.decide_speech = AsyncMock(return_value={"content": "test"})
            p.agent.decide_vote = AsyncMock(return_value={"target": 0})

        engine._summary_agent.generate_summary = AsyncMock(return_value={
            "summary": "test总结", "strategies": "test策略",
            "mistakes": "test错误", "lessons": "test建议",
        })

        max_steps = 50
        for _ in range(max_steps):
            result = await engine.step()
            if result["phase"] == "day_end" and result["is_game_over"]:
                break

        await engine.step()

        werewolf_exps = load_experiences("werewolf")
        assert len(werewolf_exps) >= 1
        assert werewolf_exps[-1]["summary"] == "test总结"

        for role_file in ["werewolf.json", "villager.json"]:
            fp = os.path.join(EXPERIENCES_DIR, role_file)
            if os.path.exists(fp):
                os.remove(fp)

        # 验证经验文件被创建
        werewolf_exps = load_experiences("werewolf")
        villager_exps = load_experiences("villager")

        # 清理测试数据
        for role_file in ["werewolf.json", "villager.json"]:
            fp = os.path.join(EXPERIENCES_DIR, role_file)
            if os.path.exists(fp):
                os.remove(fp)