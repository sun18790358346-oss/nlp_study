"""测试村民角色"""

from roles.villager import Villager
from roles.base import RoleType, Camp


class TestVillager:
    """测试村民角色"""

    def test_role_type(self):
        """测试角色类型"""
        villager = Villager(player_id=1)
        assert villager.role_type == RoleType.VILLAGER

    def test_camp(self):
        """测试阵营为善良"""
        villager = Villager(player_id=1)
        assert villager.camp == Camp.GOOD

    def test_name(self):
        """测试角色名称"""
        villager = Villager(player_id=1)
        assert villager.name == "Villager"

    def test_is_night_actionable(self):
        """测试村民在夜间不能行动"""
        villager = Villager(player_id=1)
        assert villager.is_night_actionable() is False

    def test_is_night_actionable_when_dead(self):
        """测试死亡后也不能行动"""
        villager = Villager(player_id=1)
        villager.is_alive = False
        assert villager.is_night_actionable() is False

    def test_get_night_action(self):
        """测试村民没有夜间行动"""
        villager = Villager(player_id=1)
        assert villager.get_night_action({}) is None

    def test_can_speak_when_alive(self):
        """测试存活时可以发言"""
        villager = Villager(player_id=1)
        assert villager.can_speak() is True

    def test_can_speak_when_dead(self):
        """测试死亡后不能发言"""
        villager = Villager(player_id=1)
        villager.is_alive = False
        assert villager.can_speak() is False

    def test_can_vote_when_alive(self):
        """测试存活时可以投票"""
        villager = Villager(player_id=1)
        assert villager.can_vote() is True

    def test_can_vote_when_dead(self):
        """测试死亡后不能投票"""
        villager = Villager(player_id=1)
        villager.is_alive = False
        assert villager.can_vote() is False

    def test_get_vote_target(self):
        """测试村民没有默认投票目标"""
        villager = Villager(player_id=1)
        assert villager.get_vote_target({}) is None

    def test_get_private_context(self):
        """测试私有上下文"""
        villager = Villager(player_id=1)
        ctx = villager.get_private_context()
        assert "villager" in ctx["note"].lower()

    def test_check_win_no_wolves_alive(self):
        """测试没有狼人存活时村民获胜"""
        villager = Villager(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": False},
            ]
        }
        assert villager.check_win(game_state) is True

    def test_check_win_wolves_still_alive(self):
        """测试狼人存活时村民未获胜"""
        villager = Villager(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True},
            ]
        }
        assert villager.check_win(game_state) is False

    def test_on_death(self):
        """测试村民死亡"""
        villager = Villager(player_id=1)
        villager.on_death("vote", {})
        assert villager.is_alive is False

    def test_on_death_night_kill(self):
        """测试村民被夜晚杀害"""
        villager = Villager(player_id=1)
        villager.on_death("night_kill", {})
        assert villager.is_alive is False

    def test_multiple_villagers(self):
        """测试多个村民的场景"""
        game_state = {
            "players": [
                {"player_id": 1, "role": "villager", "is_alive": True},
                {"player_id": 2, "role": "villager", "is_alive": True},
                {"player_id": 3, "role": "werewolf", "is_alive": False},
            ]
        }
        villager1 = Villager(player_id=1)
        villager2 = Villager(player_id=2)

        assert villager1.check_win(game_state) is True
        assert villager2.check_win(game_state) is True

    def test_all_villagers_dead_wolves_alive(self):
        """测试所有村民死亡但狼人存活"""
        game_state = {
            "players": [
                {"player_id": 1, "role": "villager", "is_alive": False},
                {"player_id": 2, "role": "werewolf", "is_alive": True},
            ]
        }
        villager = Villager(player_id=1)
        # 狼人赢了，所以村民没有赢
        assert villager.check_win(game_state) is False