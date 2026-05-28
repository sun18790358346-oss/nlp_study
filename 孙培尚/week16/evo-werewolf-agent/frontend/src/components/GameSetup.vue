<template>
  <div class="setup-container">
    <div class="setup-card">
      <h2 class="setup-title">创建新游戏</h2>

      <div class="form-group">
        <label class="form-label">游戏配置</label>
        <select v-model="selectedConfig" class="form-select">
          <option
            v-for="(cfg, key) in configs"
            :key="key"
            :value="key"
          >
            {{ cfg.name }}（{{ cfg.player_count }}人）— {{ cfg.description }}
          </option>
        </select>
        <p class="form-hint" v-if="selectedConfig && configs[selectedConfig]">
          玩家数量：{{ configs[selectedConfig].player_count }} 人
        </p>
      </div>

      <div class="form-group">
        <label class="form-label checkbox-label">
          <input type="checkbox" v-model="shuffle" />
          <span>打乱角色分配</span>
        </label>
      </div>

      <button
        class="primary create-btn"
        :disabled="loading"
        @click="handleCreate"
      >
        {{ loading ? '创建中...' : '🎮 开始游戏' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  configs: { type: Object, required: true },
  loading: { type: Boolean, default: false },
})

const emit = defineEmits(['create'])

const selectedConfig = ref('standard_6')
const shuffle = ref(true)

function handleCreate() {
  emit('create', selectedConfig.value, shuffle.value)
}
</script>

<style scoped>
.setup-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 60px;
}

.setup-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 36px;
  width: 100%;
  max-width: 520px;
}

.setup-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 28px;
  text-align: center;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-primary);
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--accent-green);
}

.form-select {
  width: 100%;
}

.form-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 6px;
}

.create-btn {
  width: 100%;
  padding: 12px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 8px;
}
</style>
