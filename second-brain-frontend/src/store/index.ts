import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Session, ChatMessage, ProviderID } from '../types'

// ── Auth Store ────────────────────────────────────────────────────────────────

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      setAuth: (user, token) => {
        localStorage.setItem('token', token)
        set({ user, token })
      },
      logout: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('provider-store')
        set({ user: null, token: null })
      },
      isAuthenticated: () => !!get().token,
    }),
    { name: 'auth-store' }
  )
)

// ── Session Store ─────────────────────────────────────────────────────────────

interface SessionState {
  sessions: Session[]
  activeSession: Session | null
  setSessions: (sessions: Session[]) => void
  addSession: (session: Session) => void
  removeSession: (id: number) => void
  setActiveSession: (session: Session | null) => void
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  activeSession: null,
  setSessions: (sessions) => set({ sessions }),
  addSession: (session) => set((s) => ({ sessions: [session, ...s.sessions] })),
  removeSession: (id) =>
    set((s) => ({
      sessions: s.sessions.filter((sess) => sess.id !== id),
      activeSession: s.activeSession?.id === id ? null : s.activeSession,
    })),
  setActiveSession: (session) => set({ activeSession: session }),
}))

// ── Chat Store ────────────────────────────────────────────────────────────────

interface ChatState {
  messages: Record<number, ChatMessage[]>  // sessionId → messages
  addMessage: (sessionId: number, msg: ChatMessage) => void
  setMessages: (sessionId: number, msgs: ChatMessage[]) => void
  clearMessages: (sessionId: number) => void
  getMessages: (sessionId: number) => ChatMessage[]
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: {},
  addMessage: (sessionId, msg) =>
    set((s) => ({
      messages: {
        ...s.messages,
        [sessionId]: [...(s.messages[sessionId] ?? []), msg],
      },
    })),
  setMessages: (sessionId, msgs) =>
    set((s) => ({ messages: { ...s.messages, [sessionId]: msgs } })),
  clearMessages: (sessionId) =>
    set((s) => ({ messages: { ...s.messages, [sessionId]: [] } })),
  getMessages: (sessionId) => get().messages[sessionId] ?? [],
}))

// ── Provider Store ────────────────────────────────────────────────────────────

interface ProviderState {
  provider: ProviderID
  apiKey: string
  ollamaModel: string
  setProvider: (p: ProviderID) => void
  setApiKey: (k: string) => void
  setOllamaModel: (m: string) => void
}

export const useProviderStore = create<ProviderState>()(
  persist(
    (set) => ({
      provider: 'ollama',
      apiKey: '',
      ollamaModel: 'llama3.2',
      setProvider: (provider) => set({ provider }),
      setApiKey: (apiKey) => set({ apiKey }),
      setOllamaModel: (ollamaModel) => set({ ollamaModel }),
    }),
    { name: 'provider-store' }
  )
)

// ── UI Store ──────────────────────────────────────────────────────────────────

interface UIState {
  sidebarOpen: boolean
  activeTab: string
  setSidebarOpen: (open: boolean) => void
  setActiveTab: (tab: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeTab: 'chat',
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setActiveTab: (activeTab) => set({ activeTab }),
}))
