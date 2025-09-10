'use client'

import { useState, useEffect } from 'react'
import { AuthProvider } from './components/AuthProvider'
import Dashboard from './components/Dashboard'
import LoginForm from './components/LoginForm'

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('access_token')
    if (token) {
      setIsAuthenticated(true)
    }
    setIsLoading(false)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center enterprise-gradient">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  return (
    <AuthProvider>
      <main className="min-h-screen">
        {isAuthenticated ? (
          <Dashboard onLogout={() => setIsAuthenticated(false)} />
        ) : (
          <LoginForm onLogin={() => setIsAuthenticated(true)} />
        )}
      </main>
    </AuthProvider>
  )
}
