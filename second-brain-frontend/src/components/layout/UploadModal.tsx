import { useState, useRef } from 'react'
import { X, Upload, Loader2, Plus } from 'lucide-react'
import { clsx } from 'clsx'
import { sessionsApi } from '../../api/client'
import { useSessionStore } from '../../store'

interface Props {
  open: boolean
  onClose: () => void
}

export function UploadModal({ open, onClose }: Props) {
  const { sessions, addSession, setActiveSession } = useSessionStore()
  const [uploading, setUploading] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const [ytUrl, setYtUrl] = useState('')
  const [ytMode, setYtMode] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [indexError, setIndexError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  if (!open) return null

  const reset = () => {
    setSessionName(''); setYtUrl(''); setSelectedFiles([]); setIndexError('')
    if (fileRef.current) fileRef.current.value = ''
  }

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
      reset()
      onClose()
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setIndexError(detail || 'Indexing failed. Try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={() => { reset(); onClose() }}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl shadow-black/50 animate-slide-up overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 className="font-semibold text-white text-lg">New Session</h2>
          <button
            onClick={() => { reset(); onClose() }}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <input
            value={sessionName}
            onChange={(e) => setSessionName(e.target.value)}
            placeholder="Session name (e.g. DevOps Week 3)"
            className="w-full px-4 py-3 bg-gray-800/80 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
          />

          <div className="flex gap-2 p-1 bg-gray-800/60 rounded-xl">
            <button
              onClick={() => setYtMode(false)}
              className={clsx(
                'flex-1 py-2 text-sm rounded-lg font-medium transition-all',
                !ytMode ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20' : 'text-gray-400 hover:text-gray-200'
              )}
            >
              📄 Files
            </button>
            <button
              onClick={() => setYtMode(true)}
              className={clsx(
                'flex-1 py-2 text-sm rounded-lg font-medium transition-all',
                ytMode ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20' : 'text-gray-400 hover:text-gray-200'
              )}
            >
              🎥 YouTube
            </button>
          </div>

          {ytMode ? (
            <input
              value={ytUrl}
              onChange={(e) => setYtUrl(e.target.value)}
              placeholder="https://youtu.be/..."
              className="w-full px-4 py-3 bg-gray-800/80 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 transition-all"
            />
          ) : (
            <div>
              <div
                onClick={() => fileRef.current?.click()}
                className={clsx(
                  'border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all',
                  selectedFiles.length > 0
                    ? 'border-brand-500 bg-brand-500/5'
                    : 'border-gray-700 hover:border-brand-500/60 hover:bg-gray-800/40'
                )}
              >
                <Upload className={clsx('w-6 h-6 mx-auto mb-2', selectedFiles.length > 0 ? 'text-brand-400' : 'text-gray-500')} />
                {selectedFiles.length === 0 ? (
                  <p className="text-sm text-gray-400">Click to select PDF, PPTX, TXT</p>
                ) : (
                  <p className="text-sm text-brand-400 font-medium">
                    {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected
                  </p>
                )}
                <input
                  ref={fileRef}
                  type="file"
                  multiple
                  accept=".pdf,.pptx,.txt"
                  className="hidden"
                  onChange={(e) => setSelectedFiles(Array.from(e.target.files ?? []))}
                />
              </div>

              {selectedFiles.length > 0 && (
                <div className="mt-3 space-y-1.5 max-h-32 overflow-y-auto">
                  {selectedFiles.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-2 bg-gray-800/60 rounded-lg">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-400 shrink-0" />
                      <span className="text-xs text-gray-300 truncate flex-1">{f.name}</span>
                      <span className="text-xs text-gray-500 shrink-0">{(f.size / 1024).toFixed(0)}KB</span>
                      <button
                        onClick={() => setSelectedFiles((p) => p.filter((_, j) => j !== i))}
                        className="text-gray-600 hover:text-red-400 text-xs shrink-0"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {indexError && (
            <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl">
              <p className="text-xs text-red-400">{indexError}</p>
            </div>
          )}

          <button
            onClick={handleIndex}
            disabled={uploading || (!selectedFiles.length && !ytUrl.trim())}
            className="w-full py-3 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-sm text-white font-semibold flex items-center justify-center gap-2 transition-all shadow-lg shadow-brand-600/20"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            {uploading ? 'Indexing your notes...' : 'Create Session'}
          </button>
        </div>
      </div>
    </div>
  )
}