"""Leaderboard 报告生成器

从评测数据生成自包含的 HTML 报告。
"""

import json
import os
from typing import Dict, Any, List

from evaluation.metrics import compute_all_metrics, ROLE_CN


def _truncate_text(text: str, max_len: int = 80) -> str:
    """截断文本并加省略号"""
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def generate_leaderboard_html(metrics: Dict[str, Any], results: List[Dict],
                              output_path: str = "evaluation/leaderboard.html") -> str:
    """生成 Leaderboard HTML 报告"""
    game_stats = metrics.get("game_stats", {})
    role_stats = metrics.get("role_stats", [])
    action_stats = metrics.get("action_stats", {})

    total = game_stats.get("total_games", 0)
    good_rate = game_stats.get("good_win_rate", 0)
    evil_rate = game_stats.get("evil_win_rate", 0)
    avg_days = game_stats.get("avg_days", 0)

    # 构建角色数据 JSON（前端 Chart.js 用）
    role_labels = json.dumps([s["role_cn"] for s in role_stats])
    role_win_rates = json.dumps([s["win_rate"] for s in role_stats])
    role_survival_rates = json.dumps([s["survival_rate"] for s in role_stats])

    # 操作指标 JSON
    action_json = json.dumps(action_stats, ensure_ascii=False)

    # 最近 N 局
    recent_games = results[-20:] if len(results) > 20 else results
    recent_games.reverse()

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>狼人杀多智能体 — Leaderboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0f1117;
    color: #e0e0e0;
    padding: 32px;
    line-height: 1.6;
}}

.container {{ max-width: 1200px; margin: 0 auto; }}

.header {{
    text-align: center;
    padding: 40px 0 32px;
    border-bottom: 1px solid #2a2d3a;
    margin-bottom: 32px;
}}

.header h1 {{
    font-size: 28px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 8px;
}}

.header p {{ color: #888; font-size: 14px; }}

.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 32px; }}

