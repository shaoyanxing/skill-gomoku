<template>
  <div class="panel status-bar">
    <div class="players">
      <div class="p" :class="{ active: store.currentTurn === 'B' && !store.winner }">
        <span class="dot black"></span>
        <span class="pname">{{ nameOf('B') }}</span>
        <span class="warn"><i v-for="i in 3" :key="i" :class="warnClass('B', i)"></i></span>
      </div>
      <span class="vs">VS</span>
      <div class="p" :class="{ active: store.currentTurn === 'W' && !store.winner }">
        <span class="dot white"></span>
        <span class="pname">{{ nameOf('W') }}</span>
        <span class="warn"><i v-for="i in 3" :key="i" :class="warnClass('W', i)"></i></span>
      </div>
    </div>
    <div class="stats">
      <span class="chip">👣 {{ store.stepCount }} 步</span>
      <span class="chip" :class="{ hot: store.stepsUntilForced === 0 }">
        {{ store.stepsUntilForced === 0 ? '⚡ 强制技能回合' : `⚡ ${store.stepsUntilForced} 步后强制技能` }}
      </span>
      <span class="chip phase">{{ store.phaseText }}</span>
    </div>
    <div class="flags" v-if="hasFlags">
      <span v-if="store.peaceRounds" class="flag peace">☯️ 无为而治 剩 {{ store.peaceRounds }} 回合</span>
      <span v-if="store.color && store.silenced[store.color]" class="flag silence">💧 你的技能被封印</span>
      <span v-if="store.color && store.immune[store.color]" class="flag shield">🛡️ 不动如山护体</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '../stores/gameStore'

const store = useGameStore()

const nameOf = (c) => {
  const p = store.players.find(pl => pl.color === c)
  const base = p ? p.name : (c === 'B' ? '黑方' : '白方')
  return store.color === c ? `${base}（你）` : base
}

const warnClass = (c, i) => (store.warnings[c] >= i ? `lit lit-${i}` : '')

const hasFlags = computed(() =>
  store.peaceRounds > 0 ||
  (store.color && (store.silenced[store.color] || store.immune[store.color]))
)
</script>

<style scoped>
.panel {
  background: #23243d;
  border: 1px solid #34365a;
  border-radius: 14px;
  padding: 14px 16px;
}
.players {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.p {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border-radius: 10px;
  border: 1px solid transparent;
  flex: 1;
  min-width: 0;
}
.p.active {
  border-color: #ff69b4;
  background: rgba(255, 105, 180, 0.08);
  box-shadow: 0 0 14px rgba(255, 105, 180, 0.25);
}
.dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot.black { background: radial-gradient(circle at 35% 30%, #555, #000); }
.dot.white { background: radial-gradient(circle at 35% 30%, #fff, #bbb); }
.pname {
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.vs { color: #00d4ff; font-weight: 800; font-size: 12px; }
.warn { display: flex; gap: 3px; margin-left: auto; }
.warn i {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #3a3d5c;
}
.warn i.lit-1 { background: #ffd54f; box-shadow: 0 0 6px #ffd54f; }
.warn i.lit-2 { background: #ff8c00; box-shadow: 0 0 6px #ff8c00; }
.warn i.lit-3 { background: #ff4757; box-shadow: 0 0 6px #ff4757; }
.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
.chip {
  font-size: 12px;
  background: #1a1b2f;
  border: 1px solid #34365a;
  border-radius: 999px;
  padding: 4px 10px;
  color: #aab;
}
.chip.hot {
  color: #fff;
  border-color: #ff8c00;
  background: rgba(255, 140, 0, 0.15);
  animation: blink 1s infinite;
}
.chip.phase { color: #00d4ff; border-color: rgba(0, 212, 255, 0.4); }
@keyframes blink { 50% { opacity: 0.6; } }
.flags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.flag { font-size: 12px; padding: 3px 10px; border-radius: 999px; }
.flag.peace { background: rgba(155, 89, 182, 0.2); color: #c39bd3; }
.flag.silence { background: rgba(30, 144, 255, 0.2); color: #7fbfff; }
.flag.shield { background: rgba(255, 140, 0, 0.18); color: #ffb36b; }
</style>