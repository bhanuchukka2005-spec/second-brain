import { useState } from 'react'
import { ChevronLeft, ChevronRight, Download, Loader2, RotateCcw } from 'lucide-react'
import { clsx } from 'clsx'
import { studyApi } from '../../api/client'
import { useProviderStore } from '../../store'
import type { Flashcard } from '../../types'

interface Props { sessionId: number }

export function FlashcardViewer({ sessionId }: Props) {
  const [cards, setCards] = useState<Flashcard[]>([])
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)
  const [topic, setTopic] = useState('')
  const [numCards, setNumCards] = useState(15)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { provider, apiKey, ollamaModel } = useProviderStore()

  const generate = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await studyApi.flashcards({
        session_id: sessionId,
        provider, api_key: apiKey, ollama_model: ollamaModel,
        topic, num_cards: numCards,
      })
      setCards(res.data.cards)
      setIndex(0)
      setFlipped(false)
    } catch {
      setError('Failed to generate flashcards.')
    } finally {
      setLoading(false)
    }
  }

  const exportCSV = () => {
    const rows = ['Front,Back', ...cards.map((c) => `"${c.front}","${c.back}"`)]
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'flashcards.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  const card = cards[index]

  return (
    <div className="max-w-2xl mx-auto p-8">
      <h2 className="text-2xl font-bold text-white mb-2">🃏 Flashcards</h2>
      <p className="text-gray-400 text-sm mb-8">Click the card to flip. Export to Anki as CSV.</p>

      {/* Controls */}
      <div className="flex gap-3 mb-8">
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Topic (optional)"
          className="flex-1 px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand-500"
        />
        <select
          value={numCards}
          onChange={(e) => setNumCards(Number(e.target.value))}
          className="px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-xl text-sm text-white focus:outline-none"
        >
          {[5, 10, 15, 20, 30].map((n) => <option key={n} value={n}>{n} cards</option>)}
        </select>
        <button
          onClick={generate}
          disabled={loading}
          className="px-5 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white text-sm font-medium transition-colors flex items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate'}
        </button>
      </div>

      {error && <p className="text-sm text-red-400 mb-4">{error}</p>}

      {card && (
        <>
          {/* Progress */}
          <div className="flex justify-between text-xs text-gray-500 mb-3">
            <span>Card {index + 1} of {cards.length}</span>
            <span>{flipped ? 'Back' : 'Front'}</span>
          </div>

          {/* Flip card */}
          <div
            onClick={() => setFlipped(!flipped)}
            className="cursor-pointer select-none"
            style={{ perspective: '1000px' }}
          >
            <div
              className="relative w-full transition-transform duration-500"
              style={{
                transformStyle: 'preserve-3d',
                transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                minHeight: '220px',
              }}
            >
              {/* Front */}
              <div
                className="absolute inset-0 flex items-center justify-center p-8 bg-gray-800 border border-gray-700 rounded-2xl"
                style={{ backfaceVisibility: 'hidden' }}
              >
                <p className="text-center text-white text-lg leading-relaxed">{card.front}</p>
                <RotateCcw className="absolute bottom-4 right-4 w-4 h-4 text-gray-500" />
              </div>

              {/* Back */}
              <div
                className="absolute inset-0 flex items-center justify-center p-8 bg-brand-900/40 border border-brand-700/50 rounded-2xl"
                style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
              >
                <p className="text-center text-brand-200 text-lg leading-relaxed">{card.back}</p>
                <RotateCcw className="absolute bottom-4 right-4 w-4 h-4 text-brand-600" />
              </div>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between mt-6 gap-3">
            <button
              onClick={() => { setIndex(Math.max(0, index - 1)); setFlipped(false) }}
              disabled={index === 0}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 rounded-xl text-sm text-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>

            {/* Dots */}
            <div className="flex gap-1">
              {cards.map((_, i) => (
                <button
                  key={i}
                  onClick={() => { setIndex(i); setFlipped(false) }}
                  className={clsx(
                    'w-2 h-2 rounded-full transition-colors',
                    i === index ? 'bg-brand-400' : 'bg-gray-700 hover:bg-gray-600'
                  )}
                />
              ))}
            </div>

            <button
              onClick={() => { setIndex(Math.min(cards.length - 1, index + 1)); setFlipped(false) }}
              disabled={index === cards.length - 1}
              className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 disabled:opacity-30 rounded-xl text-sm text-white transition-colors"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Export */}
          <div className="mt-6">
            <button
              onClick={exportCSV}
              className="w-full flex items-center justify-center gap-2 py-2.5 border border-gray-700 hover:border-gray-600 rounded-xl text-sm text-gray-300 transition-colors"
            >
              <Download className="w-4 h-4" /> Export as CSV (Anki)
            </button>
          </div>
        </>
      )}
    </div>
  )
}
