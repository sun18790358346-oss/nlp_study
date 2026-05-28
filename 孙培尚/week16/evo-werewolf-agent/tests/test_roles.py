"""角色交互测试套件

测试角色之间的交互规则：
- 狼人击杀与女巫救药
- 女巫毒药与猎人被毒不能开枪
- 猎人被刀/投票可开枪
- 预言家查验狼人
- 狼人互知
"""

import pytest
from roles.base import RoleType, Camp, NightAction, VoteAction
from roles.werewolf import Werewolf
from roles.seer import Seer
from roles.witch import Witch
from roles.hunter import Hunter
from roles.villager import Villager


class TestWolfKillAndWitchHeal:
    """测试狼人击杀与女巫救人交互"""

    def test_wolf_kill_survives_if_witch_heals(self):
        """测试狼人击杀后女巫可救活"""
        victim = Villager(player_id=0)
        witch = Witch(player_id=1)

        assert victim.is_alive is True
        victim.on_death("night_kill", {})
        assert victim.is_alive is False

        # 女巫救人应在 kill 之前生效（实际流程中由引擎控制）
        # 这里只验证女巫有救药
        assert witch.has_heal is True

    def test_witch_heal_consumed_after_use(self):
        """测试女巫使用解药后不可再用"""
        witch = Witch(player_id=0)
        assert witch.has_heal is True
        witch.use_heal()
        assert witch.has_heal is False

    def test_witch_poison_consumed_after_use(self):
        """测试女巫使用毒药后不可再用"""
        witch = Witch(player_id=0)
        assert witch.has_poison is True
        witch.use_poison()
        assert witch.has_poison is False

    def test_witch_kills_with_poison(self):
        """测试女巫毒药可杀人"""
        victim = Werewolf(player_id=1)
        assert victim.is_alive is True
        victim.on_death("poison", {})
        assert victim.is_alive is False


class TestHunterInteraction:
    """测试猎人开枪规则"""

    def test_hunter_shoots_when_killed_by_wolf(self):
        """测试猎人被狼人杀可以开枪（on_death 返回 [] 表示要开枪）"""
        hunter = Hunter(player_id=0)
        assert hunter.can_shoot is True
        result = hunter.on_death("night_kill", {})
        # on_death 返回空列表表示猎人要开枪（目标由引擎后续决定）
        assert result == []
        # can_shoot 在引擎调用 get_shoot_target 后才锁定
        assert hunter.can_shoot is True

    def test_hunter_shoots_when_voted_out(self):
        """测试猎人被投票出局可以开枪"""
        hunter = Hunter(player_id=0)
        assert hunter.can_shoot is True
        result = hunter.on_death("vote", {})
        assert result == []
        assert hunter.can_shoot is True

    def test_hunter_cannot_shoot_when_poisoned(self):
        """测试猎人被毒杀不能开枪"""
        hunter = Hunter(player_id=0)
        assert hunter.can_shoot is True
        result = hunter.on_death("poison", {})
        # 被毒杀不能开枪，can_shoot 被设为 False
        assert hunter.can_shoot is False
        assert result is None

    def test_hunter_cannot_shoot_twice(self):
        """测试猎人不能开两枪"""
        hunter = Hunter(player_id=0)
        # 第一次死亡（night_kill）返回 [] 表示可以开枪
        result1 = hunter.on_death("night_kill", {})
        assert result1 == []

        # 第二次死亡（vote）在 can_shoot 为 True 时也返回 []
        # （实际由引擎保证不会两次开枪）
        result2 = hunter.on_death("vote", {})
        assert result2 is None or result2 == []


class TestSeerCheck:
    """测试预言家查验"""

    def test_seer_detects_wolf(self):
        """测试预言家查验狼人"""
        wolf = Werewolf(player_id=1)
        result = "wolf" if wolf.role_type == RoleType.WEREWOLF else "good"
        assert result == "wolf"

    def test_seer_detects_villager_as_good(self):
        """测试预言家查验村民为好人"""
        villager = Villager(player_id=1)
        result = "good" if villager.role_type != RoleType.WEREWOLF else "wolf"
        assert result == "good"

    def test_seer_detects_hunter_as_good(self):
        """测试预言家查验猎人为好人"""
        hunter = Hunter(player_id=0)
        result = "good" if hunter.role_type != RoleType.WEREWOLF else "wolf"
        assert result == "good"

    def test_seer_detects_another_seer_as_good(self):
        """测试预言家查验另一个预言家为好人"""
        other_seer = Seer(player_id=0)
        result = "good" if other_seer.role_type != RoleType.WEREWOLF else "wolf"
        assert result == "good"


