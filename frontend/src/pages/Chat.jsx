import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'
import Sidebar from '../components/Sidebar'
import ChatMessage from '../components/ChatMessage'
import LoadingDots from '../components/LoadingDots'

export default function Chat() {
  const { user, logout } = useAuth()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [showLogoutModal, setShowLogoutModal] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    fetchSessions()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const fetchSessions = async () => {
    try {
      const { data } = await api.get('/sessions')
      setSessions(data)
    } catch (e) {
      console.error('Failed to load sessions')
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const payload = { question }
      if (activeSessionId) {
        payload.session_id = activeSessionId
      }
      const { data } = await api.post('/ask', payload)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          summary: data.summary,
          legal_references: data.legal_references,
          id: data.id
        }
      ])
      // If this was a new chat, set the active session
      if (!activeSessionId && data.session_id) {
        setActiveSessionId(data.session_id)
      }
      // Refresh sessions list to get new/updated titles
      fetchSessions()
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', summary: err.response?.data?.error || 'Something went wrong. Please try again.', legal_references: '' }
      ])
    } finally {
      setLoading(false)
    }
  }

  const loadSession = async (session) => {
    try {
      const { data } = await api.get(`/sessions/${session.id}/messages`)
      const msgs = data.map((m) => {
        if (m.role === 'user') {
          return { role: 'user', content: m.content }
        }
        return { role: 'assistant', summary: m.summary, legal_references: m.legal_references, id: m.id }
      })
      setMessages(msgs)
      setActiveSessionId(session.id)
    } catch (e) {
      console.error('Failed to load session messages')
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setActiveSessionId(null)
  }

  const handleDeleteSession = async (id) => {
    try {
      await api.delete(`/sessions/${id}`)
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (activeSessionId === id) {
        setMessages([])
        setActiveSessionId(null)
      }
    } catch (e) {
      console.error('Failed to delete session')
    }
  }

  const handleClearAll = async () => {
    try {
      await api.delete('/sessions')
      setSessions([])
      setMessages([])
      setActiveSessionId(null)
    } catch (e) {
      console.error('Failed to clear sessions')
    }
  }

  const handleChipClick = (text) => {
    setInput(text)
  }

  const handleLogoutRequest = () => {
    setShowLogoutModal(true)
  }

  const handleLogoutConfirm = () => {
    setShowLogoutModal(false)
    setSigningOut(true)
    setTimeout(() => {
      logout()
    }, 2500)
  }

  return (
    <div className="chat-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        open={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        onSelect={loadSession}
        onNewChat={handleNewChat}
        onDelete={handleDeleteSession}
        onClearAll={handleClearAll}
        user={user}
        onLogout={handleLogoutRequest}
      />

      <main className={`chat-main ${sidebarOpen ? '' : 'full'}`}>
        <div className="chat-messages">
          {messages.length === 0 && !loading && (
            <div className="chat-welcome">
              <div className="welcome-icon">⚖️</div>
              <h2>Nepal Law AI Assistant</h2>
              <p>Ask anything about the Constitution of Nepal</p>
              <div className="welcome-chips">
                <button className="welcome-chip" onClick={() => handleChipClick('What are the fundamental rights in Nepal\'s constitution?')}>Fundamental Rights</button>
                <button className="welcome-chip" onClick={() => handleChipClick('Explain the structure of Nepal\'s government')}>Government Structure</button>
                <button className="welcome-chip" onClick={() => handleChipClick('What does the constitution say about citizenship?')}>Citizenship Laws</button>
                <button className="welcome-chip" onClick={() => handleChipClick('What are the directive principles of Nepal?')}>Directive Principles</button>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-bubble assistant-bubble">
                <LoadingDots />
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <form className="chat-input-bar" onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about Nepal Law..."
            disabled={loading}
            maxLength={2000}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13" /><path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          </button>
        </form>
      </main>

      {showLogoutModal && (
        <div className="modal-overlay" onClick={() => setShowLogoutModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-icon">👋</div>
            <h3>Sign out?</h3>
            <p>Are you sure you want to sign out of your account?</p>
            <div className="modal-actions">
              <button className="modal-btn-cancel" onClick={() => setShowLogoutModal(false)}>Cancel</button>
              <button className="modal-btn-confirm" onClick={handleLogoutConfirm}>Sign Out</button>
            </div>
          </div>
        </div>
      )}

      {signingOut && (
        <div className="transition-overlay">
          <div className="transition-spinner" />
          <span className="transition-text">Signing out…</span>
        </div>
      )}
    </div>
  )
}
