/**
 * ErrorBoundary.jsx — Catches and displays React rendering errors gracefully.
 *
 * Prevents the entire UI from crashing when a component fails.
 * Shows a clear error message with recovery options.
 */

import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] Caught error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-surface-DEFAULT flex items-center justify-center p-6">
          <div className="max-w-md w-full rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
            <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h2 className="font-display font-bold text-white text-xl mb-2">Something went wrong</h2>
            <p className="text-gray-400 text-sm mb-2">
              PRISM encountered an unexpected error in the UI.
            </p>
            <p className="text-red-400 text-xs font-mono bg-red-500/5 rounded p-2 mb-6">
              {this.state.error?.message || 'Unknown error'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2.5 rounded-xl bg-prism-600 hover:bg-prism-500 text-white text-sm font-medium transition-all"
            >
              Reload PRISM
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
