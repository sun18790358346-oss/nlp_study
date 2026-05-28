"""玩家数据结构"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from roles.base import BaseRole, RoleType, Camp
from agents import Agent


@dataclass
class Player:
    """游戏中的玩家

    包含玩家的角色信息和AI代理
    """
    player_id: int
    role: BaseRole
    agent: Optional[Agent] = None  # 玩家控制的AI代理
    name: str = ""  # 玩家名称

    @property
    def role_type(self) -> RoleType:
        return self.role.role_type

    @property
    def camp(self) -> Camp:
        return self.role.camp

    @property
    def is_alive(self) -> bool:
        return self.role.is_alive

    @property
    def is_sheriff(self) -> bool:
        return self.role.is_sheriff

    @is_sheriff.setter
    def is_sheriff(self, value: bool):
        self.role.is_sheriff = value

    def kill(self, cause: str, game_state: Dict[str, Any]) -> Optional[list]:
        """玩家死亡，返回死亡时触发的技能影响（如猎人的枪）"""
        return self.role.on_death(cause, game_state)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于游戏状态展示"""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role.role_type.value,
            "camp": self.role.camp.value,
            "is_alive": self.role.is_alive,
            "is_sheriff": self.role.is_sheriff,
        }

    def __repr__(self):
        status = "alive" if self.is_alive else "dead"
        sheriff = " (sheriff)" if self.is_sheriff else ""
        return f"Player({self.player_id}, {self.role.name}, {status}{sheriff})"