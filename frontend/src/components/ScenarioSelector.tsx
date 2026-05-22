import type { Scenario } from '../api/types'
import { SCENARIO_META, SCENARIOS } from '../utils/labels'

interface Props {
  value: Scenario | null
  onChange: (s: Scenario) => void
  disabled?: boolean
}

export function ScenarioSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {SCENARIOS.map((sc) => {
        const meta = SCENARIO_META[sc]
        const active = value === sc
        return (
          <button
            key={sc}
            type="button"
            disabled={disabled}
            onClick={() => onChange(sc)}
            className={`text-left rounded-2xl border p-4 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${
              active
                ? 'border-blue-500 bg-blue-500/10 ring-2 ring-blue-500/40'
                : 'border-slate-800 bg-slate-900/60 hover:border-slate-600 hover:bg-slate-900'
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="font-semibold text-white">{meta.title}</div>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-mono">
                {sc}
              </span>
            </div>
            <div className="mt-1 text-sm text-slate-400">{meta.description}</div>
          </button>
        )
      })}
    </div>
  )
}
