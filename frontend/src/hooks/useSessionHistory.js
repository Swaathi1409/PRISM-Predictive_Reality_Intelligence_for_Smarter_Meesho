/**
 * useSessionHistory.js — Manages session history in localStorage.
 *
 * Stores the last 5 queries as chips so users can quickly re-run them.
 * Uses localStorage so history persists across page refreshes.
 */

import { useState, useCallback } from 'react'

const STORAGE_KEY = 'prism_session_history'
const MAX_SESSIONS = 5

export function useSessionHistory() {
  const [history, setHistory] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  const addToHistory = useCallback((query) => {
    setHistory((prev) => {
      // Avoid duplicates
      const filtered = prev.filter((item) => item.user_input !== query.user_input)
      const updated = [query, ...filtered].slice(0, MAX_SESSIONS)
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
      } catch {
        // localStorage quota exceeded — ignore
      }
      return updated
    })
  }, [])

  const clearHistory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setHistory([])
  }, [])

  return { history, addToHistory, clearHistory }
}
