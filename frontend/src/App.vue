<template>
  <div class="app">
    <RoomManager v-if="store.screen === 'lobby'" />
    <template v-else>
      <header class="topbar">
        <h1>🀄 技能五子棋</h1>
        <div class="room-info">
          房间 <b>{{ store.roomId }}</b> · {{ store.mode === 'ai' ? '单机 AI' : '联机对战' }} ·
          <span :class="{ offline: !store.connected }">{{ store.connected ? '已连接' : '连接中…' }}</span>
        </div>
        <button class="leave" @click="store.resetToLobby()">离开房间</button>
      </header>
      <main class="layout">
        <section class="left">
          <GameBoard />
        </section>
        <aside class="right">
          <StatusBar />
          <SkillPanel />
          <div class="panel log-panel">
            <div class="panel-title">📜 操作日志</div>
            <ul>
              <li v-for="(l, i) in store.logs.slice(0, 10)" :key="i">
                <time>{{ l.time }}</time>{{ l.text }}
              </li>
              <li v-if="!store.logs.length" class="empty">暂无记录</li>
            </ul>
          </div>
        </aside>
      </main>

      <!-- 等待对手 -->
      <div v-if="store.mode === 'pvp' && store.players.length < 2 && !store.winner" class="overlay">
        <div class="loader"></div>
        <p class="wait-text">等待对手加入…</p>
        <p class="room-code">房间号：<b>{{ store.roomId }}</b>（分享给好友即可加入）</p>
      </div>

      <!-- 3D 骰子 -->
      <Dice3D
        v-if="store.showDice"
        :value="store.diceValue"
        :rolling="store.diceRolling"
        :clickable="store.isMyTurn && store.turnPhase === 'roll'"
        :label="diceLabel"
        @roll="store.rollDice()"
      />

      <!-- 抽卡动画 -->
      <CardDraw v-if="store.cardOverlay && store.drawnCard" :card="store.drawnCard" @close="store.closeCard()" />

      <!-- 结算 -->
      <div v-if="store.winner" class="overlay">
        <div class="winner-card">
          <div class="trophy">🏆</div>
          <h2>{{ winnerText }}</h2>
          <p>{{ store.winReason }}</p>
          <button @click="store.resetToLobby()">返回大厅</button>
        </div>
      </div>

      <!-- 全局提示 -->
      <transition name="toast">
        <div v-if="store.toast" class="toast" :class="store.toast.type">{{ store.toast.text }}</div>
      </transition>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from './stores/gameStore'
import RoomManager from './components/RoomManager.vue'
import GameBoard from './components/GameBoard.vue'
import SkillPanel from './components/SkillPanel.vue'
import StatusBar from './components/StatusBar.vue'
import Dice3D from './components/Dice3D.vue'
import CardDraw from './components/CardDraw.vue'

const store = useGameStore()

const diceLabel = computed(() => {
  if (store.diceRolling && store.diceValue) {
    return `🎲 ${store.diceValue} 点！${store.diceValue % 2 === 1 ? '单数 · 本回合落子' : '双数 · 抽取技能卡'}`
  }
  if (store.diceRolling) return '🎲 掷骰中…'
  if (store.isMyTurn && store.turnPhase === 'roll') return '🎲 点击骰子，决定本回合命运'
  return '对方掷骰中…'
})

const winnerText = computed(() => {
  if (!store.winner) return ''
  if (store.winner === store.color) return '🎉 你赢了！'
  const p = store.players.find(pl => pl.color === store.winner)
  return `${p ? p.name : (store.winner === 'B' ? '黑方' : '白方')} 获胜！`
})
</script>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 22px;
  background: #23243d;
  border-bottom: 2px solid transparent;
  border-image: linear-gradient(90deg, #ff69b4, #00d4ff) 1;
}
.topbar h1 {
  font-size: 18px;
  background: linear-gradient(90deg, #ff69b4, #00d4ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.room-info { font-size: 13px; color: #99a; }
.room-info b { color: #ffd54f; letter-spacing: 1px; }
.room-info .offline { color: #ff4757; }
.leave {
  margin-left: auto;
  background: #2a2c47;
  border: 1px solid #34365a;
  color: #aab;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 12px;
}
.leave:hover { color: #ff69b4; border-color: #ff69b4; }
.layout {
  flex: 1;
  display: flex;
  gap: 18px;
  padding: 18px 22px;
  align-items: flex-start;
}
.left { flex: 7; min-width: 0; }
.right {
  flex: 3;
  min-width: 300px;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.panel {
  background: #23243d;
  border: 1px solid #34365a;
  border-radius: 14px;
  padding: 14px 16px;
}
.panel-title { font-size: 14px; font-weight: 700; margin-bottom: 8px; }
.log-panel ul { list-style: none; max-height: 180px; overflow-y: auto; }
.log-panel li {
  font-size: 12px;
  color: #bbc;
  padding: 4px 0;
  border-bottom: 1px dashed #2c2e4a;
  line-height: 1.5;
}
.log-panel li time { color: #667; margin-right: 8px; font-size: 11px; }
.log-panel li.empty { color: #556; border: none; }
.overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background: rgba(10, 10, 25, 0.75);
  backdrop-filter: blur(4px);
}
.loader {
  width: 46px;
  height: 46px;
  border: 4px solid #34365a;
  border-top-color: #ff69b4;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.wait-text { font-size: 16px; font-weight: 700; }
.room-code { font-size: 13px; color: #99a; }
.room-code b { color: #ffd54f; font-size: 18px; letter-spacing: 2px; }
.winner-card {
  background: #23243d;
  border: 1px solid #34365a;
  border-radius: 20px;
  padding: 40px 56px;
  text-align: center;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.6), 0 0 50px rgba(255, 105, 180, 0.25);
  animation: pop 0.45s cubic-bezier(0.2, 0.9, 0.3, 1.5);
}
@keyframes pop { from { transform: scale(0.6); opacity: 0; } }
.trophy { font-size: 58px; animation: bounce 1.2s ease-in-out infinite; }
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}
.winner-card h2 {
  margin: 12px 0 6px;
  font-size: 26px;
  background: linear-gradient(90deg, #ffd54f, #ff69b4);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.winner-card p { color: #99a; font-size: 14px; margin-bottom: 20px; }
.winner-card button {
  background: linear-gradient(90deg, #ff69b4, #ff8c00);
  border: none;
  color: #fff;
  font-weight: 700;
  padding: 10px 30px;
  border-radius: 999px;
  font-size: 14px;
}
.toast {
  position: fixed;
  top: 70px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 90;
  background: #23243d;
  border: 1px solid #ff69b4;
  color: #fff;
  padding: 10px 22px;
  border-radius: 999px;
  font-size: 13px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  max-width: 80vw;
}
.toast.error { border-color: #ff4757; }
.toast.warning { border-color: #ff8c00; }
.toast.win { border-color: #ffd54f; }
.toast.card { border-color: #9b59b6; }
.toast-enter-active, .toast-leave-active { transition: all 0.25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -12px); }
@media (max-width: 900px) {
  .layout { flex-direction: column; }
  .right { max-width: none; width: 100%; }
}
</style>