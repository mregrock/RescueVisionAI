import { useCallback, useState } from 'react'
import { ApiError, api } from '../api/client'
import type { AnalyzeResponse, Scenario } from '../api/types'
import { AnalysisResult } from '../components/AnalysisResult'
import { ScenarioSelector } from '../components/ScenarioSelector'
import { ErrorView, Spinner } from '../components/states'
import { shortId } from '../utils/ids'
import { SCENARIO_META } from '../utils/labels'

type LoadState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'success'; data: AnalyzeResponse }
  | { kind: 'error'; message: string }

export function AnalyzePage() {
  const [scenario, setScenario] = useState<Scenario | null>('single_unconscious')
  const [state, setState] = useState<LoadState>({ kind: 'idle' })

  const run = useCallback(async () => {
    if (!scenario) return
    setState({ kind: 'loading' })
    try {
      const data = await api.analyze({
        incident_id: shortId('inc'),
        rescuer_id: 'resc-demo',
        scenario,
        timestamp: new Date().toISOString(),
      })
      setState({ kind: 'success', data })
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : 'Неизвестная ошибка'
      setState({ kind: 'error', message })
    }
  }, [scenario])

  const isLoading = state.kind === 'loading'

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl sm:text-3xl font-bold text-white">
          Анализ ситуации
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Выберите demo-сценарий и запустите анализ — AI оценит риск,
          пострадавших и порекомендует действия.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-200">
          1. Выберите сценарий
        </h2>
        <ScenarioSelector
          value={scenario}
          onChange={setScenario}
          disabled={isLoading}
        />
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-200">
          2. Запустите анализ
        </h2>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={run}
            disabled={!scenario || isLoading}
            className="btn-primary w-full sm:w-auto text-lg px-6 py-4"
          >
            {isLoading && <Spinner />}
            {isLoading
              ? 'Анализируем…'
              : state.kind === 'success'
                ? 'Запустить заново'
                : 'Запустить анализ'}
          </button>
          {scenario && (
            <div className="text-sm text-slate-400">
              Сценарий:{' '}
              <span className="font-semibold text-slate-200">
                {SCENARIO_META[scenario].title}
              </span>
            </div>
          )}
        </div>
      </section>

      <section>
        {state.kind === 'idle' && (
          <div className="card text-sm text-slate-400">
            Нажмите «Запустить анализ», чтобы получить результат от backend.
          </div>
        )}
        {state.kind === 'loading' && (
          <div className="card flex items-center gap-3 text-slate-200">
            <Spinner /> Отправляем запрос в backend…
          </div>
        )}
        {state.kind === 'error' && (
          <ErrorView
            title="Не удалось выполнить анализ"
            message={state.message}
            onRetry={run}
          />
        )}
        {state.kind === 'success' && <AnalysisResult result={state.data} />}
      </section>
    </div>
  )
}
