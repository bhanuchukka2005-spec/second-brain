import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Brain, Loader2, ArrowLeft, Mail } from 'lucide-react'
import { authApi } from '../api/client'

export function ForgotPasswordPage() {
  const [identifier, setIdentifier] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authApi.forgotPassword(identifier.trim())
      // Always show success — backend intentionally never reveals
      // whether the account exists, to prevent enumeration attacks.
      setSent(true)
    } catch {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-md animate-slide-up">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 mb-4">
            <Brain className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-3xl font-bold text-white">Reset your password</h1>
          <p className="text-gray-400 mt-2 text-sm">
            Enter your username or email and we'll send you a reset link.
          </p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          {sent ? (
            <div className="text-center py-4">
              <div className="w-14 h-14 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center mx-auto mb-4">
                <Mail className="w-7 h-7 text-green-400" />
              </div>
              <h2 className="text-lg font-semibold text-white mb-2">Check your inbox</h2>
              <p className="text-sm text-gray-400 leading-relaxed">
                If an account exists for <span className="text-white">{identifier}</span>,
                a password reset link is on its way. It's valid for 30 minutes.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">Username or email</label>
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                  autoFocus
                  placeholder="your_username or you@example.com"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>

              {error && (
                <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || !identifier.trim()}
                className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? 'Sending...' : 'Send reset link'}
              </button>
            </form>
          )}

          <Link
            to="/login"
            className="flex items-center justify-center gap-1.5 text-sm text-gray-500 hover:text-gray-300 transition-colors mt-6"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  )
}