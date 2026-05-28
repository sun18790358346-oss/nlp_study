"""测试 schema 模块"""

from schema.game_record import GameRecord, DialogueRecord, DeathRecord
from schema.game_logger import GameLogger, GameRunLog, PhaseLog


# ============== DialogueRecord Tests ==============

class TestDialogueRecord:
    """测试 DialogueRecord 类"""

    def test_init(self):
        """测试初始化"""
        record = DialogueRecord(
            day=1,
            phase="speech",
            player_id=0,
            player_name="玩家1",
            role="Werewolf",
            decision_style="bold",
            action="speech",
            content="我认为玩家3是狼人"
        )
        assert record.day == 1
        assert record.phase == "speech"
        assert record.player_id == 0
        assert record.player_name == "玩家1"
        assert record.role == "Werewolf"
        assert record.decision_style == "bold"
        assert record.action == "speech"
        assert record.content == "我认为玩家3是狼人"
        assert record.target is None
        assert record.reasoning is None

    def test_init_with_optional_fields(self):
        """测试带可选字段初始化"""
        record = DialogueRecord(
            day=1,
            phase="vote",
            player_id=0,
            player_name="玩家1",
            role="Seer",
            decision_style="cautious",
            action="vote",
            content="投票给玩家2",
            target=2,
            reasoning="他发言可疑"
        )
        assert record.target == 2
        assert record.reasoning == "他发言可疑"

    def test_to_dict(self):
        """测试转换为字典"""
        record = DialogueRecord(
            day=1,
            phase="night_wolf",
            player_id=0,
            player_name="玩家1",
            role="Werewolf",
            decision_style="bold",
            action="night_action",
            content="击杀玩家3"
        )
        result = record.to_dict()
        assert isinstance(result, dict)
        assert result["day"] == 1
        assert result["phase"] == "night_wolf"
        assert result["player_id"] == 0
        assert result["action"] == "night_action"


# ============== DeathRecord Tests ==============

class TestDeathRecord:
    """测试 DeathRecord 类"""

    def test_init(self):
        """测试初始化"""
        record = DeathRecord(
            player_id=0,
            player_name="玩家1",
            role="Werewolf",
            cause="vote",
            day=2
        )
        assert record.player_id == 0
        assert record.player_name == "玩家1"
        assert record.role == "Werewolf"
        assert record.cause == "vote"
        assert record.day == 2


# ============== GameRecord Tests ==============

class TestGameRecord:
    """测试 GameRecord 类"""

    def test_init(self):
        """测试初始化"""
        record = GameRecord(
            game_id="test_001",
            start_time="2026-05-19 10:00:00"
        )
        assert record.game_id == "test_001"
        assert record.start_time == "2026-05-19 10:00:00"
        assert record.end_time is None
        assert record.dialogues == []
        assert record.death_order == []

    def test_add_dialogue(self):
        """测试添加对话记录"""
        record = GameRecord(game_id="test_001", start_time="2026-05-19 10:00:00")
        dialogue = DialogueRecord(
            day=1,
            phase="speech",
            player_id=0,
            player_name="玩家1",
            role="Werewolf",
            decision_style="bold",
            action="speech",
            content="测试发言"
        )
        record.add_dialogue(dialogue)
        assert len(record.dialogues) == 1
        assert record.dialogues[0] == dialogue

    def test_add_death(self):
        """测试添加死亡记录"""
        record = GameRecord(game_id="test_001", start_time="2026-05-19 10:00:00")
        record.add_death(
            player_id=0,
            player_name="玩家1",
            role="Werewolf",
            cause="vote",
            day=2
        )
        assert len(record.death_order) == 1
        assert record.death_order[0].player_id == 0
        assert record.death_order[0].cause == "vote"

    def test_to_dict(self):
        """测试转换为字典"""
        record = GameRecord(
            game_id="test_001",
            start_time="2026-05-19 10:00:00",
            config_name="standard_6",
            role_assignment={0: "werewolf", 1: "villager"},
            player_styles={0: "bold", 1: "cautious"}
        )
        result = record.to_dict()
        assert isinstance(result, dict)
        assert result["game_id"] == "test_001"
        assert result["config_name"] == "standard_6"
        assert result["role_assignment"] == {0: "werewolf", 1: "villager"}

    def test_save(self, tmp_path):
        """测试保存记录"""
        record = GameRecord(
            game_id="test_save_001",
            start_time="2026-05-19 10:00:00"
        )
        record.save(output_dir=str(tmp_path))
        file_path = tmp_path / "test_save_001.json"
        assert file_path.exists()

    def test_summary(self):
        """测试生成摘要"""
        record = GameRecord(
            game_id="test_001",
            start_time="2026-05-19 10:00:00",
            end_time="2026-05-19 10:30:00",
            config_name="standard_6",
            role_assignment={0: "werewolf", 1: "seer", 2: "witch", 3: "hunter", 4: "villager", 5: "villager"},
            player_styles={0: "bold", 1: "cautious", 2: "balanced", 3: "cautious", 4: "bold", 5: "random"},
            winner="good"
        )
        summary = record.summary()
        assert "test_001" in summary
        assert "好人阵营" in summary
        assert "玩家1" in summary


# ============== PhaseLog Tests ==============

