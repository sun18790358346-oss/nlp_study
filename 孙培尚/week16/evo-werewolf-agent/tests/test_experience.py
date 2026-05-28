"""经验存储系统测试"""

import json
import os
import pytest
from memory.experience import (
    load_experiences,
    save_experience,
    get_experience_prompt,
    EXPERIENCES_DIR,
)


class TestExperienceStorage:
    """测试经验的保存和加载"""

    def setup_method(self):
        """每个测试前确保目录存在并清空测试数据"""
        os.makedirs(EXPERIENCES_DIR, exist_ok=True)
        self._cleanup()

    def teardown_method(self):
        """每个测试后清理测试数据"""
        self._cleanup()

    def _cleanup(self):
        """清理测试文件"""
        test_file = os.path.join(EXPERIENCES_DIR, "test_role.json")
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_load_experiences_empty(self):
        """测试加载不存在的角色经验返回空列表"""
        exps = load_experiences("nonexistent_role")
        assert exps == []

    def test_save_and_load_experience(self):
        """测试保存并加载一条经验"""
        exp = {
            "game_id": "test123",
            "player_id": 0,
            "summary": "本局表现不错",
            "strategies": "悍跳预言家",
            "winner": "evil",
            "is_winner": True,
        }
        save_experience("test_role", exp)
        exps = load_experiences("test_role")
        assert len(exps) == 1
        assert exps[0]["game_id"] == "test123"
        assert exps[0]["summary"] == "本局表现不错"

    def test_save_multiple_experiences(self):
        """测试保存多条经验"""
        for i in range(3):
            save_experience("test_role", {"game_id": f"g{i}", "index": i})
        exps = load_experiences("test_role")
        assert len(exps) == 3

    def test_experience_persistence_across_loads(self):
        """测试经验持久化（多次加载数据一致）"""
        save_experience("test_role", {"game_id": "g1", "data": "first"})
        save_experience("test_role", {"game_id": "g2", "data": "second"})

        exps1 = load_experiences("test_role")
        exps2 = load_experiences("test_role")
        assert len(exps1) == 2
        assert len(exps2) == 2
        assert exps1 == exps2

    def test_experience_file_format(self):
        """测试经验文件格式正确"""
        exp = {"summary": "test", "strategies": "s", "mistakes": "m", "lessons": "l"}
        save_experience("test_role", exp)

        filepath = os.path.join(EXPERIENCES_DIR, "test_role.json")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["summary"] == "test"


class TestExperiencePrompt:
    """测试经验提示词生成"""

    def setup_method(self):
        os.makedirs(EXPERIENCES_DIR, exist_ok=True)
        self._cleanup()

    def teardown_method(self):
        self._cleanup()

    def _cleanup(self):
        test_file = os.path.join(EXPERIENCES_DIR, "test_role.json")
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_get_experience_prompt_empty(self):
        """测试无经验时返回空字符串"""
        prompt = get_experience_prompt("nonexistent")
        assert prompt == ""

    def test_get_experience_prompt_single(self):
        """测试单条经验格式化"""
        save_experience("test_role", {
            "summary": "本局悍跳成功",
            "strategies": "前置位跳预言家",
            "mistakes": "发言不够自信",
            "lessons": "要更坚定地发言",
            "is_winner": True,
        })
        prompt = get_experience_prompt("test_role")
        assert "过往游戏经验" in prompt
        assert "胜利" in prompt
        assert "悍跳成功" in prompt
        assert "前置位跳预言家" in prompt
        assert "发言不够自信" in prompt
        assert "要更坚定地发言" in prompt

    def test_get_experience_prompt_only_recent(self):
        """测试只返回最近3条经验"""
        for i in range(5):
            save_experience("test_role", {"summary": f"经验{i}", "is_winner": i % 2 == 0})
        prompt = get_experience_prompt("test_role")
        # 最近的3条（索引2,3,4）应在提示中
        assert "经验2" in prompt
        assert "经验3" in prompt
        assert "经验4" in prompt
        # 最早的2条（索引0,1）不应在提示中
        assert "经验0" not in prompt
        assert "经验1" not in prompt

    def test_get_experience_prompt_failure_case(self):
        """测试失败经验的显示"""
        save_experience("test_role", {
            "summary": "被首刀出局",
            "is_winner": False,
        })
        prompt = get_experience_prompt("test_role")
        assert "失败" in prompt
        assert "被首刀出局" in prompt

    def test_get_experience_prompt_partial_fields(self):
        """测试部分字段的经验"""
        save_experience("test_role", {
            "summary": "只有总结",
            "is_winner": True,
        })
        prompt = get_experience_prompt("test_role")
        assert "只有总结" in prompt


class TestExperienceEdgeCases:
    """测试经验存储的边界情况"""

    def setup_method(self):
        os.makedirs(EXPERIENCES_DIR, exist_ok=True)
        self._cleanup()

    def teardown_method(self):
        self._cleanup()

    def _cleanup(self):
        test_file = os.path.join(EXPERIENCES_DIR, "test_role.json")
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_save_experience_with_empty_summary(self):
        """测试保存空总结"""
        save_experience("test_role", {"summary": ""})
        exps = load_experiences("test_role")
        assert len(exps) == 1
        assert exps[0]["summary"] == ""

    def test_save_experience_with_unicode(self):
        """测试保存中文经验"""
        save_experience("test_role", {"summary": "悍跳预言家，成功骗过所有人 🐺"})
        exps = load_experiences("test_role")
        assert exps[0]["summary"] == "悍跳预言家，成功骗过所有人 🐺"

    def test_save_experience_overwrites_existing(self):
        """测试多次保存到同一角色文件是追加而非覆盖"""
        save_experience("test_role", {"summary": "first"})
        save_experience("test_role", {"summary": "second"})
        exps = load_experiences("test_role")
        assert len(exps) == 2

    def test_different_roles_separate_files(self):
        """测试不同角色的经验存储在不同文件"""
        # 清理可能被其他测试污染的存档
        for f in ["werewolf.json", "seer.json"]:
            fp = os.path.join(EXPERIENCES_DIR, f)
            if os.path.exists(fp):
                os.remove(fp)

        save_experience("werewolf", {"summary": "狼人经验"})
        save_experience("seer", {"summary": "预言家经验"})

        wolves = load_experiences("werewolf")
        seers = load_experiences("seer")

        assert len(wolves) == 1
        assert len(seers) == 1
        assert wolves[0]["summary"] == "狼人经验"
        assert seers[0]["summary"] == "预言家经验"

        # 清理
        for f in ["werewolf.json", "seer.json"]:
            fp = os.path.join(EXPERIENCES_DIR, f)
            if os.path.exists(fp):
                os.remove(fp)
