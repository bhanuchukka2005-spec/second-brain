import { useState } from 'react'
import { ChevronDown, Wifi, WifiOff } from 'lucide-react'
import { clsx } from 'clsx'
import { PROVIDERS } from '../../types'
import { useProviderStore } from '../../store'

interface Props {
  compact?: boolean
}

export function ProviderPicker({ compact = false }: Props) {
  const { provider, apiKey, ollamaModel, setProvider, setApiKey, setOllamaModel } = useProviderStore()
  const [open, setOpen] = useState(false)

  const current = PROVIDERS.find((p) => p.id === provider) ?? PROVIDERS[0]

  return (
    <div className="space-y-3">
      {/* Dropdown trigger */}
      <div className="relative">
        <button
          onClick={() => setOpen(!open)}
          className="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white hover:border-gray-600 transition-colors"
        >
          <span className="truncate">{current.label}</span>
          <ChevronDown className={clsx('w-4 h-4 text-gray-400 shrink-0 transition-transform', open && 'rotate-180')} />
        </button>

        {open && (
          <>
            {/* Click-outside catcher */}
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />

            {/* Scrollable list — max height + overflow-y-auto is the fix */}
            <div className="absolute z-50 mt-1 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-xl max-h-60 overflow-y-auto">
              {PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => {
                    setProvider(p.id)
                    setOpen(false)
                  }}
                  className={clsx(
                    'w-full flex items-center gap-3 px-3 py-2.5 text-sm text-left hover:bg-gray-700 transition-colors',
                    p.id === provider && 'bg-brand-500/20 text-brand-300'
                  )}
                >
                  <span className="flex-1 truncate">{p.label}</span>
                  {p.free && (
                    <span className="text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded font-medium shrink-0">
                      Free
                    </span>
                  )}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Ollama model selector */}
      {provider === 'ollama' && (
        <div>
          <label className="block text-xs text-gray-400 mb-1">Model name</label>
          <input
            type="text"
            value={ollamaModel}
            onChange={(e) => setOllamaModel(e.target.value)}
            placeholder="llama3.2"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Run: <code className="text-brand-400">ollama pull llama3.2</code>
          </p>
        </div>
      )}

      {/* API key input for cloud providers */}
      {provider !== 'ollama' && (
        <div>
          <label className="block text-xs text-gray-400 mb-1">{current.hint}</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Paste your API key..."
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500"
          />
          {apiKey ? (
            <div className="flex items-center gap-1.5 mt-1.5">
              <Wifi className="w-3 h-3 text-green-400" />
              <span className="text-xs text-green-400">Key entered</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 mt-1.5">
              <WifiOff className="w-3 h-3 text-gray-500" />
              <span className="text-xs text-gray-500">No key — add one above</span>
            </div>
          )}
        </div>
      )}

    </div>
  )
}