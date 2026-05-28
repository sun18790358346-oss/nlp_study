"""测试猎人角色"""

from roles.hunter import Hunter
from roles.base import RoleType, Camp


class TestHunter:
    """测试猎人角色"""

    def test_role_type(self):
        """测试角色类型"""
        hunter = Hunter(player_id=1)
        assert hunter.role_type == RoleType.HUNTER

    def test_camp(self):
        """测试阵营为善良"""
        hunter = Hunter(player_id=1)
        assert hunter.camp == Camp.GOOD

    def test_name(self):
        """测试角色名称"""
        hunter = Hunter(player_id=1)
        assert hunter.name == "Hunter"

    def test_initial_can_shoot(self):
        """测试初始可以开枪"""
        hunter = Hunter(player_id=1)
        assert hunter.can_shoot is True

    def test_is_night_actionable_when_alive(self):
        """测试存活时猎人在夜间不能主动行动（被动技能）"""
        hunter = Hunter(player_id=1)
        # 猎人没有主动夜间行动能力，继承自 BaseRole 返回 False
        assert hunter.is_night_actionable() is False

    def test_is_night_actionable_when_dead(self):
        """测试死亡后不能在夜间行动"""
        hunter = Hunter(player_id=1)
        hunter.is_alive = False
        assert hunter.is_night_actionable() is False

    def test_lock_shoot(self):
        """测试锁定开枪技能"""
        hunter = Hunter(player_id=1)
        hunter.lock_shoot()
        assert hunter.can_shoot is False

    def test_on_death_night_kill_can_shoot(self):
        """测试夜晚被杀可以开枪"""
        hunter = Hunter(player_id=1)
        result = hunter.on_death("night_kill", {})
        assert hunter.is_alive is False
        assert result == []  # 返回空列表表示想开枪，目标待定

    def test_on_death_vote_can_shoot(self):
        """测试被投票出局可以开枪"""
        hunter = Hunter(player_id=1)
        result = hunter.on_death("vote", {})
        assert hunter.is_alive is False
        assert result == []

    def test_on_death_poison_cannot_shoot(self):
        """测试被毒杀不能开枪"""
        hunter = Hunter(player_id=1)
        result = hunter.on_death("poison", {})
        assert hunter.is_alive is False
        assert result is None
        assert hunter.can_shoot is False

    def test_on_death_shoot_cannot_shoot_again(self):
        """测试被枪杀不能再次开枪"""
        hunter = Hunter(player_id=1)
        result = hunter.on_death("shoot", {})
        assert hunter.is_alive is False
        assert result is None

    def test_get_private_context(self):
        """测试私有上下文"""
        hunter = Hunter(player_id=1)
        ctx = hunter.get_private_context()
        assert ctx["can_shoot"] is True
        assert "hunter" in ctx["note"].lower()

    def test_get_private_context_locked(self):
        """测试技能锁定后的私有上下文"""
        hunter = Hunter(player_id=1)
        hunter.lock_shoot()
        ctx = hunter.get_private_context()
        assert ctx["can_shoot"] is False

    def test_check_win_no_wolves_alive(self):
        """测试没有狼人存活时猎人获胜"""
        hunter = Hunter(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": False},
            ]
        }
        assert hunter.check_win(game_state) is True

    def test_check_win_wolves_still_alive(self):
        """测试狼人存活时猎人未获胜"""
        hunter = Hunter(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True},
            ]
        }
        assert hunter.check_win(game_state) is False

    def test_on_death_twice(self):
        """测试猎人死亡两次（先被杀再被毒）"""
        hunter = Hunter(player_id=1)
        hunter.on_death("night_kill", {})
        assert hunter.is_alive is False
        # 再毒一次，技能已锁定
        hunter.on_death("poison", {})
        assert hunter.can_shoot is False