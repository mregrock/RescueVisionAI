import { NavLink, Outlet } from 'react-router-dom'
import { BackendStatus } from './BackendStatus'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-lg text-sm sm:text-base font-semibold transition-colors ${
    isActive
      ? 'bg-slate-800 text-white'
      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
  }`

export function Layout() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/85 backdrop-blur">
        <div className="mx-auto max-w-5xl px-4 py-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          <NavLink
            to="/"
            className="flex items-center gap-2 font-bold tracking-tight text-white"
          >
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-red-600 text-white text-sm">
              RV
            </span>
            <span className="hidden xs:inline sm:inline">RescueVisionAI</span>
          </NavLink>
          <nav className="flex items-center gap-1 sm:gap-2 order-3 sm:order-2 w-full sm:w-auto">
            <NavLink to="/" end className={navLinkClass}>
              Анализ
            </NavLink>
            <NavLink to="/protocols" className={navLinkClass}>
              Протоколы
            </NavLink>
            <NavLink to="/camera" className={navLinkClass}>
              Камера
            </NavLink>
          </nav>
          <div className="ml-auto order-2 sm:order-3">
            <BackendStatus />
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto w-full max-w-5xl px-4 py-5 sm:py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-800 text-xs text-slate-500">
        <div className="mx-auto max-w-5xl px-4 py-3">
          Учебный MVP. Система носит вспомогательный характер и не заменяет решение
          спасателя.
        </div>
      </footer>
    </div>
  )
}
