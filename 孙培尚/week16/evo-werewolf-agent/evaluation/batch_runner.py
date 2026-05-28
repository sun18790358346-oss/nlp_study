"""批量游戏运行器

支持并行运行 N 局游戏，收集原始结果数据。
"""

import asyncio
import json
import os
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

from engine.game_engine import GameEngine, get_role_config, shuffle_roles, ROLE_CONFIGS
from schema.game_record import GameRecord


# 默认决策风格分布
DEFAULT_STYLE_POOL = ["balanced", "cautious", "bold", "random"]


def _assign_styles(num_players: int, style_pool: Optional[List[str]] = None) -> Dict[int, str]:
    """随机分配决策风格给玩家"""
    if style_pool is None:
        style_pool = DEFAULT_STYLE_POOL
    return {i: random.choice(style_pool) for i in range(num_players)}


class GameResult:
    """一局游戏的原始结果"""
    def __init__(self, game_id: str, config_name: str, engine: GameEngine, game_record: GameRecord):
        self.game_id = game_id
        self.config_name = config_name
        self.engine = engine
        self.record = game_record

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典，用于持久化"""
        gs = self.engine.game_state

        # 结构化每个玩家的信息
        players = []
        for p in gs.players:
            info = {
                "player_id": p.player_id,
                "name": p.name,
                "role": p.role_type.value,
                "camp": p.camp.value,
                "is_alive": p.is_alive,
            }
            # 死亡信息
            for death in self.engine.death_records:
                if death["player_id"] == p.player_id:
                    info["death_cause"] = death["cause"]
                    info["death_day"] = death["day"]
                    break
            players.append(info)

        # 从对话中提取角色特定的行动
        seer_checks = []
        witch_actions = []
        hunter_shots = []
        wolf_votes = []
        votes = []
        speeches = []

        for d in gs.dialogues:
            action = d.get("action", "")
            if action == "seer_check":
                seer_checks.append({
                    "day": d.get("day"),
                    "player_id": d.get("player_id"),
                    "target": d.get("target"),
                    "result": d.get("result"),
                    "reasoning": d.get("reasoning", ""),
                })
            elif action in ("heal", "poison"):
                witch_actions.append({
                    "day": d.get("day"),
                    "player_id": d.get("player_id"),
                    "action": action,
                    "target": d.get("target"),
                })
            elif action == "hunter_shot":
                hunter_shots.append({
                    "day": d.get("day"),
                    "player_id": d.get("player_id"),
                    "target": d.get("target"),
                })
            elif action == "night_kill":
                wolf_votes.append({
                    "day": d.get("day"),
                    "player_id": d.get("player_id"),
                    "target": d.get("target"),
                })
            elif action == "vote":
                votes.append({
                    "day": d.get("day"),
                    "player_id": d.get("player_id"),
                    "target": d.get("target"),
                })
            elif action == "speech":
                speeches.append({
                    "day": d.get("day"),
                    "player_id": d.get("player_id"),
                    "content": d.get("content", ""),
                })

        result = {
            "game_id": self.game_id,
            "config_name": self.config_name,
            "winner": self.record.winner,
            "days_played": gs.day_number,
            "total_dialogues": len(gs.dialogues),
            "players": players,
            "seer_checks": seer_checks,
            "witch_actions": witch_actions,
            "hunter_shots": hunter_shots,
            "wolf_votes": wolf_votes,
            "votes": votes,
            "speeches": speeches,
            "role_assignment": self.record.role_assignment,
            "player_styles": self.record.player_styles,
            "start_time": self.record.start_time,
            "end_time": self.record.end_time,
        }
        return result

    def save(self, output_dir: str):
        """保存原始结果到文件"""
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{self.game_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class BatchRunner:
    """批量游戏运行器"""

    def __init__(self, config_name: str = "standard_6",
                 num_games: int = 100,
                 max_concurrent: int = 5,
                 style_pool: Optional[List[str]] = None,
                 output_dir: str = "evaluation/data"):
        self.config_name = config_name
        self.num_games = num_games
        self.max_concurrent = max_concurrent
        self.style_pool = style_pool or DEFAULT_STYLE_POOL
        self.output_dir = output_dir
        self.results: List[GameResult] = []
        self.errors: List[Dict] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _run_single(self, game_index: int) -> Optional[GameResult]:
        """运行一局游戏（带并发控制）"""
        async with self._semaphore:
            return await self._execute_game(game_index)

    async def _execute_game(self, game_index: int) -> Optional[GameResult]:
        """实际执行一局游戏"""
        game_id = f"bench_{self.config_name}_{datetime.now().strftime('%H%M%S')}_{game_index:03d}"
        role_assignment = get_role_config(self.config_name)
        role_assignment = shuffle_roles(role_assignment)
        player_styles = _assign_styles(len(role_assignment), self.style_pool)

        player_names = [f"玩家{i+1}" for i in range(len(role_assignment))]

        engine = GameEngine(player_names, logger=None)
        engine.game_id = game_id

        start_time = time.time()
        try:
            await engine.initialize(role_assignment, player_styles)

            # 使用 step() 循环而非 start()，避免过多 print 和灵活控制
            while not engine.game_state.is_game_over():
                step_result = await engine.step()
                if step_result.get("phase") == "game_over":
                    break
                if step_result.get("phase") == "summary":
                    break

            # 如果游戏没以 game_over 结束（比如 summary 后），检查是否在 day_end 后结束
            if not engine.game_state.is_game_over() and not engine._summaries_done:
                await engine._run_summaries()
                engine._summaries_done = True

        except Exception as e:
            elapsed = time.time() - start_time
            err = {
                "game_index": game_index,
                "game_id": game_id,
                "error": str(e),
                "elapsed_sec": round(elapsed, 2),
                "phase": engine.game_state.phase.value if engine.game_state else "unknown",
            }
            self.errors.append(err)
            print(f"  [FAIL] 第 {game_index+1} 局失败: {e}")
            return None

        elapsed = time.time() - start_time

        # 收集结果
        game_record = GameRecord(
            game_id=game_id,
            start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            config_name=self.config_name,
            role_assignment=role_assignment,
            player_styles=player_styles,
        )
        for death in engine.death_records:
            game_record.add_death(
                player_id=death["player_id"],
                player_name=death["player_name"],
                role=death["role"],
                cause=death["cause"],
                day=death["day"],
            )
        game_record.winner = engine.game_state.get_winner()
        game_record.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = GameResult(game_id, self.config_name, engine, game_record)
        result.save(self.output_dir)

        print(f"  [OK] 第 {game_index+1}/{self.num_games} 局 | "
              f"胜者={result.record.winner} | "
              f"天数={result.record.engine.game_state.day_number if hasattr(result.record, 'engine') else '?'} | "
              f"耗时={elapsed:.1f}s")
        return result

    async def run(self) -> List[GameResult]:
        """运行所有游戏"""
        print(f"{'='*60}")
        print(f"批量评测开始")
        print(f"  配置: {ROLE_CONFIGS.get(self.config_name, {}).get('name', self.config_name)}")
        print(f"  总局数: {self.num_games}")
        print(f"  最大并发: {self.max_concurrent}")
        print(f"  风格池: {self.style_pool}")
        print(f"{'='*60}")
        print()

        start_all = time.time()

        tasks = [self._run_single(i) for i in range(self.num_games)]
        results = await asyncio.gather(*tasks)

        self.results = [r for r in results if r is not None]

        total_elapsed = time.time() - start_all
        success = len(self.results)
        failed = self.num_games - success

        print()
        print(f"{'='*60}")
        print(f"批量运行完成")
        print(f"  成功: {success}/{self.num_games}")
        print(f"  失败: {failed}/{self.num_games}")
        print(f"  总耗时: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")
        print(f"  平均每局: {total_elapsed/max(success, 1):.1f}s")
        print(f"  结果目录: {os.path.abspath(self.output_dir)}")
        print(f"{'='*60}")

        return self.results


def load_results(data_dir: str = "evaluation/data") -> List[Dict]:
    """从数据目录加载所有游戏结果"""
    results = []
    for fname in sorted(os.listdir(data_dir)):
        if fname.endswith(".json"):
            path = os.path.join(data_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                results.append(json.load(f))
    return results
