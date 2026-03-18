import React, { createContext, useContext, useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import HeartRate from './pages/HeartRate'
import Sleep from './pages/Sleep'
import Habits from './pages/Habits'
import Correlations from './pages/Correlations'
import Insights from './pages/Insights'
import Settings from './pages/Settings'
import { auth } from './api'

export const AuthContext = createContext(null)

function PrivateRoute({ children }) {
  const { user, loading } = useContext(AuthContext)
  if (loading) return <div className="flex items-center justify-center h-screen text-gray-400">Загрузка...</div>
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      auth.me()
        .then(r => setUser(r.data))
        .catch(() => localStorage.removeItem('token'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, setUser, loading }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Dashboard />} />
            <Route path="heart" element={<HeartRate />} />
            <Route path="sleep" element={<Sleep />} />
            <Route path="habits" element={<Habits />} />
            <Route path="correlations" element={<Correlations />} />
            <Route path="insights" element={<Insights />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}
