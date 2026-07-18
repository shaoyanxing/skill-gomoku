import { defineStore } from 'pinia'
import axios from 'axios'
import { GameSocket } from '../utils/websocket'
import { SKILL_MAP } from '../utils/skills'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'

const emptyBoard = () => Array.from({ length: 15 }, () => Array(15).fill(''))

let socket = null
let diceTimer = null
let cardShowTimer = null
let cardHideTimer = null

export const useGameStore = defineStore('game', {
  state: () => ({
    screen: 'lobby',            // lobby | game
    loading: false,
    lobbyError: '',
    roomId: '',
    playerId: '',
    playerName: '',
    color: '',
    mode: 'pvp',
    connected: false,
    players: [],
    board: emptyBoard(),
    currentTurn: 'B',
    stepCount: 0,
    warnings: { B: 0, W: 0 },
    skillsRemaining: { B: {}, W: {} },
    frozenZones: [],
    peaceRounds: 0,
    lastMove: null,
    winner: '',
    winReason: '',
    // 骰子 / 抽卡
    diceValue: null,
    turnPhase: 'roll',          // roll | move | skill | move_or_skill
    drawnCard: null,
    forcedSkill: false,
    diceRolling: false,
    cardOverlay: false,
    // 技能选择
    selectedSkill: null,
    zhFrom: null,               // 纵横天下已选起点
    // 状态标记
    immune: { B: false, W: false },
    silenced: { B: false, W: false },
    logs: [],
    toast: null
  }),
  getters: {
    isMyTurn(s) { return !!s.color && s.currentTurn === s.color && !s.winner },
    mySkills(s) { return s.skillsRemaining[s.color] || {} },
    opponentInfo(s) { return s.players.find(p => p.color !== s.color) || null },
    stepsUntilForced(s) {
      if (s.stepCount === 0) return 5
      const r = s.stepCount % 5
      return r === 0 ? 0 : 5 - r
    },
    phaseText(s) {
      if (s.winner) return '对局结束'
      switch (s.turnPhase) {
        case 'roll': return '🎲 掷骰阶段'
        case 'move': return '♟️ 落子阶段'
        case 'skill': return '⚡ 强制技能回合'
        case 'move_or_skill': return '🃏 落子 / 使用卡牌'
        default: return ''
      }
    },
    canPlaceStone() {
      return this.isMyTurn && (this.turnPhase === 'move' || this.turnPhase === 'move_or_skill')
    },
    canUseSkill() {
      return this.isMyTurn
        && (this.turnPhase === 'skill' || this.turnPhase === 'move_or_skill')
        && this.peaceRounds === 0
        && !this.silenced[this.color]
    },
    showDice(s) {
      if (s.winner) return false
      if (s.diceRolling) return true
      return !!s.color && s.currentTurn === s.color && s.turnPhase === 'roll'
    }
  },
  actions: {
    addLog(text) {
      this.logs.unshift({ text, time: new Date().toLocaleTimeString() })
      if (this.logs.length > 50) this.logs.pop()
    },
    showToast(text, type = 'info') {
      const id = Date.now()
      this.toast = { text, type, id }
      setTimeout(() => { if (this.toast && this.toast.id === id) this.toast = null }, 2600)
    },
    async createRoom(name, mode) {
      this.loading = true
      this.lobbyError = ''
      try {
        const { data } = await axios.post(`${API_BASE}/api/room/create`, { player_name: name, mode })
        this.setupSession(data, name)
      } catch (e) {
        this.lobbyError = e.response?.data?.detail || '创建房间失败，请确认后端已启动'
      } finally {
        this.loading = false
      }
    },
    async joinRoom(name, roomId) {
      this.loading = true
      this.lobbyError = ''
      try {
        const { data } = await axios.post(`${API_BASE}/api/room/join`, { player_name: name, room_id: roomId })
        this.setupSession(data, name)
      } catch (e) {
        this.lobbyError = e.response?.data?.detail || '加入房间失败'
      } finally {
        this.loading = false
      }
    },
    setupSession(data, name) {
      this.roomId = data.room_id
      this.playerId = data.player_id
      this.color = data.color
      this.playerName = name
      this.mode = data.mode || 'pvp'
      this.screen = 'game'
      this.connectWs()
    },
    connectWs() {
      if (socket) socket.close()
      const url = `${WS_BASE}/ws/room/${this.roomId}/${this.playerId}`
      socket = new GameSocket(url, {
        onMessage: (msg) => this.onMessage(msg),
        onOpen: () => { this.connected = true; this.addLog('已连接到房间') },
        onClose: () => { this.connected = false }
      })
      socket.connect()
    },
    onMessage(msg) {
      if (msg.type === 'sync') {
        this.applySync(msg.data)
      } else if (msg.type === 'event') {
        this.addLog(msg.data.msg)
        if (['warning', 'win', 'card'].includes(msg.data.type)) this.showToast(msg.data.msg, msg.data.type)
      } else if (msg.type === 'error') {
        this.showToast(msg.data.msg || '操作失败', 'error')
      }
    },
    applySync(data) {
      const prevDice = this.diceValue
      const prevCard = this.drawnCard
      this.board = data.board
      this.currentTurn = data.current_turn
      this.stepCount = data.step_count
      this.warnings = data.warnings
      this.skillsRemaining = data.skills_remaining
      this.frozenZones = data.frozen_zones
      this.peaceRounds = data.peace_rounds
      this.lastMove = data.last_move
      this.winner = data.winner
      this.winReason = data.win_reason
      this.turnPhase = data.turn_phase
      this.forcedSkill = data.forced_skill
      this.players = data.players || []
      this.immune = data.immune || { B: false, W: false }
      this.silenced = data.silenced || { B: false, W: false }
      this.drawnCard = data.drawn_card
      // 骰子动画：出现新骰子值时触发滚动动画
      if (data.dice_value && data.dice_value !== prevDice) {
        this.diceValue = data.dice_value
        this.diceRolling = true
        clearTimeout(diceTimer)
        diceTimer = setTimeout(() => { this.diceRolling = false }, 1500)
      } else {
        this.diceValue = data.dice_value
      }
      // 抽卡动画：骰子动画结束后弹出
      if (data.drawn_card && data.drawn_card !== prevCard) {
        clearTimeout(cardShowTimer)
        clearTimeout(cardHideTimer)
        cardShowTimer = setTimeout(() => {
          this.cardOverlay = true
          cardHideTimer = setTimeout(() => { this.cardOverlay = false }, 3200)
        }, 1600)
      }
      if (!data.drawn_card) this.cardOverlay = false
    },
    rollDice() {
      if (!this.isMyTurn || this.turnPhase !== 'roll' || this.diceRolling) return
      this.diceRolling = true
      if (!(socket && socket.send({ type: 'roll' }))) {
        this.diceRolling = false
        this.showToast('连接已断开，正在重连…', 'error')
      }
    },
    clickCell(x, y) {
      if (!this.isMyTurn || this.winner) return
      if (this.selectedSkill) {
        const meta = SKILL_MAP[this.selectedSkill]
        if (meta && meta.twoStep) {
          if (!this.zhFrom) {
            if (this.board[y][x] !== this.color) {
              this.showToast('纵横天下：请先点击要传送的己方棋子', 'error')
              return
            }
            this.zhFrom = [x, y]
            this.showToast('再点击一个空位作为传送落点', 'info')
            return
          }
          this.sendSkill(this.selectedSkill, x, y, { from_x: this.zhFrom[0], from_y: this.zhFrom[1] })
          this.zhFrom = null
          return
        }
        if (meta && meta.needsTarget) {
          this.sendSkill(this.selectedSkill, x, y, {})
          return
        }
        this.sendSkill(this.selectedSkill, null, null, {})
        return
      }
      if (this.turnPhase === 'roll') { this.showToast('请先掷骰 🎲', 'error'); return }
      if (this.turnPhase === 'skill') { this.showToast('⚡ 强制技能回合：请使用技能', 'error'); return }
      if (!this.canPlaceStone) return
      socket && socket.send({ type: 'move', data: { x, y } })
    },
    selectSkill(name) {
      if (!this.isMyTurn) { this.showToast('还没轮到你', 'error'); return }
      if (this.turnPhase === 'roll') { this.showToast('请先掷骰 🎲', 'error'); return }
      if (this.turnPhase === 'move') { this.showToast('骰子为单数：本回合只能落子', 'error'); return }
      if (this.peaceRounds > 0) { this.showToast('无为而治生效中，技能禁用', 'error'); return }
      if (this.silenced[this.color]) { this.showToast('你的技能被封印中', 'error'); return }
      if ((this.mySkills[name] || 0) <= 0) { this.showToast('该技能次数已用尽', 'error'); return }
      const meta = SKILL_MAP[name]
      this.zhFrom = null
      if (meta && (meta.needsTarget || meta.twoStep)) {
        this.selectedSkill = this.selectedSkill === name ? null : name
        if (this.selectedSkill) {
          this.showToast(meta.twoStep ? '纵横天下：先点击要传送的己方棋子' : `点击棋盘选择【${name}】的目标`, 'info')
        }
      } else {
        this.sendSkill(name, null, null, {})
      }
    },
    sendSkill(name, tx, ty, extra) {
      const ok = socket && socket.send({
        type: 'skill',
        data: { skill_name: name, target_x: tx, target_y: ty, extra }
      })
      if (ok) {
        this.selectedSkill = null
        this.zhFrom = null
      } else {
        this.showToast('连接已断开，正在重连…', 'error')
      }
    },
    closeCard() {
      this.cardOverlay = false
      clearTimeout(cardHideTimer)
    },
    resetToLobby() {
      if (socket) { socket.close(); socket = null }
      clearTimeout(diceTimer)
      clearTimeout(cardShowTimer)
      clearTimeout(cardHideTimer)
      this.$reset()
    }
  }
})