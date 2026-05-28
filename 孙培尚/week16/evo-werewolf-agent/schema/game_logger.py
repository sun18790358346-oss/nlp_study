"""游戏运行日志模块

记录每次比赛的完整运行过程，包括：
- 游戏初始化信息
- 每个阶段的详细执行日志
- 错误和异常记录
- 调试信息
"""

import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class LogLevel(BaseModel):
    """日志级别配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_to_file: bool = True
    log_to_console: bool = True


class PhaseLog(BaseModel):
    """阶段日志"""
    day: int
    phase: str
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[int] = None
    events: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class GameRunLog(BaseModel):
    """游戏运行日志"""
    game_id: str
    start_time: str
    end_time: Optional[str] = None
    config_name: str = ""
    role_assignment: Dict[int, str] = Field(default_factory=dict)
    player_styles: Dict[int, str] = Field(default_factory=dict)
    phase_logs: list[PhaseLog] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def add_phase(self, day: int, phase: str) -> PhaseLog:
        """开始新阶段"""
        phase_log = PhaseLog(
            day=day,
            phase=phase,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.phase_logs.append(phase_log)
        return phase_log

    def add_event(self, phase_log: PhaseLog, event: str):
        """添加事件"""
        phase_log.events.append(event)

    def add_error(self, error: str):
        """添加错误"""
        self.errors.append(error)

    def finish_phase(self, phase_log: PhaseLog):
        """结束阶段"""
        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        phase_log.end_time = end_time
        # 计算耗时
        start = datetime.fromisoformat(phase_log.start_time)
        end = datetime.fromisoformat(end_time)
        phase_log.duration_ms = int((end - start).total_seconds() * 1000)

    def save(self, output_dir: str = "logs"):
        """保存日志"""
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{self.game_id}_run_log.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)


class GameLogger:
    """游戏运行日志记录器"""

    def __init__(self, game_id: str, config_name: str,
                 role_assignment: dict, player_styles: dict,
                 log_level: str = "INFO"):
        self.game_id = game_id
        self.config_name = config_name
        self.role_assignment = role_assignment
        self.player_styles = player_styles
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

        self.game_run_log = GameRunLog(
            game_id=game_id,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            config_name=config_name,
            role_assignment=role_assignment,
            player_styles=player_styles,
        )

        self.current_phase: Optional[PhaseLog] = None
        self._setup_logger()

    def _setup_logger(self):
        """设置 Python logger"""
        self.logger = logging.getLogger(f"game_{self.game_id}")
        self.logger.setLevel(self.log_level)

        # 避免重复添加 handler
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_format)
            self.logger.addHandler(console_handler)

    def start_phase(self, day: int, phase: str):
        """开始一个阶段"""
        self.logger.info(f"[第{day}天-{phase}] 阶段开始")
        self.current_phase = self.game_run_log.add_phase(day, phase)
        return self.current_phase

    def end_phase(self):
        """结束当前阶段"""
        if self.current_phase:
            self.game_run_log.finish_phase(self.current_phase)
            duration = self.current_phase.duration_ms
            self.logger.info(
                f"[{self.current_phase.phase}] 阶段结束, 耗时: {duration}ms"
            )
            self.current_phase = None

    def log_event(self, event: str):
        """记录一般事件"""
        self.logger.info(event)

    def info(self, msg: str):
        """记录信息级别日志"""
        self.logger.info(msg)

    def debug(self, msg: str):
        """记录调试级别日志"""
        self.logger.debug(msg)

    def warning(self, msg: str):
        """记录警告级别日志"""
        self.logger.warning(msg)

    def error(self, msg: str):
        """记录错误级别日志"""
        self.logger.error(msg)
        if self.current_phase:
            self.game_run_log.add_event(self.current_phase, msg)

    def log_action_event(self, event: str):
        """记录玩家动作"""
        self.logger.info(event)
        if self.current_phase:
            self.game_run_log.add_event(self.current_phase, f"[动作] {event}")

    def log_speech_event(self, event: str):
        """记录发言"""
        self.logger.info(event)
        if self.current_phase:
            self.game_run_log.add_event(self.current_phase, f"[发言] {event}")

    def log_vote_event(self, event: str):
        """记录投票"""
        self.logger.info(event)
        if self.current_phase:
            self.game_run_log.add_event(self.current_phase, f"[投票] {event}")

    def log_death_event(self, event: str):
        """记录死亡"""
        self.logger.info(event)
        if self.current_phase:
            self.game_run_log.add_event(self.current_phase, f"[死亡] {event}")

    def log_night_action_event(self, event: str):
        """记录夜间行动"""
        self.logger.info(event)
        if self.current_phase:
            self.game_run_log.add_event(self.current_phase, f"[夜行动] {event}")

    def log_action(self, player_id: int, action: str, target: Optional[int] = None):
        """记录玩家动作"""
        target_str = f", 目标: {target}" if target is not None else ""
        event = f"玩家{player_id}: {action}{target_str}"
        self.log_event(event)

    def log_speech(self, player_id: int, player_name: str, content: str):
        """记录发言"""
        # 截断过长的发言内容
        preview = content[:50] + "..." if len(content) > 50 else content
        event = f"玩家{player_id}({player_name}) 发言: {preview}"
        self.log_event(event)

    def log_vote(self, voter_id: int, target_id: int):
        """记录投票"""
        event = f"玩家{voter_id} 投票给 玩家{target_id}"
        self.log_event(event)

    def log_death(self, player_id: int, player_name: str, role: str, cause: str):
        """记录死亡"""
        event = f"玩家{player_id}({player_name}, {role}) 死亡, 原因: {cause}"
        self.log_event(event)

    def log_night_action(self, player_id: int, action_type: str, target: Optional[int] = None):
        """记录夜间行动"""
        target_str = f", 目标: {target}" if target is not None else ""
        event = f"玩家{player_id} 夜间行动: {action_type}{target_str}"
        self.log_event(event)

    def log_error(self, error: str):
        """记录错误"""
        self.logger.error(error)
        self.game_run_log.add_error(error)

    def finish(self):
        """结束日志记录"""
        self.game_run_log.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info("游戏结束")
        self.game_run_log.save("logs")

    def summary(self) -> str:
        """生成日志摘要"""
        lines = [
            f"游戏ID: {self.game_id}",
            f"开始时间: {self.game_run_log.start_time}",
            f"结束时间: {self.game_run_log.end_time}",
            f"配置: {self.config_name}",
            "",
            f"阶段数: {len(self.game_run_log.phase_logs)}",
            f"错误数: {len(self.game_run_log.errors)}",
        ]
        return "\n".join(lines)