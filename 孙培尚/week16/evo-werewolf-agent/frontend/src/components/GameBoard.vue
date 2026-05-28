<template>
  <div class="board-container">
    <!-- Winner Overlay -->
    <div v-if="isGameOver && gameStatus && !showSummary" class="winner-overlay">
      <div class="winner-card">
        <div class="winner-icon">🏆</div>
        <div class="winner-title">游戏结束</div>
        <div class="winner-team">
          {{ winnerText }}
        </div>
        <div class="winner-day">持续 {{ gameStatus.day_number }} 天</div>
        <div class="overlay-buttons">
          <button class="primary" @click="showSummary = true">
            📋 查看玩家总结
          </button>
          <button @click="$emit('reset')">返回大厅</button>
        </div>
      </div>
    </div>

    <!-- Top Info Bar -->
    <div class="info-bar">
      <div class="info-item">
        <span class="info-label">天数</span>
        <span class="info-value">{{ gameStatus?.day_number || 0 }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">阶段</span>
        <span class="info-value phase-badge">{{ phaseLabel }}</span>
      </div>
      <div class="info-item">
        <span class="info-label">存活</span>
        <span class="info-value alive-count">{{ aliveCount }} / {{ totalCount }}</span>
      </div>
    </div>

    <!-- Control Buttons -->
    <div class="controls">
      <button
        v-if="!isAutoPlaying"
        class="primary"
        :disabled="isGameOver || loading"
        @click="$emit('auto-play')"
      >
        ▶ 自动继续
      </button>
      <button
        v-else
        class="danger"
        @click="$emit('pause')"
      >
        ⏸ 暂停
      </button>
      <button
        :disabled="isAutoPlaying || isGameOver || loading"
        @click="$emit('step')"
      >
        ⏭ 单步执行
      </button>
      <button
        class="danger"
        @click="$emit('reset'); showSummary = false"
      >
        ✕ 退出游戏
      </button>
    </div>

    <!-- Player Grid -->
    <div v-if="gameStatus" class="player-grid">
      <PlayerCard
        v-for="p in sortedPlayers"
        :key="p.player_id"
        :player="p"
      />
    </div>

    <!-- Tab Switch -->
    <div v-if="isGameOver" class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: !showSummary }"
        @click="showSummary = false"
      >
        📜 游戏日志
      </button>
      <button
        class="tab-btn"
        :class="{ active: showSummary }"
        @click="showSummary = true"
      >
        📋 玩家总结
      </button>
    </div>

    <!-- Game Log (when summary tab not active) -->
    <GameLog v-if="!showSummary" :log-entries="stepLog" />

    <!-- Summary Panel -->
    <div v-if="showSummary" class="summary-panel">
      <h3 class="summary-title">📋 玩家总结与经验</h3>
      <div v-if="summaries.length === 0" class="summary-empty">
        总结生成中...
      </div>
      <div v-else class="summary-grid">
        <div
          v-for="s in summaries"
          :key="s.player_id"
          class="summary-card"
          :class="s.camp"
        >
          <div class="summary-header">
            <div class="summary-player">{{ s.player_name }}</div>
            <div class="summary-role-tag" :class="'role-' + s.role_type">
              {{ roleLabel(s.role_type) }}
            </div>
            <span class="camp-tag-sm" :class="s.camp">
              {{ s.camp === 'good' ? '好人' : '狼人' }}
            </span>
            <span class="result-tag" :class="s.is_winner ? 'win' : 'lose'">
              {{ s.is_winner ? '胜利' : '失败' }}
            </span>
          </div>
          <div v-if="s.summary" class="summary-section">
            <div class="section-label">📝 总结</div>
            <div class="section-text">{{ s.summary }}</div>
          </div>
          <div v-if="s.strategies" class="summary-section">
            <div class="section-label">🎯 策略</div>
            <div class="section-text" v-if="typeof s.strategies === 'string'">{{ s.strategies }}</div>
            <ul v-else class="section-list">
              <li v-for="(item, i) in s.strategies" :key="i">{{ item }}</li>
            </ul>
          </div>
          <div v-if="s.mistakes" class="summary-section">
            <div class="section-label">⚠️ 教训</div>
            <div class="section-text" v-if="typeof s.mistakes === 'string'">{{ s.mistakes }}</div>
            <ul v-else class="section-list">
              <li v-for="(item, i) in s.mistakes" :key="i">{{ item }}</li>
            </ul>
          </div>
          <div v-if="s.lessons" class="summary-section">
            <div class="section-label">💡 建议</div>
            <div class="section-text" v-if="typeof s.lessons === 'string'">{{ s.lessons }}</div>
            <ul v-else class="section-list">
              <li v-for="(item, i) in s.lessons" :key="i">{{ item }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import PlayerCard from './PlayerCard.vue'
import GameLog from './GameLog.vue'

const props = defineProps({
  gameStatus: { type: Object, default: null },
  stepLog: { type: Array, default: () => [] },
  summaries: { type: Array, default: () => [] },
  isAutoPlaying: { type: Boolean, default: false },
  isGameOver: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})

defineEmits(['step', 'auto-play', 'pause', 'reset'])

const showSummary = ref(false)

const phaseLabels = {
  night_wolf: '🌙 狼人杀人',
  night_seer: '🔮 预言家查验',
  night_witch: '🧪 女巫用药',
  night_result: '🌙 夜晚结算',
  day_start: '☀️ 白天开始',
  speech: '💬 公开演讲',
  vote: '🗳️ 投票环节',
  day_end: '📊 一天结束',
  summary: '📋 总结',
  game_over: '🏁 已结束',
}

const roleLabelsMap = {
  werewolf: '🐺 狼人',
  seer: '🔮 预言家',
  witch: '🧪 女巫',
  hunter: '🏹 猎人',
  villager: '👤 村民',
}

function roleLabel(roleType) {
  return roleLabelsMap[roleType] || roleType
}

const winnerText = computed(() => {
  if (!props.gameStatus || !props.gameStatus.winner) return '未知'
  return props.gameStatus.winner === 'good' ? '善良阵营（好人）' : '邪恶阵营（狼人）'
})

const phaseLabel = computed(() => {
  if (!props.gameStatus) return '—'
  const phase = props.gameStatus.phase
  return phaseLabels[phase] || phase
})

const aliveCount = computed(() => {
  if (!props.gameStatus) return 0
  return props.gameStatus.players.filter(p => p.is_alive).length
})

const totalCount = computed(() => {
  if (!props.gameStatus) return 0
  return props.gameStatus.players.length
})

const sortedPlayers = computed(() => {
  if (!props.gameStatus) return []
  return [...props.gameStatus.players].sort((a, b) => {
    if (a.is_alive !== b.is_alive) return a.is_alive ? -1 : 1
    return a.player_id - b.player_id
  })
})
</script>

<style scoped>
.board-container {
  position: relative;
}

.info-bar {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 20px;
}

.info-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px 24px;
  text-align: center;
  min-width: 120px;
}

