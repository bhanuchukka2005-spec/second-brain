import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Loader2, MessageSquare, Sparkles } from 'lucide-react'
import { useSessionStore, useProviderStore } from '../store'
import { studyApi, healthApi } from '../api/client'
import { ChatPanel } from '../components/chat/ChatPanel'
import { QuizView } from '../components/quiz/QuizView'
import { FlashcardViewer } from '../components/flashcards/FlashcardViewer'
import { Dashboard } from '../components/study/Dashboard'
import { ConceptMapView } from '../components/study/ConceptMapView'

export function SessionPage() {
  const { activeSession } = useSessionStore()
  const { provider, apiKey, ollamaModel } = useProviderStore()
  const location = useLocation()
  const activeTab = location.pathname.replace('/', '') || 'chat'

  // Track Ollama's real running state — don't just assume it's ready.
  const [ollamaOk, setOllamaOk] = useState<boolean | null>(null)

  useEffect(() => {
    if (provider === 'ollama') {
      healthApi.check()
        .then((r) => setOllamaOk(r.data.ollama_available))
        .catch(() => setOllamaOk(false))
    }
  }, [provider])

  const [summaryTopic, setSummaryTopic] = useState('')
  const [summary, setSummary] = useState('')
  const [compareA, setCompareA] = useState('')
  const [compareB, setCompareB] = useState('')
  const [comparison, setComparison] = useState('')
  const [studyLoading, setStudyLoading] = useState(false)

  const bp = () => ({ session_id: activeSession!.id, provider, api_key: apiKey, ollama_model: ollamaModel })

  const handleSummarize = async () => {
    if (!activeSession) return
    setStudyLoading(true)
    try {
      const r = await studyApi.summarize({ ...bp(), topic: summaryTopic })
      setSummary(r.data.summary)
    } catch {
      setSummary('Error generating summary.')
    } finally {
      setStudyLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!activeSession || !compareA || !compareB) return
    setStudyLoading(true)
    try {
      const r = await studyApi.compare({ ...bp(), topic_a: compareA, topic_b: compareB })
      setComparison(r.data.comparison)
    } catch {
      setComparison('Error comparing topics.')
    } finally {
      setStudyLoading(false)
    }
  }

  if (!activeSession) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center max-w-sm">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-brand-600/20 to-brand-700/10 border border-brand-500/20 flex items-center justify-center mx-auto mb-5">
            <Sparkles className="w-9 h-9 text-brand-400" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No session selected</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            Click the <span className="text-brand-400 font-medium">+</span> next to Sessions
            in the sidebar to upload your notes and get started.
          </p>
        </div>
      </div>
    )
  }

  // No aliased boolean here — check each provider path explicitly so
  // TypeScript never narrows `provider` in a way that hides a real state.
  const needsOllama = provider === 'ollama' && ollamaOk !== true
  const needsApiKey = provider !== 'ollama' && !apiKey

  if (needsOllama || needsApiKey) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center max-w-sm">
          <div className="w-20 h-20 rounded-3xl bg-gray-900 border border-gray-800 flex items-center justify-center mx-auto mb-5">
            <MessageSquare className="w-9 h-9 text-gray-600" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Configure your provider</h3>
          <p className="text-sm text-gray-400 leading-relaxed">
            {needsOllama
              ? "Ollama isn't running. Start it with: ollama serve"
              : 'Open AI Provider in the sidebar and enter your API key.'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full">
      {activeTab === 'chat'        && <ChatPanel sessionId={activeSession.id} />}
      {activeTab === 'quiz'        && <QuizView sessionId={activeSession.id} />}
      {activeTab === 'flashcards'  && <FlashcardViewer sessionId={activeSession.id} />}
      {activeTab === 'dashboard'   && <Dashboard sessionId={activeSession.id} />}
      {activeTab === 'concept-map' && <ConceptMapView sessionId={activeSession.id} />}

      {activeTab === 'summarize' && (
        <div className="max-w-2xl mx-auto p-8 space-y-5">
          <div>
            <h2 className="text-2xl font-bold text-white">📄 Summarize</h2>
            <p className="text-sm text-gray-500 mt-1">Get a clear, concise overview of your notes.</p>
          </div>
          <input
            value={summaryTopic}
            onChange={(e) => setSummaryTopic(e.target.value)}
            placeholder="Topic (optional)"
            className="w-full px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
          />
          <button
            onClick={handleSummarize}
            disabled={studyLoading}
            className="w-full py-3 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 disabled:opacity-40 rounded-xl text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-brand-600/20 transition-all"
          >
            {studyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate Summary'}
          </button>
          {summary && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <p className="text-gray-200 whitespace-pre-wrap leading-relaxed text-sm">{summary}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'compare' && (
        <div className="max-w-2xl mx-auto p-8 space-y-5">
          <div>
            <h2 className="text-2xl font-bold text-white">🔀 Compare Topics</h2>
            <p className="text-sm text-gray-500 mt-1">See similarities, differences, and key takeaways.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input
              value={compareA}
              onChange={(e) => setCompareA(e.target.value)}
              placeholder="Topic A"
              className="px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
            />
            <input
              value={compareB}
              onChange={(e) => setCompareB(e.target.value)}
              placeholder="Topic B"
              className="px-4 py-3 bg-gray-900 border border-gray-800 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
            />
          </div>
          <button
            onClick={handleCompare}
            disabled={studyLoading || !compareA || !compareB}
            className="w-full py-3 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 disabled:opacity-40 rounded-xl text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-brand-600/20 transition-all"
          >
            {studyLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Compare'}
          </button>
          {comparison && (
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
              <p className="text-gray-200 whitespace-pre-wrap leading-relaxed text-sm">{comparison}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}