import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { SessionPage } from './pages/SessionPage'
import { AppLayout } from './components/layout/AppLayout'
import { AuthGuard } from './components/layout/AuthGuard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login"           element={<LoginPage />} />
        <Route path="/register"        element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password"  element={<ResetPasswordPage />} />

        {/* Protected routes */}
        <Route element={<AuthGuard />}>
          <Route element={<AppLayout />}>
            <Route index          element={<Navigate to="/chat" replace />} />
            <Route path="/chat"        element={<SessionPage />} />
            <Route path="/quiz"        element={<SessionPage />} />
            <Route path="/flashcards"  element={<SessionPage />} />
            <Route path="/dashboard"   element={<SessionPage />} />
            <Route path="/concept-map" element={<SessionPage />} />
            <Route path="/summarize"   element={<SessionPage />} />
            <Route path="/compare"     element={<SessionPage />} />
          </Route>
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  )
}