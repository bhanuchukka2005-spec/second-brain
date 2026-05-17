// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: number
  username: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export interface Session {
  id: number
  name: string
  created_at: string
  file_names: string[]
  chunk_count: number
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  timestamp?: string
}

export interface ChatResponse {
  answer: string
  sources: string[]
  session_id: number
}

// ── Study Features ────────────────────────────────────────────────────────────

export interface MCQQuestion {
  question: string
  options: Record<string, string>
  answer: string
  explanation: string
}

export interface MCQResponse {
  questions: MCQQuestion[]
  topic: string
  total: number
}

export interface Flashcard {
  front: string
  back: string
}

export interface FlashcardResponse {
  cards: Flashcard[]
  total: number
  topic: string
}

export interface QuizScore {
  score: number
  total: number
  percentage: number
  topic: string
  timestamp: string
}

// ── Provider ──────────────────────────────────────────────────────────────────

export type ProviderID =
  | 'ollama'
  | 'groq'
  | 'gemini'
  | 'openai'
  | 'anthropic'
  | 'mistral'
  | 'cohere'
  | 'together'

export interface Provider {
  id: ProviderID
  label: string
  hint: string
  free: boolean
  local: boolean
}

export const PROVIDERS: Provider[] = [
  { id: 'ollama',    label: '🖥️ Local — Ollama (No API Key)', hint: 'Free & private — runs on your machine',       free: true,  local: true  },
  { id: 'groq',      label: 'Groq (Free & Fast ⚡)',           hint: 'Get free key → console.groq.com',            free: true,  local: false },
  { id: 'gemini',    label: 'Gemini (Google)',                  hint: 'Get free key → aistudio.google.com',         free: true,  local: false },
  { id: 'openai',    label: 'OpenAI (GPT-4o Mini)',             hint: 'Get key → platform.openai.com',              free: false, local: false },
  { id: 'anthropic', label: 'Anthropic (Claude)',               hint: 'Get key → console.anthropic.com',            free: false, local: false },
  { id: 'mistral',   label: 'Mistral AI',                       hint: 'Get free key → console.mistral.ai',          free: true,  local: false },
  { id: 'cohere',    label: 'Cohere',                           hint: 'Get free key → dashboard.cohere.com',        free: true,  local: false },
  { id: 'together',  label: 'Together AI (Free Models)',        hint: 'Get free key → api.together.xyz',            free: true,  local: false },
]

// ── Health ────────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  version: string
  ollama_available: boolean
  database: string
}
