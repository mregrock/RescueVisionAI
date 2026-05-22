import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, api } from '../api/client'
import type { ProtocolSummary } from '../api/types'
import { ErrorView, LoadingView } from '../components/states'

type State =
  | { kind: 'loading' }
  | { kind: 'success'; protocols: ProtocolSummary[] }
  | { kind: 'error'; message: string }

export function ProtocolsListPage() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  const load = () => {
    setState({ kind: 'loading' })
    api
      .listProtocols()
      .then((r) => setState({ kind: 'success', protocols: r.protocols }))
      .catch((err: unknown) => {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof Error
              ? err.message
              : 'Неизвестная ошибка'
        setState({ kind: 'error', message })
      })
  }

  useEffect(load, [])

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Протоколы</h1>
        <p className="mt-1 text-sm text-slate-400">
          Справочные алгоритмы для спасателя. Откройте любой, чтобы увидеть шаги.
        </p>
      </header>

      {state.kind === 'loading' && <LoadingView label="Загружаем список протоколов…" />}
      {state.kind === 'error' && (
        <ErrorView message={state.message} onRetry={load} />
      )}
      {state.kind === 'success' && (
        <div className="grid gap-3 sm:grid-cols-2">
          {state.protocols.map((p) => (
            <Link
              key={p.id}
              to={`/protocols/${p.id}`}
              className="card flex flex-col justify-between gap-3 transition-colors hover:border-blue-500 hover:bg-slate-900"
            >
              <div>
                <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
                  {p.id}
                </div>
                <div className="mt-1 text-lg font-semibold text-white">
                  {p.title}
                </div>
              </div>
              {p.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {p.tags.map((t) => (
                    <span
                      key={t}
                      className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300"
                    >
                      #{t}
                    </span>
                  ))}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
