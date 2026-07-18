<template>
  <div class="dice-overlay">
    <div class="dice-box">
      <div class="scene" :class="{ bob: clickable && !rolling, clickable }" @click="onClick">
        <div class="cube" :style="cubeStyle">
          <div v-for="f in 6" :key="f" class="face" :class="'face-' + f">
            <span v-for="i in 9" :key="i" class="cell"><i v-if="PIPS[f].includes(i - 1)" class="pip"></i></span>
          </div>
        </div>
      </div>
      <p class="dice-label">{{ label }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  value: { type: Number, default: null },
  rolling: Boolean,
  clickable: Boolean,
  label: { type: String, default: '' }
})
const emit = defineEmits(['roll'])

// 3x3 网格中每个点数的棋子位置
const PIPS = {
  1: [4],
  2: [0, 8],
  3: [0, 4, 8],
  4: [0, 2, 6, 8],
  5: [0, 2, 4, 6, 8],
  6: [0, 2, 3, 5, 6, 8]
}
// 各面朝前所需的立方体旋转角度 [rx, ry]
const FACE_ROT = {
  1: [0, 0],
  2: [0, -90],
  3: [-90, 0],
  4: [90, 0],
  5: [0, 90],
  6: [0, 180]
}

const spins = ref(0)
watch(() => props.value, (v) => { if (v) spins.value += 1 })

const cubeStyle = computed(() => {
  const [rx, ry] = props.value ? FACE_ROT[props.value] : [0, 0]
  const s = 720 * spins.value
  return { transform: `rotateX(${rx + s}deg) rotateY(${ry + s}deg)` }
})

function onClick() {
  if (props.clickable && !props.rolling) emit('roll')
}
</script>

<style scoped>
.dice-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 25, 0.66);
  backdrop-filter: blur(3px);
}
.dice-box { text-align: center; }
.scene {
  width: 160px;
  height: 160px;
  margin: 0 auto;
  perspective: 700px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.scene.clickable { cursor: pointer; }
.scene.bob { animation: bob 1.6s ease-in-out infinite; }
@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}
.cube {
  width: 100px;
  height: 100px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 1.35s cubic-bezier(0.15, 0.85, 0.25, 1);
}
.face {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template: repeat(3, 1fr) / repeat(3, 1fr);
  padding: 12px;
  background: linear-gradient(145deg, #ffffff, #dfe3f0);
  border-radius: 18px;
  box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.18);
  backface-visibility: hidden;
}
.face-1 { transform: translateZ(50px); }
.face-2 { transform: rotateY(90deg) translateZ(50px); }
.face-3 { transform: rotateX(90deg) translateZ(50px); }
.face-4 { transform: rotateX(-90deg) translateZ(50px); }
.face-5 { transform: rotateY(-90deg) translateZ(50px); }
.face-6 { transform: rotateX(180deg) translateZ(50px); }
.cell { display: flex; align-items: center; justify-content: center; }
.pip {
  width: 72%;
  height: 72%;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #555, #0a0a14);
  box-shadow: inset 0 -2px 3px rgba(0, 0, 0, 0.5);
}
.face-1 .pip, .face-4 .pip {
  background: radial-gradient(circle at 35% 30%, #ff9ecd, #d63384);
}
.dice-label {
  margin-top: 18px;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 12px rgba(255, 105, 180, 0.6);
  animation: glow 1.4s ease-in-out infinite;
}
@keyframes glow {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.65; }
}
</style>