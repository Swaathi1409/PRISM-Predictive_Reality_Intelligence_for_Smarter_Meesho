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

// React Query client — 0 retries on error (LLM calls are expensive)
const queryClient = new QueryClient({
  defaultOptions: {
    mutations: { retry: 0 },
    queries: { retry: 1 },
  },
})

export default function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <PrismProvider>
            <BrowserRouter>
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
