<template>
  <div class="card-overlay" @click="$emit('close')">
    <div class="sparkles"><i v-for="(s, i) in sparks" :key="i" :style="s"></i></div>
    <div class="card-scene">
      <div class="card" :class="{ flipped }">
        <div class="card-face card-back">
          <span class="back-logo">技</span>
          <span class="back-text">SKILL CARD</span>
        </div>
        <div class="card-face card-front" :style="{ '--cat': catColor }">
          <span class="c-icon">{{ meta ? meta.icon : '🎴' }}</span>
          <span class="c-name">{{ card }}</span>
          <span class="c-cat">{{ catName }}系技能</span>
          <span class="c-effect">{{ meta ? meta.desc : '' }}</span>
        </div>
      </div>
    </div>
    <p class="card-tip">🃏 抽到技能卡！本回合可额外使用一次（点击关闭）</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { SKILL_MAP, CATEGORY_COLORS, CATEGORY_NAMES } from '../utils/skills'

const props = defineProps({ card: { type: String, required: true } })
defineEmits(['close'])

const flipped = ref(false)
onMounted(() => { setTimeout(() => { flipped.value = true }, 550) })

const meta = computed(() => SKILL_MAP[props.card])
const catColor = computed(() => CATEGORY_COLORS[meta.value?.category] || '#ff69b4')
const catName = computed(() => CATEGORY_NAMES[meta.value?.category] || '')

const sparks = Array.from({ length: 18 }, () => ({
  left: `${Math.random() * 100}%`,
  top: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 1.5}s`,
  animationDuration: `${1 + Math.random() * 1.5}s`
}))
</script>

<style scoped>
.card-overlay {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 25, 0.72);
  backdrop-filter: blur(4px);
  cursor: pointer;
  overflow: hidden;
}
.sparkles { position: absolute; inset: 0; pointer-events: none; }
.sparkles i {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #ffd54f;
  box-shadow: 0 0 8px #ffd54f;
  animation: twinkle 1.6s ease-in-out infinite;
}
@keyframes twinkle {
  0%, 100% { opacity: 0; transform: scale(0.4); }
  50% { opacity: 1; transform: scale(1.4); }
}
.card-scene {
  perspective: 1000px;
  animation: cardIn 0.55s cubic-bezier(0.2, 0.9, 0.3, 1.4);
}
@keyframes cardIn {
  from { transform: translateY(90px) scale(0.5) rotateZ(-10deg); opacity: 0; }
  to { transform: translateY(0) scale(1) rotateZ(0); opacity: 1; }
}
.card {
  width: 190px;
  height: 270px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.8s cubic-bezier(0.3, 0.7, 0.3, 1);
}
.card.flipped { transform: rotateY(180deg); }
.card-face {
  position: absolute;
  inset: 0;
  border-radius: 16px;
  backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 18px;
}
.card-back {
  background: linear-gradient(150deg, #ff69b4, #9b59b6 70%);
  border: 3px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 16px 44px rgba(255, 105, 180, 0.45);
}
.back-logo {
  font-size: 64px;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
}
.back-text { color: rgba(255, 255, 255, 0.75); font-size: 12px; letter-spacing: 4px; }
.card-front {
  transform: rotateY(180deg);
  background: linear-gradient(160deg, #ffffff, #eef0f8);
  border: 4px solid var(--cat, #ff69b4);
  box-shadow: 0 16px 44px rgba(0, 0, 0, 0.5), 0 0 30px var(--cat, #ff69b4);
  color: #222;
}
.c-icon { font-size: 52px; }
.c-name { font-size: 22px; font-weight: 800; color: #1a1b2f; }
.c-cat {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: var(--cat, #ff69b4);
  padding: 2px 12px;
  border-radius: 999px;
}
.c-effect { font-size: 12px; color: #556; text-align: center; line-height: 1.6; }
.card-tip {
  margin-top: 26px;
  font-size: 15px;
  font-weight: 700;
  color: #ffd54f;
  text-shadow: 0 2px 10px rgba(255, 213, 79, 0.5);
  animation: glow 1.4s ease-in-out infinite;
}
@keyframes glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>