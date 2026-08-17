import { useState, FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Brain, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { authApi } from '../api/client'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''
  const navigate = useNavigate()

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')

    if (!token) {
      setError('This reset link is missing its token. Please request a new one.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirm) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await authApi.resetPassword(token, password)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2500)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail || 'This reset link is invalid or has expired.')
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
          <h1 className="text-3xl font-bold text-white">Set a new password</h1>
          <p className="text-gray-400 mt-2 text-sm">Choose something you haven't used before.</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          {!token && (
            <div className="flex items-start gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl mb-4">
              <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
              <p className="text-sm text-red-400">
                No reset token found in this link.{' '}
                <Link to="/forgot-password" className="underline">Request a new one</Link>.
              </p>
            </div>
          )}

          {success ? (
            <div className="text-center py-4">
              <div className="w-14 h-14 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 className="w-7 h-7 text-green-400" />
              </div>
              <h2 className="text-lg font-semibold text-white mb-2">Password reset!</h2>
              <p className="text-sm text-gray-400">Redirecting you to sign in...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">New password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Min. 8 characters"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1.5">Confirm new password</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  placeholder="Repeat password"
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
                disabled={loading || !token || !password || !confirm}
                className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                {loading ? 'Resetting...' : 'Reset password'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}