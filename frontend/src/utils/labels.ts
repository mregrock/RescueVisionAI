import type { RiskLevel, Scenario, VictimStatus } from '../api/types'

export const RISK_LABEL_RU: Record<RiskLevel, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
  critical: 'Критический',
}

export const STATUS_LABEL_RU: Record<VictimStatus, string> = {
  OK: 'Стабилен',
  Minor: 'Лёгкое',
  Serious: 'Серьёзное',
  Critical: 'Критическое',
}

export const SCENARIO_META: Record<
  Scenario,
  { title: string; description: string }
> = {
  single_unconscious: {
    title: 'Один без сознания',
    description: 'Лежит без движения, реакции нет.',
  },
  multiple_victims: {
    title: 'Несколько пострадавших',
    description: 'Массовая сортировка, разные приоритеты.',
  },
  severe_bleeding: {
    title: 'Сильное кровотечение',
    description: 'Видимая кровопотеря, нужна срочная остановка.',
  },
  low_confidence: {
    title: 'Плохое качество кадра',
    description: 'Дым / темнота, AI не уверен в оценке.',
  },
}

export const SCENARIOS: Scenario[] = [
  'single_unconscious',
  'multiple_victims',
  'severe_bleeding',
  'low_confidence',
]

const SIGNAL_LABELS: Record<string, string> = {
  lying: 'лежит',
  sitting: 'сидит',
  standing: 'стоит',
  no_movement: 'нет движения',
  possible_unconscious: 'возможно без сознания',
  bleeding: 'кровотечение',
  blood: 'кровь',
  burns: 'ожоги',
  smoke: 'дым на сцене',
  low_light: 'низкая освещённость',
  multiple_people: 'несколько людей',
}

export function humanSignal(sig: string): string {
  return SIGNAL_LABELS[sig] ?? sig.replaceAll('_', ' ')
}

export function riskClasses(risk: RiskLevel): {
  bg: string
  text: string
  border: string
  dot: string
} {
  switch (risk) {
    case 'low':
      return {
        bg: 'bg-green-500/15',
        text: 'text-green-300',
        border: 'border-green-500/40',
        dot: 'bg-green-500',
      }
    case 'medium':
      return {
        bg: 'bg-yellow-500/15',
        text: 'text-yellow-300',
        border: 'border-yellow-500/40',
        dot: 'bg-yellow-500',
      }
    case 'high':
      return {
        bg: 'bg-orange-500/15',
        text: 'text-orange-300',
        border: 'border-orange-500/40',
        dot: 'bg-orange-500',
      }
    case 'critical':
      return {
        bg: 'bg-red-500/15',
        text: 'text-red-300',
        border: 'border-red-500/50',
        dot: 'bg-red-500',
      }
  }
}

const STATUS_TO_RISK: Record<VictimStatus, RiskLevel> = {
  OK: 'low',
  Minor: 'medium',
  Serious: 'high',
  Critical: 'critical',
}

export function statusClasses(status: VictimStatus) {
  return riskClasses(STATUS_TO_RISK[status])
}