.card {{
    background: #1a1d2b;
    border: 1px solid #2a2d3a;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}}

.card .value {{
    font-size: 36px;
    font-weight: 700;
    margin-bottom: 4px;
}}

.card .label {{
    font-size: 13px;
    color: #888;
}}

.good-color {{ color: #4ade80; }}
.evil-color {{ color: #f87171; }}
.neutral-color {{ color: #60a5fa; }}

.section {{
    background: #1a1d2b;
    border: 1px solid #2a2d3a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}}

.section h2 {{
    font-size: 18px;
    font-weight: 600;
    color: #fff;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #2a2d3a;
}}

.chart-row {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}}

.chart-container {{ position: relative; height: 300px; }}

@media (max-width: 768px) {{
    .chart-row {{ grid-template-columns: 1fr; }}
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}}

th {{
    text-align: left;
    padding: 12px 16px;
    color: #888;
    font-weight: 500;
    border-bottom: 1px solid #2a2d3a;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

td {{
    padding: 12px 16px;
    border-bottom: 1px solid #252836;
}}

tr:hover td {{ background: #252836; }}

.badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 500;
}}

.badge-good {{ background: rgba(74, 222, 128, 0.15); color: #4ade80; }}
.badge-evil {{ background: rgba(248, 113, 113, 0.15); color: #f87171; }}

.win-bar {{
    display: inline-block;
    height: 8px;
    border-radius: 4px;
    background: #2a2d3a;
    overflow: hidden;
    width: 120px;
    vertical-align: middle;
    margin-right: 8px;
}}

.win-bar-fill {{
    height: 100%;
    border-radius: 4px;
    transition: width 0.3s;
}}

.win-bar-good .win-bar-fill {{ background: #4ade80; }}
.win-bar-evil .win-bar-fill {{ background: #f87171; }}

.game-list {{
    max-height: 400px;
    overflow-y: auto;
}}

.game-list::-webkit-scrollbar {{ width: 6px; }}
.game-list::-webkit-scrollbar-track {{ background: transparent; }}
.game-list::-webkit-scrollbar-thumb {{ background: #2a2d3a; border-radius: 3px; }}

.game-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #252836;
    font-size: 13px;
}}

.action-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
}}

.action-card {{
    background: #252836;
    border-radius: 8px;
    padding: 16px;
}}

.action-card h3 {{
    font-size: 14px;
    color: #aaa;
    margin-bottom: 8px;
    font-weight: 500;
}}

.action-card .stat {{ font-size: 24px; font-weight: 700; margin-bottom: 4px; }}
.action-card .detail {{ font-size: 12px; color: #888; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
    <h1>狼人杀多智能体 Leaderboard</h1>
    <p>{total} 局标准6人局 · qwen-flash 模型 · 4 种决策风格混合</p>
</div>

<!-- 概览卡片 -->
<div class="grid">
    <div class="card">
        <div class="value" style="color:#4ade80;">{total}</div>
        <div class="label">总对局数</div>
    </div>
    <div class="card">
        <div class="value good-color">{good_rate}%</div>
        <div class="label">好人阵营胜率</div>
    </div>
    <div class="card">
        <div class="value evil-color">{evil_rate}%</div>
        <div class="label">狼人阵营胜率</div>
    </div>
    <div class="card">
        <div class="value neutral-color">{avg_days}</div>
        <div class="label">平均存活天数</div>
    </div>
</div>

<!-- 角色胜率图 -->
<div class="section">
    <h2>角色表现</h2>
    <div class="chart-row">
        <div class="chart-container">
            <canvas id="winRateChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="survivalRateChart"></canvas>
        </div>
    </div>
</div>

<!-- 操作指标 -->
<div class="section">
    <h2>决策指标</h2>
    <div class="action-grid" id="actionGrid"></div>
</div>

<!-- 详细表格 -->
<div class="section">
    <h2>角色数据详情</h2>
    <table>
        <thead>
            <tr>
                <th>角色</th>
                <th>上场次数</th>
                <th>胜利</th>
                <th>胜率</th>
                <th>存活</th>
                <th>存活率</th>
            </tr>
        </thead>
        <tbody>
"""

    # 角色表格行
    for s in role_stats:
        role = s["role_cn"]
        camp_class = "badge-evil" if s["role"] == "werewolf" else "badge-good"
        html += f"""            <tr>
                <td><span class="badge {camp_class}">{role}</span></td>
                <td>{s["appearances"]}</td>
                <td>{s["wins"]}</td>
                <td>
                    <div class="win-bar win-bar-{'evil' if s['role'] == 'werewolf' else 'good'}">
                        <div class="win-bar-fill" style="width:{s['win_rate']}%"></div>
                    </div>
                    {s['win_rate']}%
                </td>
                <td>{s["survivals"]}</td>
                <td>{s['survival_rate']}%</td>
            </tr>
"""

    html += """        </tbody>
    </table>
</div>

<!-- 最近对局 -->
<div class="section">
    <h2>最近对局记录</h2>
    <div class="game-list">
"""

    for g in recent_games:
        w = g.get("winner", "?")
        w_label = "好人" if w == "good" else "狼人"
        w_class = "badge-good" if w == "good" else "badge-evil"
        days = g.get("days_played", "?")
        gid = g.get("game_id", "?")
        html += f"""        <div class="game-item">
            <span>{gid}</span>
            <span>{days} 天</span>
            <span><span class="badge {w_class}">{w_label}胜利</span></span>
        </div>
"""

    html += """    </div>
</div>

</div>

<script>
// 角色胜率图
new Chart(document.getElementById('winRateChart'), {
    type: 'bar',
    data: {
        labels: """ + role_labels + """,
        datasets: [{
            label: '胜率 (%)',
            data: """ + role_win_rates + """,
            backgroundColor: [
                '#f87171', '#4ade80', '#4ade80', '#4ade80', '#4ade80'
            ],
            borderRadius: 4,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: true, text: '各角色胜率', color: '#e0e0e0', font: { size: 14 } }
        },
        scales: {
            y: { beginAtZero: true, max: 100, grid: { color: '#2a2d3a' },
                 ticks: { color: '#888', callback: v => v + '%' } },
            x: { grid: { display: false }, ticks: { color: '#e0e0e0' } }
        }
    }
});

// 存活率图
new Chart(document.getElementById('survivalRateChart'), {
    type: 'bar',
    data: {
        labels: """ + role_labels + """,
        datasets: [{
            label: '存活率 (%)',
            data: """ + role_survival_rates + """,
            backgroundColor: [
                '#fb923c', '#60a5fa', '#60a5fa', '#60a5fa', '#60a5fa'
            ],
            borderRadius: 4,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: true, text: '各角色存活率', color: '#e0e0e0', font: { size: 14 } }
        },
        scales: {
            y: { beginAtZero: true, max: 100, grid: { color: '#2a2d3a' },
                 ticks: { color: '#888', callback: v => v + '%' } },
            x: { grid: { display: false }, ticks: { color: '#e0e0e0' } }
        }
    }
});

// 决策指标
const actionData = """ + action_json + """;
const grid = document.getElementById('actionGrid');

function addActionCard(title, statValue, detail) {
    const div = document.createElement('div');
    div.className = 'action-card';
    div.innerHTML = `<h3>${title}</h3><div class="stat">${statValue}</div><div class="detail">${detail}</div>`;
    grid.appendChild(div);
}

// 预言家
if (actionData.seer)
    addActionCard('预言家查验准确率', actionData.seer.accuracy + '%',
        `${actionData.seer.correct} 正确 / ${actionData.seer.wrong} 错误`);

// 女巫毒药
if (actionData.witch_poison)
    addActionCard('女巫毒药命中率', actionData.witch_poison.wolf_hit_rate + '%',
        `${actionData.witch_poison.hit_wolf} 狼人 / ${actionData.witch_poison.hit_good} 好人`);

// 猎人
if (actionData.hunter)
    addActionCard('猎人开枪准确率', actionData.hunter.accuracy + '%',
        `${actionData.hunter.hit_wolf} 狼人 / ${actionData.hunter.hit_good} 好人`);

// 投票
if (actionData.voting)
    addActionCard('投票指向狼人率', actionData.voting.wolf_target_rate + '%',
        `共 ${actionData.voting.total_votes} 票`);

// 狼人内部一致性
if (actionData.wolf_internal)
    addActionCard('狼人内部投票一致率', actionData.wolf_internal.agreement_rate + '%',
        `${actionData.wolf_internal.rounds_with_votes} 轮投票`);

</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Leaderboard 已生成: {os.path.abspath(output_path)}")
    return output_path
