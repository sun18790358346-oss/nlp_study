"""游戏引擎模块

包含游戏状态管理、阶段控制、玩家数据结构和游戏引擎
"""

from engine.state import GameState
from engine.phase import GamePhase, TurnOrder
from engine.player import Player
from engine.game_engine import (
    GameEngine,
    create_game,
    run_game,
    get_role_config,
    shuffle_roles,
    create_random_roles,
    ROLE_CONFIGS,
    STANDARD_6P_ROLES,
)

__all__ = [
    "GameState",
    "GamePhase",
    "TurnOrder",
    "Player",
    "GameEngine",
    "create_game",
    "run_game",
    "get_role_config",
    "shuffle_roles",
    "create_random_roles",
    "ROLE_CONFIGS",
    "STANDARD_6P_ROLES",
]