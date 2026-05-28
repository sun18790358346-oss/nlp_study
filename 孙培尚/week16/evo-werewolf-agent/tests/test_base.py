"""测试角色基类"""

from roles.base import BaseRole, RoleType, Camp, NightAction, VoteAction


class MockRole(BaseRole):
    """模拟角色用于测试基类"""

    @property
    def role_type(self) -> RoleType:
        return RoleType.VILLAGER

    @property
    def camp(self) -> Camp:
        return Camp.GOOD

    def check_win(self, game_state):
        return False


class TestBaseRole:
    """测试 BaseRole 基类"""

    def test_init(self):
        """测试初始化"""
        role = MockRole(player_id=1)
        assert role.player_id == 1
        assert role.is_alive is True
        assert role.is_sheriff is False

    def test_is_alive_setter(self):
        """测试存活状态设置"""
        role = MockRole(player_id=1)
        role.is_alive = False
        assert role.is_alive is False

    def test_is_sheriff_setter(self):
        """测试警长状态设置"""
        role = MockRole(player_id=1)
        role.is_sheriff = True
        assert role.is_sheriff is True

    def test_name(self):
        """测试角色名称"""
        role = MockRole(player_id=1)
        assert role.name == "Villager"

    def test_is_night_actionable_default(self):
        """测试默认夜间行动能力"""
        role = MockRole(player_id=1)
        assert role.is_night_actionable() is False

    def test_get_night_action_default(self):
        """测试默认夜间行动返回 None"""
        role = MockRole(player_id=1)
        assert role.get_night_action({}) is None

    def test_can_speak_when_alive(self):
        """测试存活时可以发言"""
        role = MockRole(player_id=1)
        assert role.can_speak() is True

    def test_can_speak_when_dead(self):
        """测试死亡后不能发言"""
        role = MockRole(player_id=1)
        role.is_alive = False
        assert role.can_speak() is False

    def test_can_vote_when_alive(self):
        """测试存活时可以投票"""
        role = MockRole(player_id=1)
        assert role.can_vote() is True

    def test_can_vote_when_dead(self):
        """测试死亡后不能投票"""
        role = MockRole(player_id=1)
        role.is_alive = False
        assert role.can_vote() is False

    def test_get_speech_default(self):
        """测试默认发言为空字符串"""
        role = MockRole(player_id=1)
        assert role.get_speech({}) == ""

    def test_get_vote_target_default(self):
        """测试默认投票目标返回 None"""
        role = MockRole(player_id=1)
        assert role.get_vote_target({}) is None

    def test_on_death_sets_alive_false(self):
        """测试死亡时设置存活状态为 False"""
        role = MockRole(player_id=1)
        role.on_death("vote", {})
        assert role.is_alive is False

    def test_get_private_context(self):
        """测试私有上下文"""
        role = MockRole(player_id=1)
        ctx = role.get_private_context()
        assert ctx["role"] == "Villager"
        assert ctx["player_id"] == 1
        assert ctx["camp"] == "good"

    def test_repr_alive(self):
        """测试存活状态的字符串表示"""
        role = MockRole(player_id=1)
        assert "alive" in repr(role)
        assert "player_id=1" in repr(role)

    def test_repr_dead(self):
        """测试死亡状态的字符串表示"""
        role = MockRole(player_id=1)
        role.is_alive = False
        assert "dead" in repr(role)

    def test_repr_sheriff(self):
        """测试警长状态的字符串表示"""
        role = MockRole(player_id=1)
        role.is_sheriff = True
        assert "sheriff" in repr(role)


class TestRoleType:
    """测试角色类型枚举"""

    def test_all_roles_defined(self):
        """测试所有角色类型都已定义"""
        assert RoleType.WEREWOLF.value == "werewolf"
        assert RoleType.SEER.value == "seer"
        assert RoleType.WITCH.value == "witch"
        assert RoleType.HUNTER.value == "hunter"
        assert RoleType.VILLAGER.value == "villager"


class TestCamp:
    """测试阵营枚举"""

    def test_good_camp(self):
        """测试善良阵营"""
        assert Camp.GOOD.value == "good"

    def test_evil_camp(self):
        """测试邪恶阵营"""
        assert Camp.EVIL.value == "evil"


class TestNightAction:
    """测试夜间行动数据类"""

    def test_create_night_action(self):
        """测试创建夜间行动"""
        action = NightAction(action_type="kill", target=1)
        assert action.action_type == "kill"
        assert action.target == 1

    def test_night_action_with_metadata(self):
        """测试带元数据的夜间行动"""
        action = NightAction(
            action_type="check",
            target=2,
            metadata={"allies": [3, 4]}
        )
        assert action.metadata["allies"] == [3, 4]


class TestVoteAction:
    """测试投票行动数据类"""

    def test_create_vote_action(self):
        """测试创建投票行动"""
        action = VoteAction(target=1)
        assert action.target == 1