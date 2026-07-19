/**
 * useBackendStatus.js — Detects if Render backend is sleeping and polls until alive.
 * Render free tier sleeps after 15 mins of inactivity; first request takes ~30s.
 */

import { useState, useEffect, useRef } from 'react'
import { getHealth } from '../utils/api'

export function useBackendStatus() {
  const [status, setStatus] = useState('checking') // 'checking' | 'waking' | 'online'
  const pollRef = useRef(null)

  const check = async () => {
    try {
      await getHealth()
      setStatus('online')
      if (pollRef.current) clearInterval(pollRef.current)
    } catch {
      setStatus('waking')
    }
  }

  useEffect(() => {
    check()
    // Poll every 6s until online
    pollRef.current = setInterval(check, 6000)
    return () => clearInterval(pollRef.current)
  }, [])

  return status
}
