const BASE = ''

export async function createGame(configName, shuffle = true) {
  const res = await fetch(`${BASE}/games`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ config_name: configName, shuffle }),
  })
  if (!res.ok) throw new Error(`创建游戏失败: ${res.status}`)
  return res.json()
}

export async function stepGame(gameId) {
  const res = await fetch(`${BASE}/games/${gameId}/step`, { method: 'POST' })
  if (!res.ok) throw new Error(`推进游戏失败: ${res.status}`)
  return res.json()
}

export async function getGameStatus(gameId) {
  const res = await fetch(`${BASE}/games/${gameId}`)
  if (!res.ok) throw new Error(`获取游戏状态失败: ${res.status}`)
  return res.json()
}

export async function deleteGame(gameId) {
  const res = await fetch(`${BASE}/games/${gameId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`删除游戏失败: ${res.status}`)
  return res.json()
}

export async function getConfigs() {
  const res = await fetch(`${BASE}/configs`)
  if (!res.ok) throw new Error(`获取配置失败: ${res.status}`)
  return res.json()
}

export async function getGameSummaries(gameId) {
  const res = await fetch(`${BASE}/games/${gameId}/summaries`)
  if (!res.ok) throw new Error(`获取总结失败: ${res.status}`)
  return res.json()
}
