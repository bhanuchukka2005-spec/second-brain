import axios from 'axios'
import type {
  User, TokenResponse, Session, SessionListResponse,
  ChatResponse, MCQResponse, FlashcardResponse,
  QuizScore, HealthResponse, ProviderID,
} from '../types'

const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (username: string, password: string, email?: string) =>
    api.post<User>('/auth/register', { username, password, email: email || undefined }),

  login: (username: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { username, password }),

  googleLogin: (idToken: string) =>
    api.post<TokenResponse>('/auth/google', { id_token: idToken }),

  forgotPassword: (identifier: string) =>
    api.post<{ message: string }>('/auth/forgot-password', { identifier }),

  resetPassword: (token: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/reset-password', { token, new_password: newPassword }),

  me: () => api.get<User>('/auth/me'),
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export const sessionsApi = {
  list: () => api.get<SessionListResponse>('/sessions'),
  delete: (id: number) => api.delete(`/sessions/${id}`),

  index: (
    _sessionId: number,
    files: File[],
    sessionName: string,
    youtubeUrl?: string
  ) => {
    const form = new FormData()
    files.forEach((f) => form.append('files', f))
    form.append('session_name', sessionName)
    if (youtubeUrl) form.append('youtube_url', youtubeUrl)
    return api.post<Session>(`/sessions/0/index`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    })
  },

  history: (id: number) =>
    api.get<{ history: Array<{ role: string; content: string }>; session_id: number }>(
      `/sessions/${id}/history`
    ),
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export const chatApi = {
  ask: (
    question: string,
    sessionId: number,
    provider: ProviderID,
    apiKey: string,
    ollamaModel: string
  ) =>
    api.post<ChatResponse>('/chat/ask', {
      question,
      session_id: sessionId,
      provider,
      api_key: apiKey,
      ollama_model: ollamaModel,
    }),

  askStream: (
    question: string,
    sessionId: number,
    ollamaModel: string,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (e: string) => void
  ) => {
    const token = localStorage.getItem('token')
    fetch(`${BASE_URL}/chat/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        question,
        session_id: sessionId,
        provider: 'ollama',
        api_key: '',
        ollama_model: ollamaModel,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        if (!res.body) throw new Error('No response body')
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          onToken(decoder.decode(value, { stream: true }))
        }
        onDone()
      })
      .catch((e: Error) => onError(e.message))
  },
}

// ── Study ─────────────────────────────────────────────────────────────────────

interface StudyBase {
  session_id: number
  provider: ProviderID
  api_key: string
  ollama_model: string
  topic?: string
}

export const studyApi = {
  mcq: (params: StudyBase & { num_questions: number; wrong_topics?: string[] }) =>
    api.post<MCQResponse>('/study/mcq', params),

  flashcards: (params: StudyBase & { num_cards: number }) =>
    api.post<FlashcardResponse>('/study/flashcards', params),

  summarize: (params: StudyBase) =>
    api.post<{ summary: string; topic: string; session_id: number }>('/study/summarize', params),

  compare: (params: StudyBase & { topic_a: string; topic_b: string }) =>
    api.post<{ comparison: string; topic_a: string; topic_b: string }>('/study/compare', params),

  conceptMap: (params: StudyBase) =>
    api.post<{ mermaid: string; topic: string }>('/study/concept-map', params),

  studyPlan: (params: {
    session_id: number
    weak_topics: string[]
    provider: ProviderID
    api_key: string
    ollama_model: string
  }) => api.post<{ plan: string; weak_topics: string[] }>('/study/study-plan', params),

  saveScore: (sessionId: number, score: number, total: number, topic: string) =>
    api.post<QuizScore>('/study/quiz-score', {
      session_id: sessionId,
      score,
      total,
      topic,
    }),

  scores: (sessionId: number) =>
    api.get<{ scores: QuizScore[]; session_id: number; total: number }>(
      `/study/quiz-scores/${sessionId}`
    ),
}

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => api.get<HealthResponse>('/health'),
}