class TestPhaseLog:
    """测试 PhaseLog 类"""

    def test_init(self):
        """测试初始化"""
        phase_log = PhaseLog(
            day=1,
            phase="night_wolf",
            start_time="2026-05-19 22:00:00"
        )
        assert phase_log.day == 1
        assert phase_log.phase == "night_wolf"
        assert phase_log.start_time == "2026-05-19 22:00:00"
        assert phase_log.end_time is None
        assert phase_log.duration_ms is None
        assert phase_log.events == []
        assert phase_log.errors == []

    def test_add_event(self):
        """测试添加事件"""
        phase_log = PhaseLog(day=1, phase="night_wolf", start_time="2026-05-19 22:00:00")
        phase_log.events.append("狼人决定击杀玩家3")
        assert len(phase_log.events) == 1

    def test_add_error(self):
        """测试添加错误"""
        phase_log = PhaseLog(day=1, phase="night_wolf", start_time="2026-05-19 22:00:00")
        phase_log.errors.append("解析失败")
        assert len(phase_log.errors) == 1


# ============== GameRunLog Tests ==============

class TestGameRunLog:
    """测试 GameRunLog 类"""

    def test_init(self):
        """测试初始化"""
        log = GameRunLog(
            game_id="run_001",
            start_time="2026-05-19 10:00:00",
            config_name="standard_6",
            role_assignment={0: "werewolf"},
            player_styles={0: "bold"}
        )
        assert log.game_id == "run_001"
        assert log.phase_logs == []
        assert log.errors == []

    def test_add_phase(self):
        """测试添加阶段"""
        log = GameRunLog(
            game_id="run_001",
            start_time="2026-05-19 10:00:00"
        )
        phase = log.add_phase(day=1, phase="night_wolf")
        assert len(log.phase_logs) == 1
        assert phase.day == 1
        assert phase.phase == "night_wolf"

    def test_add_error(self):
        """测试添加错误"""
        log = GameRunLog(
            game_id="run_001",
            start_time="2026-05-19 10:00:00"
        )
        log.add_error("测试错误")
        assert len(log.errors) == 1
        assert log.errors[0] == "测试错误"

    def test_save(self, tmp_path):
        """测试保存运行日志"""
        log = GameRunLog(
            game_id="run_save_001",
            start_time="2026-05-19 10:00:00"
        )
        log.save(output_dir=str(tmp_path))
        file_path = tmp_path / "run_save_001_run_log.json"
        assert file_path.exists()


# ============== GameLogger Tests ==============

class TestGameLogger:
    """测试 GameLogger 类"""

    def test_init(self):
        """测试初始化"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={0: "werewolf"},
            player_styles={0: "bold"}
        )
        assert logger.game_id == "logger_001"
        assert logger.game_run_log is not None
        assert logger.current_phase is None

    def test_start_phase(self):
        """测试开始阶段"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        phase = logger.start_phase(day=1, phase="night_wolf")
        assert logger.current_phase is not None
        assert len(logger.game_run_log.phase_logs) == 1
        assert phase.day == 1

    def test_end_phase(self):
        """测试结束阶段"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="night_wolf")
        logger.end_phase()
        assert logger.current_phase is None
        assert logger.game_run_log.phase_logs[0].duration_ms is not None

    def test_log_event(self):
        """测试记录事件"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="night_wolf")
        logger.log_event("测试事件")
        # log_event 只记录到 logger，不添加到 PhaseLog 的 events 列表
        assert len(logger.game_run_log.phase_logs[0].events) == 0

    def test_log_action_event(self):
        """测试记录动作事件"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="night_wolf")
        logger.log_action_event("狼人击杀玩家3")
        assert len(logger.game_run_log.phase_logs[0].events) == 1
        assert "[动作]" in logger.game_run_log.phase_logs[0].events[0]

    def test_log_speech_event(self):
        """测试记录发言事件"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="speech")
        logger.log_speech_event("玩家1发言测试")
        assert len(logger.game_run_log.phase_logs[0].events) == 1
        assert "[发言]" in logger.game_run_log.phase_logs[0].events[0]

    def test_log_vote_event(self):
        """测试记录投票事件"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="vote")
        logger.log_vote_event("玩家1投票给玩家2")
        assert len(logger.game_run_log.phase_logs[0].events) == 1
        assert "[投票]" in logger.game_run_log.phase_logs[0].events[0]

    def test_log_death_event(self):
        """测试记录死亡事件"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="night_wolf")
        logger.log_death_event("玩家1死亡")
        assert len(logger.game_run_log.phase_logs[0].events) == 1
        assert "[死亡]" in logger.game_run_log.phase_logs[0].events[0]

    def test_log_night_action_event(self):
        """测试记录夜间行动事件"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.start_phase(day=1, phase="night_seer")
        logger.log_night_action_event("预言家查验玩家2")
        assert len(logger.game_run_log.phase_logs[0].events) == 1
        assert "[夜行动]" in logger.game_run_log.phase_logs[0].events[0]

    def test_log_error(self):
        """测试记录错误"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.log_error("测试错误信息")
        assert len(logger.game_run_log.errors) == 1

    def test_finish(self):
        """测试结束日志"""
        logger = GameLogger(
            game_id="logger_finish_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        logger.finish()
        assert logger.game_run_log.end_time is not None

    def test_summary(self):
        """测试生成摘要"""
        logger = GameLogger(
            game_id="logger_001",
            config_name="standard_6",
            role_assignment={},
            player_styles={}
        )
        summary = logger.summary()
        assert "logger_001" in summary
        assert "standard_6" in summary


# ============== DECISION_STYLES Tests ==============

class TestDecisionStylesLogger:
    """测试 DECISION_STYLES 常量"""

    def test_decision_styles_exists(self):
        """测试 DECISION_STYLES 存在"""
        from agent.player_agent import DECISION_STYLES
        assert isinstance(DECISION_STYLES, dict)

    def test_decision_styles_has_all_styles(self):
        """测试包含所有风格"""
        from agent.player_agent import DECISION_STYLES
        assert "cautious" in DECISION_STYLES
        assert "bold" in DECISION_STYLES
        assert "random" in DECISION_STYLES
        assert "balanced" in DECISION_STYLES