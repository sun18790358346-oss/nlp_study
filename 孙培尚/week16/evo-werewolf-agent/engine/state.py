"""游戏状态管理"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from engine.player import Player
from engine.phase import GamePhase
from roles.base import RoleType


@dataclass
class GameState:
    """游戏状态

    记录当前游戏的完整状态
    """
    players: List[Player] = field(default_factory=list)
    phase: GamePhase = GamePhase.DAY_START
    day_number: int = 1
    speaker_order: List[int] = field(default_factory=list)  # 发言顺序
    current_speaker: int = 0  # 当前发言者索引
    last_words: List[Dict[str, Any]] = field(default_factory=list)  # 遗言记录
    vote_record: List[Dict[str, Any]] = field(default_factory=list)  # 投票记录
    night_deaths: List[int] = field(default_factory=list)  # 夜晚死亡玩家ID列表
    dialogues: List[Dict[str, Any]] = field(default_factory=list)  # 历史对话记录

    def get_alive_players(self) -> List[Player]:
        """获取存活玩家列表"""
        return [p for p in self.players if p.is_alive]

    def get_player(self, player_id: int) -> Optional[Player]:
        """根据ID获取玩家"""
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    def get_players_by_role(self, role_type: str) -> List[Player]:
        """根据角色类型获取玩家"""
        return [p for p in self.players if p.role_type.value == role_type]

    def get_players_by_camp(self, camp: str) -> List[Player]:
        """根据阵营获取玩家"""
        return [p for p in self.players if p.camp.value == camp]

    def is_game_over(self) -> bool:
        """判断游戏是否结束"""
        alive_players = self.get_alive_players()
        if not alive_players:
            return True

        # 检查狼人是否全部死亡（好人胜利）
        alive_wolves = [p for p in alive_players if p.role_type.value == "werewolf"]
        if not alive_wolves:
            return True

        # 检查好人是否全部死亡（狼人胜利）
        alive_good = [p for p in alive_players if p.camp.value == "good"]
        if not alive_good:
            return True

        return False

    def get_winner(self) -> Optional[str]:
        """获取胜利方"""
        if not self.is_game_over():
            return None

        alive_players = self.get_alive_players()
        alive_wolves = [p for p in alive_players if p.role_type.value == "werewolf"]

        if not alive_wolves:
            return "good"  # 好人胜利
        else:
            return "evil"  # 狼人胜利

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于给AI代理提供上下文"""
        return {
            "day_number": self.day_number,
            "phase": self.phase.value,
            "players": [p.to_dict() for p in self.players],
            "alive_players": [p.player_id for p in self.get_alive_players()],
            "speaker_order": self.speaker_order,
            "current_speaker": self.current_speaker,
            "last_words": self.last_words,
            "vote_record": self.vote_record,
            "night_deaths": self.night_deaths,
        }

    def get_public_context(self) -> Dict[str, Any]:
        """获取公开上下文（所有玩家都能看到的信息）"""
        return {
            "day_number": self.day_number,
            "phase": self.phase.value,
            "alive_players": [
                {"player_id": p.player_id, "name": p.name}
                for p in self.get_alive_players()
            ],
            "last_words": self.last_words,
            "vote_record": self.vote_record,
            "night_deaths": self.night_deaths,
            "dialogues": self.dialogues,  # 历史对话记录
        }

    def get_player_private_context(self, player_id: int) -> Dict[str, Any]:
        """获取某个玩家的私有上下文（只有该玩家能看到的信息）"""
        player = self.get_player(player_id)
        if not player:
            return {}

        public_ctx = self.get_public_context()
        private_ctx = player.role.get_private_context()

        # 过滤历史对话：根据角色决定能看到哪些对话
        visible_dialogues = self._filter_visible_dialogues(player)

        return {
            **public_ctx,
            **private_ctx,
            "dialogues": visible_dialogues,  # 使用过滤后的对话历史
            "other_players": [
                {
                    "player_id": p.player_id,
                    "name": p.name,
                    "is_alive": p.is_alive,
                    "is_sheriff": p.is_sheriff,
                }
                for p in self.players if p.player_id != player_id
            ],
        }

    def _filter_visible_dialogues(self, player: Player) -> List[Dict[str, Any]]:
        """根据玩家角色过滤可见的历史对话

        公开对话（所有人可见）：公开演讲、投票
        私有对话（仅本人可见）：夜间行动决策及原因
        """
        visible = []
        for d in self.dialogues:
            # 公开对话：所有人都能看到
            if d["phase"] in ["公开演讲", "投票"]:
                visible.append(d)
            # 私有对话：只有本人能看到
            elif d["player_id"] == player.player_id:
                visible.append(d)
            # 狼人可以看到队友的决策
            elif d["action"] == "night_kill" and player.role_type == RoleType.WEREWOLF:
                # 检查是否同为狼人
                target_player = self.get_player(d["player_id"])
                if target_player and target_player.role_type == RoleType.WEREWOLF:
                    visible.append(d)

        return visible

    def add_last_words(self, player_id: int, words: str):
        """添加遗言"""
        self.last_words.append({
            "player_id": player_id,
            "words": words,
            "day": self.day_number,
        })

    def add_vote(self, voter_id: int, target_id: int):
        """添加投票记录"""
        self.vote_record.append({
            "voter_id": voter_id,
            "target_id": target_id,
            "day": self.day_number,
        })

    def reset_vote_record(self):
        """重置投票记录"""
        self.vote_record = []

    def next_speaker(self):
        """切换到下一个发言者"""
        if self.speaker_order:
            self.current_speaker = (self.current_speaker + 1) % len(self.speaker_order)

    def set_speaker_order(self, order: List[int]):
        """设置发言顺序"""
        self.speaker_order = order
        self.current_speaker = 0

    def clear_night_deaths(self):
        """清除夜晚死亡记录"""
        self.night_deaths = []

    def add_night_death(self, player_id: int):
        """添加夜晚死亡"""
        self.night_deaths.append(player_id)