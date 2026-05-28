"""测试女巫角色"""

from roles.witch import Witch
from roles.base import RoleType, Camp


class TestWitch:
    """测试女巫角色"""

    def test_role_type(self):
        """测试角色类型"""
        witch = Witch(player_id=1)
        assert witch.role_type == RoleType.WITCH

    def test_camp(self):
        """测试阵营为善良"""
        witch = Witch(player_id=1)
        assert witch.camp == Camp.GOOD

    def test_name(self):
        """测试角色名称"""
        witch = Witch(player_id=1)
        assert witch.name == "Witch"

    def test_initial_heal_and_poison(self):
        """测试初始有救人药和毒药"""
        witch = Witch(player_id=1)
        assert witch.has_heal is True
        assert witch.has_poison is True

    def test_is_night_actionable_when_alive_with_potions(self):
        """测试存活且有药水时可以在夜间行动"""
        witch = Witch(player_id=1)
        assert witch.is_night_actionable() is True

    def test_is_night_actionable_when_dead(self):
        """测试死亡后不能在夜间行动"""
        witch = Witch(player_id=1)
        witch.is_alive = False
        assert witch.is_night_actionable() is False

    def test_is_night_actionable_when_no_potions(self):
        """测试没有药水时不能在夜间行动"""
        witch = Witch(player_id=1)
        witch._used_heal = True
        witch._used_poison = True
        assert witch.is_night_actionable() is False

    def test_get_night_action(self):
        """测试夜间行动返回 witch 类型"""
        witch = Witch(player_id=1)
        action = witch.get_night_action({})
        assert action is not None
        assert action.action_type == "witch"

    def test_get_night_action_includes_potion_status(self):
        """测试夜间行动包含药水状态"""
        witch = Witch(player_id=1)
        action = witch.get_night_action({})
        assert action.metadata["has_heal"] is True
        assert action.metadata["has_poison"] is True

    def test_get_night_action_includes_tonight_death(self):
        """测试夜间行动包含今晚死亡信息"""
        witch = Witch(player_id=1)
        game_state = {"tonight_death": 3}
        action = witch.get_night_action(game_state)
        assert action.metadata["tonight_death"] == 3

    def test_get_night_action_can_heal_self_false(self):
        """测试今晚死亡是自己时不能救自己"""
        witch = Witch(player_id=1)
        game_state = {"tonight_death": 1}
        action = witch.get_night_action(game_state)
        assert action.metadata["can_heal_self"] is False

    def test_get_night_action_can_heal_self_true(self):
        """测试今晚死亡不是自己时能救自己"""
        witch = Witch(player_id=1)
        game_state = {"tonight_death": 2}
        action = witch.get_night_action(game_state)
        assert action.metadata["can_heal_self"] is True

    def test_use_heal(self):
        """测试使用救人药"""
        witch = Witch(player_id=1)
        witch.use_heal()
        assert witch.has_heal is False
        assert witch._used_heal is True

    def test_use_poison(self):
        """测试使用毒药"""
        witch = Witch(player_id=1)
        witch.use_poison()
        assert witch.has_poison is False
        assert witch._used_poison is True

    def test_get_private_context(self):
        """测试私有上下文"""
        witch = Witch(player_id=1)
        ctx = witch.get_private_context()
        assert ctx["has_heal"] is True
        assert ctx["has_poison"] is True
        assert "witch" in ctx["note"].lower()

    def test_check_win_no_wolves_alive(self):
        """测试没有狼人存活时女巫获胜"""
        witch = Witch(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": False},
            ]
        }
        assert witch.check_win(game_state) is True

    def test_check_win_wolves_still_alive(self):
        """测试狼人存活时女巫未获胜"""
        witch = Witch(player_id=1)
        game_state = {
            "players": [
                {"player_id": 1, "role": "werewolf", "is_alive": True},
            ]
        }
        assert witch.check_win(game_state) is False

    def test_on_death(self):
        """测试女巫死亡"""
        witch = Witch(player_id=1)
        witch.on_death("vote", {})
        assert witch.is_alive is False

    def test_heal_and_poison_after_use(self):
        """测试使用药后状态正确"""
        witch = Witch(player_id=1)
        # 使用救人药
        witch.use_heal()
        assert witch.has_heal is False
        assert witch.has_poison is True

        # 使用毒药
        witch.use_poison()
        assert witch.has_heal is False
        assert witch.has_poison is False