.info-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
}

.phase-badge {
  color: var(--accent-blue);
}

.alive-count {
  color: var(--accent-green);
}

.controls {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.player-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

@media (max-width: 900px) {
  .player-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 500px) {
  .player-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.tab-btn {
  padding: 10px 24px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--accent-blue);
  border-bottom-color: var(--accent-blue);
}

/* Winner Overlay */
.winner-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.winner-card {
  background: var(--bg-secondary);
  border: 2px solid var(--accent-yellow);
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  max-width: 420px;
  width: 90%;
}

.winner-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.winner-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
}

.winner-team {
  font-size: 20px;
  font-weight: 600;
  color: var(--accent-yellow);
  margin-bottom: 8px;
}

.winner-day {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 24px;
}

.overlay-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.overlay-buttons button {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
}

/* Summary Panel */
.summary-panel {
  margin-top: 8px;
}

.summary-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-secondary);
}

.summary-empty {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.summary-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.summary-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

.summary-card.good {
  border-left: 3px solid var(--good-color);
}

.summary-card.evil {
  border-left: 3px solid var(--evil-color);
}

.summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.summary-player {
  font-size: 16px;
  font-weight: 700;
}

.summary-role-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.role-werewolf { color: var(--wolf-color); }
.role-seer { color: var(--seer-color); }
.role-witch { color: var(--witch-color); }
.role-hunter { color: var(--hunter-color); }
.role-villager { color: var(--villager-color); }

.camp-tag-sm {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.camp-tag-sm.good {
  background: rgba(63, 185, 80, 0.15);
  color: var(--good-color);
}

.camp-tag-sm.evil {
  background: rgba(248, 81, 73, 0.15);
  color: var(--evil-color);
}

.result-tag {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
}

.result-tag.win {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
}

.result-tag.lose {
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red);
}

.summary-section {
  margin-bottom: 12px;
}

.summary-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.section-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
}

.section-list {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.7;
}

.section-list li {
  margin-bottom: 2px;
}
</style>
