import { useState, useEffect, useRef } from 'react'
import { Loader2, Download, RefreshCw, AlertCircle } from 'lucide-react'
import { studyApi } from '../../api/client'
import { useProviderStore } from '../../store'

interface Props { sessionId: number }

export function ConceptMapView({ sessionId }: Props) {
  const [topic, setTopic] = useState('')
  const [mermaid, setMermaid] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [renderError, setRenderError] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const { provider, apiKey, ollamaModel } = useProviderStore()

  useEffect(() => {
    if (!mermaid || !containerRef.current) return
    setRenderError('')
    const render = async () => {
      try {
        const { default: m } = await import('mermaid')
        m.initialize({
          startOnLoad: false,
          theme: 'dark',
          themeVariables: {
            primaryColor: '#6366f1',
            primaryTextColor: '#f9fafb',
            primaryBorderColor: '#4f46e5',
            lineColor: '#6b7280',
            background: '#0f172a',
            mainBkg: '#1e1b4b',
          },
        })
        const { svg } = await m.render(`mermaid-${Date.now()}`, mermaid)
        if (containerRef.current) {
          containerRef.current.innerHTML = svg
          const svgEl = containerRef.current.querySelector('svg')
          if (svgEl) { svgEl.style.width = '100%'; svgEl.style.height = 'auto'; svgEl.style.maxHeight = '500px' }
        }
      } catch {
        setRenderError('Could not render diagram. The AI may have generated invalid Mermaid syntax.')
        if (containerRef.current) containerRef.current.innerHTML = ''
      }
    }
    render()
  }, [mermaid])

  const generate = async () => {
    setLoading(true); setError(''); setRenderError(''); setMermaid('')
    try {
      const r = await studyApi.conceptMap({ session_id: sessionId, provider, api_key: apiKey, ollama_model: ollamaModel, topic })
      if (!r.data.mermaid) setError('No concept map generated. Try a more specific topic.')
      else setMermaid(r.data.mermaid)
    } catch { setError('Failed to generate concept map.') }
    finally { setLoading(false) }
  }

  const downloadSVG = () => {
    const svg = containerRef.current?.querySelector('svg')
    if (!svg) return
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([svg.outerHTML], { type: 'image/svg+xml' }))
    a.download = `concept-map-${topic || 'notes'}.svg`; a.click()
  }

  const downloadCode = () => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([mermaid], { type: 'text/plain' }))
    a.download = 'concept-map.mmd'; a.click()
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-5">
      <h2 className="text-2xl font-bold text-white">🗺️ Concept Map</h2>
      <p className="text-sm text-gray-400">Generates a visual mind map from your notes, rendered live in the browser.</p>

      <div className="flex gap-3">
        <input value={topic} onChange={(e) => setTopic(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && generate()}
          placeholder="Topic (optional — leave blank for full overview)"
          className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500" />
        <button onClick={generate} disabled={loading}
          className="px-5 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white text-sm font-medium flex items-center gap-2 whitespace-nowrap">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" />Generating...</>
            : mermaid ? <><RefreshCw className="w-4 h-4" />Regenerate</> : '🗺️ Generate'}
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {mermaid && (
        <div className="space-y-3">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-4 overflow-auto min-h-32">
            {renderError ? (
              <div className="space-y-3">
                <div className="flex items-start gap-2 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-yellow-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-yellow-400">{renderError}</p>
                </div>
                <pre className="text-xs text-gray-300 font-mono p-3 bg-gray-800 rounded-lg overflow-x-auto">{mermaid}</pre>
              </div>
            ) : (
              <div ref={containerRef} className="flex justify-center" />
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            {!renderError && (
              <button onClick={downloadSVG} className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 transition-colors">
                <Download className="w-4 h-4" /> Download SVG
              </button>
            )}
            <button onClick={downloadCode} className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 transition-colors">
              <Download className="w-4 h-4" /> Download .mmd
            </button>
            <a href="https://mermaid.live" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-sm text-gray-300 transition-colors">
              Open in mermaid.live ↗
            </a>
          </div>

          <details className="group">
            <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-400">View raw Mermaid code</summary>
            <pre className="mt-2 text-xs text-gray-400 font-mono p-3 bg-gray-800 rounded-lg overflow-x-auto">{mermaid}</pre>
          </details>
        </div>
      )}
    </div>
  )
}