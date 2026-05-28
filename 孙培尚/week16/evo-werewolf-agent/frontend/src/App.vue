<template>
  <div class="app-container">
    <header class="app-header">
      <h1 class="app-title">🐺 狼人杀 AI 观战台</h1>
      <p class="app-subtitle">Multi-Agent Werewolf Spectator Dashboard</p>
    </header>

    <main class="app-main">
      <GameSetup
        v-if="!gameId"
        :configs="configs"
        :loading="creating"
        @create="handleCreate"
      />

      <GameBoard
        v-else
        :game-status="gameStatus"
        :step-log="stepLog"
        :summaries="summaries"
        :is-auto-playing="isAutoPlaying"
        :is-game-over="isGameOver"
        :loading="stepping"
        @step="handleStep"
        @auto-play="handleAutoPlay"
        @pause="handlePause"
        @reset="handleReset"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import GameSetup from './components/GameSetup.vue'
import GameBoard from './components/GameBoard.vue'
import { createGame, stepGame, getGameStatus, getConfigs, deleteGame, getGameSummaries } from './api.js'

const configs = ref({})
const gameId = ref(null)
const gameStatus = ref(null)
const stepLog = ref([])
const summaries = ref([])
const isAutoPlaying = ref(false)
const isGameOver = ref(false)
const creating = ref(false)
const stepping = ref(false)

let autoPlayTimer = null

onMounted(async () => {
  try {
    configs.value = await getConfigs()
  } catch (e) {
    console.error('获取配置失败:', e)
  }
})

onUnmounted(() => {
  stopAutoPlay()
})

function stopAutoPlay() {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
  isAutoPlaying.value = false
}

function addPhaseLog(phase, text) {
  stepLog.value.push({
    id: Date.now() + Math.random(),
    type: 'phase',
    phase,
    text,
    timestamp: new Date(),
  })
}

function addDeathLog(death) {
  const causeMap = {
    night_kill: '被狼人杀害',
    poison: '被女巫毒杀',
    shoot: '被猎人枪杀',
    vote: '被投票出局',
  }
  stepLog.value.push({
    id: Date.now() + Math.random(),
    type: 'death',
    player_id: death.player_id,
    text: `💀 ${death.player_name}（${death.role}）${causeMap[death.cause] || death.cause}`,
    timestamp: new Date(),
  })
}

function addDialogueLog(d) {
  const actionMap = {
    night_kill: `🐺 ${d.player_name} 投票击杀 玩家${d.target}`,
    seer_check: {
      good: `🔮 ${d.player_name} 查验 玩家${d.target} → 好人`,
      wolf: `🔮 ${d.player_name} 查验 玩家${d.target} → 狼人`,
    },
    heal: `🧪 ${d.player_name} 使用解药 救活 玩家${d.target}`,
    poison: `🧪 ${d.player_name} 使用毒药 毒杀 玩家${d.target}`,
    hunter_shot: `🏹 ${d.player_name} 开枪带走 玩家${d.target}`,
    speech: `💬 ${d.player_name}："${d.content}"`,
    vote: `🗳️ ${d.player_name} 投票给 玩家${d.target}`,
  }

  let text = ''
  if (d.action === 'seer_check') {
    text = actionMap.seer_check[d.result]
  } else {
    text = actionMap[d.action]
  }

  if (!text) return

  stepLog.value.push({
    id: Date.now() + Math.random(),
    type: 'dialogue',
    player_id: d.player_id,
    action: d.action,
    text,
    timestamp: new Date(),
  })
}

function processStepResponse(resp) {
  // Phase transition announcements
  const isNight = ['night_wolf', 'night_seer', 'night_witch', 'night_result'].includes(resp.phase)
  if (resp.phase === 'night_wolf') {
    addPhaseLog(resp.phase, `🌙 第 ${resp.day_number} 夜 开始`)
  } else if (resp.phase === 'day_start') {
    addPhaseLog(resp.phase, `☀️ 第 ${resp.day_number} 天 开始`)
  } else if (resp.phase === 'day_end') {
    addPhaseLog(resp.phase, `📊 第 ${resp.day_number - 1} 天 结束`)
  } else if (resp.phase === 'summary') {
    addPhaseLog(resp.phase, `📋 生成玩家总结...`)
  } else if (resp.phase === 'game_over') {
    addPhaseLog(resp.phase, `🏁 游戏结束`)
  }

  // Process dialogues
  if (resp.dialogues) {
    for (const d of resp.dialogues) {
      addDialogueLog(d)
    }
  }

  // Process deaths
  if (resp.deaths) {
    for (const death of resp.deaths) {
      addDeathLog(death)
    }
  }

  // Game over
  if (resp.is_game_over) {
    const winnerText = resp.winner === 'good' ? '善良阵营（好人）' : resp.winner === 'evil' ? '邪恶阵营（狼人）' : resp.winner || '未知'
    stepLog.value.push({
      id: Date.now() + Math.random(),
      type: 'gameover',
      text: `🏆 游戏结束！胜利方：${winnerText}`,
      timestamp: new Date(),
    })
    isGameOver.value = true
    stopAutoPlay()

    // Fetch summaries
    fetchSummaries()
  }
}

async function fetchSummaries() {
  try {
    const data = await getGameSummaries(gameId.value)
    summaries.value = data.summaries || []
  } catch (e) {
    console.error('获取总结失败:', e)
  }
}

async function handleCreate(configName, shuffle) {
  creating.value = true
  try {
    // Reset state
    stepLog.value = []
    isGameOver.value = false
    isAutoPlaying.value = false
    stopAutoPlay()

    const result = await createGame(configName, shuffle)
    gameId.value = result.game_id

    // Fetch full game status
    const status = await getGameStatus(result.game_id)
    gameStatus.value = status
  } catch (e) {
    alert('创建游戏失败: ' + e.message)
  } finally {
    creating.value = false
  }
}

async function handleStep() {
  if (!gameId.value || stepping.value) return
  stepping.value = true
  try {
    const resp = await stepGame(gameId.value)
    processStepResponse(resp)
    // Update game status
    gameStatus.value = await getGameStatus(gameId.value)
  } catch (e) {
    console.error('推进游戏失败:', e)
    stopAutoPlay()
  } finally {
    stepping.value = false
  }
}

function handleAutoPlay() {
  if (isAutoPlaying.value) return
  isAutoPlaying.value = true

  autoPlayTimer = setInterval(async () => {
    if (isGameOver.value) {
      stopAutoPlay()
      return
    }
    try {
      const resp = await stepGame(gameId.value)
      processStepResponse(resp)
      gameStatus.value = await getGameStatus(gameId.value)
    } catch (e) {
      console.error('自动推进失败:', e)
      stopAutoPlay()
    }
  }, 2000)
}

function handlePause() {
  stopAutoPlay()
}

async function handleReset() {
  stopAutoPlay()
  if (gameId.value) {
    try {
      await deleteGame(gameId.value)
    } catch (e) {
      // Game might already be gone
    }
  }
  gameId.value = null
  gameStatus.value = null
  stepLog.value = []
  summaries.value = []
  isGameOver.value = false
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  text-align: center;
  padding: 24px 0 20px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 24px;
}

.app-title {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 1px;
}

.app-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

.app-main {
  min-height: calc(100vh - 140px);
}
</style>
