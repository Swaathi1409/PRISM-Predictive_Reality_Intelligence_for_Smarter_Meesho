/**
 * api.js — Axios instance and API functions for PRISM frontend.
 *
 * Library: axios (MIT License) — chosen for interceptors, automatic JSON
 * serialization, and consistent error handling across all requests.
 *
 * BACKEND_URL is read from Vite's env system (VITE_ prefix).
 * Falls back to localhost:8000 for local development.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s — LLM calls can take time
  headers: {
    'Content-Type': 'application/json',
  },
})

// ── Request interceptor: log outgoing requests in dev ─────────────────────
api.interceptors.request.use((config) => {
  if (import.meta.env.DEV) {
    console.log(`[PRISM API] ${config.method?.toUpperCase()} ${config.url}`)
  }
  return config
})

// ── Response interceptor: normalise errors ────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred. Please try again.'
    return Promise.reject(new Error(message))
  }
)

// ── API functions ──────────────────────────────────────────────────────────

/**
 * Runs a full PRISM analysis for the given user context.
 * @param {Object} params
 * @param {string} params.user_input - Natural language purchase context
 * @param {string} params.user_pincode - 6-digit delivery pincode
 * @param {number|null} params.budget - Max budget in INR, or null
 */
export async function analyzePrism({ user_input, user_pincode, budget }) {
  const response = await api.post('/api/prism/analyze', {
    user_input,
    user_pincode,
    budget: budget || null,
  })
  return response.data
}

/**
 * Fetches session history from the database.
 * @param {number} limit - Number of sessions to fetch (1–20)
 */
export async function getSessionHistory(limit = 5) {
  const response = await api.get('/api/sessions/history', { params: { limit } })
  return response.data
}

/**
 * Checks backend health status.
 */
export async function getHealth() {
  const response = await api.get('/api/health')
  return response.data
}
