"""狼人杀游戏演示

展示带有决策风格的AI玩家对战，所有决策和发言都会被记录用于分析和学习。

支持游戏控制功能：
- 每局游戏开始前可选择：执行(e)、跳过(s)、逐天执行(d)、退出(q)
- 逐天执行时每天开始前询问是否继续

Usage:
    python main_demo.py                          # 默认运行
    python main_demo.py -c simple_4             # 使用4人局配置
    python main_demo.py --no-shuffle            # 不打乱角色
    python main_demo.py -s '{"0":"bold"}'       # 自定义风格
    python main_demo.py -i                      # 交互模式（每步询问）
    python main_demo.py --day-by-day            # 逐天模式（每天询问）
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from agent.player_agent import create_player_agent
from engine.game_engine import GameEngine, get_role_config, shuffle_roles
from schema.game_record import GameRecord
from schema.game_logger import GameLogger


class GameController:
    """游戏控制器，支持手动控制游戏流程"""

    MODE_AUTO = "auto"        # 自动执行
    MODE_DAY_BY_DAY = "day"   # 逐天执行
    MODE_INTERACTIVE = "interactive"  # 完全交互

    def __init__(self, mode: str = MODE_AUTO):
        self.mode = mode
        self._action = "continue"  # continue, skip_to_end, stop

    async def wait_if_needed(self, day_number: int, phase: str) -> str:
        """根据模式决定是否需要等待用户输入"""
        if self.mode == self.MODE_AUTO:
            return "continue"

        if self.mode == self.MODE_DAY_BY_DAY and phase != "day_start":
            return "continue"

        if phase == "night":
            return "continue"

        print(f"\n--- 当前: 第{day_number}天 {phase} ---")
        print("[Enter] 继续  [s]跳过至结束  [q]退出")
        inp = await asyncio.get_event_loop().run_in_executor(
            None, lambda: input("请输入: ").strip().lower()
        )

        if inp == "s":
            return "skip_to_end"
        elif inp == "q":
            return "stop"
        else:
            return "continue"


async def run_demo(
    config_name: str = "standard_6",
    player_styles: Optional[dict] = None,
    shuffle: bool = True,
    save_record: bool = True,
    log_level: str = "INFO",
    control_mode: str = GameController.MODE_AUTO,
):
    """运行演示游戏"""
    if player_styles is None:
        player_styles = {
            0: "bold",
            1: "cautious",
            2: "balanced",
            3: "cautious",
            4: "bold",
            5: "random",
        }

    game_id = f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    role_assignment = get_role_config(config_name)

    if shuffle:
        role_assignment = shuffle_roles(role_assignment)

    # 创建日志记录器
    logger = GameLogger(
        game_id=game_id,
        config_name=config_name,
        role_assignment=role_assignment,
        player_styles=player_styles,
        log_level=log_level,
    )
    logger.log_event(f"游戏初始化，配置: {config_name}")

    # 创建游戏记录
    game_record = GameRecord(
        game_id=game_id,
        start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        config_name=config_name,
        role_assignment=role_assignment,
        player_styles=player_styles,
    )

    # 初始化游戏引擎（传入logger）
    player_names = [f"玩家{i+1}" for i in range(len(role_assignment))]
    engine = GameEngine(player_names, logger=logger)
    engine.game_id = game_id  # 用于总结经验时记录 game_id

    # 使用引擎的initialize方法（避免重复初始化逻辑）
    await engine.initialize(role_assignment, player_styles)

    # 初始化日志中的玩家信息
    for player_id, name in enumerate(player_names):
        role_type = role_assignment.get(player_id, "villager")
        role_name = {"werewolf": "狼人", "seer": "预言家", "witch": "女巫",
                     "hunter": "猎人", "villager": "村民"}.get(role_type, role_type)
        style = player_styles.get(player_id, "balanced")
        logger.log_event(f"玩家{player_id} {name} 加入游戏，角色: {role_name}, 风格: {style}")

    print("=" * 60)
    print(f"狼人杀游戏演示 - {get_role_config(config_name).get('name', config_name)}")
    print("=" * 60)
    print(f"游戏ID: {game_id}")
    print(f"角色分配: {role_assignment}")
    print(f"决策风格: {player_styles}")
    print(f"控制模式: {control_mode}")
    print("=" * 60)

    # 设置游戏控制器
    controller = GameController(control_mode)

    # 启动游戏（传入控制器）
    await engine.start(controller=controller)

    # 更新游戏记录
    for d in engine.game_state.dialogues:
        game_record.add_dialogue_from_dict(d)
    for death in engine.death_records:
        game_record.add_death(
            player_id=death["player_id"],
            player_name=death["player_name"],
            role=death["role"],
            cause=death["cause"],
            day=death["day"]
        )
    game_record.winner = engine.game_state.get_winner()
    game_record.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if save_record:
        game_record.save("logs")
        logger.log_event("游戏记录已保存")

    # 完成日志记录
    logger.finish()

    print("\n" + "=" * 60)
    print("游戏摘要")
    print("=" * 60)
    print(game_record.summary())

    return game_record


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="狼人杀游戏演示")
    parser.add_argument("--config", "-c", default="standard_6",
                        choices=["standard_6", "simple_4", "big_9"],
                        help="角色配置")
    parser.add_argument("--no-shuffle", action="store_true",
                        help="不打乱角色分配")
    parser.add_argument("--styles", "-s", type=str, default=None,
                        help="玩家风格配置，JSON格式")
    parser.add_argument("--log-level", "-l", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="日志级别")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="交互模式（每步询问）")
    parser.add_argument("--day-by-day", "-d", action="store_true",
                        help="逐天模式（每天开始前询问）")

    args = parser.parse_args()

    player_styles = None
    if args.styles:
        try:
            player_styles = json.loads(args.styles)
        except json.JSONDecodeError:
            print("警告: 无效的JSON格式，使用默认风格配置")

    # 确定控制模式
    if args.interactive:
        control_mode = GameController.MODE_INTERACTIVE
    elif args.day_by_day:
        control_mode = GameController.MODE_DAY_BY_DAY
    else:
        control_mode = GameController.MODE_AUTO

    record = await run_demo(
        config_name=args.config,
        player_styles=player_styles,
        shuffle=not args.no_shuffle,
        log_level=args.log_level,
        control_mode=control_mode,
    )

    return record


if __name__ == "__main__":
    asyncio.run(main())
