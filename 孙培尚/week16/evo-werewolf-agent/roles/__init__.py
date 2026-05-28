"""Role definitions for Werewolf game."""

from roles.base import BaseRole, RoleType, Camp
from roles.werewolf import Werewolf
from roles.seer import Seer
from roles.witch import Witch
from roles.hunter import Hunter
from roles.villager import Villager

__all__ = [
    "BaseRole",
    "RoleType",
    "Camp",
    "Werewolf",
    "Seer",
    "Witch",
    "Hunter",
    "Villager",
]