"""游戏记录数据结构"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DialogueRecord(BaseModel):
    """对话记录"""
    day: int
    phase: str
    player_id: int
    player_name: str
    role: str
    decision_style: Optional[str] = None
    action: str
    content: Optional[str] = None
    target: Optional[int] = None
    reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class DeathRecord(BaseModel):
    """死亡记录"""
    player_id: int
    player_name: str
    role: str
    cause: str
    day: int


class GameRecord(BaseModel):
    """游戏记录"""
    game_id: str
    start_time: str
    end_time: Optional[str] = None
    config_name: str = ""
    role_assignment: Dict[int, str] = Field(default_factory=dict)
    player_styles: Dict[int, str] = Field(default_factory=dict)
    dialogues: List[DialogueRecord] = Field(default_factory=list)
    winner: Optional[str] = None
    death_order: List[DeathRecord] = Field(default_factory=list)

    def add_dialogue(self, dialogue: DialogueRecord):
        self.dialogues.append(dialogue)

    def add_dialogue_from_dict(self, dialogue: Dict[str, Any]):
        """从字典添加对话记录"""
        self.dialogues.append(DialogueRecord(**dialogue))

    def add_death(self, player_id: int, player_name: str, role: str, cause: str, day: int):
        self.death_order.append(DeathRecord(
            player_id=player_id,
            player_name=player_name,
            role=role,
            cause=cause,
            day=day,
        ))

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    def save(self, output_dir: str = "logs"):
        import os
        import json
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{self.game_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"游戏记录已保存至: {file_path}")

    def summary(self) -> str:
        from agent.player_agent import DECISION_STYLES

        lines = [
            f"游戏ID: {self.game_id}",
            f"开始时间: {self.start_time}",
            f"结束时间: {self.end_time}",
            f"胜利方: {'好人阵营' if self.winner == 'good' else '狼人阵营'}",
            f"总对话数: {len(self.dialogues)}",
            "",
            "玩家配置:",
        ]
        for pid, style in self.player_styles.items():
            role = self.role_assignment.get(pid, "unknown")
            style_name = DECISION_STYLES.get(style, {}).get("name", style)
            lines.append(f"  玩家{pid+1}: {role} ({style_name})")

        lines.append("")
        lines.append("死亡顺序:")
        for death in self.death_order:
            if isinstance(death, dict):
                lines.append(f"  第{death['day']}天: {death['player_name']}({death['role']}) - {death['cause']}")
            else:
                lines.append(f"  第{death.day}天: {death.player_name}({death.role}) - {death.cause}")

        return "\n".join(lines)