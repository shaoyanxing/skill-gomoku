<template>
  <div class="lobby">
    <div class="lobby-card">
      <h1>🀄 技能五子棋</h1>
      <p class="sub">B站物理魔改版 · 技能乱斗五子棋</p>
      <input v-model.trim="name" placeholder="输入你的昵称" maxlength="12" @keyup.enter="create('ai')" />
      <div class="btn-col">
        <button class="primary" :disabled="store.loading" @click="create('ai')">🤖 单机挑战 AI</button>
        <button :disabled="store.loading" @click="create('pvp')">🌐 创建联机房间</button>
        <div class="join-row">
          <input v-model.trim="roomId" placeholder="房间号" maxlength="6" @keyup.enter="join" />
          <button :disabled="store.loading || !roomId" @click="join">加入</button>
        </div>
      </div>
      <p v-if="store.lobbyError" class="err">{{ store.lobbyError }}</p>
      <div class="rules">
        <p>🎲 每回合先掷骰：<b>单数</b>本回合落子，<b>双数</b>抽一张技能卡</p>
        <p>⚡ 每 5 步强制技能回合 · ⚠️ 三次犯规直接判负</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useGameStore } from '../stores/gameStore'

const store = useGameStore()
const name = ref('')
const roomId = ref('')

const nick = () => name.value || `玩家${Math.floor(Math.random() * 9000 + 1000)}`
const create = (mode) => store.createRoom(nick(), mode)
const join = () => { if (roomId.value) store.joinRoom(nick(), roomId.value) }
</script>

<style scoped>
.lobby {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(600px 400px at 20% 20%, rgba(255, 105, 180, 0.12), transparent),
    radial-gradient(600px 400px at 80% 80%, rgba(0, 212, 255, 0.1), transparent),
    #1a1b2f;
  padding: 20px;
}
.lobby-card {
  width: 100%;
  max-width: 400px;
  background: #23243d;
  border: 1px solid #34365a;
  border-radius: 18px;
  padding: 34px 30px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
  text-align: center;
}
h1 {
  font-size: 26px;
  background: linear-gradient(90deg, #ff69b4, #00d4ff);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.sub { color: #889; font-size: 13px; margin: 6px 0 22px; }
input {
  width: 100%;
  padding: 11px 14px;
  border-radius: 10px;
  border: 1px solid #34365a;
  background: #1a1b2f;
  color: #e8eaf6;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}
input:focus { border-color: #ff69b4; }
.btn-col { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }
button {
  padding: 11px;
  border-radius: 10px;
  border: 1px solid #34365a;
  background: #2a2c47;
  color: #e8eaf6;
  font-size: 14px;
  font-weight: 600;
  transition: transform 0.15s, box-shadow 0.15s;
}
button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(0, 0, 0, 0.4); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
button.primary {
  background: linear-gradient(90deg, #ff69b4, #ff8c00);
  border: none;
}
.join-row { display: flex; gap: 8px; }
.join-row input { flex: 1; }
.join-row button { padding: 0 18px; }
.err { color: #ff4757; font-size: 13px; margin-top: 12px; }
.rules {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed #34365a;
  font-size: 12px;
  color: #889;
  line-height: 1.9;
}
.rules b { color: #ff69b4; }
</style>