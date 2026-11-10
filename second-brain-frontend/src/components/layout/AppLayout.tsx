import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Brain, MessageSquare, BookOpen, CreditCard,
  BarChart3, Map, FileText, GitCompare,
  LogOut, Menu, X, Plus, Settings, Trash2,
  ChevronDown, Wifi, WifiOff,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useAuthStore, useSessionStore, useUIStore, useProviderStore } from '../../store'
import { sessionsApi, healthApi } from '../../api/client'
import { UploadModal } from './UploadModal'
import { ProviderModal } from './ProviderModal'
import type { Session } from '../../types'

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
  const { sessions, activeSession, setSessions, setActiveSession, removeSession } = useSessionStore()
  const { provider, apiKey } = useProviderStore()
  const { sidebarOpen, setSidebarOpen } = useUIStore()
  const navigate = useNavigate()

  const [uploadOpen, setUploadOpen] = useState(false)
  const [providerOpen, setProviderOpen] = useState(false)
  const [sessionsExpanded, setSessionsExpanded] = useState(true)
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null)

  useEffect(() => {
    sessionsApi.list().then((r) => setSessions(r.data.sessions)).catch(() => {})
  }, [setSessions])

  useEffect(() => {
    if (provider === 'ollama') {
      healthApi.check().then((r) => setOllamaOk(r.data.ollama_available)).catch(() => setOllamaOk(false))
    }
  }, [provider])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    await sessionsApi.delete(id).catch(() => {})
    removeSession(id)
  }

  const providerReady = provider === 'ollama' ? ollamaOk === true : !!apiKey

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <aside
        className={clsx(
          'flex flex-col h-full bg-gradient-to-b from-gray-900 to-gray-950 border-r border-gray-800/80 transition-all duration-300 shrink-0',
          sidebarOpen ? 'w-72' : 'w-[68px]'
        )}
      >
        {/* Logo — pinned, never scrolls */}
        <div className="shrink-0 flex items-center gap-3 px-4 py-5 border-b border-gray-800/80">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shrink-0 shadow-lg shadow-brand-600/30">
            <Brain className="w-5 h-5 text-white" />
          </div>
          {sidebarOpen && (
            <span className="font-semibold text-white truncate tracking-tight">AI Second Brain</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="ml-auto text-gray-500 hover:text-gray-200 transition-colors p-1 rounded-lg hover:bg-gray-800"
          >
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Scrollable middle region — nav AND sessions scroll together here.
            This is the fix: previously nav was fixed-height and sessions
            was squeezed into whatever tiny space was left over on short
            windows. Now the whole region scrolls as one unit, so sessions
            always get a fair, readable amount of space. */}
        <div className="flex-1 min-h-0 overflow-y-auto">
          {/* Primary nav */}
          <nav className="px-2.5 py-4 space-y-0.5">
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group relative',
                    isActive
                      ? 'bg-brand-600/15 text-brand-300'
                      : 'text-gray-400 hover:bg-gray-800/70 hover:text-white'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-brand-400 rounded-r-full" />
                    )}
                    <Icon className="w-4 h-4 shrink-0" />
                    {sidebarOpen && <span className="truncate">{label}</span>}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* Sessions */}
          <div className="border-t border-gray-800/80 mt-1">
            <div className="px-4 pt-4 pb-2 flex items-center justify-between">
              {sidebarOpen ? (
                <button
                  onClick={() => setSessionsExpanded(!sessionsExpanded)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-300 transition-colors"
                >
                  Sessions
                  <ChevronDown className={clsx('w-3 h-3 transition-transform', !sessionsExpanded && '-rotate-90')} />
                </button>
              ) : (
                <div className="w-full h-3" />
              )}
              <button
                onClick={() => setUploadOpen(true)}
                className={clsx(
                  'text-brand-400 hover:text-brand-300 hover:bg-brand-500/10 rounded-lg transition-colors',
                  sidebarOpen ? 'p-1' : 'p-1.5 mx-auto'
                )}
                title="New session"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {sessionsExpanded && (
              <div className="px-2.5 pb-3 space-y-1">
                {sessions.length === 0 && sidebarOpen && (
                  <p className="text-xs text-gray-600 px-2.5 py-2 leading-relaxed">
                    No sessions yet.<br />Click + to upload notes.
                  </p>
                )}
                {sessions.map((s: Session) => (
                  <div
                    key={s.id}
                    onClick={() => setActiveSession(s)}
                    className={clsx(
                      'group flex items-center gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer transition-all',
                      activeSession?.id === s.id
                        ? 'bg-brand-500/15 ring-1 ring-brand-500/30'
                        : 'hover:bg-gray-800/60'
                    )}
                  >
                    <div
                      className={clsx(
                        'w-2 h-2 rounded-full shrink-0',
                        activeSession?.id === s.id ? 'bg-brand-400' : 'bg-gray-700'
                      )}
                    />
                    {sidebarOpen && (
                      <>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white truncate font-medium">{s.name}</p>
                          <p className="text-xs text-gray-500 truncate">
                            {s.chunk_count} chunks · {s.created_at.slice(0, 10)}
                          </p>
                        </div>
                        <button
                          onClick={(e) => handleDelete(e, s.id)}
                          className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all shrink-0"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Provider + user footer — pinned, never scrolls */}
        <div className="shrink-0 border-t border-gray-800/80 px-2.5 py-3 space-y-1">
          <button
            onClick={() => setProviderOpen(true)}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-400 hover:bg-gray-800/70 hover:text-white transition-all"
          >
            <Settings className="w-4 h-4 shrink-0" />
            {sidebarOpen && (
              <>
                <span className="flex-1 text-left truncate">AI Provider</span>
                {providerReady ? (
                  <Wifi className="w-3.5 h-3.5 text-green-400 shrink-0" />
                ) : (
                  <WifiOff className="w-3.5 h-3.5 text-gray-600 shrink-0" />
                )}
              </>
            )}
          </button>

          <div className={clsx('flex items-center gap-2.5 px-3 py-2', !sidebarOpen && 'justify-center')}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-sm font-bold text-white shrink-0 shadow-md">
              {user?.username?.[0]?.toUpperCase()}
            </div>
            {sidebarOpen && (
              <>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate font-medium">{user?.username}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-gray-500 hover:text-red-400 transition-colors p-1"
                  title="Log out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-gray-950">
        <Outlet />
      </main>

      <UploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <ProviderModal open={providerOpen} onClose={() => setProviderOpen(false)} />
    </div>
  )
}