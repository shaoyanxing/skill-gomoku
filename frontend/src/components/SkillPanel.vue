<template>
  <div class="panel skill-panel">
    <div class="panel-title">
      <span>🃏 技能面板</span>
      <span v-if="store.drawnCard && store.isMyTurn" class="card-hint">本回合卡牌：{{ store.drawnCard }}</span>
    </div>
    <div class="skill-grid">
      <button
        v-for="s in SKILLS"
        :key="s.name"
        class="skill-btn"
        :class="{ selected: store.selectedSkill === s.name, disabled: isDisabled(s.name), drawn: store.drawnCard === s.name && store.isMyTurn }"
        :style="{ '--cat': CATEGORY_COLORS[s.category] }"
        :title="`${s.desc}（${CATEGORY_NAMES[s.category]}系）`"
        @click="store.selectSkill(s.name)"
      >
        <span class="icon">{{ s.icon }}</span>
        <span class="name">{{ s.name }}</span>
        <span class="count">{{ remaining(s.name) }}</span>
      </button>
    </div>
    <p class="tip">💡 骰子双数抽卡 · 每 5 步强制技能 · 三次犯规判负</p>
  </div>
</template>

<script setup>
import { useGameStore } from '../stores/gameStore'
import { SKILLS, CATEGORY_COLORS, CATEGORY_NAMES } from '../utils/skills'

const store = useGameStore()
const remaining = (name) => store.mySkills[name] ?? 0
const isDisabled = (name) => remaining(name) <= 0 || !store.canUseSkill
</script>

<style scoped>
.panel {
  background: #23243d;
  border: 1px solid #34365a;
  border-radius: 14px;
  padding: 14px 16px;
}
.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 10px;
}
.card-hint {
  font-size: 11px;
  color: #ff69b4;
  background: rgba(255, 105, 180, 0.12);
  border: 1px solid rgba(255, 105, 180, 0.4);
  padding: 2px 8px;
  border-radius: 999px;
  animation: blink 1.2s infinite;
}
@keyframes blink { 50% { opacity: 0.55; } }
.skill-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.skill-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 9px 4px 8px;
  background: #1a1b2f;
  border: 1px solid #34365a;
  border-left: 3px solid var(--cat, #666);
  border-radius: 10px;
  color: #e8eaf6;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}
.skill-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 14px rgba(0, 0, 0, 0.4); }
.skill-btn .icon { font-size: 20px; line-height: 1; }
.skill-btn .name { font-size: 12px; font-weight: 600; }
.skill-btn .count {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: #ff69b4;
  border-radius: 999px;
  padding: 0 4px;
  box-shadow: 0 2px 6px rgba(255, 105, 180, 0.5);
}
.skill-btn.selected {
  border-color: var(--cat);
  box-shadow: 0 0 0 2px var(--cat), 0 0 18px var(--cat);
}
.skill-btn.drawn {
  background: linear-gradient(135deg, rgba(255, 105, 180, 0.18), rgba(155, 89, 182, 0.18));
  border-color: #ff69b4;
}
.skill-btn.disabled {
  filter: grayscale(1);
  opacity: 0.45;
  cursor: not-allowed;
}
.skill-btn.disabled::after {
  content: '✕';
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #ff4757;
  text-shadow: 0 0 6px #000;
}
.tip { margin-top: 10px; font-size: 11px; color: #778; }
</style>