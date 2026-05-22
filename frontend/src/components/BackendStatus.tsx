import { useEffect, useState } from 'react'
import { api, API_BASE_LABEL } from '../api/client'

type Status = 'checking' | 'ok' | 'down'

export function BackendStatus() {
  const [status, setStatus] = useState<Status>('checking')
  const [version, setVersion] = useState<string | null>(null)

  useEffect(() => {
    let alive = true

    const ping = async () => {
      try {
        const h = await api.health()
        if (!alive) return
        setStatus(h.status?.toLowerCase() === 'ok' ? 'ok' : 'down')
        setVersion(h.version ?? null)
      } catch {
        if (!alive) return
        setStatus('down')
      }
    }

    ping()
    const t = window.setInterval(ping, 15_000)
    return () => {
      alive = false
      window.clearInterval(t)
    }
  }, [])

  const dot =
    status === 'ok'
      ? 'bg-green-500'
      : status === 'down'
        ? 'bg-red-500'
        : 'bg-yellow-400 animate-pulse'

  const label =
    status === 'ok'
      ? `backend online${version ? ` · v${version}` : ''}`
      : status === 'down'
        ? `backend offline (${API_BASE_LABEL})`
        : 'проверка backend…'

  return (
    <div
      className="flex items-center gap-2 text-xs sm:text-sm text-slate-300"
      title={API_BASE_LABEL}
    >
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${dot}`} />
      <span className="truncate">{label}</span>
    </div>
  )
}
