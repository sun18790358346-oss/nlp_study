"""快速验证：生成模拟数据测试评测流水线"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from evaluation.metrics import compute_all_metrics
from evaluation.report import generate_leaderboard_html

DATA_DIR = "evaluation/data"
os.makedirs(DATA_DIR, exist_ok=True)

def make_mock_game(i):
    players = [
        {"player_id": 0, "name": "玩家1", "role": "werewolf", "camp": "evil", "is_alive": False, "death_cause": "vote", "death_day": 2},
        {"player_id": 1, "name": "玩家2", "role": "werewolf", "camp": "evil", "is_alive": True},
        {"player_id": 2, "name": "玩家3", "role": "seer", "camp": "good", "is_alive": False, "death_cause": "night_kill", "death_day": 1},
        {"player_id": 3, "name": "玩家4", "role": "witch", "camp": "good", "is_alive": False, "death_cause": "night_kill", "death_day": 2},
        {"player_id": 4, "name": "玩家5", "role": "hunter", "camp": "good", "is_alive": False, "death_cause": "vote", "death_day": 3},
        {"player_id": 5, "name": "玩家6", "role": "villager", "camp": "good", "is_alive": False, "death_cause": "night_kill", "death_day": 3},
    ]
    winner = "evil" if i % 2 == 0 else "good"
    days = random.randint(2, 4)

    seer_checks = []
    if winner == "evil":
        seer_checks.append({"day": 1, "player_id": 2, "target": 1, "result": "wolf"})
    else:
        seer_checks.append({"day": 1, "player_id": 2, "target": 3, "result": "good"})
        seer_checks.append({"day": 2, "player_id": 2, "target": 1, "result": "wolf"})

    witch_actions = []
    witch_actions.append({"day": 1, "player_id": 3, "action": "heal", "target": 2})

    hunter_shots = []
    if i % 3 == 0:
        hunter_shots.append({"day": 3, "player_id": 4, "target": 1 if winner == "good" else 5})

    wolf_votes = [
        {"day": 1, "player_id": 0, "target": 2},
        {"day": 1, "player_id": 1, "target": 2},
    ]

    votes = [
        {"day": 2, "player_id": 2, "target": 0},
        {"day": 2, "player_id": 3, "target": 0},
        {"day": 2, "player_id": 4, "target": 0},
        {"day": 2, "player_id": 5, "target": 0},
        {"day": 2, "player_id": 1, "target": 5},
        {"day": 2, "player_id": 0, "target": 5},
    ]

    return {
        "game_id": f"test_{i:03d}",
        "config_name": "standard_6",
        "winner": winner,
        "days_played": days,
        "total_dialogues": 30 + random.randint(0, 20),
        "players": players,
        "seer_checks": seer_checks,
        "witch_actions": witch_actions,
        "hunter_shots": hunter_shots,
        "wolf_votes": wolf_votes,
        "votes": votes,
        "speeches": [],
        "role_assignment": {0: "werewolf", 1: "werewolf", 2: "seer", 3: "witch", 4: "hunter", 5: "villager"},
        "player_styles": {i: "balanced" for i in range(6)},
    }

# 生成 50 局 mock 数据
for i in range(50):
    data = make_mock_game(i)
    with open(os.path.join(DATA_DIR, f"mock_{i:03d}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print(f"生成 50 局 mock 数据到 {DATA_DIR}")

# 计算指标
from evaluation.batch_runner import load_results
results = load_results(DATA_DIR)
metrics = compute_all_metrics(results)

# 生成报告
out = generate_leaderboard_html(metrics, results, "evaluation/leaderboard.html")

print(f"Leaderboard 已生成: {os.path.abspath(out)}")

# 打印摘要
gs = metrics["game_stats"]
print(f"\n=== 指标摘要 ===")
print(f"总对局: {gs['total_games']}")
print(f"好人胜率: {gs['good_win_rate']}%")
print(f"狼人胜率: {gs['evil_win_rate']}%")
print(f"平均天数: {gs['avg_days']}")
print(f"\n角色表现:")
for s in metrics["role_stats"]:
    print(f"  {s['role_cn']}: 胜率={s['win_rate']}%  存活率={s['survival_rate']}%")
print(f"\n操作指标:")
for k, v in metrics["action_stats"].items():
    print(f"  {k}: {v}")
