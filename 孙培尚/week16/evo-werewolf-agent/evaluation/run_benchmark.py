"""狼人杀多智能体评测系统 — 主入口

批量运行游戏 → 计算指标 → 生成 Leaderboard 报告

Usage:
    # 默认：标准6人局，50局，并发5
    python -m evaluation.run_benchmark

    # 自定义
    python -m evaluation.run_benchmark --config standard_6 --games 100 --concurrent 8

    # 仅从已有数据生成报告（不跑新游戏）
    python -m evaluation.run_benchmark --report-only

    # 简易4人局（更快）
    python -m evaluation.run_benchmark --config simple_4 --games 50
"""

import asyncio
import argparse
import os
import sys

# 确保项目根在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.batch_runner import BatchRunner, load_results
from evaluation.metrics import compute_all_metrics
from evaluation.report import generate_leaderboard_html


DATA_DIR = "evaluation/data"
REPORT_PATH = "evaluation/leaderboard.html"


async def run_benchmark(config_name: str, num_games: int, max_concurrent: int,
                        style_pool: list):
    """完整流程：运行 → 评测 → 报告"""
    runner = BatchRunner(
        config_name=config_name,
        num_games=num_games,
        max_concurrent=max_concurrent,
        style_pool=style_pool,
        output_dir=DATA_DIR,
    )
    results = await runner.run()

    if not results and not os.path.exists(DATA_DIR):
        print("错误：没有游戏结果可分析")
        return

    generate_report(dry_run=False)
    print()
    print(f"完成！打开 {os.path.abspath(REPORT_PATH)} 查看 Leaderboard")


def generate_report(dry_run: bool = False):
    """从已有数据生成报告"""
    if not os.path.exists(DATA_DIR):
        print(f"数据目录不存在: {DATA_DIR}")
        return

    results = load_results(DATA_DIR)
    if not results:
        print("数据目录为空")
        return

    if dry_run:
        print(f"数据目录: {DATA_DIR}")
        print(f"结果文件数: {len(results)}")
        return

    metrics = compute_all_metrics(results)
    out = generate_leaderboard_html(metrics, results, REPORT_PATH)
    gs = metrics["game_stats"]
    print(f"\n评测摘要:")
    print(f"  总对局: {gs.get('total_games', 0)}")
    print(f"  好人胜率: {gs.get('good_win_rate', 0)}%")
    print(f"  狼人胜率: {gs.get('evil_win_rate', 0)}%")
    print(f"  平均天数: {gs.get('avg_days', 0)}")


def main():
    parser = argparse.ArgumentParser(description="狼人杀多智能体评测系统")
    parser.add_argument("--config", "-c", default="standard_6",
                        choices=["standard_6", "simple_4", "big_9"],
                        help="角色配置（默认 standard_6）")
    parser.add_argument("--games", "-g", type=int, default=50,
                        help="对局数量（默认 50）")
    parser.add_argument("--concurrent", "-n", type=int, default=5,
                        help="最大并发数（默认 5）")
    parser.add_argument("--report-only", "-r", action="store_true",
                        help="仅从已有数据生成报告，不运行新游戏")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅检查数据目录，不生成报告")
    parser.add_argument("--styles", "-s", nargs="+",
                        default=["balanced", "cautious", "bold", "random"],
                        help="决策风格池（默认四种混合）")

    args = parser.parse_args()

    if args.report_only or args.dry_run:
        generate_report(dry_run=args.dry_run)
        return

    asyncio.run(run_benchmark(
        config_name=args.config,
        num_games=args.games,
        max_concurrent=args.concurrent,
        style_pool=args.styles,
    ))


if __name__ == "__main__":
    main()
