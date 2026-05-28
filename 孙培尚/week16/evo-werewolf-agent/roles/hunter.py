"""猎人角色实现。

阵营：善良阵营
胜利条件：消灭所有狼人
被动技能：夜晚被杀或白天被投票出局时，可在死前开枪带走一人
特殊：如果被女巫毒杀，无法开枪（技能锁定）
"""

from typing import Optional, List, Dict, Any
from roles.base import BaseRole, RoleType, Camp


class Hunter(BaseRole):
    """Hunter role - belongs to good camp.

    Win Condition: Eliminate all wolves.
    Passive Ability: When killed at night or voted during day, can shoot one player before dying.
    Special: If poisoned by witch, cannot shoot (skill locked).
    """

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self._can_shoot = True  # Locked if poisoned

    @property
    def role_type(self) -> RoleType:
        return RoleType.HUNTER

    @property
    def camp(self) -> Camp:
        return Camp.GOOD

    @property
    def can_shoot(self) -> bool:
        return self._can_shoot

    def lock_shoot(self):
        """Lock hunter's ability (when poisoned)."""
        self._can_shoot = False

    def on_death(self, cause: str, game_state: Dict[str, Any]) -> Optional[List[int]]:
        """Hunter can shoot one player when dying (unless poisoned).

        Args:
            cause: "night_kill", "vote", "shoot", "poison"
            game_state: Current game state

        Returns:
            List of player IDs to be shot, or None
        """
        self._is_alive = False

        # If poisoned, cannot shoot
        if cause == "poison":
            self._can_shoot = False
            return None

        # Can shoot if killed by night kill or vote
        if cause in ("night_kill", "vote") and self._can_shoot:
            # Hunter's shoot target will be determined by agent
            return []  # Empty list means hunter wants to shoot, target TBD

        return None

    def get_shoot_target(self, game_state: Dict[str, Any]) -> int:
        """Get hunter's shoot target.

        This is called after on_death returns an non-empty list.
        Returns player_id to shoot.
        """
        # Agent will decide target
        return -1

    def get_private_context(self) -> Dict[str, Any]:
        ctx = super().get_private_context()
        ctx.update({
            "can_shoot": self._can_shoot,
            "note": "You are the Hunter. When you die (unless poisoned), you can shoot one player."
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