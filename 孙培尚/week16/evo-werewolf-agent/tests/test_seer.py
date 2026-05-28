"""测试预言家角色"""

from roles.seer import Seer
from roles.base import RoleType, Camp


class TestSeer:
    """测试预言家角色"""

    def test_role_type(self):
        """测试角色类型"""
        seer = Seer(player_id=1)
        assert seer.role_type == RoleType.SEER

    def test_camp(self):
        """测试阵营为善良"""
        seer = Seer(player_id=1)
        assert seer.camp == Camp.GOOD

    def test_name(self):
        """测试角色名称"""
        seer = Seer(player_id=1)
        assert seer.name == "Seer"

    def test_is_night_actionable_when_alive(self):
        """测试存活时可以在夜间行动"""
        seer = Seer(player_id=1)
        assert seer.is_night_actionable() is True

    def test_is_night_actionable_when_dead(self):
        """测试死亡后不能在夜间行动"""
        seer = Seer(player_id=1)
        seer.is_alive = False
        assert seer.is_night_actionable() is False

    def test_get_night_action_returns_check(self):
        """测试夜间行动返回 check 类型"""
        seer = Seer(player_id=1)
        action = seer.get_night_action({})
        assert action is not None
        assert action.action_type == "check"

    def test_get_private_context(self):
        """测试私有上下文"""
        seer = Seer(player_id=1)
        ctx = seer.get_private_context()
        assert "seer" in ctx["note"].lower()

    def test_check_win_no_wolves_alive(self):
        """测试没有狼人存活时预言家获胜"""
        seer = Seer(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": False},
            ]
        }
        assert seer.check_win(game_state) is True

    def test_check_win_wolves_still_alive(self):
        """测试狼人存活时预言家未获胜"""
        seer = Seer(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True},
                {"player_id": 2, "role": "werewolf", "is_alive": True},
            ]
        }
        assert seer.check_win(game_state) is False

    def test_check_win_multiple_wolves(self):
        """测试有多只狼人存活时未获胜"""
        seer = Seer(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "seer", "is_alive": True},
                {"player_id": 2, "role": "werewolf", "is_alive": True},
                {"player_id": 3, "role": "werewolf", "is_alive": True},
            ]
        }
        assert seer.check_win(game_state) is False

    def test_on_death(self):
        """测试预言家死亡"""
        seer = Seer(player_id=1)
        seer.on_death("night_kill", {})
        assert seer.is_alive is False