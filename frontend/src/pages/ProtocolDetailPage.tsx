import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, api } from '../api/client'
import type { Protocol } from '../api/types'
import { ErrorView, LoadingView } from '../components/states'

type State =
  | { kind: 'loading' }
  | { kind: 'success'; protocol: Protocol }
  | { kind: 'error'; message: string; notFound?: boolean }

export function ProtocolDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const [state, setState] = useState<State>({ kind: 'loading' })

  const load = () => {
    if (!id) return
    setState({ kind: 'loading' })
    api
      .getProtocol(id)
      .then((p) => setState({ kind: 'success', protocol: p }))
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setState({
            kind: 'error',
            message: err.message,
            notFound: err.status === 404,
          })
        } else {
          setState({
            kind: 'error',
            message: err instanceof Error ? err.message : 'Неизвестная ошибка',
          })
        }
      })
  }

  useEffect(load, [id])

  return (
    <div className="space-y-5">
      <div>
        <Link
          to="/protocols"
          className="text-sm text-slate-400 hover:text-white"
        >
          ← К списку протоколов
        </Link>
      </div>

      {state.kind === 'loading' && <LoadingView label="Загружаем протокол…" />}
      {state.kind === 'error' && (
        <ErrorView
          title={state.notFound ? 'Протокол не найден' : 'Ошибка загрузки'}
          message={state.notFound ? `Нет протокола с id «${id}».` : state.message}
          onRetry={state.notFound ? undefined : load}
        />
      )}
      {state.kind === 'success' && <ProtocolView protocol={state.protocol} />}
    </div>
  )
}

function ProtocolView({ protocol }: { protocol: Protocol }) {
  return (
    <article className="space-y-5">
      <header>
        <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
          {protocol.id}
        </div>
        <h1 className="mt-1 text-2xl sm:text-3xl font-bold text-white">
          {protocol.title}
        </h1>
        {protocol.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {protocol.tags.map((t) => (
              <span
                key={t}
                className="rounded-md bg-slate-800 px-2 py-0.5 text-xs text-slate-300"
              >
                #{t}
              </span>
            ))}
          </div>
        )}
        {protocol.summary && (
          <p className="mt-3 text-slate-300">{protocol.summary}</p>
        )}
      </header>

      <section className="card">
        <h2 className="text-lg font-bold text-white">Шаги</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-slate-100">
          {protocol.steps.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ol>
      </section>

      {protocol.warnings && protocol.warnings.length > 0 && (
        <section className="card border-yellow-500/40 bg-yellow-500/5">
          <h2 className="text-lg font-bold text-yellow-200">Внимание</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-yellow-100">
            {protocol.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </section>
      )}

      {protocol.disclaimer && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">
          {protocol.disclaimer}
        </div>
      )}
    </article>
  )
}
