/**
 * App.jsx — Root router and layout for PRISM frontend.
 *
 * Library: react-router-dom (MIT) for client-side routing.
 * Wraps everything in PrismProvider and QueryClientProvider.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PrismProvider } from './context/PrismContext'
import { AuthProvider } from './context/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import Navbar from './components/Navbar'
import AuthPage from './pages/AuthPage'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Demo from './pages/Demo'
import About from './pages/About'
import { useBackendStatus } from './hooks/useBackendStatus'

// React Query client — 0 retries on error (LLM calls are expensive)
const queryClient = new QueryClient({
  defaultOptions: {
    mutations: { retry: 0 },
    queries: { retry: 1 },
  },
})

function WakeupBanner() {
  const status = useBackendStatus()
  if (status === 'online') return null
  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 9999,
      background: 'linear-gradient(90deg,#7c3aed,#2563eb)',
      color: '#fff', textAlign: 'center',
      padding: '10px 16px', fontSize: '14px', fontWeight: 500,
      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px'
    }}>
      <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite', fontSize: '16px' }}>⚙️</span>
      {status === 'checking'
        ? 'Connecting to PRISM backend…'
        : '⏳ Backend is waking up from sleep — this takes ~30 seconds. Please wait before logging in.'}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <PrismProvider>
            <BrowserRouter>
              <WakeupBanner />
              <Routes>
                <Route path="/" element={<AuthPage />} />
                <Route 
                  path="/chat" 
                  element={
                    <ProtectedRoute>
                      <Home />
                    </ProtectedRoute>
                  } 
                />
                <Route path="/about" element={<About />} />
                {/* Catch-all */}
                <Route path="*" element={<AuthPage />} />
              </Routes>
            </BrowserRouter>
          </PrismProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

