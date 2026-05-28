"""测试狼人角色"""

from roles.werewolf import Werewolf
from roles.base import RoleType, Camp


class TestWerewolf:
    """测试狼人角色"""

    def test_role_type(self):
        """测试角色类型"""
        wolf = Werewolf(player_id=1)
        assert wolf.role_type == RoleType.WEREWOLF

    def test_camp(self):
        """测试阵营为邪恶"""
        wolf = Werewolf(player_id=1)
        assert wolf.camp == Camp.EVIL

    def test_name(self):
        """测试角色名称"""
        wolf = Werewolf(player_id=1)
        assert wolf.name == "Werewolf"

    def test_is_night_actionable_when_alive(self):
        """测试存活时可以在夜间行动"""
        wolf = Werewolf(player_id=1)
        assert wolf.is_night_actionable() is True

    def test_is_night_actionable_when_dead(self):
        """测试死亡后不能在夜间行动"""
        wolf = Werewolf(player_id=1)
        wolf.is_alive = False
        assert wolf.is_night_actionable() is False

    def test_get_night_action(self):
        """测试夜间行动返回 kill 类型"""
        wolf = Werewolf(player_id=1)
        action = wolf.get_night_action({})
        assert action is not None
        assert action.action_type == "kill"

    def test_get_night_action_includes_allies(self):
        """测试夜间行动包含队友信息"""
        wolf = Werewolf(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True},
                {"player_id": 2, "role": "werewolf", "is_alive": True},
                {"player_id": 3, "role": "werewolf", "is_alive": False},
            ]
        }
        action = wolf.get_night_action(game_state)
        assert 2 in action.metadata["allies"]

    def test_get_private_context_knows_wolves(self):
        """测试私有上下文包含狼人信息"""
        wolf = Werewolf(player_id=1)
        ctx = wolf.get_private_context()
        assert ctx["knows_wolves"] is True
        assert "werewolf" in ctx["note"].lower()

    def test_check_win_no_wolves_alive(self):
        """测试没有狼人存活时返回 False"""
        wolf = Werewolf(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": False},
            ]
        }
        assert wolf.check_win(game_state) is False

    def test_check_win_all_gods_dead(self):
        """测试所有神职死亡时狼人胜利"""
        wolf = Werewolf(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True, "is_god": True},
                {"player_id": 2, "role": "seer", "is_alive": False, "is_god": True},
            ]
        }
        assert wolf.check_win(game_state) is True

    def test_check_win_all_villagers_dead(self):
        """测试所有村民死亡时狼人胜利"""
        wolf = Werewolf(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True, "is_god": False},
                {"player_id": 2, "role": "villager", "is_alive": False, "is_god": False},
            ]
        }
        assert wolf.check_win(game_state) is True

    def test_check_win_goods_still_alive(self):
        """测试好人和狼人都存活时狼人未获胜"""
        wolf = Werewolf(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True, "is_god": True},
                {"player_id": 2, "role": "seer", "is_alive": True, "is_god": True},
                {"player_id": 3, "role": "villager", "is_alive": True, "is_god": False},
            ]
        }
        assert wolf.check_win(game_state) is False

    def test_on_death(self):
        """测试狼人死亡"""
        wolf = Werewolf(player_id=1)
        wolf.on_death("vote", {})
        assert wolf.is_alive is False