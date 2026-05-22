import { useEffect, useState } from 'react'
import type { Action } from '../api/types'

interface Props {
  actions: Action[]
  resetKey?: string
}

export function ActionChecklist({ actions, resetKey }: Props) {
  const [done, setDone] = useState<Record<string, boolean>>({})

  useEffect(() => {
    setDone({})
  }, [resetKey])

  if (actions.length === 0) {
    return (
      <div className="text-sm text-slate-400">Нет рекомендованных действий.</div>
    )
  }

  const sorted = [...actions].sort((a, b) => a.priority - b.priority)
  const completedCount = sorted.filter((a) => done[a.id]).length

  return (
    <div>
      <div className="mb-3 text-xs text-slate-400">
        Выполнено {completedCount} из {sorted.length}
      </div>
      <ul className="space-y-2">
        {sorted.map((a) => {
          const checked = !!done[a.id]
          return (
            <li key={a.id}>
              <label
                className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors ${
                  a.critical
                    ? 'border-red-500/50 bg-red-950/20 hover:bg-red-950/30'
                    : 'border-slate-800 bg-slate-900/60 hover:bg-slate-900'
                } ${checked ? 'opacity-60' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) =>
                    setDone((prev) => ({ ...prev, [a.id]: e.target.checked }))
                  }
                  className="mt-1 h-5 w-5 flex-none cursor-pointer accent-blue-500"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-semibold ${
                        checked ? 'line-through text-slate-400' : 'text-white'
                      }`}
                    >
                      {a.priority}. {a.title}
                    </span>
                    {a.critical && (
                      <span className="rounded-full bg-red-600/80 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        critical
                      </span>
                    )}
                  </div>
                  <div
                    className={`mt-1 text-sm ${
                      checked ? 'text-slate-500' : 'text-slate-300'
                    }`}
                  >
                    {a.description}
                  </div>
                </div>
              </label>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
