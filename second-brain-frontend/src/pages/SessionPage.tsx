import { useState, useEffect, useRef } from 'react'
import {
  Upload, Trash2, Loader2, Plus,
  MessageSquare, BookOpen, CreditCard, BarChart3,
  Map, FileText, GitCompare,
} from 'lucide-react'
import { clsx } from 'clsx'
import { useLocation, useNavigate } from 'react-router-dom'
import { sessionsApi, studyApi, healthApi } from '../api/client'
import { useSessionStore, useProviderStore } from '../store'
import { ProviderPicker } from '../components/layout/ProviderPicker'
import { ChatPanel } from '../components/chat/ChatPanel'
import { QuizView } from '../components/quiz/QuizView'
import { FlashcardViewer } from '../components/flashcards/FlashcardViewer'
import { Dashboard } from '../components/study/Dashboard'
import { ConceptMapView } from '../components/study/ConceptMapView'
import type { Session } from '../types'

const TABS = [
  { id: 'chat',        icon: MessageSquare, label: 'Chat'        },
  { id: 'quiz',        icon: BookOpen,      label: 'Quiz'        },
  { id: 'flashcards',  icon: CreditCard,    label: 'Flashcards'  },
  { id: 'dashboard',   icon: BarChart3,     label: 'Dashboard'   },
  { id: 'concept-map', icon: Map,           label: 'Concept Map' },
  { id: 'summarize',   icon: FileText,      label: 'Summarize'   },
  { id: 'compare',     icon: GitCompare,    label: 'Compare'     },
]

