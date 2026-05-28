<template>
  <div class="player-card" :class="{ dead: !player.is_alive, [player.camp]: true }">
    <div class="status-dot" :class="player.is_alive ? 'alive' : 'dead'"></div>

    <div class="player-id">#{{ player.player_id }}</div>
    <div class="player-name">{{ player.name }}</div>

    <div class="player-role" :class="'role-' + player.role">
      {{ roleLabel }}
    </div>

    <div class="player-camp">
      <span :class="'camp-tag ' + player.camp">
        {{ player.camp === 'good' ? '好人' : '狼人' }}
      </span>
    </div>

    <div v-if="player.is_sheriff" class="sheriff-badge">👑 警长</div>
    <div v-if="!player.is_alive" class="dead-badge">💀 已出局</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  player: { type: Object, required: true },
})

const roleLabels = {
  werewolf: '🐺 狼人',
  seer: '🔮 预言家',
  witch: '🧪 女巫',
  hunter: '🏹 猎人',
  villager: '👤 村民',
  idiot: '🃏 白痴',
}

const roleLabel = computed(() => {
  return roleLabels[props.player.role] || props.player.role
})
</script>

<style scoped>
.player-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px 12px;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
}

.player-card.good {
  border-left: 3px solid var(--good-color);
}

.player-card.evil {
  border-left: 3px solid var(--evil-color);
}

.player-card.dead {
  opacity: 0.5;
  background: #111;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  position: absolute;
  top: 10px;
  right: 10px;
}

.status-dot.alive {
  background: var(--accent-green);
  box-shadow: 0 0 6px var(--accent-green);
}

.status-dot.dead {
  background: var(--accent-red);
}

.player-id {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.player-name {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
}

.player-role {
  font-size: 13px;
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 6px;
}

.role-werewolf { color: var(--wolf-color); }
.role-seer { color: var(--seer-color); }
.role-witch { color: var(--witch-color); }
.role-hunter { color: var(--hunter-color); }
.role-villager { color: var(--villager-color); }

.camp-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.camp-tag.good {
  background: rgba(63, 185, 80, 0.15);
  color: var(--good-color);
}

.camp-tag.evil {
  background: rgba(248, 81, 73, 0.15);
  color: var(--evil-color);
}

.sheriff-badge {
  font-size: 11px;
  margin-top: 4px;
}

.dead-badge {
  font-size: 11px;
  margin-top: 4px;
  color: var(--accent-red);
}
</style>
