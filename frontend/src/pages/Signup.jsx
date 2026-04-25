import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api/axios'

export default function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/signup', { name, email, password })
      setLoading(false)
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed')
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="auth-brand-content">
          <div className="auth-brand-icon">⚖️</div>
          <h1>Nepal Law AI</h1>
          <p>Get instant answers about the Constitution of Nepal with AI-powered legal research.</p>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          {success ? (
            <div className="auth-success">
              <div className="success-icon">✓</div>
              <h3>Account Created!</h3>
              <p>You have signed up successfully. You can now sign in to your account.</p>
              <button className="auth-btn" onClick={() => navigate('/login')}>
                Go to Sign In
              </button>
            </div>
          ) : (
            <>
              <div className="auth-card-header">
                <h2>Create account</h2>
                <p>Start exploring Nepal's constitutional law</p>
              </div>
              <form onSubmit={handleSubmit}>
                {error && <div className="auth-error">{error}</div>}
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Ram Bahadur"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <div className="password-wrapper">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Min 6 characters"
                      required
                      minLength={6}
                    />
                    <button type="button" className="eye-toggle" onClick={() => setShowPassword(!showPassword)}>
                      {showPassword ? (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                      ) : (
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                      )}
                    </button>
                  </div>
                </div>
                <button type="submit" className="auth-btn" disabled={loading}>
                  {loading ? 'Creating account…' : 'Create Account'}
                </button>
              </form>
              <p className="auth-switch">
                Already have an account? <Link to="/login">Sign In</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
