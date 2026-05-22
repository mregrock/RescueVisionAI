interface ErrorViewProps {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorView({
  title = 'Что-то пошло не так',
  message,
  onRetry,
}: ErrorViewProps) {
  return (
    <div className="card border-red-500/50 bg-red-950/20">
      <div className="text-base font-bold text-red-200">{title}</div>
      <div className="mt-1 text-sm text-red-100/90">{message}</div>
      {onRetry && (
        <button onClick={onRetry} className="btn-danger mt-3">
          Повторить
        </button>
      )}
    </div>
  )
}

export function LoadingView({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="card flex items-center gap-3 text-slate-200">
      <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-blue-400" />
      <span>{label}</span>
    </div>
  )
}

export function Spinner({ className = '' }: { className?: string }) {
  return (
    <span
      className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent ${className}`}
      aria-hidden
    />
  )
}
