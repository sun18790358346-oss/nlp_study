"""经验存储系统

按角色类型保存和加载过往游戏经验，用于跨游戏的经验共享。
"""

import json
import os
from typing import Dict, List, Optional

EXPERIENCES_DIR = os.path.join(os.path.dirname(__file__), "experiences")


def _ensure_dir() -> None:
    """确保经验存储目录存在"""
    os.makedirs(EXPERIENCES_DIR, exist_ok=True)


def _get_file_path(role_type: str) -> str:
    """获取某角色类型的经验文件路径"""
    return os.path.join(EXPERIENCES_DIR, f"{role_type}.json")


def load_experiences(role_type: str) -> List[Dict]:
    """加载某角色类型的过往经验

    Args:
        role_type: 角色类型，如 "werewolf", "seer" 等

    Returns:
        经验列表，按时间倒序排列（最新的在前）
    """
    _ensure_dir()
    filepath = _get_file_path(role_type)
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_experience(role_type: str, experience: Dict) -> None:
    """保存一条新经验

    Args:
        role_type: 角色类型
        experience: 经验数据，包含 summary, strategies, mistakes, lessons 等字段
    """
    _ensure_dir()
    filepath = _get_file_path(role_type)
    experiences = load_experiences(role_type)
    experiences.append(experience)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(experiences, f, ensure_ascii=False, indent=2)


def get_experience_prompt(role_type: str) -> str:
    """将过往经验格式化为提示词文本，供 PlayerAgent 构建指令时使用

    Args:
        role_type: 角色类型

    Returns:
        格式化的经验文本，若没有经验则返回空字符串
    """
    experiences = load_experiences(role_type)
    if not experiences:
        return ""

    # 取最近 3 条经验
    recent = experiences[-3:]

    lines = ["", "## 你的过往游戏经验"]
    lines.append("以下是你以往扮演此角色时学到的经验教训，请参考：")

    for i, exp in enumerate(recent, 1):
        outcome = "胜利" if exp.get("is_winner", False) else "失败"
        lines.append(f"\n--- 第{i}次经验（{outcome}）---")
        if exp.get("summary"):
            lines.append(f"  总结：{exp['summary']}")
        if exp.get("strategies"):
            lines.append(f"  策略：{exp['strategies']}")
        if exp.get("mistakes"):
            lines.append(f"  教训：{exp['mistakes']}")
        if exp.get("lessons"):
            lines.append(f"  建议：{exp['lessons']}")

    return "\n".join(lines)


__all__ = [
    "load_experiences",
    "save_experience",
    "get_experience_prompt",
]