export function SessionPage() {
  const { sessions, activeSession, setSessions, addSession, removeSession, setActiveSession } = useSessionStore()
  const { provider, apiKey, ollamaModel } = useProviderStore()
  const location = useLocation()
  const navigate = useNavigate()
  const activeTab = location.pathname.replace('/', '') || 'chat'

  const [uploading, setUploading] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const [ytUrl, setYtUrl] = useState('')
  const [ytMode, setYtMode] = useState(false)
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [indexError, setIndexError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  const [summaryTopic, setSummaryTopic] = useState('')
  const [summary, setSummary] = useState('')
  const [compareA, setCompareA] = useState('')
  const [compareB, setCompareB] = useState('')
  const [comparison, setComparison] = useState('')
  const [studyLoading, setStudyLoading] = useState(false)

  useEffect(() => {
    sessionsApi.list().then((r) => setSessions(r.data.sessions)).catch(() => {})
    if (provider === 'ollama') {
      healthApi.check().then((r) => setOllamaOk(r.data.ollama_available)).catch(() => setOllamaOk(false))
    }
  }, [provider, setSessions])

  const handleIndex = async () => {
    if (!selectedFiles.length && !ytUrl.trim()) return
    setUploading(true)
    setIndexError('')
    try {
      const res = await sessionsApi.index(
        0, selectedFiles,
        sessionName || `Session ${sessions.length + 1}`,
        ytUrl.trim() || undefined
      )
      addSession(res.data)
      setActiveSession(res.data)
      setSessionName(''); setYtUrl(''); setSelectedFiles([])
      if (fileRef.current) fileRef.current.value = ''
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setIndexError(detail || 'Indexing failed. Try again.')
    } finally { setUploading(false) }
  }

  const handleDelete = async (id: number) => {
    await sessionsApi.delete(id).catch(() => {})
    removeSession(id)
  }

  const bp = () => ({ session_id: activeSession!.id, provider, api_key: apiKey, ollama_model: ollamaModel })

  const handleSummarize = async () => {
    if (!activeSession) return
    setStudyLoading(true)
    try { const r = await studyApi.summarize({ ...bp(), topic: summaryTopic }); setSummary(r.data.summary) }
    catch { setSummary('Error generating summary.') }
    finally { setStudyLoading(false) }
  }

  const handleCompare = async () => {
    if (!activeSession || !compareA || !compareB) return
    setStudyLoading(true)
    try { const r = await studyApi.compare({ ...bp(), topic_a: compareA, topic_b: compareB }); setComparison(r.data.comparison) }
    catch { setComparison('Error comparing topics.') }
    finally { setStudyLoading(false) }
  }

  const canUse = activeSession && (provider === 'ollama' ? ollamaOk : !!apiKey)

  return (
    <div className="flex h-full">

      {/* ── Left panel ── */}
      <aside className="w-72 shrink-0 border-r border-gray-800 flex flex-col bg-gray-900">

        {/* Provider */}
        <div className="p-4 border-b border-gray-800">
          <h2 className="font-semibold text-white mb-4">Provider</h2>
          <ProviderPicker />
        </div>

        {/* Upload */}
        <div className="p-4 border-b border-gray-800 space-y-3">
          <h2 className="font-semibold text-white">Upload Material</h2>
          <input value={sessionName} onChange={(e) => setSessionName(e.target.value)} placeholder="Session name"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500" />

          <div className="flex gap-2">
            <button onClick={() => setYtMode(false)} className={clsx('flex-1 py-2 text-xs rounded-lg transition-colors', !ytMode ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400')}>Files</button>
            <button onClick={() => setYtMode(true)}  className={clsx('flex-1 py-2 text-xs rounded-lg transition-colors',  ytMode ? 'bg-brand-600 text-white' : 'bg-gray-800 text-gray-400')}>YouTube</button>
          </div>

          {ytMode ? (
            <input value={ytUrl} onChange={(e) => setYtUrl(e.target.value)} placeholder="https://youtu.be/..."
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500" />
          ) : (
            <div>
              <div onClick={() => fileRef.current?.click()}
                className={clsx('border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors',
                  selectedFiles.length > 0 ? 'border-brand-500 bg-brand-500/5' : 'border-gray-700 hover:border-brand-500')}>
                <Upload className={clsx('w-5 h-5 mx-auto mb-1', selectedFiles.length > 0 ? 'text-brand-400' : 'text-gray-500')} />
                {selectedFiles.length === 0
                  ? <p className="text-xs text-gray-400">Click to select PDF, PPTX, TXT</p>
                  : <p className="text-xs text-brand-400 font-medium">{selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected</p>}
                <input ref={fileRef} type="file" multiple accept=".pdf,.pptx,.txt" className="hidden"
                  onChange={(e) => setSelectedFiles(Array.from(e.target.files ?? []))} />
              </div>
              {selectedFiles.length > 0 && (
                <div className="mt-2 space-y-1">
                  {selectedFiles.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-2 py-1.5 bg-gray-800 rounded-lg">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-400 shrink-0" />
                      <span className="text-xs text-gray-300 truncate flex-1">{f.name}</span>
                      <span className="text-xs text-gray-500 shrink-0">{(f.size / 1024).toFixed(0)}KB</span>
                      <button onClick={() => setSelectedFiles((p) => p.filter((_, j) => j !== i))}
                        className="text-gray-600 hover:text-red-400 text-xs shrink-0">✕</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <button onClick={handleIndex} disabled={uploading || (!selectedFiles.length && !ytUrl.trim())}
            className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-lg text-sm text-white font-medium flex items-center justify-center gap-2 transition-colors">
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {uploading ? 'Indexing...' : 'Index'}
          </button>

          {indexError && (
            <div className="px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-xs text-red-400">{indexError}</p>
            </div>
          )}
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h2 className="font-semibold text-white text-sm mb-3">Sessions</h2>
          {sessions.length === 0 && <p className="text-xs text-gray-500">No sessions yet. Upload files to get started.</p>}
          {sessions.map((s: Session) => (
            <div key={s.id} onClick={() => setActiveSession(s)}
              className={clsx('group flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-colors',
                activeSession?.id === s.id ? 'bg-brand-500/20 border border-brand-500/30' : 'hover:bg-gray-800')}>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white truncate">{s.name}</p>
                <p className="text-xs text-gray-500">{s.chunk_count} chunks · {s.created_at.slice(0, 10)}</p>
              </div>
              <button onClick={(e) => { e.stopPropagation(); handleDelete(s.id) }}
                className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-all">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Tab bar */}
        <div className="flex gap-1 px-4 pt-4 border-b border-gray-800 bg-gray-950 overflow-x-auto shrink-0">
          {TABS.map(({ id, icon: Icon, label }) => (
            <button key={id} onClick={() => navigate(`/${id}`)}
              className={clsx('flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg whitespace-nowrap transition-colors border-b-2',
                activeTab === id ? 'border-brand-500 text-brand-300 bg-brand-500/5' : 'border-transparent text-gray-400 hover:text-white')}>
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {!canUse && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-sm">
                <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-gray-600" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {!activeSession ? 'Select or create a session' : 'Configure your provider'}
                </h3>
                <p className="text-sm text-gray-400">
                  {!activeSession ? 'Upload study material on the left to get started.'
                    : provider === 'ollama' ? 'Make sure Ollama is running: ollama serve'
                    : 'Enter your API key in the provider settings.'}
                </p>
              </div>
            </div>
          )}

          {canUse && activeTab === 'chat'        && <ChatPanel sessionId={activeSession!.id} />}
          {canUse && activeTab === 'quiz'        && <QuizView sessionId={activeSession!.id} />}
          {canUse && activeTab === 'flashcards'  && <FlashcardViewer sessionId={activeSession!.id} />}
          {canUse && activeTab === 'dashboard'   && <Dashboard sessionId={activeSession!.id} />}
          {canUse && activeTab === 'concept-map' && <ConceptMapView sessionId={activeSession!.id} />}

          {canUse && activeTab === 'summarize' && (
            <div className="max-w-2xl mx-auto p-8 space-y-4">
              <h2 className="text-2xl font-bold text-white">📄 Summarize</h2>
              <input value={summaryTopic} onChange={(e) => setSummaryTopic(e.target.value)} placeholder="Topic (optional)"
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500" />
              <button onClick={handleSummarize} disabled={studyLoading}
                className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium flex items-center justify-center gap-2">
                {studyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Summary'}
              </button>
              {summary && (
                <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
                  <p className="text-gray-200 whitespace-pre-wrap leading-relaxed text-sm">{summary}</p>
                </div>
              )}
            </div>
          )}

          {canUse && activeTab === 'compare' && (
            <div className="max-w-2xl mx-auto p-8 space-y-4">
              <h2 className="text-2xl font-bold text-white">🔀 Compare Topics</h2>
              <div className="grid grid-cols-2 gap-3">
                <input value={compareA} onChange={(e) => setCompareA(e.target.value)} placeholder="Topic A"
                  className="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500" />
                <input value={compareB} onChange={(e) => setCompareB(e.target.value)} placeholder="Topic B"
                  className="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500" />
              </div>
              <button onClick={handleCompare} disabled={studyLoading || !compareA || !compareB}
                className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium flex items-center justify-center gap-2">
                {studyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Compare'}
              </button>
              {comparison && (
                <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
                  <p className="text-gray-200 whitespace-pre-wrap leading-relaxed text-sm">{comparison}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}