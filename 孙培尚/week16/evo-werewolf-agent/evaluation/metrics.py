"""评测指标计算

从原始游戏结果计算各类量化指标。
"""

from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict


# 角色中文名映射
ROLE_CN = {
    "werewolf": "狼人",
    "seer": "预言家",
    "witch": "女巫",
    "hunter": "猎人",
    "villager": "村民",
}


def compute_game_stats(results: List[Dict]) -> Dict[str, Any]:
    """计算全局游戏统计"""
    total = len(results)
    if total == 0:
        return {"error": "无数据"}

    winners = [r["winner"] for r in results]
    good_wins = sum(1 for w in winners if w == "good")
    evil_wins = sum(1 for w in winners if w == "evil")

    days = [r.get("days_played", 0) for r in results]

    return {
        "total_games": total,
        "good_win_count": good_wins,
        "evil_win_count": evil_wins,
        "good_win_rate": round(good_wins / total * 100, 1),
        "evil_win_rate": round(evil_wins / total * 100, 1),
        "avg_days": round(sum(days) / len(days), 2),
        "max_days": max(days) if days else 0,
        "min_days": min(days) if days else 0,
    }


def compute_role_stats(results: List[Dict]) -> List[Dict]:
    """计算每个角色的表现统计"""
    total = len(results)
    if total == 0:
        return []

    # 角色数据聚合 keyed by role_type
    role_data = defaultdict(lambda: {
        "appearances": 0,     # 出现次数
        "wins": 0,            # 胜利次数
        "survivals": 0,       # 存活次数
        "total_players": 0,   # 总上场人次
    })

    for game in results:
        winner = game.get("winner", "")
        for p in game.get("players", []):
            role = p["role"]
            camp = p["camp"]
            rd = role_data[role]
            rd["appearances"] += 1
            rd["total_players"] += 1
            # 如果该角色所属阵营胜利
            if (camp == "good" and winner == "good") or (camp == "evil" and winner == "evil"):
                rd["wins"] += 1
            if p.get("is_alive", False):
                rd["survivals"] += 1

    # 整理成排序列表
    stats = []
    for role, data in role_data.items():
        n = data["appearances"]
        stats.append({
            "role": role,
            "role_cn": ROLE_CN.get(role, role),
            "appearances": n,
            "wins": data["wins"],
            "win_rate": round(data["wins"] / n * 100, 1) if n > 0 else 0,
            "survivals": data["survivals"],
            "survival_rate": round(data["survivals"] / n * 100, 1) if n > 0 else 0,
        })

    # 按出现次数降序
    stats.sort(key=lambda x: -x["appearances"])
    return stats


