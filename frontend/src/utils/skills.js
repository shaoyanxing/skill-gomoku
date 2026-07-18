// 技能元数据（与后端 SkillName 保持一致）
export const SKILLS = [
  { name: '排山倒海', icon: '🌊', category: 'move', desc: '全体棋子向随机方向平移1格，边界阻挡不动（未移动记犯规）' },
  { name: '飞沙走石', icon: '🌪️', category: 'move', needsTarget: true, desc: '移除目标点的对方棋子，该点本回合禁落（目标无敌子记犯规）' },
  { name: '移花接木', icon: '🎭', category: 'move', desc: '夺取对方活三中的一子，己方随机2子倒戈（全局1次）' },
  { name: '力拔山兮', icon: '⛰️', category: 'move', desc: '全体棋子向随机方向位移1~2格，越界者被震落' },
  { name: '拨云见日', icon: '🌤️', category: 'move', needsTarget: true, desc: '点击选择一行，己方棋子整体左/右移1格' },
  { name: '静如止水', icon: '💧', category: 'freeze', desc: '封印对手下回合的技能' },
  { name: '冰冻三尺', icon: '❄️', category: 'freeze', needsTarget: true, desc: '冻结目标周围3x3区域3回合，禁止落子' },
  { name: '不动如山', icon: '🛡️', category: 'freeze', desc: '本回合己方棋子免疫位移，并反制对手凝结技' },
  { name: '无为而治', icon: '☯️', category: 'yinyang', desc: '双方2回合内禁用所有技能（全局1次）' },
  { name: '暗渡陈仓', icon: '🥷', category: 'yinyang', desc: '在棋子稀疏的3x3区域中心自动落一子' },
  { name: '纵横天下', icon: '👑', category: 'yinyang', needsTarget: true, twoStep: true, desc: '传送己方1子至任意空位，并封印对手下回合技能（全局2次）' }
]

export const SKILL_MAP = Object.fromEntries(SKILLS.map(s => [s.name, s]))

export const CATEGORY_COLORS = {
  move: '#ff8c00',
  freeze: '#1e90ff',
  yinyang: '#9b59b6'
}

export const CATEGORY_NAMES = {
  move: '位移',
  freeze: '凝结',
  yinyang: '阴阳'
}