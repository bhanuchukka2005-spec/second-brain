import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Brain, Loader2, Eye, EyeOff } from 'lucide-react'
import { authApi } from '../api/client'
import { useAuthStore, useProviderStore, useSessionStore, useChatStore } from '../store'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { setAuth, user } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const tokenRes = await authApi.login(username, password)
      localStorage.setItem('token', tokenRes.data.access_token)
      const userRes = await authApi.me()

      // If a different user was previously logged in on this browser,
      // wipe their leftover provider/session/chat data before setting new auth.
      if (user && user.username !== userRes.data.username) {
        useProviderStore.getState().reset()
        useSessionStore.getState().reset()
        useChatStore.getState().resetAll()
      }

      setAuth(userRes.data, tokenRes.data.access_token)
      navigate('/chat')
    } catch {
      setError('Invalid username or password.')
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
          <h1 className="text-3xl font-bold text-white">AI Second Brain</h1>
          <p className="text-gray-400 mt-2 text-sm">Chat with your notes. Ace your exams.</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Sign in</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                placeholder="your_username"
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white text-sm placeholder-gray-500 focus:outline-none focus:border-brand-500 transition-colors pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl">
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full py-3 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 rounded-xl text-white font-medium transition-colors flex items-center justify-center gap-2 mt-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Don't have an account?{' '}
            <Link to="/register" className="text-brand-400 hover:text-brand-300 transition-colors">
              Register
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}