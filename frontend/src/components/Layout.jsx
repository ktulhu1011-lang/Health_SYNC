import React, { useContext } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { AuthContext } from '../App'

const links = [
  { to: '/', label: '🏠 Сводка', end: true },
  { to: '/heart', label: '💗 Пульс' },
  { to: '/sleep', label: '💤 Сон' },
  { to: '/habits', label: '📋 Привычки' },
  { to: '/correlations', label: '📊 Корреляции' },
  { to: '/insights', label: '🤖 AI-инсайты' },
  { to: '/settings', label: '⚙️ Настройки' },
]

export default function Layout() {
  const { setUser } = useContext(AuthContext)
  const navigate = useNavigate()

  function logout() {
    localStorage.removeItem('token')
    setUser(null)
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-950">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-xl font-bold text-blue-400">💗 HealthSync</h1>
          <p className="text-xs text-gray-500 mt-1">v2.0</p>
        </div>
        <nav className="flex-1 py-4 overflow-y-auto">
          {links.map(({ to, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `block px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600/20 text-blue-400 border-r-2 border-blue-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={logout}
            className="w-full text-left text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            🚪 Выйти
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-6xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
