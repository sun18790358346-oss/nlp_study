"""女巫角色实现。

阵营：善良阵营
胜利条件：消灭所有狼人
夜间行动：
    - 有一瓶救人药（复活今晚死亡的人）和一瓶毒药（杀死任意玩家）
    - 各只能使用一次
    - 不能救自己
    - 同一晚上不能同时使用
"""

from typing import Optional, Dict, Any
from roles.base import BaseRole, RoleType, Camp, NightAction


class Witch(BaseRole):
    """Witch role - belongs to good camp.

    Win Condition: Eliminate all wolves.
    Night Actions:
        - Has one heal (resurrect tonight's death) and one poison (kill any player)
        - Each usable once
        - Cannot heal self
        - Cannot use both same night
    """

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self._has_heal = True
        self._has_poison = True
        self._used_heal = False
        self._used_poison = False

    @property
    def role_type(self) -> RoleType:
        return RoleType.WITCH

    @property
    def camp(self) -> Camp:
        return Camp.GOOD

    @property
    def has_heal(self) -> bool:
        return self._has_heal and not self._used_heal

    @property
    def has_poison(self) -> bool:
        return self._has_poison and not self._used_poison

    def is_night_actionable(self) -> bool:
        """Witch acts during night phase if has any usable potion."""
        return self._is_alive and (self.has_heal or self.has_poison)

    def get_night_action(self, game_state: Dict[str, Any]) -> Optional[NightAction]:
        """Get witch action (heal or poison).

        The witch sees tonight's death victim and decides whether to save/poison.
        """
        tonight_death = game_state.get("tonight_death")  # player_id who will die tonight

        return NightAction(
            action_type="witch",
            target=None,
            metadata={
                "has_heal": self.has_heal,
                "has_poison": self.has_poison,
                "tonight_death": tonight_death,
                "can_heal_self": tonight_death != self.player_id if tonight_death else True,
            }
        )

    def use_heal(self):
        """Mark heal as used."""
        self._used_heal = True

    def use_poison(self):
        """Mark poison as used."""
        self._used_poison = True

    def get_private_context(self) -> Dict[str, Any]:
        ctx = super().get_private_context()
        ctx.update({
            "has_heal": self.has_heal,
            "has_poison": self.has_poison,
            "note": "You are the Witch. You have one heal and one poison. Heal saves tonight's death. Poison kills any player."
        })
        return ctx

    def check_win(self, game_state: Dict[str, Any]) -> bool:
        """Good camp wins when all wolves eliminated."""
        players = game_state.get("players", [])

        alive_wolves = [
            p for p in players
            if p.get("role") == RoleType.WEREWOLF.value and p.get("is_alive")
        ]

        return len(alive_wolves) == 0