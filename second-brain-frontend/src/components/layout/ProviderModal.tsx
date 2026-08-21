import { X, Settings } from 'lucide-react'
import { ProviderPicker } from './ProviderPicker'

interface Props {
  open: boolean
  onClose: () => void
}

export function ProviderModal({ open, onClose }: Props) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />
      {/* No overflow-hidden here — it was clipping the provider dropdown
          list, since the dropdown renders as an absolutely-positioned
          element that can extend past this box's own content height. */}
      <div className="relative w-full max-w-md bg-gray-900 border border-gray-800 rounded-2xl shadow-2xl shadow-black/50 animate-slide-up">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 rounded-t-2xl bg-gray-900">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-brand-400" />
            <h2 className="font-semibold text-white text-lg">AI Provider</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 rounded-b-2xl">
          <ProviderPicker />
        </div>
      </div>
    </div>
  )
}