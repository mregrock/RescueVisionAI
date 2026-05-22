import type { RiskLevel, VictimStatus } from '../api/types'
import {
  RISK_LABEL_RU,
  STATUS_LABEL_RU,
  riskClasses,
  statusClasses,
} from '../utils/labels'

interface RiskBadgeProps {
  risk: RiskLevel
  size?: 'sm' | 'md' | 'lg'
}

export function RiskBadge({ risk, size = 'md' }: RiskBadgeProps) {
  const c = riskClasses(risk)
  const sizeCls =
    size === 'lg'
      ? 'text-base px-4 py-1.5'
      : size === 'sm'
        ? 'text-xs px-2.5 py-0.5'
        : 'text-sm px-3 py-1'
  return (
    <span
      className={`pill border ${c.bg} ${c.text} ${c.border} ${sizeCls} uppercase tracking-wide`}
    >
      <span className={`h-2 w-2 rounded-full ${c.dot}`} />
      {RISK_LABEL_RU[risk]}
    </span>
  )
}

export function StatusBadge({ status }: { status: VictimStatus }) {
  const c = statusClasses(status)
  return (
    <span className={`pill border ${c.bg} ${c.text} ${c.border}`}>
      <span className={`h-2 w-2 rounded-full ${c.dot}`} />
      {STATUS_LABEL_RU[status]}
    </span>
  )
}
