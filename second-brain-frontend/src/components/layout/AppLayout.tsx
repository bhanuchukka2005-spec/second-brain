import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Brain, MessageSquare, BookOpen, CreditCard,
  BarChart3, Map, FileText, GitCompare,
  LogOut, Menu, X, ChevronRight,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore, useSessionStore, useUIStore } from '../../store'

const NAV_ITEMS = [
  { to: '/chat',        icon: MessageSquare, label: 'Chat'         },
  { to: '/quiz',        icon: BookOpen,      label: 'MCQ Quiz'     },
  { to: '/flashcards',  icon: CreditCard,    label: 'Flashcards'   },
  { to: '/dashboard',   icon: BarChart3,     label: 'Dashboard'    },
  { to: '/concept-map', icon: Map,           label: 'Concept Map'  },
  { to: '/summarize',   icon: FileText,      label: 'Summarize'    },
  { to: '/compare',     icon: GitCompare,    label: 'Compare'      },
]

export function AppLayout() {
  const { user, logout } = useAuthStore()
  const { activeSession } = useSessionStore()
  const { sidebarOpen, setSidebarOpen } = useUIStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={clsx(
          'flex flex-col bg-gray-900 border-r border-gray-800 transition-all duration-300 shrink-0',
          sidebarOpen ? 'w-56' : 'w-16'
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-800">
          <Brain className="w-7 h-7 text-brand-400 shrink-0" />
          {sidebarOpen && (
            <span className="font-semibold text-white truncate">Second Brain</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="ml-auto text-gray-400 hover:text-white transition-colors"
            aria-label="Toggle sidebar"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Active session indicator */}
        {activeSession && (
          <div className={clsx(
            'mx-3 mt-3 px-3 py-2 rounded-lg bg-brand-500/10 border border-brand-500/20',
            !sidebarOpen && 'px-2'
          )}>
            {sidebarOpen ? (
              <>
                <p className="text-xs text-brand-400 font-medium truncate">Active Session</p>
                <p className="text-xs text-gray-300 truncate mt-0.5">{activeSession.name}</p>
              </>
            ) : (
              <div className="w-2 h-2 rounded-full bg-brand-400 mx-auto" />
            )}
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group',
                  isActive
                    ? 'bg-brand-500/20 text-brand-300'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
              {sidebarOpen && (
                <ChevronRight className="w-3 h-3 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
              )}
            </NavLink>
          ))}
        </nav>

        {/* User + logout */}
        <div className="px-3 py-4 border-t border-gray-800">
          {sidebarOpen ? (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-sm font-bold text-white shrink-0">
                {user?.username?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate font-medium">{user?.username}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-400 hover:text-red-400 transition-colors"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={handleLogout}
              className="w-full flex justify-center text-gray-400 hover:text-red-400 transition-colors py-1"
              aria-label="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