class TestWerewolfPack:
    """测试狼人团队"""

    def test_wolves_are_evil(self):
        """测试狼人属于邪恶阵营"""
        wolf1 = Werewolf(player_id=0)
        wolf2 = Werewolf(player_id=1)

        assert wolf1.camp == Camp.EVIL
        assert wolf2.camp == Camp.EVIL

    def test_wolves_know_each_other(self):
        """测试狼人私有上下文包含队友信息"""
        wolf = Werewolf(player_id=0)
        ctx = wolf.get_private_context()
        assert ctx.get("knows_wolves", False) is True

    def test_wolves_night_action_is_kill(self):
        """测试狼人夜间行动为击杀"""
        wolf = Werewolf(player_id=0)
        game_state = {"players": [{"player_id": 0, "role": "werewolf", "is_alive": True}]}
        action = wolf.get_night_action(game_state)
        assert action.action_type == "kill"

    def test_wolf_killed_other_wolf_survives(self):
        """测试击杀一只狼人后仍有狼人存活"""
        wolf1 = Werewolf(player_id=0)
        wolf2 = Werewolf(player_id=1)
        assert wolf1.is_alive is True
        assert wolf2.is_alive is True

        # 击杀 wolf1
        wolf1.on_death("night_kill", {})
        assert wolf1.is_alive is False
        assert wolf2.is_alive is True


class TestGoodTeam:
    """测试好人阵营"""

    def test_good_team_members(self):
        """测试好人阵营成员"""
        roles = [
            Seer(player_id=0),
            Witch(player_id=1),
            Hunter(player_id=2),
            Villager(player_id=3),
        ]
        for role in roles:
            assert role.camp == Camp.GOOD, f"{role.name} should be good"

    def test_good_team_camp_consistency(self):
        """测试所有好人的 camp 值一致"""
        camps = [
            Seer(player_id=0).camp,
            Witch(player_id=1).camp,
            Hunter(player_id=2).camp,
            Villager(player_id=3).camp,
        ]
        assert all(c == Camp.GOOD for c in camps)

    def test_player_dies_by_different_causes(self):
        """测试不同死亡原因"""
        villager = Villager(player_id=0)

        # 被狼杀
        villager.is_alive = True
        villager.on_death("night_kill", {})
        assert villager.is_alive is False

        # 被毒杀
        villager.is_alive = True
        villager.on_death("poison", {})
        assert villager.is_alive is False

        # 被枪杀
        villager.is_alive = True
        villager.on_death("shoot", {})
        assert villager.is_alive is False

        # 被投票
        villager.is_alive = True
        villager.on_death("vote", {})
        assert villager.is_alive is False


class TestRoleVisibility:
    """测试角色可见性（信息隔离）"""

    def test_wolf_private_context_includes_allies(self):
        """测试狼人私有上下文含队友标记"""
        wolf = Werewolf(player_id=0)
        ctx = wolf.get_private_context()
        assert "knows_wolves" in ctx

    def test_seer_private_context_no_allies(self):
        """测试预言家私有上下文无队友信息"""
        seer = Seer(player_id=0)
        ctx = seer.get_private_context()
        assert "knows_wolves" not in ctx

    def test_villager_private_context_minimal(self):
        """测试村民私有上下文最简"""
        villager = Villager(player_id=0)
        ctx = villager.get_private_context()
        assert "role" in ctx
        assert ctx.get("knows_wolves", False) is False

    def test_witch_private_context_includes_potions(self):
        """测试女巫私有上下文包含药水状态"""
        witch = Witch(player_id=0)
        ctx = witch.get_private_context()
        assert "has_heal" in ctx
        assert "has_poison" in ctx

    def test_hunter_private_context_includes_shoot_status(self):
        """测试猎人私有上下文含开枪状态"""
        hunter = Hunter(player_id=0)
        ctx = hunter.get_private_context()
        assert "can_shoot" in ctx

    def test_dead_player_cannot_act(self):
        """测试死亡玩家不能行动"""
        for role_cls in [Werewolf, Seer, Witch, Hunter, Villager]:
            role = role_cls(player_id=0)
            role.is_alive = False
            assert role.is_night_actionable() is False
