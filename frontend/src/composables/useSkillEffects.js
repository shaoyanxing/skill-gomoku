// 技能效果辅助：目标需求、提示语、分类色（动画由组件根据 anim 字段触发）
import { SKILL_MAP, CATEGORY_COLORS, CATEGORY_NAMES } from '../utils/skills'

export function useSkillEffects() {
  const needsTarget = (name) => {
    const meta = SKILL_MAP[name]
    return !!(meta && (meta.needsTarget || meta.twoStep))
  }

  const targetHint = (name) => {
    const meta = SKILL_MAP[name]
    if (!meta) return ''
    if (meta.twoStep) return '先点选己方棋子，再点选传送落点'
    if (meta.needsTarget) return '点击棋盘选择技能目标'
    return '无需目标，立即生效'
  }

  const categoryColor = (name) => CATEGORY_COLORS[SKILL_MAP[name]?.category] || '#ff69b4'
  const categoryName = (name) => CATEGORY_NAMES[SKILL_MAP[name]?.category] || ''

  return { needsTarget, targetHint, categoryColor, categoryName }
}