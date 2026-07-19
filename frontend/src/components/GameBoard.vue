<template>
  <div class="board-wrap">
    <canvas
      ref="canvasRef"
      :width="size"
      :height="size"
      @click="onClick"
      @mousemove="onMove"
      @mouseleave="hover = null"
    ></canvas>
    <transition name="fade">
      <div v-if="aiThinking" class="ai-banner">🤖 AI 思考中…</div>
    </transition>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useGameStore } from '../stores/gameStore'

const store = useGameStore()
const canvasRef = ref(null)
const hover = ref(null)
const padding = 34
const cell = 40
const size = padding * 2 + cell * 14
let raf = null

const toPixel = (i) => padding + i * cell
const aiThinking = computed(() =>
  store.mode === 'ai' && !store.winner && store.currentTurn !== store.color && !store.diceRolling
)

function roundRectPath(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.arcTo(x + w, y, x + w, y + h, r)
  ctx.arcTo(x + w, y + h, x, y + h, r)
  ctx.arcTo(x, y + h, x, y, r)
  ctx.arcTo(x, y, x + w, y, r)
  ctx.closePath()
}

function drawStone(ctx, x, y, color) {
  const cx = toPixel(x)
  const cy = toPixel(y)
  const r = cell * 0.44
  ctx.save()
  ctx.shadowColor = 'rgba(0, 0, 0, 0.45)'
  ctx.shadowBlur = 6
  ctx.shadowOffsetY = 3
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  const g = ctx.createRadialGradient(cx - r * 0.35, cy - r * 0.35, r * 0.15, cx, cy, r)
  if (color === 'B') {
    g.addColorStop(0, '#666')
    g.addColorStop(0.4, '#222')
    g.addColorStop(1, '#000')
  } else {
    g.addColorStop(0, '#fff')
    g.addColorStop(0.7, '#f2f2f2')
    g.addColorStop(1, '#c9c9c9')
  }
  ctx.fillStyle = g
  ctx.fill()
  ctx.restore()
}

function ring(ctx, x, y, color, t) {
  const pulse = 1 + 0.12 * Math.sin(t * 5)
  ctx.beginPath()
  ctx.arc(toPixel(x), toPixel(y), cell * 0.5 * pulse, 0, Math.PI * 2)
  ctx.strokeStyle = color
  ctx.lineWidth = 2.5
  ctx.stroke()
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) {
    raf = requestAnimationFrame(draw)
    return
  }
  const ctx = canvas.getContext('2d')
  const t = performance.now() / 1000
  // 木纹底色
  const g = ctx.createLinearGradient(0, 0, size, size)
  g.addColorStop(0, '#eccb9e')
  g.addColorStop(1, '#dcb17e')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, size, size)
  // 网格
  ctx.strokeStyle = 'rgba(90, 60, 20, 0.7)'
  ctx.lineWidth = 1
  for (let i = 0; i < 15; i++) {
    ctx.beginPath(); ctx.moveTo(toPixel(0), toPixel(i)); ctx.lineTo(toPixel(14), toPixel(i)); ctx.stroke()
    ctx.beginPath(); ctx.moveTo(toPixel(i), toPixel(0)); ctx.lineTo(toPixel(i), toPixel(14)); ctx.stroke()
  }
  ctx.lineWidth = 2.5
  ctx.strokeStyle = 'rgba(90, 60, 20, 0.9)'
  ctx.strokeRect(toPixel(0), toPixel(0), cell * 14, cell * 14)
  // 星位 + 天元
  for (const [sx, sy] of [[3, 3], [3, 11], [11, 3], [11, 11], [7, 7]]) {
    ctx.beginPath()
    ctx.arc(toPixel(sx), toPixel(sy), 4.5, 0, Math.PI * 2)
    ctx.fillStyle = '#5a3c14'
    ctx.fill()
  }
  // 冰冻区域（冰晶脉冲）
  for (const z of store.frozenZones) {
    const pulse = 0.22 + 0.13 * Math.sin(t * 4)
    const x0 = toPixel(z.x - 1) - cell / 2
    const y0 = toPixel(z.y - 1) - cell / 2
    roundRectPath(ctx, x0, y0, cell * 3, cell * 3, 10)
    ctx.fillStyle = `rgba(30, 144, 255, ${pulse})`
    ctx.fill()
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.85)'
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.font = '18px serif'
    ctx.fillStyle = 'rgba(255, 255, 255, 0.95)'
    ctx.fillText('❄', toPixel(z.x) - 9, toPixel(z.y) + 7)
  }
  // 悬停预览
  if (hover.value && store.isMyTurn && !store.winner && store.turnPhase !== 'roll') {
    const [hx, hy] = hover.value
    if (!store.board[hy][hx]) {
      ctx.beginPath()
      ctx.arc(toPixel(hx), toPixel(hy), cell * 0.42, 0, Math.PI * 2)
      ctx.fillStyle = store.selectedSkill
        ? 'rgba(255, 105, 180, 0.55)'
        : (store.color === 'B' ? 'rgba(0, 0, 0, 0.35)' : 'rgba(255, 255, 255, 0.55)')
      ctx.fill()
    }
  }
  // 棋子
  for (let y = 0; y < 15; y++) {
    for (let x = 0; x < 15; x++) {
      const c = store.board[y][x]
      if (c) drawStone(ctx, x, y, c)
    }
  }
  // 纵横天下起点 / 最后落子标记
  if (store.zhFrom) ring(ctx, store.zhFrom[0], store.zhFrom[1], '#9b59b6', t)
  if (store.lastMove) ring(ctx, store.lastMove[0], store.lastMove[1], '#ff69b4', t)
  raf = requestAnimationFrame(draw)
}

function pick(e) {
  const rect = canvasRef.value.getBoundingClientRect()
  const scale = size / rect.width
  const px = (e.clientX - rect.left) * scale
  const py = (e.clientY - rect.top) * scale
  const x = Math.round((px - padding) / cell)
  const y = Math.round((py - padding) / cell)
  if (x < 0 || x > 14 || y < 0 || y > 14) return null
  if (Math.abs(px - toPixel(x)) > cell / 2 || Math.abs(py - toPixel(y)) > cell / 2) return null
  return [x, y]
}

function onClick(e) {
  const p = pick(e)
  if (p) store.clickCell(p[0], p[1])
}

function onMove(e) {
  hover.value = pick(e)
}

onMounted(() => { raf = requestAnimationFrame(draw) })
onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<style scoped>
.board-wrap { position: relative; display: flex; justify-content: center; }
canvas {
  width: 100%;
  max-width: 640px;
  height: auto;
  border-radius: 14px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.55), 0 0 0 6px #2a2c47, 0 0 0 8px #3d2f1c;
  cursor: pointer;
}

.ai-banner {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(35, 36, 61, 0.9);
  border: 1px solid #00d4ff;
  color: #00d4ff;
  padding: 6px 18px;
  border-radius: 999px;
  font-size: 13px;
  pointer-events: none;
}
@keyframes pulse {
  0%, 100% { transform: translateX(-50%) scale(1); }
  50% { transform: translateX(-50%) scale(1.06); }
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>