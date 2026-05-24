import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid,
} from 'recharts'
import { Trophy, Target, TrendingUp, BookOpen } from 'lucide-react'
import { studyApi } from '../../api/client'
import type { QuizScore } from '../../types'

interface Props { sessionId: number }

export function Dashboard({ sessionId }: Props) {
  const [scores, setScores] = useState<QuizScore[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    studyApi.scores(sessionId)
      .then((r) => setScores(r.data.scores))
      .catch(() => setScores([]))
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (scores.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <BookOpen className="w-12 h-12 text-gray-600 mb-3" />
        <h3 className="text-lg font-semibold text-white mb-1">No quiz data yet</h3>
        <p className="text-sm text-gray-400 max-w-sm">
          Take some quizzes in the MCQ Quiz tab and your scores will appear here.
        </p>
      </div>
    )
  }

  const latest = scores[0]
  const best = scores.reduce((a, b) => a.percentage > b.percentage ? a : b)
  const avg = Math.round(scores.reduce((a, b) => a + b.percentage, 0) / scores.length)
  const trend = scores.length > 1 ? scores[0].percentage - scores[scores.length - 1].percentage : 0

  const chartData = [...scores].reverse().map((s, i) => ({
    name: `Q${i + 1}`,
    score: Math.round(s.percentage),
    topic: s.topic || 'General',
  }))

  const topicMap: Record<string, number[]> = {}
  scores.forEach((s) => {
    const t = s.topic || 'General'
    if (!topicMap[t]) topicMap[t] = []
    topicMap[t].push(s.percentage)
  })
  const topicData = Object.entries(topicMap).map(([topic, percs]) => ({
    topic: topic.length > 12 ? topic.slice(0, 12) + '…' : topic,
    avg: Math.round(percs.reduce((a, b) => a + b, 0) / percs.length),
  }))

  const tooltipStyle = {
    contentStyle: { background: '#111827', border: '1px solid #374151', borderRadius: 8 },
    labelStyle: { color: '#f9fafb' },
  }

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold text-white">📊 Dashboard</h2>

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { icon: <Trophy className="w-5 h-5 text-yellow-400" />, label: 'Best Score', value: `${Math.round(best.percentage)}%`, sub: best.topic || 'General' },
          { icon: <Target className="w-5 h-5 text-brand-400" />, label: 'Latest', value: `${Math.round(latest.percentage)}%`, sub: latest.timestamp?.slice(0, 10) ?? '' },
          { icon: <TrendingUp className="w-5 h-5 text-green-400" />, label: 'Average', value: `${avg}%`, sub: `${scores.length} quiz${scores.length !== 1 ? 'zes' : ''}` },
          { icon: <BookOpen className="w-5 h-5 text-purple-400" />, label: 'Trend', value: trend >= 0 ? `+${Math.round(trend)}%` : `${Math.round(trend)}%`, sub: 'vs first attempt' },
        ].map((m) => (
          <div key={m.label} className="bg-gray-900 border border-gray-800 rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-2">{m.icon}<span className="text-xs text-gray-400">{m.label}</span></div>
            <p className="text-2xl font-bold text-white">{m.value}</p>
            <p className="text-xs text-gray-500 truncate mt-0.5">{m.sub}</p>
          </div>
        ))}
      </div>

      {/* Score over time */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
        <h3 className="text-sm font-medium text-gray-400 mb-4">Score Over Time</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [`${v}%`, 'Score']} />
            <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1', r: 4 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Topic performance */}
      {topicData.length > 1 && (
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Performance by Topic</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={topicData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="topic" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
              <Tooltip {...tooltipStyle} formatter={(v: number) => [`${v}%`, 'Avg']} />
              <Bar dataKey="avg" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent scores table */}
      <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-800">
          <h3 className="text-sm font-medium text-gray-400">Recent Quizzes</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="text-xs text-gray-500 border-b border-gray-800">
              <th className="px-5 py-3 text-left">Topic</th>
              <th className="px-5 py-3 text-left">Score</th>
              <th className="px-5 py-3 text-left">Grade</th>
              <th className="px-5 py-3 text-left">Date</th>
            </tr>
          </thead>
          <tbody>
            {scores.slice(0, 10).map((s, i) => {
              const pct = Math.round(s.percentage)
              const grade = pct >= 90 ? 'A' : pct >= 75 ? 'B' : pct >= 60 ? 'C' : 'F'
              const gc = pct >= 75 ? 'text-green-400' : pct >= 60 ? 'text-yellow-400' : 'text-red-400'
              return (
                <tr key={i} className="border-b border-gray-800 last:border-0 hover:bg-gray-800/50">
                  <td className="px-5 py-3 text-sm text-white">{s.topic || 'General'}</td>
                  <td className="px-5 py-3 text-sm text-gray-300">{s.score}/{s.total} ({pct}%)</td>
                  <td className={`px-5 py-3 text-sm font-bold ${gc}`}>{grade}</td>
                  <td className="px-5 py-3 text-sm text-gray-500">{s.timestamp.slice(0, 10)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}