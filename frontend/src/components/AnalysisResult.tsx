import { Link } from 'react-router-dom'
import type { AnalyzeResponse } from '../api/types'
import { ActionChecklist } from './ActionChecklist'
import { RiskBadge } from './RiskBadge'
import { VictimCard } from './VictimCard'

interface Props {
  result: AnalyzeResponse
}

export function AnalysisResult({ result }: Props) {
  const confidencePct = Math.round(result.confidence * 100)
  return (
    <section className="space-y-5">
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Общий риск
            </div>
            <div className="mt-1 flex items-center gap-3">
              <RiskBadge risk={result.overall_risk} size="lg" />
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Уверенность AI
            </div>
            <div className="mt-1 text-2xl font-bold text-white">
              {confidencePct}%
            </div>
            <div className="mt-1 h-1.5 w-40 max-w-full rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-blue-500"
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>
        </div>

        {result.quality.low_confidence && (
          <div className="mt-4 rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-3 text-sm text-yellow-200">
            <div className="font-semibold">Низкая уверенность AI</div>
            {result.quality.notes.length > 0 && (
              <ul className="mt-1 list-disc pl-5">
                {result.quality.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            )}
            <div className="mt-1 text-yellow-200/80">
              Полагайтесь на собственную оценку сцены.
            </div>
          </div>
        )}

        <div className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <span className="text-slate-400">Людей на сцене:</span>{' '}
            <span className="font-semibold text-white">
              {result.scene.people_count}
            </span>
          </div>
          <div className="font-mono text-xs text-slate-500 sm:text-right">
            analysis_id: {result.analysis_id}
          </div>
        </div>

        {result.scene.observations.length > 0 && (
          <div className="mt-3">
            <div className="text-xs uppercase tracking-wider text-slate-500">
              Наблюдения сцены
            </div>
            <ul className="mt-1.5 list-disc space-y-0.5 pl-5 text-sm text-slate-200">
              {result.scene.observations.map((o, i) => (
                <li key={i}>{o}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-lg font-bold text-white">
          Пострадавшие · {result.victims.length}
        </h2>
        {result.victims.length === 0 ? (
          <div className="card text-sm text-slate-400">
            Пострадавшие не обнаружены.
          </div>
        ) : (
          <div className="grid gap-3">
            {result.victims.map((v) => (
              <VictimCard key={v.id} victim={v} />
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="mb-3 text-lg font-bold text-white">
          Чеклист действий
        </h2>
        <ActionChecklist
          actions={result.recommended_actions}
          resetKey={result.analysis_id}
        />
      </div>

      {result.protocols.length > 0 && (
        <div className="card">
          <h2 className="mb-3 text-lg font-bold text-white">
            Применимые протоколы
          </h2>
          <div className="flex flex-wrap gap-2">
            {result.protocols.map((p) => (
              <Link
                key={p}
                to={`/protocols/${p}`}
                className="rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-2 text-sm font-semibold text-slate-100 hover:border-blue-500 hover:text-white"
              >
                {p}
              </Link>
            ))}
          </div>
          <div className="mt-3 text-xs text-slate-500">
            Нажмите, чтобы открыть полный текст протокола.
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs text-slate-400">
        {result.disclaimer}
      </div>
    </section>
  )
}
