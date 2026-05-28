"""预言家角色实现。

阵营：善良阵营
胜利条件：消灭所有狼人
夜间行动：每晚查验一名玩家，返回"好人"或"狼人"
"""

from typing import Optional, Dict, Any
from roles.base import BaseRole, RoleType, Camp, NightAction


class Seer(BaseRole):
    """Seer role - belongs to good camp.

    Win Condition: Eliminate all wolves.
    Night Action: Check one player per night, returns "good" or "wolf" only.
    """

    @property
    def role_type(self) -> RoleType:
        return RoleType.SEER

    @property
    def camp(self) -> Camp:
        return Camp.GOOD

    def is_night_actionable(self) -> bool:
        """Seer acts during night phase."""
        return self._is_alive

    def get_night_action(self, game_state: Dict[str, Any]) -> Optional[NightAction]:
        """Get seer check target.

        Returns the check result as metadata (game engine will validate and reveal).
        """
        return NightAction(
            action_type="check",
            target=None,  # Agent will decide target
            metadata={}
        )

    def get_private_context(self) -> Dict[str, Any]:
        ctx = super().get_private_context()
        ctx["note"] = "You are the Seer. You can check one player each night to see if they are a wolf."
        return ctx

    def check_win(self, game_state: Dict[str, Any]) -> bool:
        """Good camp wins when all wolves eliminated."""
        players = game_state.get("players", [])

        # Good wins when no wolves alive
        alive_wolves = [
            p for p in players
            if p.get("role") == RoleType.WEREWOLF.value and p.get("is_alive")
        ]

        return len(alive_wolves) == 0