<template>
  <div class="log-container">
    <h3 class="log-title">📜 游戏日志</h3>
    <div class="log-list" ref="logListRef">
      <div
        v-for="entry in logEntries"
        :key="entry.id"
        class="log-entry"
        :class="'log-' + entry.type"
      >
        <span class="log-time">{{ formatTime(entry.timestamp) }}</span>
        <span class="log-text">{{ entry.text }}</span>
      </div>
      <div v-if="logEntries.length === 0" class="log-empty">
        暂无日志，等待游戏开始...
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logEntries: { type: Array, default: () => [] },
})

const logListRef = ref(null)

watch(
  () => props.logEntries.length,
  async () => {
    await nextTick()
    if (logListRef.value) {
      logListRef.value.scrollTop = logListRef.value.scrollHeight
    }
  }
)

function formatTime(date) {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}
</script>

<style scoped>
.log-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  overflow: hidden;
}

.log-title {
  font-size: 14px;
  font-weight: 600;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.log-list {
  max-height: 320px;
  overflow-y: auto;
  padding: 8px 0;
}

.log-list::-webkit-scrollbar {
  width: 6px;
}

.log-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.log-entry {
  padding: 4px 16px;
  font-size: 13px;
  line-height: 1.6;
  display: flex;
  gap: 8px;
}

.log-entry:hover {
  background: var(--bg-hover);
}

.log-time {
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
  font-family: monospace;
  padding-top: 1px;
}

.log-text {
  flex: 1;
}

.log-phase .log-text {
  color: var(--accent-blue);
  font-weight: 600;
}

.log-death .log-text {
  color: var(--accent-red);
}

.log-gameover .log-text {
  color: var(--accent-yellow);
  font-size: 15px;
  font-weight: 700;
}

.log-empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}
</style>
