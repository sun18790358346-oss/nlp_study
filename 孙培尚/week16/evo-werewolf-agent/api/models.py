"""API 请求/响应模型"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CreateGameRequest(BaseModel):
    """创建游戏请求"""
    config_name: str = "standard_6"
    player_names: Optional[List[str]] = None
    shuffle: bool = True
    player_styles: Optional[Dict[int, str]] = None


class StepResponse(BaseModel):
    """一步执行响应"""
    phase: str
    day_number: int
    step_data: Dict[str, Any] = Field(default_factory=dict)
    players: List[Dict[str, Any]] = Field(default_factory=list)
    dialogues: List[Dict[str, Any]] = Field(default_factory=list)
    deaths: List[Dict[str, Any]] = Field(default_factory=list)
    is_game_over: bool = False
    winner: Optional[str] = None
    summaries: List[Dict[str, Any]] = Field(default_factory=list)


class GameStatusResponse(BaseModel):
    """游戏状态响应"""
    game_id: str
    phase: str
    day_number: int
    players: List[Dict[str, Any]] = Field(default_factory=list)
    dialogues: List[Dict[str, Any]] = Field(default_factory=list)
    death_records: List[Dict[str, Any]] = Field(default_factory=list)
    winner: Optional[str] = None
    is_game_over: bool = False
    config_name: str = ""
    summaries: List[Dict[str, Any]] = Field(default_factory=list)


class GameSummaryResponse(BaseModel):
    """游戏摘要响应"""
    game_id: str
    phase: str
    day_number: int
    alive_count: int
    is_game_over: bool
    summaries: List[Dict[str, Any]] = Field(default_factory=list)


class ConfigInfo(BaseModel):
    """配置信息"""
    name: str
    description: str
    player_count: int
