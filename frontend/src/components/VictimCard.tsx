import { Link } from 'react-router-dom'
import type { Victim } from '../api/types'
import { humanSignal } from '../utils/labels'
import { RiskBadge, StatusBadge } from './RiskBadge'

interface Props {
  victim: Victim
}

export function VictimCard({ victim }: Props) {
  const isCritical =
    victim.severity_label === 'critical' || victim.status === 'Critical'
  return (
    <div
      className={`card transition-colors ${
        isCritical ? 'border-red-500/60 bg-red-950/20' : ''
      }`}
    >
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-800 text-lg font-bold text-white">
          #{victim.priority}
        </div>
        <div>
          <div className="text-sm text-slate-400">Пострадавший</div>
          <div className="font-semibold text-white">
            ID {victim.id} · приоритет {victim.priority}
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <StatusBadge status={victim.status} />
          <RiskBadge risk={victim.severity_label} size="sm" />
        </div>
      </div>

      <div className="mt-3 text-sm text-slate-300">
        Тяжесть: <span className="font-semibold text-white">
          {Math.round(victim.severity_score * 100)}%
        </span>
        {victim.bbox && (
          <span className="ml-3 font-mono text-xs text-slate-500">
            bbox [{victim.bbox.join(', ')}]
          </span>
        )}
      </div>

      {victim.signals.length > 0 && (
        <div className="mt-3">
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Признаки
          </div>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {victim.signals.map((s) => (
              <span
                key={s}
                className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-200"
              >
                {humanSignal(s)}
              </span>
            ))}
          </div>
        </div>
      )}

      {victim.first_aid.length > 0 && (
        <div className="mt-3">
          <div className="text-xs uppercase tracking-wider text-slate-500">
            Первая помощь
          </div>
          <ol className="mt-1.5 list-decimal space-y-1 pl-5 text-sm text-slate-200">
            {victim.first_aid.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {victim.protocols.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {victim.protocols.map((p) => (
            <Link
              key={p}
              to={`/protocols/${p}`}
              className="rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1 text-xs font-medium text-slate-100 hover:border-blue-500 hover:text-white"
            >
              {p}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
