import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Chat from './pages/Chat'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" />
}

function GuestRoute({ children }) {
  const { token } = useAuth()
  return !token ? children : <Navigate to="/" />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/signup" element={<GuestRoute><Signup /></GuestRoute>} />
      <Route path="/" element={<ProtectedRoute><Chat /></ProtectedRoute>} />
    </Routes>
  )
}