def compute_action_stats(results: List[Dict]) -> Dict[str, Any]:
    """计算操作类指标（预言家查对率、女巫准确率等）"""
    total = len(results)
    if total == 0:
        return {}

    # --- 预言家 ---
    seer_total = 0
    seer_correct = 0  # 查验出狼人
    seer_wrong = 0    # 查验好人标记为狼？实际上预言家只返回 result，不判断对错，我们要对照 ground truth

    for game in results:
        # 建立 player_id -> role 的映射
        player_roles = {p["player_id"]: p["role"] for p in game.get("players", [])}
        for check in game.get("seer_checks", []):
            seer_total += 1
            target = check.get("target")
            result = check.get("result")
            target_role = player_roles.get(target, "")
            # result == "wolf" 且 target_role == "werewolf" => 正确
            # result == "good" 且 target_role != "werewolf" => 正确
            is_correct = (result == "wolf" and target_role == "werewolf") or \
                         (result == "good" and target_role != "werewolf")
            if is_correct:
                seer_correct += 1
            else:
                seer_wrong += 1

    # --- 女巫 ---
    witch_heal_total = 0
    witch_heal_correct = 0  # 救的是被刀的好人（信息完善时不判断好坏，只判断是否有效使用）
    witch_poison_total = 0
    witch_poison_hit_wolf = 0  # 毒中狼人
    witch_poison_hit_good = 0  # 毒中好人

    for game in results:
        player_roles = {p["player_id"]: p["role"] for p in game.get("players", [])}
        for action in game.get("witch_actions", []):
            if action.get("action") == "heal":
                witch_heal_total += 1
                # 救人药本身总是"有效"（救的是被刀的人），不计对错
                witch_heal_correct += 1
            elif action.get("action") == "poison":
                witch_poison_total += 1
                target = action.get("target")
                if player_roles.get(target) == "werewolf":
                    witch_poison_hit_wolf += 1
                else:
                    witch_poison_hit_good += 1

    # --- 猎人 ---
    hunter_total = 0
    hunter_hit_wolf = 0
    hunter_hit_good = 0

    for game in results:
        player_roles = {p["player_id"]: p["role"] for p in game.get("players", [])}
        for shot in game.get("hunter_shots", []):
            hunter_total += 1
            target = shot.get("target")
            if player_roles.get(target) == "werewolf":
                hunter_hit_wolf += 1
            else:
                hunter_hit_good += 1

    # --- 投票准确率 ---
    vote_total = 0
    vote_on_wolf = 0       # 投给狼人的票
    vote_on_good = 0       # 投给好人的票
    vote_on_dead = 0       # 投给已死玩家的无效票

    for game in results:
        player_roles = {p["player_id"]: p["role"] for p in game.get("players", [])}
        alive_status = {p["player_id"]: p.get("is_alive", True) for p in game.get("players", [])}
        # 需要知道投票时的存活状态。简化：用最终存活状态近似
        for v in game.get("votes", []):
            vote_total += 1
            target = v.get("target")
            if target is None:
                continue
            if player_roles.get(target) == "werewolf":
                vote_on_wolf += 1
            else:
                vote_on_good += 1

    # --- 狼人内部一致性 ---
    wolf_internal_agreement = 0.0
    wolf_vote_rounds = 0
    for game in results:
        # 按天分组狼人投票
        wolf_votes_by_day = defaultdict(list)
        for wv in game.get("wolf_votes", []):
            day = wv.get("day", 0)
            wolf_votes_by_day[day].append(wv.get("target"))
        for day, targets in wolf_votes_by_day.items():
            if len(targets) >= 2:
                wolf_vote_rounds += 1
                most_common = Counter(targets).most_common(1)[0][1]
                agreement = most_common / len(targets)
                wolf_internal_agreement += agreement

    if wolf_vote_rounds > 0:
        wolf_internal_agreement = round(wolf_internal_agreement / wolf_vote_rounds * 100, 1)

    stats = {}

    # 预言家
    if seer_total > 0:
        stats["seer"] = {
            "total_checks": seer_total,
            "correct": seer_correct,
            "wrong": seer_wrong,
            "accuracy": round(seer_correct / seer_total * 100, 1),
        }

    # 女巫
    if witch_heal_total > 0:
        stats["witch_heal"] = {
            "total": witch_heal_total,
        }
    if witch_poison_total > 0:
        stats["witch_poison"] = {
            "total": witch_poison_total,
            "hit_wolf": witch_poison_hit_wolf,
            "hit_good": witch_poison_hit_good,
            "wolf_hit_rate": round(witch_poison_hit_wolf / witch_poison_total * 100, 1),
        }

    # 猎人
    if hunter_total > 0:
        stats["hunter"] = {
            "total_shots": hunter_total,
            "hit_wolf": hunter_hit_wolf,
            "hit_good": hunter_hit_good,
            "accuracy": round(hunter_hit_wolf / hunter_total * 100, 1),
        }

    # 投票
    if vote_total > 0:
        stats["voting"] = {
            "total_votes": vote_total,
            "on_wolf": vote_on_wolf,
            "on_good": vote_on_good,
            "wolf_target_rate": round(vote_on_wolf / vote_total * 100, 1),
        }

    # 狼人内部一致性
    if wolf_vote_rounds > 0:
        stats["wolf_internal"] = {
            "rounds_with_votes": wolf_vote_rounds,
            "agreement_rate": wolf_internal_agreement,
        }

    return stats


def compute_all_metrics(results: List[Dict]) -> Dict[str, Any]:
    """计算所有指标的汇总"""
    return {
        "game_stats": compute_game_stats(results),
        "role_stats": compute_role_stats(results),
        "action_stats": compute_action_stats(results),
    }
