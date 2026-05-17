import { useState } from 'react'
import { Trophy, RefreshCw, Loader2, CheckCircle, XCircle, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { studyApi } from '../../api/client'
import { useProviderStore } from '../../store'
import type { MCQQuestion } from '../../types'

interface Props {
  sessionId: number
}

type QuizState = 'setup' | 'active' | 'result'

export function QuizView({ sessionId }: Props) {
  const [state, setState] = useState<QuizState>('setup')
  const [topic, setTopic] = useState('')
  const [numQ, setNumQ] = useState(10)
  const [questions, setQuestions] = useState<MCQQuestion[]>([])
  const [index, setIndex] = useState(0)
  const [score, setScore] = useState(0)
  const [selected, setSelected] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)
  const [wrongTopics, setWrongTopics] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { provider, apiKey, ollamaModel } = useProviderStore()

  const startQuiz = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await studyApi.mcq({
        session_id: sessionId,
        provider,
        api_key: apiKey,
        ollama_model: ollamaModel,
        topic,
        num_questions: numQ,
        wrong_topics: wrongTopics,
      })
      if (res.data.questions.length === 0) {
        setError('No questions generated. Try uploading more notes.')
        return
      }
      setQuestions(res.data.questions)
      setIndex(0)
      setScore(0)
      setSelected(null)
      setSubmitted(false)
      setState('active')
    } catch {
      setError('Failed to generate quiz. Check your provider settings.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!selected) return
    setSubmitted(true)
    const q = questions[index]
    if (selected === q.answer) {
      setScore((s) => s + 1)
    } else {
      setWrongTopics((wt) => [...wt, ...q.question.split(' ').slice(0, 3)])
    }

    if (index + 1 >= questions.length) {
      // Save score
      try {
        await studyApi.saveScore(sessionId, score + (selected === q.answer ? 1 : 0), questions.length, topic)
      } catch { /* non-critical */ }
      setTimeout(() => setState('result'), 800)
    }
  }

  const nextQuestion = () => {
    setIndex((i) => i + 1)
    setSelected(null)
    setSubmitted(false)
  }

  const pct = Math.round((score / questions.length) * 100)
  const grade = pct >= 90 ? 'A' : pct >= 75 ? 'B' : pct >= 60 ? 'C' : 'F'
  const gradeColor = pct >= 75 ? 'text-green-400' : pct >= 60 ? 'text-yellow-400' : 'text-red-400'

  if (state === 'setup') {
    return (
      <div className="max-w-lg mx-auto p-8">
        <h2 className="text-2xl font-bold text-white mb-2">📝 MCQ Quiz</h2>
        <p className="text-gray-400 mb-8 text-sm">Adaptive questions — gets harder on your weak topics.</p>

        <div className="space-y-5">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Topic (optional)</label>
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Docker networking"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm placeholder-gray-500 focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1.5">
              Number of questions: <span className="text-white font-medium">{numQ}</span>
            </label>
            <input
              type="range" min={5} max={20} value={numQ}
              onChange={(e) => setNumQ(Number(e.target.value))}
              className="w-full accent-brand-500"
            />
          </div>

          {wrongTopics.length > 0 && (
            <div className="px-4 py-3 bg-orange-500/10 border border-orange-500/20 rounded-xl">
              <p className="text-xs text-orange-400">⚡ Adaptive mode on — will focus on your {wrongTopics.length} weak areas</p>
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            onClick={startQuiz}
            disabled={loading}
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '⚡ Start Quiz'}
          </button>
        </div>
      </div>
    )
  }

  if (state === 'result') {
    return (
      <div className="max-w-lg mx-auto p-8 text-center">
        <Trophy className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-white mb-1">Quiz Complete!</h2>
        <div className="grid grid-cols-3 gap-4 my-8">
          <div className="bg-gray-800 rounded-xl p-4">
            <p className="text-2xl font-bold text-white">{score}/{questions.length}</p>
            <p className="text-xs text-gray-400 mt-1">Score</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-4">
            <p className="text-2xl font-bold text-white">{pct}%</p>
            <p className="text-xs text-gray-400 mt-1">Accuracy</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-4">
            <p className={clsx('text-2xl font-bold', gradeColor)}>{grade}</p>
            <p className="text-xs text-gray-400 mt-1">Grade</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => { setState('setup'); setWrongTopics([]) }}
            className="flex-1 py-3 bg-gray-800 hover:bg-gray-700 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-4 h-4" /> New Quiz
          </button>
          <button
            onClick={startQuiz}
            className="flex-1 py-3 bg-brand-600 hover:bg-brand-500 rounded-xl text-white font-medium transition-colors"
          >
            Retake (Harder)
          </button>
        </div>
      </div>
    )
  }

  const q = questions[index]
  return (
    <div className="max-w-2xl mx-auto p-8 animate-fade-in">
      {/* Progress */}
      <div className="flex items-center justify-between mb-6">
        <span className="text-sm text-gray-400">Question {index + 1} / {questions.length}</span>
        <span className="text-sm text-gray-400">Score: {score}</span>
      </div>
      <div className="w-full bg-gray-800 rounded-full h-1.5 mb-8">
        <div
          className="bg-brand-500 h-1.5 rounded-full transition-all"
          style={{ width: `${((index) / questions.length) * 100}%` }}
        />
      </div>

      <h3 className="text-lg font-semibold text-white mb-6">{q.question}</h3>

      <div className="space-y-3 mb-6">
        {Object.entries(q.options).map(([key, val]) => {
          const isCorrect = key === q.answer
          const isSelected = selected === key
          return (
            <button
              key={key}
              onClick={() => !submitted && setSelected(key)}
              disabled={submitted}
              className={clsx(
                'w-full flex items-center gap-3 px-4 py-3.5 rounded-xl border text-sm text-left transition-all',
                submitted && isCorrect && 'border-green-500 bg-green-500/10 text-green-300',
                submitted && isSelected && !isCorrect && 'border-red-500 bg-red-500/10 text-red-300',
                !submitted && isSelected && 'border-brand-500 bg-brand-500/10 text-brand-300',
                !submitted && !isSelected && 'border-gray-700 text-gray-300 hover:border-gray-600 hover:bg-gray-800'
              )}
            >
              <span className="font-mono text-xs w-5 shrink-0">{key}</span>
              <span className="flex-1">{val}</span>
              {submitted && isCorrect && <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />}
              {submitted && isSelected && !isCorrect && <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
            </button>
          )
        })}
      </div>

      {submitted && q.explanation && (
        <div className="px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl mb-6 animate-fade-in">
          <p className="text-xs text-gray-400 mb-1">Explanation</p>
          <p className="text-sm text-gray-300">{q.explanation}</p>
        </div>
      )}

      <div className="flex gap-3">
        {!submitted ? (
          <button
            onClick={handleSubmit}
            disabled={!selected}
            className="flex-1 py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium transition-colors"
          >
            Submit Answer
          </button>
        ) : (
          <button
            onClick={nextQuestion}
            className="flex-1 py-3 bg-brand-600 hover:bg-brand-500 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
          >
            {index + 1 < questions.length ? 'Next Question' : 'See Results'}
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
