"""村民角色实现。

阵营：善良阵营
胜利条件：消灭所有狼人
夜间行动：无（整晚睡觉）
"""

from typing import Dict, Any
from roles.base import BaseRole, RoleType, Camp


class Villager(BaseRole):
    """Villager role - belongs to good camp.

    Win Condition: Eliminate all wolves.
    Night Action: None (sleeps through the night).
    """

    @property
    def role_type(self) -> RoleType:
        return RoleType.VILLAGER

    @property
    def camp(self) -> Camp:
        return Camp.GOOD

    def is_night_actionable(self) -> bool:
        """Villagers cannot act at night."""
        return False

    def get_private_context(self) -> Dict[str, Any]:
        ctx = super().get_private_context()
        ctx["note"] = "You are a Villager. You have no special abilities. Use your reasoning to find wolves."
        return ctx

    def check_win(self, game_state: Dict[str, Any]) -> bool:
        """Good camp wins when all wolves eliminated."""
        players = game_state.get("players", [])

        alive_wolves = [
            p for p in players
            if p.get("role") == RoleType.WEREWOLF.value and p.get("is_alive")
        ]

        return len(alive_wolves) == 0